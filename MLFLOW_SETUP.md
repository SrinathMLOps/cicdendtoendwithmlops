# MLflow Integration Guide

Complete guide for setting up MLflow with your MLOps pipeline.

## What is MLflow?

MLflow is an open-source platform for managing the ML lifecycle, including:
- **Experiment Tracking**: Log parameters, metrics, and artifacts
- **Model Registry**: Version and manage models
- **Model Deployment**: Deploy models to production
- **Model Serving**: Serve models via REST API

## Architecture

```
Training → MLflow Tracking → MLflow Model Registry → Production Deployment
    ↓           ↓                    ↓                        ↓
  Metrics    Experiments         Versions                  EKS/K8s
```

## Setup Options

### Option 1: Local MLflow Server (Development)

#### 1.1 Using Docker Compose (Recommended)

```bash
# Set AWS credentials
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key

# Start MLflow with PostgreSQL backend
docker-compose up -d

# Verify services are running
docker-compose ps

# Access MLflow UI
# Open: http://localhost:5000
```

#### 1.2 Using SQLite (Simple Setup)

```bash
# Start MLflow server with local SQLite backend
mlflow server \
  --backend-store-uri sqlite:///mlflow.db \
  --default-artifact-root ./mlflow-artifacts \
  --host 0.0.0.0 \
  --port 5000
```

### Option 2: AWS-Hosted MLflow (Production)

#### 2.1 Create RDS PostgreSQL Database

```bash
# Create RDS instance for MLflow backend
aws rds create-db-instance \
  --db-instance-identifier mlflow-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --master-username mlflow \
  --master-user-password YourSecurePassword123 \
  --allocated-storage 20 \
  --vpc-security-group-ids sg-xxxxxxxx \
  --db-name mlflow \
  --region us-east-1

# Wait for database to be available
aws rds wait db-instance-available \
  --db-instance-identifier mlflow-db
```

#### 2.2 Create S3 Bucket for Artifacts

```bash
# Run the setup script
# Windows:
powershell -ExecutionPolicy Bypass -File mlflow-setup.ps1

# Linux/Mac:
bash mlflow-setup.sh
```

#### 2.3 Deploy MLflow on EC2

```bash
# Launch EC2 instance
aws ec2 run-instances \
  --image-id ami-0c55b159cbfafe1f0 \
  --instance-type t3.medium \
  --key-name your-key-pair \
  --security-group-ids sg-xxxxxxxx \
  --subnet-id subnet-xxxxxxxx \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=mlflow-server}]'

# SSH into instance
ssh -i your-key.pem ec2-user@<EC2_PUBLIC_IP>

# Install dependencies
sudo yum update -y
sudo yum install python3-pip -y
pip3 install mlflow psycopg2-binary boto3

# Start MLflow server
mlflow server \
  --backend-store-uri postgresql://mlflow:password@<RDS_ENDPOINT>:5432/mlflow \
  --default-artifact-root s3://mlflow-artifacts-bucket/mlflow \
  --host 0.0.0.0 \
  --port 5000
```

#### 2.4 Deploy MLflow on EKS (Advanced)

```bash
# Create namespace
kubectl create namespace mlflow

# Create secret for database
kubectl create secret generic mlflow-db-secret \
  --from-literal=username=mlflow \
  --from-literal=password=YourSecurePassword123 \
  --namespace=mlflow

# Apply Kubernetes manifests
kubectl apply -f k8s/mlflow-deployment.yaml
kubectl apply -f k8s/mlflow-service.yaml
```

## Configuration

### Update params.yaml

```yaml
mlflow:
  tracking_uri: http://localhost:5000  # or your MLflow server URL
  experiment_name: iris-classification
  model_name: iris-model
  s3_bucket: mlflow-artifacts-bucket-xxxxx
```

### Environment Variables

```bash
# Set MLflow tracking URI
export MLFLOW_TRACKING_URI=http://localhost:5000

# Set AWS credentials (if using S3)
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=us-east-1
```

## Usage

### 1. Training with MLflow

```bash
# Train model (logs to MLflow automatically)
python src/train.py

# View in MLflow UI
# Open: http://localhost:5000
```

### 2. View Experiments

```bash
# List experiments
mlflow experiments list

# Search runs
mlflow runs list --experiment-id 0
```

### 3. Model Registry

```bash
# Register model
mlflow models register \
  --model-uri runs:/<RUN_ID>/model \
  --name iris-model

# Transition to production
mlflow models transition \
  --name iris-model \
  --version 1 \
  --stage Production
```

### 4. Serve Model from MLflow

```bash
# Serve model locally
mlflow models serve \
  --model-uri models:/iris-model/Production \
  --port 8001

# Test prediction
curl -X POST http://localhost:8001/invocations \
  -H "Content-Type: application/json" \
  -d '{"dataframe_split": {"columns": ["sepal length", "sepal width", "petal length", "petal width"], "data": [[5.1, 3.5, 1.4, 0.2]]}}'
```

## MLflow UI Features

### Experiments View
- Compare multiple runs
- Visualize metrics over time
- Filter and sort runs
- Download artifacts

### Model Registry
- Version management
- Stage transitions (None → Staging → Production)
- Model lineage tracking
- Annotations and descriptions

### Run Details
- Parameters logged
- Metrics tracked
- Artifacts stored
- Code version
- Tags and notes

## Integration with Jenkins

The Jenkinsfile now includes:

1. **Start MLflow Server** stage
2. **MLflow Model Registry** stage
3. Automatic logging during training
4. Model promotion in registry

## Testing MLflow Integration

### Test 1: Local Training

```bash
# Set tracking URI
export MLFLOW_TRACKING_URI=http://localhost:5000

# Run training
python src/train.py

# Check MLflow UI
# You should see a new run in the experiment
```

### Test 2: Model Registry

```bash
# Check registered models
python -c "
import mlflow
from mlflow.tracking import MlflowClient

mlflow.set_tracking_uri('http://localhost:5000')
client = MlflowClient()

models = client.search_registered_models()
for model in models:
    print(f'Model: {model.name}')
    for version in model.latest_versions:
        print(f'  Version: {version.version}, Stage: {version.current_stage}')
"
```

### Test 3: Load Model from Registry

```bash
# Load and test production model
python -c "
import mlflow
import numpy as np

mlflow.set_tracking_uri('http://localhost:5000')
model = mlflow.sklearn.load_model('models:/iris-model/Production')

# Test prediction
X_test = np.array([[5.1, 3.5, 1.4, 0.2]])
prediction = model.predict(X_test)
print(f'Prediction: {prediction}')
"
```

## Monitoring and Maintenance

### View Logs

```bash
# Docker Compose logs
docker-compose logs -f mlflow

# Check PostgreSQL
docker-compose exec postgres psql -U mlflow -d mlflow -c "SELECT * FROM experiments;"
```

### Backup

```bash
# Backup PostgreSQL database
docker-compose exec postgres pg_dump -U mlflow mlflow > mlflow_backup.sql

# Backup S3 artifacts
aws s3 sync s3://mlflow-artifacts-bucket ./mlflow-backup
```

### Cleanup

```bash
# Stop services
docker-compose down

# Remove volumes (WARNING: deletes all data)
docker-compose down -v

# Clean up old runs (Python script)
python -c "
import mlflow
from mlflow.tracking import MlflowClient

mlflow.set_tracking_uri('http://localhost:5000')
client = MlflowClient()

# Delete old experiments
experiments = client.search_experiments()
for exp in experiments:
    if exp.name.startswith('old_'):
        client.delete_experiment(exp.experiment_id)
"
```

## Troubleshooting

### Issue: Cannot connect to MLflow server

```bash
# Check if server is running
curl http://localhost:5000

# Check Docker containers
docker-compose ps

# Restart services
docker-compose restart
```

### Issue: S3 access denied

```bash
# Verify AWS credentials
aws sts get-caller-identity

# Check S3 bucket permissions
aws s3 ls s3://mlflow-artifacts-bucket

# Update IAM policy
aws iam attach-user-policy \
  --user-name mlops-jenkins \
  --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess
```

### Issue: Database connection error

```bash
# Check PostgreSQL is running
docker-compose exec postgres psql -U mlflow -d mlflow -c "SELECT 1;"

# Reset database
docker-compose down -v
docker-compose up -d
```

### Issue: Model not found in registry

```bash
# List all registered models
mlflow models list

# Check if model was logged
python -c "
import mlflow
mlflow.set_tracking_uri('http://localhost:5000')
runs = mlflow.search_runs(experiment_ids=['0'])
print(runs[['run_id', 'metrics.accuracy', 'params.n_estimators']])
"
```

## Best Practices

1. **Use Descriptive Names**: Name experiments and runs clearly
2. **Tag Runs**: Add tags for easy filtering (e.g., 'production', 'experiment')
3. **Log Everything**: Parameters, metrics, artifacts, code version
4. **Version Models**: Use semantic versioning in model registry
5. **Archive Old Versions**: Keep registry clean
6. **Monitor Performance**: Track model performance in production
7. **Backup Regularly**: Backup database and artifacts
8. **Secure Access**: Use authentication in production
9. **Use S3 for Artifacts**: Don't store large files in database
10. **Document Models**: Add descriptions and notes in registry

## Advanced Features

### Custom Metrics

```python
import mlflow

with mlflow.start_run():
    # Log custom metrics
    mlflow.log_metric("custom_score", 0.95)
    mlflow.log_metric("inference_time_ms", 12.5)
```

### Artifacts

```python
import mlflow

with mlflow.start_run():
    # Log plots
    mlflow.log_artifact("confusion_matrix.png")
    
    # Log datasets
    mlflow.log_artifact("test_data.csv")
```

### Model Signatures

```python
import mlflow
from mlflow.models.signature import infer_signature

# Infer signature from data
signature = infer_signature(X_train, model.predict(X_train))

# Log model with signature
mlflow.sklearn.log_model(model, "model", signature=signature)
```

## Resources

- MLflow Documentation: https://mlflow.org/docs/latest/index.html
- MLflow GitHub: https://github.com/mlflow/mlflow
- MLflow Examples: https://github.com/mlflow/mlflow/tree/master/examples
- AWS MLflow Guide: https://aws.amazon.com/blogs/machine-learning/managing-your-machine-learning-lifecycle-with-mlflow-and-amazon-sagemaker/
