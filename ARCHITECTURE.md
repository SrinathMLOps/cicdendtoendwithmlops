# MLOps Pipeline Architecture

## System Overview

This document describes the complete end-to-end MLOps architecture integrating Jenkins, DVC, MLflow, Docker, AWS ECR, and Kubernetes.

## High-Level Architecture

```
┌─────────────┐
│   GitHub    │ Source Code Repository
└──────┬──────┘
       │ Webhook/Poll
       ▼
┌─────────────┐
│   Jenkins   │ CI/CD Orchestration
└──────┬──────┘
       │
       ├──────────────────────────────────────────┐
       │                                          │
       ▼                                          ▼
┌─────────────┐                          ┌─────────────┐
│  DVC + S3   │ Data Version Control     │   MLflow    │ Experiment Tracking
│             │                          │  + Model    │ & Model Registry
│  - Raw Data │                          │   Registry  │
│  - Models   │                          │             │
│  - Metrics  │                          │  - Runs     │
└─────────────┘                          │  - Metrics  │
                                         │  - Artifacts│
                                         │  - Versions │
                                         └──────┬──────┘
                                                │
       ┌────────────────────────────────────────┘
       │
       ▼
┌─────────────┐
│   Docker    │ Containerization
│   Build     │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  AWS ECR    │ Container Registry
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  AWS EKS    │ Kubernetes Deployment
│  (K8s)      │
│             │
│  - Pods     │
│  - Services │
│  - Ingress  │
└─────────────┘
```

## Component Details

### 1. Source Control (GitHub)

**Purpose**: Version control for code, configurations, and pipeline definitions

**Contents**:
- Python source code (training, evaluation, serving)
- Jenkinsfile (pipeline definition)
- DVC configuration (.dvc/)
- Kubernetes manifests (k8s/)
- Docker configuration
- Documentation

**Triggers**:
- Webhook on push to main branch
- Manual trigger from Jenkins

### 2. CI/CD Pipeline (Jenkins)

**Purpose**: Orchestrate the entire MLOps workflow

**Stages**:
1. **Checkout Code**: Clone from GitHub
2. **Verify Environment**: Check AWS access, Python, Docker
3. **Install Dependencies**: pip install requirements
4. **Start MLflow Server**: Launch tracking server
5. **DVC Pull**: Download data from S3
6. **Train Model**: Execute training with MLflow logging
7. **Show Metrics**: Display model performance
8. **MLflow Registry**: Check model versions
9. **Approve Promotion**: Manual approval gate
10. **Promote Model**: Move to production in MLflow
11. **Push Artifacts**: Upload to S3 via DVC
12. **Build Docker Image**: Create container
13. **Test Docker Image**: Validate container
14. **Login to ECR**: Authenticate with AWS
15. **Push to ECR**: Upload container image
16. **Deploy to EKS**: Deploy to Kubernetes

**Credentials**:
- AWS credentials (for S3, ECR, EKS)
- GitHub credentials (for repository access)

### 3. Data Version Control (DVC + S3)

**Purpose**: Version control for data, models, and large files

**Tracked Assets**:
- `data/raw/`: Training datasets
- `models/staging/`: Staging models
- `models/production/`: Production models
- `metrics/`: Model metrics (JSON)

**S3 Structure**:
```
s3://mlops-dvc-storage/
├── dvc-storage/
│   ├── files/
│   │   ├── md5/
│   │   │   └── <hash>
│   └── tmp/
```

**DVC Pipeline** (dvc.yaml):
- `train`: Train model → staging
- `evaluate`: Evaluate model → metrics
- `promote`: Promote model → production

### 4. Experiment Tracking (MLflow)

**Purpose**: Track experiments, log metrics, and manage model lifecycle

**Components**:

#### MLflow Tracking Server
- **Backend Store**: PostgreSQL (metadata)
- **Artifact Store**: S3 (models, plots, files)
- **Port**: 5000
- **UI**: Web interface for experiments

#### MLflow Model Registry
- **Stages**: None → Staging → Production → Archived
- **Versioning**: Automatic version numbering
- **Lineage**: Track model origin and metrics
- **Annotations**: Add descriptions and tags

**Logged Information**:
- Parameters: n_estimators, max_depth, test_size
- Metrics: accuracy, precision, recall, f1_score
- Artifacts: model.pkl, confusion_matrix.png
- Tags: experiment_type, data_version
- Code version: Git commit hash

**S3 Structure**:
```
s3://mlflow-artifacts-bucket/
├── mlflow/
│   ├── <experiment_id>/
│   │   ├── <run_id>/
│   │   │   ├── artifacts/
│   │   │   │   └── model/
│   │   │   └── metrics/
```

### 5. Model Training Pipeline

**Workflow**:

```
Data Loading → Feature Engineering → Model Training → Evaluation → Promotion
     ↓               ↓                    ↓              ↓           ↓
  DVC Pull      Transform           MLflow Log      Metrics    Registry
```

**Training Script** (src/train.py):
1. Load data from DVC
2. Split train/test
3. Start MLflow run
4. Log parameters
5. Train RandomForest model
6. Log metrics
7. Save model to MLflow
8. Register in Model Registry
9. Save model locally

**Evaluation Script** (src/evaluate.py):
1. Load test data
2. Load model from staging
3. Make predictions
4. Calculate metrics
5. Log to MLflow
6. Save metrics locally

**Promotion Script** (scripts/promote.py):
1. Load evaluation metrics
2. Check accuracy threshold
3. If passed:
   - Copy model to production
   - Transition in MLflow Registry
4. If failed:
   - Exit with error

### 6. Model Serving (FastAPI)

**Purpose**: Serve production models via REST API

**Endpoints**:
- `GET /`: Health check and status
- `GET /health`: Kubernetes health probe
- `GET /model-info`: Model metadata
- `POST /predict`: Make predictions

**Model Loading Priority**:
1. Try MLflow Model Registry (Production stage)
2. Fallback to local filesystem

**Request/Response**:
```json
// Request
{
  "features": [5.1, 3.5, 1.4, 0.2]
}

// Response
{
  "prediction": 0,
  "probability": [0.99, 0.005, 0.005],
  "model_version": "Production",
  "model_source": "MLflow Model Registry"
}
```

### 7. Containerization (Docker)

**Purpose**: Package application with dependencies

**Dockerfile Layers**:
1. Base: python:3.9-slim
2. Dependencies: requirements.txt
3. Application: src/ code
4. Model: models/production/
5. Entrypoint: uvicorn server

**Image Tags**:
- `mlops-serving:${BUILD_NUMBER}`: Specific build
- `mlops-serving:latest`: Latest build

**Health Check**:
- Interval: 30s
- Timeout: 3s
- Retries: 3
- Command: `curl -f http://localhost:8000/`

### 8. Container Registry (AWS ECR)

**Purpose**: Store and manage Docker images

**Repository**: mlops-serving

**Image URI Format**:
```
<ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/mlops-serving:<TAG>
```

**Lifecycle Policy**:
- Keep last 10 images
- Remove untagged images after 7 days

### 9. Kubernetes Deployment (AWS EKS)

**Purpose**: Orchestrate containerized applications

**Resources**:

#### Deployment (k8s/deployment.yaml)
- **Replicas**: 2 (for high availability)
- **Image**: From ECR
- **Resources**:
  - Requests: 256Mi memory, 250m CPU
  - Limits: 512Mi memory, 500m CPU
- **Probes**:
  - Liveness: /health endpoint
  - Readiness: /health endpoint

#### Service (k8s/service.yaml)
- **Type**: LoadBalancer
- **Port**: 80 → 8000
- **Selector**: app=mlops-serving

#### MLflow Deployment (k8s/mlflow-deployment.yaml)
- **Replicas**: 1
- **Backend**: PostgreSQL
- **Artifacts**: S3
- **Service**: LoadBalancer on port 5000

**Deployment Strategy**:
- Rolling update
- Max surge: 1
- Max unavailable: 0
- Zero-downtime deployment

### 10. AWS Infrastructure

**Services Used**:

#### S3 (Simple Storage Service)
- **DVC Bucket**: Data and model storage
- **MLflow Bucket**: Experiment artifacts
- **Versioning**: Enabled
- **Encryption**: AES-256

#### ECR (Elastic Container Registry)
- **Repository**: mlops-serving
- **Scanning**: On push
- **Encryption**: AES-256

#### EKS (Elastic Kubernetes Service)
- **Cluster**: mlops-cluster
- **Node Type**: t3.medium
- **Nodes**: 2-3 (auto-scaling)
- **Region**: us-east-1

#### IAM (Identity and Access Management)
- **User**: mlops-jenkins
- **Policies**:
  - AmazonS3FullAccess
  - AmazonEC2ContainerRegistryFullAccess
  - AmazonEKSClusterPolicy

#### RDS (Relational Database Service) - Optional
- **Engine**: PostgreSQL 14
- **Instance**: db.t3.micro
- **Database**: mlflow
- **Purpose**: MLflow backend store

## Data Flow

### Training Flow

```
1. Developer pushes code to GitHub
2. Jenkins webhook triggered
3. Jenkins pulls code
4. Jenkins starts MLflow server
5. Jenkins pulls data from S3 via DVC
6. Training script executes:
   - Loads data
   - Trains model
   - Logs to MLflow
   - Saves to staging
7. Evaluation script executes:
   - Loads model
   - Calculates metrics
   - Logs to MLflow
8. Manual approval in Jenkins
9. Promotion script executes:
   - Checks threshold
   - Promotes in MLflow
   - Copies to production
10. Jenkins pushes artifacts to S3 via DVC
```

### Deployment Flow

```
1. Jenkins builds Docker image
2. Jenkins tests container locally
3. Jenkins logs into ECR
4. Jenkins pushes image to ECR
5. Jenkins updates EKS deployment
6. Kubernetes pulls new image
7. Kubernetes performs rolling update
8. New pods start with new model
9. Health checks pass
10. Old pods terminated
11. Service routes traffic to new pods
```

### Prediction Flow

```
1. Client sends POST /predict request
2. Load balancer routes to service
3. Service routes to pod
4. FastAPI receives request
5. Model loads from MLflow Registry
6. Model makes prediction
7. Response returned to client
```

## Security Considerations

### Authentication & Authorization
- AWS IAM for service access
- ECR authentication via AWS CLI
- EKS RBAC for Kubernetes access
- MLflow authentication (optional)

### Secrets Management
- Jenkins credentials store
- Kubernetes secrets for AWS credentials
- Environment variables for sensitive data

### Network Security
- VPC for EKS cluster
- Security groups for access control
- Private subnets for nodes
- Public subnet for load balancer

### Data Security
- S3 encryption at rest
- ECR encryption at rest
- TLS for data in transit
- IAM policies for least privilege

## Monitoring & Observability

### Metrics
- Model performance metrics (accuracy, precision, recall)
- System metrics (CPU, memory, disk)
- Application metrics (request rate, latency)
- Business metrics (predictions per day)

### Logging
- Jenkins build logs
- MLflow experiment logs
- Kubernetes pod logs
- Application logs (FastAPI)

### Alerting
- Model performance degradation
- System resource exhaustion
- Deployment failures
- API errors

## Scalability

### Horizontal Scaling
- Kubernetes pod auto-scaling
- EKS node auto-scaling
- MLflow server replication

### Vertical Scaling
- Increase pod resources
- Upgrade node instance types
- Scale RDS instance

### Performance Optimization
- Model caching
- Request batching
- Connection pooling
- CDN for static assets

## Disaster Recovery

### Backup Strategy
- S3 versioning for data
- ECR image retention
- PostgreSQL backups
- Git for code

### Recovery Procedures
- Restore from S3 versions
- Rollback Kubernetes deployment
- Restore database from backup
- Redeploy from Git tag

## Cost Optimization

### AWS Costs
- Use spot instances for nodes
- S3 lifecycle policies
- ECR lifecycle policies
- Right-size resources

### Efficiency
- Batch predictions
- Model compression
- Efficient data formats
- Resource limits

## Future Enhancements

1. **A/B Testing**: Deploy multiple model versions
2. **Feature Store**: Centralized feature management
3. **Model Monitoring**: Track drift and performance
4. **Auto-retraining**: Trigger on performance degradation
5. **Multi-region**: Deploy across regions
6. **Canary Deployments**: Gradual rollout
7. **Shadow Mode**: Test without affecting production
8. **Model Explainability**: SHAP, LIME integration
9. **Data Quality**: Great Expectations integration
10. **Cost Tracking**: Tag resources for cost allocation

## References

- Jenkins: https://www.jenkins.io/
- DVC: https://dvc.org/
- MLflow: https://mlflow.org/
- Docker: https://www.docker.com/
- Kubernetes: https://kubernetes.io/
- AWS EKS: https://aws.amazon.com/eks/
- FastAPI: https://fastapi.tiangolo.com/
