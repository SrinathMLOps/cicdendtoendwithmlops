# MLOps Project - Complete End-to-End CI/CD Pipeline with MLflow

End-to-end MLOps pipeline with Jenkins, DVC, MLflow, Docker, AWS ECR, and Kubernetes (EKS).

## Project Overview

This project demonstrates a production-ready MLOps pipeline that includes:
- **Experiment Tracking** with MLflow
- **Model Registry** with MLflow Model Registry
- **Data Version Control** with DVC (S3 backend)
- **CI/CD Automation** with Jenkins
- **Containerization** with Docker
- **Model Serving** with FastAPI
- **Orchestration** with Kubernetes (EKS)
- **Cloud Infrastructure** on AWS

## Architecture

```
GitHub → Jenkins → DVC (S3) → MLflow → Docker → ECR → EKS
   ↓         ↓         ↓          ↓        ↓      ↓      ↓
 Code    Pipeline   Data    Experiments  Image  Registry Deploy
```

## Key Features

✅ Automated model training and evaluation  
✅ Experiment tracking with MLflow  
✅ Model versioning and registry  
✅ Data versioning with DVC  
✅ Automated CI/CD pipeline  
✅ Docker containerization  
✅ Kubernetes deployment  
✅ Model promotion workflow  
✅ Production-ready serving API

## Prerequisites

- AWS Account with appropriate permissions
- Jenkins server
- Docker and Docker Compose installed
- kubectl and AWS CLI configured
- Python 3.8+
- PostgreSQL (for MLflow backend)

## Quick Start

1. **MLflow Setup**: See [MLFLOW_SETUP.md](MLFLOW_SETUP.md)
2. **Complete Setup**: See [SETUP_GUIDE.md](SETUP_GUIDE.md)

### Quick Local Test

```bash
# Install dependencies
pip install -r requirements.txt

# Start MLflow server
docker-compose up -d

# Train model
export MLFLOW_TRACKING_URI=http://localhost:5000
python src/train.py

# View experiments
# Open: http://localhost:5000

# Serve model
python src/serve.py
# Open: http://localhost:8000
```

## Project Structure

```
.
├── data/
│   └── raw/                    # Raw data (tracked by DVC)
├── src/
│   ├── train.py                # Model training with MLflow
│   ├── evaluate.py             # Model evaluation with MLflow
│   └── serve.py                # FastAPI serving app with MLflow
├── scripts/
│   └── promote.py              # Model promotion with MLflow Registry
├── models/                     # Trained models (tracked by DVC)
├── metrics/                    # Model metrics (JSON)
├── k8s/
│   ├── deployment.yaml         # App deployment
│   ├── service.yaml            # App service
│   └── mlflow-deployment.yaml  # MLflow deployment
├── .dvc/                       # DVC configuration
├── dvc.yaml                    # DVC pipeline definition
├── dvc.lock                    # DVC pipeline lock file
├── params.yaml                 # Hyperparameters + MLflow config
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Container definition
├── Jenkinsfile                 # CI/CD pipeline with MLflow
├── docker-compose.yml          # MLflow + PostgreSQL setup
├── mlflow-setup.sh             # MLflow AWS setup (Linux/Mac)
├── mlflow-setup.ps1            # MLflow AWS setup (Windows)
├── README.md                   # This file
├── SETUP_GUIDE.md              # Complete setup guide
└── MLFLOW_SETUP.md             # MLflow-specific guide
```

## Pipeline Stages

1. **Checkout Code** - Clone from GitHub
2. **Verify Environment** - Check AWS access and tools
3. **Install Dependencies** - Install Python packages
4. **Start MLflow Server** - Launch MLflow tracking server
5. **DVC Pull** - Download data from S3
6. **Train Model** - Train with MLflow tracking
7. **Show Metrics** - Display model performance
8. **MLflow Registry** - Check model versions
9. **Approve Promotion** - Manual approval gate
10. **Promote Model** - Move to production in MLflow
11. **Push Artifacts** - Upload to S3 via DVC
12. **Build Docker Image** - Create container
13. **Test Docker Image** - Validate container
14. **Login to ECR** - Authenticate with AWS
15. **Push to ECR** - Upload container image
16. **Deploy to EKS** - Deploy to Kubernetes

## License

MIT
