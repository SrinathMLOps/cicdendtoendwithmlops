# MLflow Setup Script for AWS (PowerShell)

Write-Host "🚀 Setting up MLflow infrastructure..." -ForegroundColor Green

# Variables
$AWS_REGION = if ($env:AWS_REGION) { $env:AWS_REGION } else { "us-east-1" }
$MLFLOW_BUCKET = if ($env:MLFLOW_BUCKET) { $env:MLFLOW_BUCKET } else { "mlflow-artifacts-bucket-$(Get-Date -Format 'yyyyMMddHHmmss')" }

# Create S3 bucket for MLflow artifacts
Write-Host "📦 Creating S3 bucket for MLflow artifacts..." -ForegroundColor Cyan
aws s3 mb "s3://$MLFLOW_BUCKET" --region $AWS_REGION

# Enable versioning
aws s3api put-bucket-versioning `
  --bucket $MLFLOW_BUCKET `
  --versioning-configuration Status=Enabled

Write-Host "✅ S3 bucket created: s3://$MLFLOW_BUCKET" -ForegroundColor Green

# Update params.yaml with bucket name
Write-Host "📝 Updating params.yaml with MLflow bucket..." -ForegroundColor Cyan
(Get-Content params.yaml) -replace 's3_bucket: .*', "s3_bucket: $MLFLOW_BUCKET" | Set-Content params.yaml

Write-Host "✅ MLflow infrastructure setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Start MLflow server: docker-compose up -d"
Write-Host "2. Access MLflow UI: http://localhost:5000"
Write-Host "3. Update params.yaml with your MLflow tracking URI"
