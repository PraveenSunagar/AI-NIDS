import os
from backend.ml.predict import PredictionEngine

class MLService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MLService, cls).__new__(cls)
            cls._instance.engine = PredictionEngine()
        return cls._instance

    def predict_traffic(self, feature_dict: dict, model_name: str = "best") -> dict:
        return self.engine.predict(feature_dict, selected_model_name=model_name)

ml_service = MLService()
