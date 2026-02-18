import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
import joblib
import json
import yaml
import os
import mlflow
import mlflow.sklearn

def load_params():
    with open('params.yaml', 'r') as f:
        params = yaml.safe_load(f)
    return params

def evaluate_model():
    params = load_params()
    
    # Configure MLflow
    mlflow.set_tracking_uri(params['mlflow']['tracking_uri'])
    
    # Load data
    df = pd.read_csv('data/raw/train.csv')
    X = df.drop('target', axis=1)
    y = df['target']
    
    # Split data (same split as training)
    _, X_test, _, y_test = train_test_split(
        X, y,
        test_size=params['train']['test_size'],
        random_state=params['train']['random_state']
    )
    
    # Load model
    model = joblib.load('models/staging/model.pkl')
    
    # Make predictions
    y_pred = model.predict(X_test)
    
    # Calculate metrics
    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred, average='weighted')
    recall = recall_score(y_test, y_pred, average='weighted')
    f1 = f1_score(y_test, y_pred, average='weighted')
    conf_matrix = confusion_matrix(y_test, y_pred)
    
    metrics = {
        'accuracy': float(accuracy),
        'precision': float(precision),
        'recall': float(recall),
        'f1_score': float(f1),
        'confusion_matrix': conf_matrix.tolist()
    }
    
    # Log evaluation metrics to MLflow (if run_id exists)
    try:
        with open('metrics/train_metrics.json', 'r') as f:
            train_metrics = json.load(f)
            if 'mlflow_run_id' in train_metrics:
                with mlflow.start_run(run_id=train_metrics['mlflow_run_id']):
                    mlflow.log_metrics({
                        'eval_accuracy': accuracy,
                        'eval_precision': precision,
                        'eval_recall': recall,
                        'eval_f1_score': f1
                    })
    except Exception as e:
        print(f"⚠️ Could not log to MLflow: {e}")
    
    # Save metrics
    os.makedirs('metrics', exist_ok=True)
    with open('metrics/eval_metrics.json', 'w') as f:
        json.dump(metrics, f, indent=2)
    
    print(f"✅ Model evaluated - Accuracy: {metrics['accuracy']:.4f}")
    print(f"   Precision: {metrics['precision']:.4f}")
    print(f"   Recall: {metrics['recall']:.4f}")
    print(f"   F1 Score: {metrics['f1_score']:.4f}")

if __name__ == '__main__':
    evaluate_model()
