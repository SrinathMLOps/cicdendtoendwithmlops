import shutil
import json
import yaml
import os

def load_params():
    with open('params.yaml', 'r') as f:
        params = yaml.safe_load(f)
    return params

def promote_model():
    params = load_params()
    
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
        print(f"✅ Model promoted to production!")
    else:
        print(f"❌ Model accuracy {accuracy:.4f} is below threshold {min_accuracy:.4f}")
        print("Model NOT promoted to production")
        exit(1)

if __name__ == '__main__':
    promote_model()
