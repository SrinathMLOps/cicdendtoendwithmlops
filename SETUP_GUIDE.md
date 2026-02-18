# Complete MLOps Project Setup Guide

## Table of Contents
1. [AWS Setup](#1-aws-setup)
2. [Local Environment Setup](#2-local-environment-setup)
3. [MLflow Setup](#3-mlflow-setup)
4. [DVC Configuration](#4-dvc-configuration)
5. [Jenkins Setup](#5-jenkins-setup)
6. [Docker Setup](#6-docker-setup)
7. [Kubernetes (EKS) Setup](#7-kubernetes-eks-setup)
8. [Running the Pipeline](#8-running-the-pipeline)
9. [Troubleshooting](#9-troubleshooting)

---

## 1. AWS Setup

### 1.1 Create IAM User

```bash
# Create IAM user with programmatic access
aws iam create-user --user-name mlops-jenkins

# Attach required policies
aws iam attach-user-policy --user-name mlops-jenkins \
  --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess

aws iam attach-user-policy --user-name mlops-jenkins \
  --policy-arn arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryFullAccess

aws iam attach-user-policy --user-name mlops-jenkins \
  --policy-arn arn:aws:iam::aws:policy/AmazonEKSClusterPolicy

# Create access keys
aws iam create-access-key --user-name mlops-jenkins
```

Save the `AccessKeyId` and `SecretAccessKey` - you'll need them for Jenkins.

### 1.2 Create S3 Bucket for DVC

```bash
# Replace with your bucket name
export BUCKET_NAME="mlops-dvc-storage-$(date +%s)"
export AWS_REGION="us-east-1"

# Create bucket
aws s3 mb s3://${BUCKET_NAME} --region ${AWS_REGION}

# Enable versioning (recommended)
aws s3api put-bucket-versioning \
  --bucket ${BUCKET_NAME} \
  --versioning-configuration Status=Enabled
```

### 1.3 Create ECR Repository

```bash
# Create ECR repository
aws ecr create-repository \
  --repository-name mlops-serving \
  --region ${AWS_REGION}

# Note the repositoryUri from output
# Format: <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/mlops-serving
```

### 1.4 Create EKS Cluster

```bash
# Install eksctl if not already installed
# Windows: choco install eksctl
# Or download from: https://github.com/weaveworks/eksctl/releases

# Create EKS cluster (takes 15-20 minutes)
eksctl create cluster \
  --name mlops-cluster \
  --region ${AWS_REGION} \
  --nodegroup-name mlops-nodes \
  --node-type t3.medium \
  --nodes 2 \
  --nodes-min 1 \
  --nodes-max 3 \
  --managed

# Verify cluster
kubectl get nodes
```

---

## 2. Local Environment Setup

### 2.1 Install Python Dependencies

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2.2 Install DVC

```bash
pip install "dvc[s3]"

# Verify installation
dvc version
```

### 2.3 Install Docker

Download and install Docker Desktop:
- Windows: https://docs.docker.com/desktop/install/windows-install/
- Verify: `docker --version`

### 2.4 Install kubectl

```bash
# Windows (using chocolatey):
choco install kubernetes-cli

# Or download from:
# https://kubernetes.io/docs/tasks/tools/install-kubectl-windows/

# Verify
kubectl version --client
```

### 2.5 Install AWS CLI

```bash
# Windows:
# Download from: https://aws.amazon.com/cli/

# Configure AWS CLI
aws configure
# Enter your AWS Access Key ID
# Enter your AWS Secret Access Key
# Default region: us-east-1
# Default output format: json
```

---

## 3. MLflow Setup

### 3.1 Start MLflow Server (Local Development)

**Option A: Using Docker Compose (Recommended)**

```bash
# Set AWS credentials for artifact storage
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key

# Start MLflow with PostgreSQL backend
docker-compose up -d

# Verify services
docker-compose ps

# Check logs
docker-compose logs -f mlflow

# Access MLflow UI
# Open: http://localhost:5000
```

**Option B: Simple Local Setup**

```bash
# Start MLflow with SQLite backend
mlflow server \
  --backend-store-uri sqlite:///mlflow.db \
  --default-artifact-root ./mlflow-artifacts \
  --host 0.0.0.0 \
  --port 5000

# Access MLflow UI
# Open: http://localhost:5000
```

### 3.2 Configure MLflow for AWS (Production)

```bash
# Run setup script
# Windows:
powershell -ExecutionPolicy Bypass -File mlflow-setup.ps1

# Linux/Mac:
bash mlflow-setup.sh
```

This script will:
- Create S3 bucket for MLflow artifacts
- Enable versioning on the bucket
- Update params.yaml with bucket name

### 3.3 Verify MLflow Setup

```bash
# Test MLflow connection
curl http://localhost:5000/health

# Run a test training
export MLFLOW_TRACKING_URI=http://localhost:5000
python src/train.py

# Check MLflow UI for new experiment
# Open: http://localhost:5000
```

### 3.4 MLflow Model Registry

```bash
# View registered models
mlflow models list

# Check model versions
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

For detailed MLflow setup, see [MLFLOW_SETUP.md](MLFLOW_SETUP.md)

---

## 4. DVC Configuration

### 4.1 Initialize DVC

```bash
# Initialize DVC in your project
dvc init

# Configure S3 remote storage
dvc remote add -d myremote s3://${BUCKET_NAME}/dvc-storage

# Set AWS region
dvc remote modify myremote region us-east-1

# Commit DVC configuration
git add .dvc/config .dvcignore
git commit -m "Initialize DVC with S3 remote"
```

### 4.2 Add Data to DVC

```bash
# Add raw data to DVC tracking
dvc add data/raw/train.csv

# Commit the .dvc file
git add data/raw/train.csv.dvc data/raw/.gitignore
git commit -m "Track raw data with DVC"

# Push data to S3
dvc push
```

### 4.3 Verify DVC Setup

```bash
# Check DVC status
dvc status

# List remote storage
dvc remote list

# Test pull
dvc pull
```

---

## 5. Jenkins Setup

### 5.1 Install Jenkins

**Option A: Docker (Recommended for testing)**
```bash
docker run -d -p 8080:8080 -p 50000:50000 \
  -v jenkins_home:/var/jenkins_home \
  --name jenkins \
  jenkins/jenkins:lts
```

**Option B: Windows Installer**
- Download from: https://www.jenkins.io/download/
- Follow installation wizard

### 5.2 Initial Jenkins Configuration

```bash
# Get initial admin password (Docker)
docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword

# Or for Windows installation, check:
# C:\Program Files\Jenkins\secrets\initialAdminPassword
```

1. Open http://localhost:8080
2. Enter initial admin password
3. Install suggested plugins
4. Create admin user

### 5.3 Install Required Jenkins Plugins

Go to: Manage Jenkins → Manage Plugins → Available

Install these plugins:
- Pipeline
- Git plugin
- AWS Credentials Plugin
- Docker Pipeline
- Kubernetes CLI Plugin

### 5.4 Configure AWS Credentials in Jenkins

1. Go to: Manage Jenkins → Manage Credentials
2. Click on "(global)" domain
3. Click "Add Credentials"
4. Select "AWS Credentials"
5. Enter:
   - ID: `aws-access-key`
   - Access Key ID: (from step 1.1)
   - Secret Access Key: (from step 1.1)
6. Click "OK"

### 5.5 Create Jenkins Pipeline Job

1. Click "New Item"
2. Enter name: "mlops-pipeline"
3. Select "Pipeline"
4. Click "OK"
5. Under "Pipeline" section:
   - Definition: "Pipeline script from SCM"
   - SCM: "Git"
   - Repository URL: `https://github.com/SrinathMLOps/cicdendtoendwithmlops.git`
   - Branch: `*/main`
   - Script Path: `Jenkinsfile`
6. Click "Save"

---

## 6. Docker Setup

### 6.1 Test Docker Build Locally

```bash
# Build image
docker build -t mlops-serving:test .

# Run container
docker run -d -p 8000:8000 --name test_app mlops-serving:test

# Test API
curl http://localhost:8000/
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"features": [5.1, 3.5, 1.4, 0.2]}'

# Stop and remove
docker stop test_app
docker rm test_app
```

### 6.2 Login to ECR

```bash
# Get login command
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com
```

---

## 7. Kubernetes (EKS) Setup

### 7.1 Configure kubectl for EKS

```bash
# Update kubeconfig
aws eks update-kubeconfig --region us-east-1 --name mlops-cluster

# Verify connection
kubectl get nodes
kubectl get namespaces
```

### 7.2 Create Kubernetes Namespace

```bash
kubectl create namespace mlops

# Set as default namespace (optional)
kubectl config set-context --current --namespace=mlops
```

### 7.3 Deploy Application to EKS

```bash
# Apply Kubernetes manifests
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml

# Check deployment status
kubectl get deployments
kubectl get pods
kubectl get services

# Get service URL
kubectl get service mlops-serving -o wide
```

### 7.4 Test Deployment

```bash
# Port forward to test locally
kubectl port-forward service/mlops-serving 8000:80

# Test in another terminal
curl http://localhost:8000/
```

---

## 8. Running the Pipeline

### 8.1 Push Code to GitHub

```bash
# Initialize git repository
git init
git add .
git commit -m "Initial commit: MLOps project setup"

# Add remote and push
git remote add origin https://github.com/SrinathMLOps/cicdendtoendwithmlops.git
git branch -M main
git push -u origin main
```

### 8.2 Trigger Jenkins Pipeline

**Option A: Manual Trigger**
1. Go to Jenkins dashboard
2. Click on "mlops-pipeline"
3. Click "Build Now"

**Option B: Automatic Trigger (Webhook)**
1. In GitHub repo: Settings → Webhooks → Add webhook
2. Payload URL: `http://YOUR_JENKINS_URL:8080/github-webhook/`
3. Content type: `application/json`
4. Select "Just the push event"
5. Click "Add webhook"

### 8.3 Monitor Pipeline Execution

1. Click on build number (e.g., #1)
2. Click "Console Output" to see logs
3. Watch each stage execute:
   - Checkout Code
   - Verify Environment
   - Install Dependencies
   - Start MLflow Server
   - DVC Pull
   - Train Model
   - Show Metrics
   - MLflow Model Registry
   - Approve Promotion (manual step)
   - Promote Model
   - Push Artifacts
   - Build Docker Image
   - Test Docker Image
   - Login to ECR
   - Push to ECR
   - Deploy to EKS

### 8.4 Approve Production Deployment

When pipeline reaches "Approve Promotion" stage:
1. Click on the build
2. Click "Proceed" to approve
3. Or click "Abort" to cancel

---

## 9. Troubleshooting

### Common Issues

**Issue: DVC push fails**
```bash
# Check AWS credentials
aws sts get-caller-identity

# Check S3 bucket access
aws s3 ls s3://${BUCKET_NAME}

# Re-configure DVC remote
dvc remote modify myremote access_key_id YOUR_KEY
dvc remote modify myremote secret_access_key YOUR_SECRET
```

**Issue: Docker build fails**
```bash
# Check Docker is running
docker ps

# Clean up Docker
docker system prune -a

# Rebuild with no cache
docker build --no-cache -t mlops-serving:test .
```

**Issue: kubectl cannot connect to EKS**
```bash
# Update kubeconfig
aws eks update-kubeconfig --region us-east-1 --name mlops-cluster

# Check AWS credentials
aws sts get-caller-identity

# Verify cluster exists
aws eks describe-cluster --name mlops-cluster --region us-east-1
```

**Issue: Jenkins cannot access AWS**
```bash
# Verify credentials in Jenkins
# Go to: Manage Jenkins → Manage Credentials
# Check that aws-access-key exists

# Test in Jenkins pipeline:
withCredentials([[$class: 'AmazonWebServicesCredentialsBinding',
                  credentialsId: 'aws-access-key']]) {
    sh 'aws sts get-caller-identity'
}
```

**Issue: ECR login fails**
```bash
# Get fresh login token
aws ecr get-login-password --region us-east-1

# Verify ECR repository exists
aws ecr describe-repositories --region us-east-1
```

### Logs and Debugging

```bash
# Check Jenkins logs
docker logs jenkins

# Check Kubernetes pod logs
kubectl logs <pod-name>

# Describe pod for events
kubectl describe pod <pod-name>

# Check DVC logs
dvc doctor

# Check Docker logs
docker logs <container-name>
```

---

## Next Steps

1. Set up monitoring with Prometheus/Grafana
2. Implement model versioning strategy
3. Add automated testing (unit, integration)
4. Set up alerts for model performance degradation
5. Implement A/B testing for model deployment
6. Add CI/CD for infrastructure (Terraform)

## Support

For issues and questions:
- Check logs in respective services
- Review AWS CloudWatch logs
- Check Jenkins console output
- Review Kubernetes events: `kubectl get events`
