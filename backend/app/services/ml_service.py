from typing import Optional
from backend.ml.predict import PredictionEngine

class MLService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MLService, cls).__new__(cls)
            cls._instance.engine = PredictionEngine()
        return cls._instance

    def predict_traffic(
        self,
        feature_dict: dict,
        model_name: str = "best",
        source_ip: Optional[str] = None,
        destination_ip: Optional[str] = None,
    ) -> dict:
        return self.engine.predict(
            feature_dict,
            selected_model_name=model_name,
            source_ip=source_ip,
            destination_ip=destination_ip,
        )

ml_service = MLService()
