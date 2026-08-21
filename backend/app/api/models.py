import os
import json
from fastapi import APIRouter, HTTPException
from backend.app.config import settings

router = APIRouter(prefix="/models", tags=["ML Models"])

@router.get("/metrics")
def get_model_metrics():
    metrics_path = os.path.join(settings.MODEL_DIR, "metrics.json")
    if not os.path.exists(metrics_path):
        raise HTTPException(status_code=404, detail="Model metrics file not found. Please train models first.")
    
    with open(metrics_path, "r") as f:
        data = json.load(f)
    return data

@router.get("/features")
def get_model_features():
    metrics_path = os.path.join(settings.MODEL_DIR, "metrics.json")
    if not os.path.exists(metrics_path):
        return {"features": [], "feature_importance": {}}
    
    with open(metrics_path, "r") as f:
        data = json.load(f)
    return {
        "features": data.get("features", []),
        "feature_importance": data.get("feature_importance", {})
    }
