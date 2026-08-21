import os
import json
import joblib
import numpy as np
import pandas as pd
from datetime import datetime

from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier

from preprocess import Preprocessor
from feature_selection import select_top_features, DEFAULT_20_FEATURES
from evaluate import evaluate_model

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DATA_DIR = os.path.join(BASE_DIR, "data", "raw")
TRAINED_MODELS_DIR = os.path.join(BASE_DIR, "trained_models")

def train_and_evaluate():
    print("==================================================")
    print("      AI-NIDS ML TRAINING PIPELINE (NSL-KDD)      ")
    print("==================================================")
    
    os.makedirs(TRAINED_MODELS_DIR, exist_ok=True)
    
    train_file = os.path.join(RAW_DATA_DIR, "KDDTrain+.txt")
    test_file = os.path.join(RAW_DATA_DIR, "KDDTest+.txt")
    
    preprocessor = Preprocessor()
    
    print("\n1. Loading NSL-KDD raw datasets...")
    df_train = preprocessor.load_data(train_file)
    df_test = preprocessor.load_data(test_file)
    
    print(f"   Train samples: {len(df_train)}, Test samples: {len(df_test)}")
    
    print("\n2. Preprocessing & Feature Selection...")
    # Preprocess training data with initial encode to find 20 top features
    X_train_raw_scaled, y_train_binary, y_train_attack, df_train_encoded = preprocessor.fit_transform(df_train)
    
    selected_20_features, feature_importances = select_top_features(
        df_train_encoded.drop(columns=["label", "difficulty_level"], errors="ignore"),
        y_train_binary,
        num_features=20
    )
    
    print(f"   Selected 20 Discriminative Features:\n   {selected_20_features}")
    
    # Re-fit preprocessor restricted to selected 20 features
    preprocessor = Preprocessor()
    X_train, y_train, y_train_attacks, _ = preprocessor.fit_transform(df_train, selected_features=selected_20_features)
    X_test = preprocessor.transform(df_test[selected_20_features])
    y_test, _ = preprocessor.transform_labels(df_test["label"].values)
    
    print(f"\n3. Training Decision Tree Classifier...")
    dt_clf = DecisionTreeClassifier(max_depth=12, random_state=42)
    dt_clf.fit(X_train, y_train)
    dt_metrics = evaluate_model(dt_clf, X_test, y_test)
    print(f"   Decision Tree Metrics:")
    print(f"     - Accuracy:  {dt_metrics['accuracy'] * 100:.2f}%")
    print(f"     - Precision: {dt_metrics['precision'] * 100:.2f}%")
    print(f"     - Recall:    {dt_metrics['recall'] * 100:.2f}%")
    print(f"     - F1-Score:  {dt_metrics['f1_score'] * 100:.2f}%")
    print(f"     - Confusion Matrix: {dt_metrics['confusion_matrix']}")

    print(f"\n4. Training Random Forest Classifier...")
    rf_clf = RandomForestClassifier(n_estimators=100, max_depth=15, random_state=42, n_jobs=-1)
    rf_clf.fit(X_train, y_train)
    rf_metrics = evaluate_model(rf_clf, X_test, y_test)
    print(f"   Random Forest Metrics:")
    print(f"     - Accuracy:  {rf_metrics['accuracy'] * 100:.2f}%")
    print(f"     - Precision: {rf_metrics['precision'] * 100:.2f}%")
    print(f"     - Recall:    {rf_metrics['recall'] * 100:.2f}%")
    print(f"     - F1-Score:  {rf_metrics['f1_score'] * 100:.2f}%")
    print(f"     - Confusion Matrix: {rf_metrics['confusion_matrix']}")

    # Select best model based on F1-score
    if rf_metrics["f1_score"] >= dt_metrics["f1_score"]:
        best_model_name = "RandomForest"
        best_model = rf_clf
        best_metrics = rf_metrics
    else:
        best_model_name = "DecisionTree"
        best_model = dt_clf
        best_metrics = dt_metrics

    print(f"\n5. Best Performing Model Selected: {best_model_name}")

    print("\n6. Saving Model Artifacts...")
    dt_path = os.path.join(TRAINED_MODELS_DIR, "decision_tree.pkl")
    rf_path = os.path.join(TRAINED_MODELS_DIR, "random_forest.pkl")
    best_path = os.path.join(TRAINED_MODELS_DIR, "best_model.pkl")
    scaler_path = os.path.join(TRAINED_MODELS_DIR, "scaler.pkl")
    encoders_path = os.path.join(TRAINED_MODELS_DIR, "encoder.pkl")
    features_path = os.path.join(TRAINED_MODELS_DIR, "feature_columns.pkl")
    metrics_path = os.path.join(TRAINED_MODELS_DIR, "metrics.json")

    joblib.dump(dt_clf, dt_path)
    joblib.dump(rf_clf, rf_path)
    joblib.dump(best_model, best_path)
    joblib.dump(preprocessor.scaler, scaler_path)
    joblib.dump(preprocessor.encoders, encoders_path)
    joblib.dump(selected_20_features, features_path)

    all_metrics = {
        "dataset_name": "NSL-KDD",
        "feature_count": len(selected_20_features),
        "training_date": datetime.now().isoformat(),
        "selected_model": best_model_name,
        "features": selected_20_features,
        "feature_importance": {
            feat: round(float(imp), 4)
            for feat, imp in zip(selected_20_features, rf_clf.feature_importances_)
        },
        "models": {
            "DecisionTree": dt_metrics,
            "RandomForest": rf_metrics
        }
    }

    with open(metrics_path, "w") as f:
        json.dump(all_metrics, f, indent=2)

    print(f"   Artifacts saved successfully to {TRAINED_MODELS_DIR}")
    print("==================================================")
    return all_metrics

if __name__ == "__main__":
    train_and_evaluate()
