import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import joblib
import json
import yaml
import os

def load_params():
    with open('params.yaml', 'r') as f:
        params = yaml.safe_load(f)
    return params

def evaluate_model():
    params = load_params()
    
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
    metrics = {
        'accuracy': float(accuracy_score(y_test, y_pred)),
        'precision': float(precision_score(y_test, y_pred, average='weighted')),
        'recall': float(recall_score(y_test, y_pred, average='weighted')),
        'f1_score': float(f1_score(y_test, y_pred, average='weighted'))
    }
    
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
