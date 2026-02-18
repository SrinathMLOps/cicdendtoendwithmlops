import pandas as pd
import numpy as np
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import joblib
import json
import yaml
import os

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
    
    # Train model
    model = RandomForestClassifier(
        n_estimators=params['model']['n_estimators'],
        max_depth=params['model']['max_depth'],
        random_state=params['model']['random_state']
    )
    model.fit(X_train, y_train)
    
    # Save model
    os.makedirs('models/staging', exist_ok=True)
    joblib.dump(model, 'models/staging/model.pkl')
    
    # Calculate and save metrics
    train_score = model.score(X_train, y_train)
    test_score = model.score(X_test, y_test)
    
    metrics = {
        'train_accuracy': float(train_score),
        'test_accuracy': float(test_score)
    }
    
    os.makedirs('metrics', exist_ok=True)
    with open('metrics/train_metrics.json', 'w') as f:
        json.dump(metrics, f, indent=2)
    
    print(f"✅ Model trained - Train Accuracy: {train_score:.4f}, Test Accuracy: {test_score:.4f}")

if __name__ == '__main__':
    train_model()
