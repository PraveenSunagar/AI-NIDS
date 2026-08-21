import numpy as np
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report
)

def evaluate_model(model, X_test, y_test):
    """
    Evaluates a trained classifier and returns performance metrics.
    """
    y_pred = model.predict(X_test)
    
    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, pos_label="ATTACK", zero_division=0)
    rec = recall_score(y_test, y_pred, pos_label="ATTACK", zero_division=0)
    f1 = f1_score(y_test, y_pred, pos_label="ATTACK", zero_division=0)
    
    cm = confusion_matrix(y_test, y_pred, labels=["NORMAL", "ATTACK"])
    report = classification_report(y_test, y_pred, output_dict=True, zero_division=0)
    
    # Format confusion matrix as dictionary
    cm_dict = {
        "true_normal": int(cm[0][0]),
        "false_attack": int(cm[0][1]),
        "false_normal": int(cm[1][0]),
        "true_attack": int(cm[1][1])
    }
    
    return {
        "accuracy": round(float(acc), 4),
        "precision": round(float(prec), 4),
        "recall": round(float(rec), 4),
        "f1_score": round(float(f1), 4),
        "confusion_matrix": cm_dict,
        "classification_report": report
    }
