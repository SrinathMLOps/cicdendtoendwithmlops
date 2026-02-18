#!/bin/bash

# MLflow Setup Script for AWS

set -e

echo "🚀 Setting up MLflow infrastructure..."

# Variables
AWS_REGION=${AWS_REGION:-us-east-1}
MLFLOW_BUCKET=${MLFLOW_BUCKET:-mlflow-artifacts-bucket-$(date +%s)}

# Create S3 bucket for MLflow artifacts
echo "📦 Creating S3 bucket for MLflow artifacts..."
aws s3 mb s3://${MLFLOW_BUCKET} --region ${AWS_REGION}

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket ${MLFLOW_BUCKET} \
  --versioning-configuration Status=Enabled

echo "✅ S3 bucket created: s3://${MLFLOW_BUCKET}"

# Update params.yaml with bucket name
echo "📝 Updating params.yaml with MLflow bucket..."
sed -i "s/s3_bucket: .*/s3_bucket: ${MLFLOW_BUCKET}/" params.yaml

echo "✅ MLflow infrastructure setup complete!"
echo ""
echo "Next steps:"
echo "1. Start MLflow server: docker-compose up -d"
echo "2. Access MLflow UI: http://localhost:5000"
echo "3. Update params.yaml with your MLflow tracking URI"
