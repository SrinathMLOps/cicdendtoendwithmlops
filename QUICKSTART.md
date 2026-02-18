# Quick Start Guide - MLOps Pipeline with MLflow

Get your complete MLOps pipeline running in 30 minutes!

## Prerequisites Check

```bash
# Check installations
python --version        # Should be 3.8+
docker --version        # Should be installed
aws --version          # Should be installed
git --version          # Should be installed
```

## Step 1: Clone Repository (1 min)

```bash
git clone https://github.com/SrinathMLOps/cicdendtoendwithmlops.git
cd cicdendtoendwithmlops
```

## Step 2: Install Python Dependencies (2 min)

```bash
# Create virtual environment
python -m venv venv

# Activate
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Step 3: Start MLflow Server (2 min)

```bash
# Set AWS credentials (if using S3 for artifacts)
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret

# Start MLflow with Docker Compose
docker-compose up -d

# Verify
docker-compose ps
curl http://localhost:5000/health
```

**MLflow UI**: http://localhost:5000

## Step 4: Train Your First Model (3 min)

```bash
# Set MLflow tracking URI
export MLFLOW_TRACKING_URI=http://localhost:5000

# Train model
python src/train.py
```

**Output:**
```
✅ Sample data created
✅ Model trained - Train Accuracy: 1.0000, Test Accuracy: 1.0000
📊 MLflow Run ID: abc123...
🔗 MLflow UI: http://localhost:5000
```

**Check MLflow UI** to see your experiment!

## Step 5: Evaluate Model (1 min)

```bash
python src/evaluate.py
```

**Output:**
```
✅ Model evaluated - Accuracy: 1.0000
   Precision: 1.0000
   Recall: 1.0000
   F1 Score: 1.0000
```

## Step 6: Promote Model to Production (1 min)

```bash
python scripts/promote.py
```

**Output:**
```
Model Accuracy: 1.0000
Minimum Required Accuracy: 0.8500
✅ Model promoted to production in MLflow Registry!
📦 Model: iris-model, Version: 1
```

## Step 7: Serve Model (2 min)

```bash
# Start FastAPI server
python src/serve.py
```

**API Endpoints:**
- Health: http://localhost:8000/health
- Docs: http://localhost:8000/docs
- Model Info: http://localhost:8000/model-info

## Step 8: Test Predictions (1 min)

```bash
# Test prediction
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"features": [5.1, 3.5, 1.4, 0.2]}'
```

**Response:**
```json
{
  "prediction": 0,
  "probability": [0.99, 0.005, 0.005],
  "model_version": "Production",
  "model_source": "MLflow Model Registry"
}
```

## Step 9: AWS Setup (10 min)

### 9.1 Configure AWS CLI

```bash
aws configure
# Enter your AWS Access Key ID
# Enter your AWS Secret Access Key
# Default region: us-east-1
# Default output format: json
```

### 9.2 Create S3 Buckets

```bash
# For DVC
aws s3 mb s3://mlops-dvc-storage-$(date +%s) --region us-east-1

# For MLflow artifacts
aws s3 mb s3://mlflow-artifacts-$(date +%s) --region us-east-1
```

### 9.3 Create ECR Repository

```bash
aws ecr create-repository \
  --repository-name mlops-serving \
  --region us-east-1
```

### 9.4 Initialize DVC

```bash
# Initialize DVC
dvc init

# Configure S3 remote (replace with your bucket)
dvc remote add -d myremote s3://mlops-dvc-storage-xxxxx/dvc-storage
dvc remote modify myremote region us-east-1

# Commit DVC config
git add .dvc/config .dvcignore
git commit -m "Initialize DVC"
```

## Step 10: Build and Test Docker Image (5 min)

```bash
# Build image
docker build -t mlops-serving:test .

# Run container
docker run -d -p 8001:8000 --name test_app mlops-serving:test

# Test
curl http://localhost:8001/
curl http://localhost:8001/model-info

# Stop and remove
docker stop test_app
docker rm test_app
```

## Step 11: Jenkins Setup (Optional - 10 min)

See [SETUP_GUIDE.md](SETUP_GUIDE.md#5-jenkins-setup) for detailed Jenkins setup.

Quick steps:
1. Install Jenkins
2. Install required plugins
3. Add AWS credentials
4. Create pipeline job pointing to your GitHub repo
5. Run pipeline

## Verification Checklist

- [ ] MLflow UI accessible at http://localhost:5000
- [ ] Model trained and logged in MLflow
- [ ] Model registered in MLflow Model Registry
- [ ] Model promoted to Production stage
- [ ] FastAPI server running at http://localhost:8000
- [ ] Predictions working via API
- [ ] Docker image builds successfully
- [ ] AWS credentials configured
- [ ] S3 buckets created
- [ ] ECR repository created

## Common Commands

### MLflow

```bash
# Start MLflow
docker-compose up -d

# Stop MLflow
docker-compose down

# View logs
docker-compose logs -f mlflow

# List experiments
mlflow experiments list

# List models
mlflow models list
```

### Training Pipeline

```bash
# Full pipeline
export MLFLOW_TRACKING_URI=http://localhost:5000
python src/train.py
python src/evaluate.py
python scripts/promote.py
```

### DVC

```bash
# Add data to DVC
dvc add data/raw/train.csv

# Push to S3
dvc push

# Pull from S3
dvc pull

# Run pipeline
dvc repro
```

### Docker

```bash
# Build
docker build -t mlops-serving:latest .

# Run
docker run -d -p 8000:8000 mlops-serving:latest

# Logs
docker logs <container_id>

# Stop
docker stop <container_id>
```

## Troubleshooting

### MLflow not starting

```bash
# Check Docker
docker ps

# Restart services
docker-compose restart

# Check logs
docker-compose logs mlflow
docker-compose logs postgres
```

### Model not loading

```bash
# Check model exists
ls -la models/production/

# Check MLflow registry
python -c "
import mlflow
mlflow.set_tracking_uri('http://localhost:5000')
print(mlflow.search_registered_models())
"
```

### API not responding

```bash
# Check if server is running
curl http://localhost:8000/health

# Check logs
# If running in terminal, check the output
# If running in Docker, check container logs
```

## Next Steps

1. **Complete AWS Setup**: Follow [SETUP_GUIDE.md](SETUP_GUIDE.md)
2. **MLflow Deep Dive**: Read [MLFLOW_SETUP.md](MLFLOW_SETUP.md)
3. **Deploy to EKS**: Set up Kubernetes cluster
4. **Configure Jenkins**: Automate the entire pipeline
5. **Add Monitoring**: Set up Prometheus/Grafana
6. **Implement A/B Testing**: Deploy multiple model versions

## Resources

- **Main Guide**: [SETUP_GUIDE.md](SETUP_GUIDE.md)
- **MLflow Guide**: [MLFLOW_SETUP.md](MLFLOW_SETUP.md)
- **Project README**: [README.md](README.md)
- **GitHub Repo**: https://github.com/SrinathMLOps/cicdendtoendwithmlops

## Support

If you encounter issues:
1. Check the troubleshooting sections in guides
2. Review logs (MLflow, Docker, application)
3. Verify all prerequisites are installed
4. Check AWS credentials and permissions
5. Ensure ports are not in use (5000, 8000, 5432)

Happy MLOps! 🚀
