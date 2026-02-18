from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import joblib
import numpy as np
import os
import mlflow
import mlflow.sklearn
import yaml

app = FastAPI(title="MLOps Model Serving API with MLflow")

# Global variables
model = None
model_version = None
model_source = None

def load_params():
    with open('params.yaml', 'r') as f:
        return yaml.safe_load(f)

@app.on_event("startup")
async def load_model():
    global model, model_version, model_source
    
    # Try loading from MLflow first
    try:
        params = load_params()
        mlflow.set_tracking_uri(params['mlflow']['tracking_uri'])
        model_name = params['mlflow']['model_name']
        
        # Load production model from MLflow Model Registry
        model_uri = f"models:/{model_name}/Production"
        model = mlflow.sklearn.load_model(model_uri)
        model_source = "MLflow Model Registry"
        model_version = "Production"
        print(f"✅ Model loaded from MLflow Registry: {model_uri}")
    except Exception as e:
        print(f"⚠️ Could not load from MLflow: {e}")
        
        # Fallback to local model
        MODEL_PATH = 'models/production/model.pkl'
        if os.path.exists(MODEL_PATH):
            model = joblib.load(MODEL_PATH)
            model_source = "Local filesystem"
            model_version = "latest"
            print(f"✅ Model loaded from {MODEL_PATH}")
        else:
            print(f"❌ Model not found at {MODEL_PATH}")

class PredictionRequest(BaseModel):
    features: list

class PredictionResponse(BaseModel):
    prediction: int
    probability: list
    model_version: str
    model_source: str

@app.get("/")
async def root():
    return {
        "message": "MLOps Model Serving API with MLflow",
        "status": "running",
        "model_loaded": model is not None,
        "model_source": model_source,
        "model_version": model_version
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "model_loaded": model is not None
    }

@app.get("/model-info")
async def model_info():
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    return {
        "model_source": model_source,
        "model_version": model_version,
        "model_type": type(model).__name__,
        "model_params": model.get_params() if hasattr(model, 'get_params') else {}
    }

@app.post("/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest):
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
        # Convert features to numpy array
        features = np.array(request.features).reshape(1, -1)
        
        # Make prediction
        prediction = int(model.predict(features)[0])
        probability = model.predict_proba(features)[0].tolist()
        
        return PredictionResponse(
            prediction=prediction,
            probability=probability,
            model_version=model_version,
            model_source=model_source
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Prediction error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
