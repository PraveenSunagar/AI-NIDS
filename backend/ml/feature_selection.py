import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier

# Standard top 20 features for NSL-KDD intrusion detection
DEFAULT_20_FEATURES = [
    "duration",
    "protocol_type",
    "service",
    "flag",
    "src_bytes",
    "dst_bytes",
    "logged_in",
    "count",
    "srv_count",
    "serror_rate",
    "same_srv_rate",
    "diff_srv_rate",
    "dst_host_count",
    "dst_host_srv_count",
    "dst_host_same_srv_rate",
    "dst_host_diff_srv_rate",
    "dst_host_same_src_port_rate",
    "dst_host_srv_diff_host_rate",
    "dst_host_serror_rate",
    "dst_host_srv_serror_rate"
]

def select_top_features(df_features, df_labels, num_features=20):
    """
    Dynamically select top N important features using a Random Forest feature importance selector.
    """
    rf = RandomForestClassifier(n_estimators=50, random_state=42)
    rf.fit(df_features, df_labels)
    importances = rf.feature_importances_
    
    indices = np.argsort(importances)[::-1]
    top_indices = indices[:num_features]
    selected_cols = [df_features.columns[i] for i in top_indices]
    
    feature_importance_dict = {
        col: float(importances[i])
        for i, col in enumerate(df_features.columns)
    }
    
    return selected_cols, feature_importance_dict
