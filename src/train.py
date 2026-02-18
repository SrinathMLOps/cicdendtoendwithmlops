import pandas as pd
import numpy as np
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
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

def create_sample_data():
    """Create sample data if not exists"""
    os.makedirs('data/raw', exist_ok=True)
    iris = load_iris()
    df = pd.DataFrame(iris.data, columns=iris.feature_names)
    df['target'] = iris.target
    df.to_csv('data/raw/train.csv', index=False)
    print("✅ Sample data created")

def train_model():
    params = load_params()
    
    # Configure MLflow
    mlflow.set_tracking_uri(params['mlflow']['tracking_uri'])
    mlflow.set_experiment(params['mlflow']['experiment_name'])
    
    # Load data
    if not os.path.exists('data/raw/train.csv'):
        create_sample_data()
    
    df = pd.read_csv('data/raw/train.csv')
    X = df.drop('target', axis=1)
    y = df['target']
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, 
        test_size=params['train']['test_size'],
        random_state=params['train']['random_state']
    )
    
    # Start MLflow run
    with mlflow.start_run() as run:
        # Log parameters
        mlflow.log_params({
            'n_estimators': params['model']['n_estimators'],
            'max_depth': params['model']['max_depth'],
            'random_state': params['model']['random_state'],
            'test_size': params['train']['test_size']
        })
        
        # Train model
        model = RandomForestClassifier(
            n_estimators=params['model']['n_estimators'],
            max_depth=params['model']['max_depth'],
            random_state=params['model']['random_state']
        )
        model.fit(X_train, y_train)
        
        # Make predictions
        y_train_pred = model.predict(X_train)
        y_test_pred = model.predict(X_test)
        
        # Calculate metrics
        train_accuracy = accuracy_score(y_train, y_train_pred)
        test_accuracy = accuracy_score(y_test, y_test_pred)
        precision = precision_score(y_test, y_test_pred, average='weighted')
        recall = recall_score(y_test, y_test_pred, average='weighted')
        f1 = f1_score(y_test, y_test_pred, average='weighted')
        
        # Log metrics to MLflow
        mlflow.log_metrics({
            'train_accuracy': train_accuracy,
            'test_accuracy': test_accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1
        })
        
        # Log model to MLflow
        mlflow.sklearn.log_model(
            model, 
            "model",
            registered_model_name=params['mlflow']['model_name']
        )
        
        # Save model locally
        os.makedirs('models/staging', exist_ok=True)
        joblib.dump(model, 'models/staging/model.pkl')
        
        # Save metrics locally
        metrics = {
            'train_accuracy': float(train_accuracy),
            'test_accuracy': float(test_accuracy),
            'precision': float(precision),
            'recall': float(recall),
            'f1_score': float(f1),
            'mlflow_run_id': run.info.run_id
        }
        
        os.makedirs('metrics', exist_ok=True)
        with open('metrics/train_metrics.json', 'w') as f:
            json.dump(metrics, f, indent=2)
        
        print(f"✅ Model trained - Train Accuracy: {train_accuracy:.4f}, Test Accuracy: {test_accuracy:.4f}")
        print(f"📊 MLflow Run ID: {run.info.run_id}")
        print(f"🔗 MLflow UI: {params['mlflow']['tracking_uri']}")

if __name__ == '__main__':
    train_model()
