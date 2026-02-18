pipeline {
    agent any
    
    environment {
        AWS_REGION = "us-east-1"
        ECR_REPO = "<ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/mlops-serving"
        IMAGE_TAG = "${BUILD_NUMBER}"
        PATH = "$PATH:$HOME/.local/bin"
        MLFLOW_TRACKING_URI = "http://mlflow-server:5000"
    }
    
    stages {
        stage('Checkout Code') {
            steps {
                git branch: 'main',
                    url: 'https://github.com/SrinathMLOps/cicdendtoendwithmlops.git'
            }
        }
        
        stage('Verify Environment & AWS Access') {
            steps {
                withCredentials([[$class: 'AmazonWebServicesCredentialsBinding',
                                  credentialsId: 'aws-access-key']]) {
                    sh '''
                        python3 --version
                        aws sts get-caller-identity
                        echo "MLflow Tracking URI: $MLFLOW_TRACKING_URI"
                    '''
                }
            }
        }
        
        stage('Install Dependencies') {
            steps {
                sh '''
                    pip3 install --user -r requirements.txt
                    pip3 install --user "dvc[s3]"
                '''
            }
        }
        
        stage('Start MLflow Server') {
            steps {
                script {
                    try {
                        sh '''
                            # Check if MLflow is already running
                            if ! curl -s http://localhost:5000 > /dev/null; then
                                echo "Starting MLflow server..."
                                docker-compose up -d mlflow
                                sleep 10
                            else
                                echo "MLflow server already running"
                            fi
                        '''
                    } catch (Exception e) {
                        echo "⚠️ MLflow server start failed, continuing without MLflow: ${e.message}"
                    }
                }
            }
        }
        
        stage('DVC Pull (from S3)') {
            steps {
                withCredentials([[$class: 'AmazonWebServicesCredentialsBinding',
                                  credentialsId: 'aws-access-key']]) {
                    sh 'dvc pull --force || echo "No data to pull"'
                }
            }
        }
        
        stage('Train Model (Staging)') {
            steps {
                withCredentials([[$class: 'AmazonWebServicesCredentialsBinding',
                                  credentialsId: 'aws-access-key']]) {
                    sh '''
                        export MLFLOW_TRACKING_URI=http://localhost:5000
                        dvc repro
                    '''
                }
            }
        }
        
        stage('Show Metrics') {
            steps {
                sh '''
                    echo "=== DVC Metrics ==="
                    dvc metrics show
                    echo ""
                    echo "=== Training Metrics ==="
                    cat metrics/train_metrics.json
                    echo ""
                    echo "=== Evaluation Metrics ==="
                    cat metrics/eval_metrics.json
                '''
            }
        }
        
        stage('MLflow Model Registry') {
            steps {
                script {
                    try {
                        sh '''
                            export MLFLOW_TRACKING_URI=http://localhost:5000
                            python3 -c "
import mlflow
from mlflow.tracking import MlflowClient
import yaml

with open('params.yaml', 'r') as f:
    params = yaml.safe_load(f)

mlflow.set_tracking_uri('http://localhost:5000')
client = MlflowClient()

# Get latest model version
model_name = params['mlflow']['model_name']
versions = client.search_model_versions(f\\"name='{model_name}'\\"")
if versions:
    latest = versions[0]
    print(f'📦 Latest Model Version: {latest.version}')
    print(f'🔗 MLflow UI: http://localhost:5000')
else:
    print('⚠️ No model versions found')
"
                        '''
                    } catch (Exception e) {
                        echo "⚠️ MLflow registry check failed: ${e.message}"
                    }
                }
            }
        }
        
        stage('Approve Promotion') {
            steps {
                script {
                    def metricsFile = readFile('metrics/eval_metrics.json')
                    def metrics = readJSON text: metricsFile
                    echo "Model Accuracy: ${metrics.accuracy}"
                    
                    input message: "Approve promotion of model to PRODUCTION? (Accuracy: ${metrics.accuracy})"
                }
            }
        }
        
        stage('Promote Model (Production)') {
            steps {
                withCredentials([[$class: 'AmazonWebServicesCredentialsBinding',
                                  credentialsId: 'aws-access-key']]) {
                    sh '''
                        export MLFLOW_TRACKING_URI=http://localhost:5000
                        dvc repro -s promote
                    '''
                }
            }
        }
        
        stage('Push Artifacts to S3') {
            steps {
                withCredentials([[$class: 'AmazonWebServicesCredentialsBinding',
                                  credentialsId: 'aws-access-key']]) {
                    sh 'dvc push'
                }
            }
        }
        
        /* ======================= CD STAGES ======================= */
        
        stage('Build Docker Image') {
            steps {
                sh '''
                    docker build -t mlops-serving:${IMAGE_TAG} .
                '''
            }
        }
        
        stage('Test Docker Image') {
            steps {
                sh '''
                    docker run -d -p 8000:8000 --name test_container mlops-serving:${IMAGE_TAG}
                    sleep 10
                    curl http://localhost:8000/
                    curl http://localhost:8000/model-info
                    docker rm -f test_container
                '''
            }
        }
        
        stage('Login to ECR') {
            steps {
                withCredentials([[$class: 'AmazonWebServicesCredentialsBinding',
                                  credentialsId: 'aws-access-key']]) {
                    sh '''
                        aws ecr get-login-password --region $AWS_REGION | \
                        docker login --username AWS --password-stdin $ECR_REPO
                    '''
                }
            }
        }
        
        stage('Push Image to ECR') {
            steps {
                sh '''
                    docker tag mlops-serving:${IMAGE_TAG} $ECR_REPO:${IMAGE_TAG}
                    docker tag mlops-serving:${IMAGE_TAG} $ECR_REPO:latest
                    docker push $ECR_REPO:${IMAGE_TAG}
                    docker push $ECR_REPO:latest
                '''
            }
        }
        
        stage('Deploy to EKS') {
            steps {
                withCredentials([[$class: 'AmazonWebServicesCredentialsBinding',
                                  credentialsId: 'aws-access-key']]) {
                    sh '''
                        aws eks update-kubeconfig --region $AWS_REGION --name mlops-cluster
                        kubectl set image deployment/mlops-serving \
                            mlops-serving=$ECR_REPO:${IMAGE_TAG}
                        kubectl rollout status deployment/mlops-serving
                    '''
                }
            }
        }
    }
    
    post {
        success {
            echo "✅ Full MLOps pipeline (CI + CD + MLflow) completed successfully"
            echo "🔗 MLflow UI: http://localhost:5000"
        }
        failure {
            echo "❌ MLOps pipeline failed"
        }
        always {
            // Archive metrics
            archiveArtifacts artifacts: 'metrics/*.json', allowEmptyArchive: true
        }
    }
}
