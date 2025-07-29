import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from sqlalchemy import create_engine, Column, String, Text, DateTime, Integer
from sqlalchemy.orm import sessionmaker, declarative_base

# === Logger Setup ===
logger = logging.getLogger("anomaly_logger")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

# === SQLAlchemy Base and Table ===
Base = declarative_base()


class Anomaly(Base):
    __tablename__ = "anomalies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    request_id = Column(String(128), nullable=False)
    anomaly_type = Column(String(64), nullable=False)
    details = Column(Text, nullable=True)

# === Synchronous Anomaly Storage ===


class AnomalyStorage:
    def __init__(self, dsn: Optional[str] = None, env_var: str = "ANOMALY_DB_DSN"):
        self.dsn = dsn or os.getenv(env_var)
        if not self.dsn:
            raise ValueError(
                f"DSN not provided and env var '{env_var}' not set.")

        self.engine = create_engine(self.dsn, echo=False)
        self.Session = sessionmaker(bind=self.engine)

    def init(self):
        """Create table if it doesn't exist."""
        Base.metadata.create_all(self.engine)
        logger.info("[AnomalyLogger] Database initialized.")

    def store_anomaly(
        self,
        request_id: str,
        anomaly_type: str,
        details: Dict[str, Any]
    ) -> None:
        logger.info(
            f"[AnomalyLogger] Preparing to store anomaly for {request_id}")
        anomaly = Anomaly(
            request_id=request_id,
            anomaly_type=anomaly_type,
            details=json.dumps(details, default=str),
        )

        session = self.Session()
        try:
            session.add(anomaly)
            session.commit()

        except Exception as e:
            logger.error(
                f"[AnomalyLogger] Failed to store anomaly for {request_id}: {e}", exc_info=True)
            session.rollback()

        finally:
            session.close()
