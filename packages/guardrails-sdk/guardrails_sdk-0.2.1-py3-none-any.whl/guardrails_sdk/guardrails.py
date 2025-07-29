import os
import asyncio
from pydantic import BaseModel
from typing import List, Dict, Optional, Literal
from uuid import uuid4
import threading

from guardrails_sdk.pii.pii import analyze_and_mask_text
from guardrails_sdk.toxicity.toxic_bert import detect_toxicity
from guardrails_sdk.prompt_secure.prompt_break import classify_prompt_injection
from guardrails_sdk.compitator_banned_words.block_words import moderate_text
from guardrails_sdk.log_guardrails.log_anomaly import AnomalyStorage


# === Request Models ===

class ToxiRequest(BaseModel):
    content: str
    treshold: float = 0.5


class Prompt(BaseModel):
    content: str


class TransformRequest(BaseModel):
    content: str
    guardrails: List[str]
    treshold: float = 0.5
    custom_entities: Optional[List[Dict]] = None
    action: Optional[Literal["mask", "block"]] = None
    compitator_loc: Optional[str] = None
    block_loc: Optional[str] = None


class Compitator(BaseModel):
    content: str
    action: Literal["mask", "block"]
    compitator_loc: Optional[str] = None
    block_loc: Optional[str] = None


# === Guardrails Client ===

class GuardrailsClient:
    def __init__(self, enable_logging: bool = False, dsn: Optional[str] = None):
        self.logger: Optional[AnomalyStorage] = (
            AnomalyStorage(dsn=dsn) if enable_logging else None
        )

    def init(self):
        if self.logger:
            self.logger.init()

    def _generate_request_id(self, prefix: str) -> str:
        return f"{prefix}-{uuid4().hex[:8]}"

    def _log_async(self, anomaly_type: str, details: Dict[str, any]):
        if self.logger:
            request_id = self._generate_request_id(anomaly_type)
            threat = threading.Thread(
                target=self.logger.store_anomaly,
                args=(request_id, anomaly_type, details),
                daemon=True
            )
            threat.start()
            threat.join()  # Wait for the thread to finish

    async def validate_content(self, request: ToxiRequest):
        result = await detect_toxicity(request.content, request.treshold)
        if result.get("toxic", False):
            self._log_async("toxicity", result)
        return result

    async def transform_content(self, request: TransformRequest):
        result = await analyze_and_mask_text(
            request.content,
            request.guardrails,
            request.custom_entities,
            request.treshold
        )
        if result.get("pii_found"):
            self._log_async("pii", result)
        return result

    async def prompt_injection(self, request: Prompt):
        result = await classify_prompt_injection(request.content)
        if result.get("is_prompt_injection", False):
            self._log_async("prompt_injection", result)
        return result

    async def compitator_banned(self, request: Compitator):
        result = await moderate_text(
            text=request.content,
            banned_words_file=request.block_loc,
            competitor_words_file=request.compitator_loc,
            action=request.action
        )
        if result.get("action_taken"):
            self._log_async("banned_words", result)
        return result

    async def run_all_guardrails(self, request: TransformRequest):
        pii_result, toxicity_result, prompt_result, moderate_result = await asyncio.gather(
            analyze_and_mask_text(
                request.content,
                request.guardrails,
                request.custom_entities,
                request.treshold
            ),
            detect_toxicity(request.content, request.treshold),
            classify_prompt_injection(request.content),
            moderate_text(
                request.content,
                request.block_loc,
                request.compitator_loc,
                request.action
            )
        )

        result_summary = {
            "pii": pii_result,
            "toxicity": toxicity_result,
            "prompt_injection": prompt_result,
            "moderate_result": moderate_result
        }

        # Collect triggered anomalies
        triggered = []
        if pii_result.get("action_taken") or pii_result.get("pii_found"):
            triggered.append("pii")
        if toxicity_result.get("toxic", False):
            triggered.append("toxicity")
        if prompt_result.get("is_prompt_injection", False):
            triggered.append("prompt_injection")
        if moderate_result.get("action_taken"):
            triggered.append("banned_words")

        if triggered:
            self._log_async(
                anomaly_type=",".join(triggered),  # or store as a JSON array
                details={
                    "anomalies_detected": triggered,
                    "summary": result_summary
                }
            )

        return result_summary
