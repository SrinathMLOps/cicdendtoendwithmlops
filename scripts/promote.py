import shutil
import json
import yaml
import os
import mlflow
from mlflow.tracking import MlflowClient

def load_params():
    with open('params.yaml', 'r') as f:
        params = yaml.safe_load(f)
    return params

def promote_model():
    params = load_params()
    
    # Configure MLflow
    mlflow.set_tracking_uri(params['mlflow']['tracking_uri'])
    client = MlflowClient()
    
    # Load evaluation metrics
    with open('metrics/eval_metrics.json', 'r') as f:
        metrics = json.load(f)
    
    accuracy = metrics['accuracy']
    min_accuracy = params['promote']['min_accuracy']
    
    print(f"Model Accuracy: {accuracy:.4f}")
    print(f"Minimum Required Accuracy: {min_accuracy:.4f}")
    
    if accuracy >= min_accuracy:
        # Create production directory
        os.makedirs('models/production', exist_ok=True)
        
        # Copy model from staging to production
        shutil.copy2(
            params['promote']['staging_model'],
            params['promote']['production_model']
        )
        
        # Promote model in MLflow Model Registry
        try:
            model_name = params['mlflow']['model_name']
            
            # Get the latest version in None/Staging
            versions = client.search_model_versions(f"name='{model_name}'")
            if versions:
                latest_version = versions[0]
                version_number = latest_version.version
                
                # Transition to Production
                client.transition_model_version_stage(
                    name=model_name,
                    version=version_number,
                    stage="Production",
                    archive_existing_versions=True
                )
                print(f"✅ Model promoted to production in MLflow Registry!")
                print(f"📦 Model: {model_name}, Version: {version_number}")
            else:
                print("⚠️ No model versions found in MLflow Registry")
        except Exception as e:
            print(f"⚠️ MLflow promotion warning: {e}")
            print("✅ Model promoted to production locally!")
    else:
        print(f"❌ Model accuracy {accuracy:.4f} is below threshold {min_accuracy:.4f}")
        print("Model NOT promoted to production")
        exit(1)

if __name__ == '__main__':
    promote_model()
