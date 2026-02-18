# MLOps Project - Complete CI/CD Pipeline

End-to-end MLOps pipeline with Jenkins, DVC, Docker, AWS ECR, and Kubernetes (EKS).

## Project Overview

This project demonstrates a production-ready MLOps pipeline that includes:
- Model training with DVC (Data Version Control)
- CI/CD automation with Jenkins
- Containerization with Docker
- Model serving with FastAPI
- Deployment to AWS EKS (Kubernetes)

## Architecture

```
GitHub → Jenkins → DVC (S3) → Docker → ECR → EKS
```

## Prerequisites

- AWS Account with appropriate permissions
- Jenkins server
- Docker installed
- kubectl and AWS CLI configured
- Python 3.8+

## Quick Start

See [SETUP_GUIDE.md](SETUP_GUIDE.md) for detailed setup instructions.

## Project Structure

```
.
├── data/
│   └── raw/              # Raw data (tracked by DVC)
├── src/
│   ├── train.py          # Model training script
│   ├── evaluate.py       # Model evaluation
│   └── serve.py          # FastAPI serving app
├── scripts/
│   └── promote.py        # Model promotion script
├── models/               # Trained models (tracked by DVC)
├── metrics/              # Model metrics
├── .dvc/                 # DVC configuration
├── dvc.yaml              # DVC pipeline definition
├── dvc.lock              # DVC pipeline lock file
├── params.yaml           # Model hyperparameters
├── requirements.txt      # Python dependencies
├── Dockerfile            # Container definition
├── Jenkinsfile           # CI/CD pipeline
└── k8s/                  # Kubernetes manifests
    ├── deployment.yaml
    └── service.yaml
```

## License

MIT
