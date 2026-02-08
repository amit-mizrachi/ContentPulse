from datetime import datetime

from sqlalchemy import Column, Integer, String, Float, Text, DateTime, JSON, Index

from src.services.persistence.models.base import Base


class RequestHistory(Base):
    __tablename__ = "request_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    request_id = Column(String(36), unique=True, nullable=False, index=True)
    prompt = Column(Text, nullable=False)
    target_model = Column(String(100), nullable=False)
    judge_model = Column(String(100), nullable=False)
    inference_response = Column(Text, nullable=True)
    inference_latency_ms = Column(Float, nullable=True)
    inference_tokens = Column(Integer, nullable=True)
    judge_score = Column(Float, nullable=True)
    judge_reasoning = Column(Text, nullable=True)
    judge_categories = Column(JSON, nullable=True)
    judge_latency_ms = Column(Float, nullable=True)
    status = Column(String(20), nullable=False)  # Completed, Failed
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_status", "status"),
        Index("idx_created_at", "created_at"),
    )
