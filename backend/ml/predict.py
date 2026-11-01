import os
import ipaddress
import joblib
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRAINED_MODELS_DIR = os.path.join(BASE_DIR, "trained_models")


def is_broadcast_or_multicast_address(ip_str: Optional[str]) -> bool:
    """
    Determine whether an IPv4 or IPv6 address is a broadcast or multicast address.
    Examples: 255.255.255.255, 192.168.31.255 (subnet directed broadcast),
    224.0.0.251 (mDNS), 239.255.255.250 (SSDP), ff02::1 (IPv6 multicast).
    """
    if not ip_str:
        return False
    ip_clean = str(ip_str).strip()
    if ip_clean == "255.255.255.255":
        return True
    # Check standard /24 subnet directed broadcast suffix (.255) on private/LAN IPv4 ranges
    if ip_clean.endswith(".255") and ip_clean.count(".") == 3:
        return True
    try:
        addr = ipaddress.ip_address(ip_clean)
        if addr.is_multicast:
            return True
    except ValueError:
        pass
    return False


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
            if hasattr(self.rf_model, "n_jobs"):
                self.rf_model.n_jobs = 1
        if os.path.exists(best_path):
            self.model = joblib.load(best_path)
            if hasattr(self.model, "n_jobs"):
                self.model.n_jobs = 1
        else:
            self.model = self.rf_model or self.dt_model

        if os.path.exists(scaler_path):
            self.scaler = joblib.load(scaler_path)
        if os.path.exists(encoders_path):
            self.encoders = joblib.load(encoders_path)
        if os.path.exists(features_path):
            self.feature_columns = joblib.load(features_path)

    def predict(
        self,
        feature_dict: Dict[str, Any],
        selected_model_name: str = "best",
        source_ip: Optional[str] = None,
        destination_ip: Optional[str] = None,
    ) -> Dict[str, Any]:
        if self.model is None or self.scaler is None:
            return self._heuristic_predict(feature_dict)

        # Build feature DataFrame
        df_input = pd.DataFrame([feature_dict])

        # Categorical encoding with safe fallback
        for col in ["protocol_type", "service", "flag"]:
            if col in df_input.columns and self.encoders and col in self.encoders:
                le = self.encoders[col]
                val_str = str(df_input[col].iloc[0])
                if val_str in le.classes_:
                    df_input[col] = le.transform([val_str])[0]
                else:
                    # Fallback to 'other' for unseen service, 'SF' for flag, 'tcp' for protocol
                    fallback_map = {"service": "other", "flag": "SF", "protocol_type": "tcp"}
                    fb = fallback_map.get(col, "")
                    df_input[col] = le.transform([fb])[0] if fb in le.classes_ else 0

        # Ensure 20 required features in exact trained column order
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

        # Calculate model prediction and probability confidence in a single pass
        if hasattr(active_model, "predict_proba"):
            probs = active_model.predict_proba(X_scaled)[0]
            classes = list(active_model.classes_)
            class_idx = int(np.argmax(probs))
            pred_class = str(classes[class_idx])
            confidence = float(probs[class_idx])
        else:
            pred_class = str(active_model.predict(X_scaled)[0])
            confidence = 0.95

        # Extract key feature values for validation and evidence generation
        count = int(feature_dict.get("count", 1))
        srv_count = int(feature_dict.get("srv_count", 1))
        serror_rate = float(feature_dict.get("serror_rate", 0.0))
        dst_host_serror_rate = float(feature_dict.get("dst_host_serror_rate", 0.0))
        dst_host_rerror_rate = float(feature_dict.get("dst_host_rerror_rate", 0.0))
        diff_srv_rate = float(feature_dict.get("diff_srv_rate", 0.0))
        dst_host_diff_srv_rate = float(feature_dict.get("dst_host_diff_srv_rate", 0.0))
        dst_host_same_src_port_rate = float(feature_dict.get("dst_host_same_src_port_rate", 0.0))
        src_bytes = int(feature_dict.get("src_bytes", 0))
        dst_bytes = int(feature_dict.get("dst_bytes", 0))
        flag = str(feature_dict.get("flag", "SF"))
        protocol_type = str(feature_dict.get("protocol_type", "tcp")).lower()
        service = str(feature_dict.get("service", "other"))
        duration = float(feature_dict.get("duration", 0.0))

        dst_ip_str = destination_ip or feature_dict.get("destination_ip")
        is_bcast = bool(feature_dict.get("is_broadcast", False) or is_broadcast_or_multicast_address(dst_ip_str))

        evidence: List[str] = []
        validation_status = "NORMAL"
        attack_type = "Normal"

        # Rule: Never classify broadcast/multicast traffic as an attack solely because
        # its destination is a broadcast address (where dst_bytes == 0 is normal).
        if is_bcast and pred_class == "ATTACK":
            has_broadcast_flood = (count > 30 or serror_rate > 0.5)
            if not has_broadcast_flood:
                pred_class = "NORMAL"
                attack_type = "Normal"
                validation_status = "VERIFIED_BENIGN_BROADCAST"
                evidence.append(
                    f"Destination {dst_ip_str or 'broadcast'} is a local broadcast/multicast address; "
                    f"one-way UDP/ICMP payload (dst_bytes=0, count={count}) is normal broadcast behavior."
                )

        if pred_class == "ATTACK":
            # Build transparent evidence explaining why the flow was flagged
            has_strong_dos_evidence = (
                count >= 50
                or serror_rate >= 0.5
                or dst_host_serror_rate >= 0.5
                or flag in ("S0", "S1", "S2", "S3")
            )
            has_strong_probe_evidence = (
                flag in ("REJ", "RSTO", "RSTR", "RSTOS0", "SH")
                or diff_srv_rate >= 0.5
                or dst_host_diff_srv_rate >= 0.5
                or dst_host_rerror_rate >= 0.4
                or (dst_bytes == 0 and not is_bcast and count >= 10)
                or (dst_bytes == 0 and not is_bcast and dst_host_same_src_port_rate >= 0.5 and count >= 5)
            )

            if has_strong_dos_evidence and (count >= 50 or serror_rate >= 0.4 or flag == "S0"):
                attack_type = "DoS"
                if flag in ("S0", "S1", "S2", "S3"):
                    evidence.append(f"TCP connection flag={flag} indicates unanswered SYN connection attempts.")
                if serror_rate >= 0.4 or dst_host_serror_rate >= 0.4:
                    evidence.append(
                        f"Elevated SYN error rate (serror_rate={serror_rate:.2f}, "
                        f"dst_host_serror_rate={dst_host_serror_rate:.2f})."
                    )
                if count >= 50:
                    evidence.append(f"High connection volume to destination within 2s window (count={count}, srv_count={srv_count}).")
            elif has_strong_probe_evidence:
                attack_type = "Probe"
                if flag in ("REJ", "RSTO", "RSTR", "RSTOS0"):
                    evidence.append(f"Connection rejected/reset by target host (flag={flag}, dst_host_rerror_rate={dst_host_rerror_rate:.2f}).")
                if diff_srv_rate >= 0.5 or dst_host_diff_srv_rate >= 0.5:
                    evidence.append(
                        f"Multiple distinct services probed on target host (diff_srv_rate={diff_srv_rate:.2f}, "
                        f"dst_host_diff_srv_rate={dst_host_diff_srv_rate:.2f})."
                    )
                if dst_bytes == 0 and not is_bcast:
                    evidence.append(f"Unanswered unicast probe payload (src_bytes={src_bytes}, dst_bytes=0, count={count}).")
                if dst_host_same_src_port_rate >= 0.5:
                    evidence.append(f"Repeated connections originating from identical source port (dst_host_same_src_port_rate={dst_host_same_src_port_rate:.2f}).")
            elif dst_bytes == 0 and not is_bcast:
                attack_type = "Probe"
                evidence.append(f"One-way flow with zero response bytes (src_bytes={src_bytes}, dst_bytes=0, service={service}).")
            else:
                attack_type = "R2L"
                evidence.append(
                    f"Application flow feature profile matched NSL-KDD R2L decision boundary "
                    f"(service={service}, duration={duration:.2f}s, src_bytes={src_bytes}, dst_bytes={dst_bytes})."
                )

            # Determine verification state based on confidence and concrete behavioral indicators
            has_concrete_indicator = has_strong_dos_evidence or has_strong_probe_evidence
            if confidence < 0.72 or not has_concrete_indicator:
                validation_status = "UNVERIFIED"
                evidence.append(
                    f"Validation State: UNVERIFIED / NEEDS INVESTIGATION — Model confidence is {confidence*100:.1f}% "
                    f"({'below 72% verification threshold' if confidence < 0.72 else 'without corroborating SYN/RST/scan error rates'}). "
                    f"Not a confirmed attack; analyst review recommended."
                )
            else:
                validation_status = "VERIFIED_SUSPICIOUS"
                evidence.append(
                    f"Validation State: VERIFIED SUSPICIOUS — Model confidence {confidence*100:.1f}% corroborated by "
                    f"flow anomaly indicators ({attack_type} pattern)."
                )
        else:
            if not evidence:
                evidence.append(
                    f"Benign traffic profile (protocol={protocol_type}, service={service}, flag={flag}, "
                    f"src_bytes={src_bytes}, dst_bytes={dst_bytes}, confidence={confidence*100:.1f}%)."
                )

        return {
            "prediction": pred_class,
            "attack_type": attack_type,
            "confidence": round(confidence, 4),
            "model_name": model_used,
            "validation_status": validation_status,
            "is_broadcast": is_bcast,
            "evidence": evidence,
        }

    def _heuristic_predict(self, feature_dict):
        count = feature_dict.get("count", 0)
        serror_rate = feature_dict.get("serror_rate", 0.0)
        if count > 150 or serror_rate > 0.5:
            return {
                "prediction": "ATTACK",
                "attack_type": "DoS",
                "confidence": 0.92,
                "model_name": "HeuristicFallback",
                "validation_status": "VERIFIED_SUSPICIOUS",
                "is_broadcast": False,
                "evidence": [f"Heuristic fallback triggered: count={count}, serror_rate={serror_rate}"],
            }
        return {
            "prediction": "NORMAL",
            "attack_type": "Normal",
            "confidence": 0.97,
            "model_name": "HeuristicFallback",
            "validation_status": "NORMAL",
            "is_broadcast": False,
            "evidence": ["Heuristic fallback: normal flow metrics."],
        }
