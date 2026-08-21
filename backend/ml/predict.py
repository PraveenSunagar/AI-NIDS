import os
import joblib
import pandas as pd
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRAINED_MODELS_DIR = os.path.join(BASE_DIR, "trained_models")

class PredictionEngine:
    def __init__(self, model_name="best"):
        self.model_name = model_name
        self.model = None
        self.dt_model = None
        self.rf_model = None
        self.scaler = None
        self.encoders = None
        self.feature_columns = []
        self._load_artifacts()

    def _load_artifacts(self):
        best_path = os.path.join(TRAINED_MODELS_DIR, "best_model.pkl")
        dt_path = os.path.join(TRAINED_MODELS_DIR, "decision_tree.pkl")
        rf_path = os.path.join(TRAINED_MODELS_DIR, "random_forest.pkl")
        scaler_path = os.path.join(TRAINED_MODELS_DIR, "scaler.pkl")
        encoders_path = os.path.join(TRAINED_MODELS_DIR, "encoder.pkl")
        features_path = os.path.join(TRAINED_MODELS_DIR, "feature_columns.pkl")

        if os.path.exists(dt_path):
            self.dt_model = joblib.load(dt_path)
        if os.path.exists(rf_path):
            self.rf_model = joblib.load(rf_path)
        if os.path.exists(best_path):
            self.model = joblib.load(best_path)
        else:
            self.model = self.rf_model or self.dt_model

        if os.path.exists(scaler_path):
            self.scaler = joblib.load(scaler_path)
        if os.path.exists(encoders_path):
            self.encoders = joblib.load(encoders_path)
        if os.path.exists(features_path):
            self.feature_columns = joblib.load(features_path)

    def predict(self, feature_dict, selected_model_name="best"):
        if self.model is None or self.scaler is None:
            # Fallback rule-based heuristic prediction if artifacts not yet trained
            return self._heuristic_predict(feature_dict)

        # Build feature DataFrame
        df_input = pd.DataFrame([feature_dict])

        # Categorical encoding
        for col in ["protocol_type", "service", "flag"]:
            if col in df_input.columns and self.encoders and col in self.encoders:
                le = self.encoders[col]
                val_str = str(df_input[col].iloc[0])
                if val_str in le.classes_:
                    df_input[col] = le.transform([val_str])[0]
                else:
                    df_input[col] = 0

        # Ensure 20 required features
        for col in self.feature_columns:
            if col not in df_input.columns:
                df_input[col] = 0.0

        df_input = df_input[self.feature_columns]

        # Scale features
        X_scaled = self.scaler.transform(df_input)

        # Select model
        active_model = self.model
        model_used = "BestModel"
        if selected_model_name.lower() == "decisiontree" and self.dt_model:
            active_model = self.dt_model
            model_used = "DecisionTree"
        elif selected_model_name.lower() == "randomforest" and self.rf_model:
            active_model = self.rf_model
            model_used = "RandomForest"

        pred_class = active_model.predict(X_scaled)[0]
        
        # Calculate confidence
        if hasattr(active_model, "predict_proba"):
            probs = active_model.predict_proba(X_scaled)[0]
            classes = list(active_model.classes_)
            class_idx = classes.index(pred_class)
            confidence = float(probs[class_idx])
        else:
            confidence = 0.95

        # Infer attack type heuristic from features if ATTACK
        attack_type = "Normal"
        if pred_class == "ATTACK":
            count = feature_dict.get("count", 0)
            serror_rate = feature_dict.get("serror_rate", 0)
            dst_bytes = feature_dict.get("dst_bytes", 0)
            if count > 100 or serror_rate > 0.5:
                attack_type = "DoS"
            elif dst_bytes == 0:
                attack_type = "Probe"
            else:
                attack_type = "R2L"

        return {
            "prediction": str(pred_class),
            "attack_type": attack_type,
            "confidence": round(confidence, 4),
            "model_name": model_used
        }

    def _heuristic_predict(self, feature_dict):
        count = feature_dict.get("count", 0)
        serror_rate = feature_dict.get("serror_rate", 0.0)
        if count > 150 or serror_rate > 0.5:
            return {
                "prediction": "ATTACK",
                "attack_type": "DoS",
                "confidence": 0.92,
                "model_name": "HeuristicFallback"
            }
        return {
            "prediction": "NORMAL",
            "attack_type": "Normal",
            "confidence": 0.97,
            "model_name": "HeuristicFallback"
        }
