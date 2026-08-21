from typing import Dict, Any, List, Optional
from pydantic import BaseModel

class ModelMetricsResponse(BaseModel):
    dataset_name: str
    feature_count: int
    training_date: str
    selected_model: str
    features: List[str]
    feature_importance: Dict[str, float]
    models: Dict[str, Any]

class FeatureImportanceItem(BaseModel):
    feature: str
    importance: float
