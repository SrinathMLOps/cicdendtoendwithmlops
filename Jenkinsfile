pipeline {
    agent any
    
    environment {
        AWS_REGION = "us-east-1"
        ECR_REPO = "<ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/mlops-serving"
        IMAGE_TAG = "${BUILD_NUMBER}"
        PATH = "$PATH:$HOME/.local/bin"
    }
    
    stages {
        stage('Checkout Code') {
            steps {
                git branch: 'master',
                    url: 'https://github.com/<YOUR_USERNAME>/mlops-project.git'
            }
        }
        
        stage('Verify Environment & AWS Access') {
            steps {
                withCredentials([[$class: 'AmazonWebServicesCredentialsBinding',
                                  credentialsId: 'aws-access-key']]) {
                    sh '''
                        python3 --version
                        aws sts get-caller-identity
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
        
        stage('DVC Pull (from S3)') {
            steps {
                withCredentials([[$class: 'AmazonWebServicesCredentialsBinding',
                                  credentialsId: 'aws-access-key']]) {
                    sh 'dvc pull --force'
                }
            }
        }
        
        stage('Train Model (Staging)') {
            steps {
                sh 'dvc repro'
            }
        }
        
        stage('Show Metrics') {
            steps {
                sh 'dvc metrics show'
            }
        }
        
        stage('Approve Promotion') {
            steps {
                input message: 'Approve promotion of model to PRODUCTION?'
            }
        }
        
        stage('Promote Model (Production)') {
            steps {
                sh 'dvc repro -s promote'
            }
        }
        
        stage('Push Artifacts to S3') {
            steps {
                sh 'dvc push'
            }
        }
        
        /* ======================= NEW CD STAGES ======================= */
        
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
                    sleep 5
                    curl http://localhost:8000/
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
                    docker push $ECR_REPO:${IMAGE_TAG}
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
                    '''
                }
            }
        }
    }
    
    post {
        success {
            echo "✅ Full MLOps pipeline (CI + CD) completed successfully"
        }
        failure {
            echo "❌ MLOps pipeline failed"
        }
    }
}
