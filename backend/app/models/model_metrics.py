from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime
from backend.app.database import Base

class ModelMetrics(Base):
    __tablename__ = "model_metrics"

    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String(50), nullable=False)
    version = Column(String(20), default="1.0.0")
    accuracy = Column(Float, nullable=False)
    precision = Column(Float, nullable=False)
    recall = Column(Float, nullable=False)
    f1_score = Column(Float, nullable=False)
    training_date = Column(DateTime, default=datetime.utcnow)
    dataset_name = Column(String(50), default="NSL-KDD")
    feature_count = Column(Integer, default=20)
