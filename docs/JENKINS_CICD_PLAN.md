# Jenkins CI/CD Pipeline Plan
## LLM_Judge Project

---

## Overview

This plan establishes a Jenkins-based CI/CD pipeline for running unit and integration tests on-demand ("click of a button") with a clear path to automated deployments.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              DEVELOPER WORKFLOW                                  │
│                                                                                  │
│  ┌──────────┐     ┌──────────┐     ┌──────────────────────────────────────────┐ │
│  │Developer │────▶│  GitHub  │────▶│              JENKINS                     │ │
│  │  Push    │     │   Repo   │     │                                          │ │
│  └──────────┘     └──────────┘     │  ┌─────────────────────────────────────┐ │ │
│                         │          │  │         PIPELINE STAGES              │ │ │
│                         │          │  │                                      │ │ │
│                         ▼          │  │  ┌─────────┐  ┌─────────┐  ┌───────┐│ │ │
│                    Webhook         │  │  │ Build   │─▶│  Test   │─▶│Deploy ││ │ │
│                    Trigger         │  │  │ Images  │  │Unit+Int │  │(Manual)│ │ │
│                         │          │  │  └─────────┘  └─────────┘  └───────┘│ │ │
│                         ▼          │  │                                      │ │ │
│              ┌──────────────────┐  │  └─────────────────────────────────────┘ │ │
│              │  Jenkins Master  │◀─┘                                          │ │
│              │  (K8s Pod)       │                                             │ │
│              └────────┬─────────┘                                             │ │
│                       │                                                        │ │
│                       ▼                                                        │ │
│              ┌──────────────────┐                                             │ │
│              │  Jenkins Agents  │  Dynamic pods spun up per build             │ │
│              │  (K8s Pods)      │                                             │ │
│              └────────┬─────────┘                                             │ │
│                       │                                                        │ │
│                       ▼                                                        │ │
│  ┌────────────────────────────────────────────────────────────────────────┐   │
│  │                        TEST ENVIRONMENT                                 │   │
│  │                                                                         │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐          │   │
│  │  │ Gateway │ │Inference│ │  Judge  │ │  Redis  │ │Persiste.│          │   │
│  │  │ :8000   │ │ :8003   │ │ :8004   │ │ :8001   │ │ :8002   │          │   │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘          │   │
│  │                                                                         │   │
│  │  ┌─────────────────┐  ┌─────────────────┐                              │   │
│  │  │   Redis :6379   │  │   MySQL :3306   │   (Ephemeral test DBs)       │   │
│  │  └─────────────────┘  └─────────────────┘                              │   │
│  └────────────────────────────────────────────────────────────────────────┘   │
│                                                                                │
└────────────────────────────────────────────────────────────────────────────────┘
```

---

## Git Branching Strategy

```
main (production)
  │
  ├── develop (integration branch)
  │     │
  │     ├── feature/add-new-judge-model
  │     ├── feature/improve-inference-latency
  │     └── bugfix/fix-redis-timeout
  │
  └── release/v1.2.0 (release candidates)
```

### Branch Rules

| Branch | Trigger | Tests Run | Deploy To |
|--------|---------|-----------|-----------|
| `feature/*`, `bugfix/*` | Push | Unit only | None |
| `develop` | PR merge | Unit + Integration | Dev/Staging (auto) |
| `release/*` | Manual | Unit + Integration + E2E | Staging (auto) |
| `main` | PR merge from release | Full suite | Production (manual approval) |

### Your "Click of a Button" Scenarios

1. **Quick Test (Feature Branch)**
   - Click "Build Now" on any branch
   - Runs unit tests in ~2-3 mins
   - No deployment

2. **Full Test (Develop/Release)**
   - Click "Build with Parameters"
   - Select: `RUN_INTEGRATION_TESTS=true`
   - Spins up full Docker Compose stack
   - Runs all 153 tests
   - Tears down after completion

3. **Deploy to Staging**
   - Click "Build with Parameters"
   - Select: `DEPLOY_TO=staging`
   - Runs tests → Builds images → Deploys to K8s

---

## Jenkins Deployment Options

### Option A: Jenkins in Your Kubernetes Cluster (Recommended)

```
┌─────────────────────────────────────────────────┐
│           Your Kubernetes Cluster                │
│                                                  │
│  ┌─────────────────┐  ┌─────────────────────┐   │
│  │ Jenkins Master  │  │  LLM_Judge Services │   │
│  │ (Namespace:     │  │  (Namespace:        │   │
│  │  jenkins)       │  │   llm-judge)        │   │
│  └────────┬────────┘  └─────────────────────┘   │
│           │                                      │
│           ▼                                      │
│  ┌─────────────────┐                            │
│  │ Jenkins Agents  │  Ephemeral pods for builds │
│  │ (Dynamic Pods)  │                            │
│  └─────────────────┘                            │
└─────────────────────────────────────────────────┘
```

**Pros:**
- Agents scale dynamically (Kubernetes plugin)
- Same cluster = easy to deploy to staging namespace
- No external infrastructure needed
- Agents have Docker-in-Docker for building images

**Cons:**
- Shares resources with your app (can isolate with node selectors)

### Option B: Standalone Jenkins Server

```
┌──────────────────┐         ┌─────────────────────────┐
│  Jenkins Server  │────────▶│  Kubernetes Cluster     │
│  (EC2/VM)        │  kubectl│  (LLM_Judge Services)   │
│                  │         │                         │
│  - Docker        │         │                         │
│  - kubectl       │         │                         │
└──────────────────┘         └─────────────────────────┘
```

**Pros:**
- Isolated from production workloads
- Persistent (no pod restarts)

**Cons:**
- Extra infrastructure to manage
- Need to configure kubectl access

### Recommendation: Option A (Jenkins in K8s)

For your setup, running Jenkins in Kubernetes makes sense because:
1. You already have K8s manifests
2. Dynamic agents = no idle resources
3. Easy transition to EKS later

---

## Pipeline Stages Explained

### Stage 1: Checkout

```groovy
stage('Checkout') {
    steps {
        checkout scm
        // or specific branch:
        git branch: 'develop', url: 'https://github.com/your-org/LLM_Judge.git'
    }
}
```

**What happens:**
- Jenkins clones your repo from GitHub
- Branch determined by: webhook trigger, manual selection, or Jenkinsfile config

---

### Stage 2: Build Base Image

```groovy
stage('Build Base Image') {
    steps {
        sh 'docker build -f docker/Dockerfile.base -t llm-judge-base:${BUILD_NUMBER} .'
    }
}
```

**What happens:**
- Builds the shared base image with all Python dependencies
- Tagged with build number for traceability
- Cached layers speed up subsequent builds

---

### Stage 3: Build Service Images

```groovy
stage('Build Services') {
    parallel {
        stage('Gateway') {
            steps {
                sh 'docker build -f ingress_gateway_service/Dockerfile -t gateway:${BUILD_NUMBER} .'
            }
        }
        stage('Inference') {
            steps {
                sh 'docker build -f external_inference_service/Dockerfile -t inference:${BUILD_NUMBER} .'
            }
        }
        // ... other services
    }
}
```

**What happens:**
- Builds all 5 service images in parallel
- Each image tagged with build number
- Uses base image from Stage 2

---

### Stage 4: Unit Tests

```groovy
stage('Unit Tests') {
    steps {
        sh '''
            docker run --rm \
                -v ${WORKSPACE}/tests:/app/tests \
                -v ${WORKSPACE}/test-results:/app/test-results \
                llm-judge-base:${BUILD_NUMBER} \
                pytest tests/unit/ \
                    --junitxml=test-results/unit-results.xml \
                    -v
        '''
    }
    post {
        always {
            junit 'test-results/unit-results.xml'
        }
    }
}
```

**What happens:**
- Runs pytest against `tests/unit/` directory
- No external services needed (mocked)
- Results published to Jenkins UI
- ~2-3 minutes

---

### Stage 5: Integration Tests

```groovy
stage('Integration Tests') {
    when {
        anyOf {
            branch 'develop'
            branch 'release/*'
            branch 'main'
            expression { params.RUN_INTEGRATION_TESTS == true }
        }
    }
    steps {
        sh '''
            # Start test infrastructure
            docker-compose -f docker-compose.test.yml up -d

            # Wait for services to be healthy
            ./scripts/wait-for-services.sh

            # Run integration tests
            docker run --rm \
                --network llm-judge-test-network \
                -e LOCAL_MODE=true \
                -e REDIS_HOST=redis \
                -e MYSQL_HOST=mysql \
                -v ${WORKSPACE}/tests:/app/tests \
                llm-judge-base:${BUILD_NUMBER} \
                pytest tests/integration/ \
                    --junitxml=test-results/integration-results.xml \
                    -v

            # Cleanup
            docker-compose -f docker-compose.test.yml down -v
        '''
    }
}
```

**What happens:**
1. Spins up Redis + MySQL + mock SQS/SNS using Docker Compose
2. Waits for health checks to pass
3. Runs integration tests against real (local) services
4. Tests service-to-service communication
5. Tears down everything after
6. ~5-10 minutes

---

### Stage 6: Push Images (On Success)

```groovy
stage('Push to Registry') {
    when {
        anyOf {
            branch 'develop'
            branch 'release/*'
            branch 'main'
        }
    }
    steps {
        withCredentials([usernamePassword(credentialsId: 'docker-registry', ...)]) {
            sh '''
                docker tag gateway:${BUILD_NUMBER} your-registry/llm-judge/gateway:${BUILD_NUMBER}
                docker push your-registry/llm-judge/gateway:${BUILD_NUMBER}
                // ... other services
            '''
        }
    }
}
```

**What happens:**
- Tags images with registry prefix
- Pushes to Docker Hub, ECR, or private registry
- Only on protected branches (not feature branches)

---

### Stage 7: Deploy to Staging

```groovy
stage('Deploy to Staging') {
    when {
        branch 'develop'
    }
    steps {
        sh '''
            # Update image tags in K8s manifests
            sed -i "s|image:.*gateway.*|image: your-registry/llm-judge/gateway:${BUILD_NUMBER}|g" \
                local/k8s/gateway-service.yaml

            # Apply to staging namespace
            kubectl apply -f local/k8s/ -n llm-judge-staging
        '''
    }
}
```

**What happens:**
- Updates Kubernetes manifests with new image tags
- Applies to staging namespace
- K8s handles rolling update

---

### Stage 8: Deploy to Production (Manual Approval)

```groovy
stage('Deploy to Production') {
    when {
        branch 'main'
    }
    steps {
        input message: 'Deploy to Production?', ok: 'Deploy'

        sh '''
            kubectl apply -f local/k8s/ -n llm-judge-prod
        '''
    }
}
```

**What happens:**
- Pipeline pauses and waits for human approval
- Click "Deploy" in Jenkins UI to proceed
- Applies to production namespace

---

## How Tests Run In Your Setup

### Unit Tests (tests/unit/)

```
┌─────────────────────────────────────────────────────────────────┐
│                     UNIT TEST EXECUTION                          │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Docker Container                             │   │
│  │                                                           │   │
│  │  pytest tests/unit/                                       │   │
│  │    ├── test_gateway_service.py     (mocked Redis/SNS)    │   │
│  │    ├── test_inference_service.py   (mocked OpenAI)       │   │
│  │    ├── test_judge_service.py       (mocked persistence)  │   │
│  │    ├── test_objects.py             (pure unit tests)     │   │
│  │    └── test_queue.py               (mocked SQS)          │   │
│  │                                                           │   │
│  │  Dependencies: Mocked via pytest fixtures in conftest.py │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  No external services needed. Fast. Isolated.                   │
└─────────────────────────────────────────────────────────────────┘
```

### Integration Tests (tests/integration/)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                   INTEGRATION TEST EXECUTION                             │
│                                                                          │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                 Docker Compose Test Stack                          │  │
│  │                                                                    │  │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐ │  │
│  │  │ Gateway │  │Inference│  │  Judge  │  │Redis Svc│  │Persist. │ │  │
│  │  │  :8000  │  │  :8003  │  │  :8004  │  │  :8001  │  │  :8002  │ │  │
│  │  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘ │  │
│  │       │            │            │            │            │       │  │
│  │       └────────────┴─────┬──────┴────────────┴────────────┘       │  │
│  │                          │                                        │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐   │  │
│  │  │ Redis:6379  │  │ MySQL:3306  │  │ LocalStack (SQS/SNS)    │   │  │
│  │  │ (real)      │  │ (real)      │  │ or Local Mock Services  │   │  │
│  │  └─────────────┘  └─────────────┘  └─────────────────────────┘   │  │
│  │                                                                    │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  Tests verify:                                                           │
│  - Gateway → Redis state storage                                         │
│  - Gateway → SNS message publishing                                      │
│  - Inference service → SQS consumption → Redis update                   │
│  - Judge service → Persistence service → MySQL                          │
│  - End-to-end request flow                                               │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## File Structure for Jenkins

```
LLM_Judge/
├── Jenkinsfile                          # Main pipeline definition
├── jenkins/
│   ├── Jenkinsfile.unit                 # Unit tests only pipeline
│   ├── Jenkinsfile.integration          # Integration tests pipeline
│   ├── Jenkinsfile.deploy               # Deployment pipeline
│   └── agents/
│       └── docker-agent.yaml            # K8s pod template for agents
├── docker/
│   ├── Dockerfile.base                  # Base image (exists)
│   └── Dockerfile.test                  # Test runner image
├── docker-compose.yml                   # Local dev (exists)
├── docker-compose.test.yml              # CI test environment
└── scripts/
    ├── wait-for-services.sh             # Health check waiter
    ├── run-unit-tests.sh                # Unit test wrapper
    └── run-integration-tests.sh         # Integration test wrapper
```

---

## Complete Jenkinsfile

```groovy
// Jenkinsfile
pipeline {
    agent {
        kubernetes {
            yaml '''
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: docker
    image: docker:24-dind
    securityContext:
      privileged: true
    volumeMounts:
    - name: docker-socket
      mountPath: /var/run/docker.sock
  - name: kubectl
    image: bitnami/kubectl:latest
    command: ['sleep', 'infinity']
  volumes:
  - name: docker-socket
    emptyDir: {}
'''
        }
    }

    parameters {
        booleanParam(name: 'RUN_INTEGRATION_TESTS', defaultValue: false,
            description: 'Run integration tests (slower, requires Docker Compose)')
        choice(name: 'DEPLOY_TO', choices: ['none', 'staging', 'production'],
            description: 'Deploy after successful tests')
    }

    environment {
        DOCKER_REGISTRY = 'your-registry.com/llm-judge'
        KUBECONFIG = credentials('kubeconfig')
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                script {
                    env.GIT_COMMIT_SHORT = sh(script: 'git rev-parse --short HEAD', returnStdout: true).trim()
                    env.IMAGE_TAG = "${env.BUILD_NUMBER}-${env.GIT_COMMIT_SHORT}"
                }
            }
        }

        stage('Build Base Image') {
            steps {
                container('docker') {
                    sh '''
                        docker build -f docker/Dockerfile.base \
                            -t llm-judge-base:${IMAGE_TAG} .
                    '''
                }
            }
        }

        stage('Build Service Images') {
            parallel {
                stage('Gateway') {
                    steps {
                        container('docker') {
                            sh 'docker build -f ingress_gateway_service/Dockerfile -t gateway:${IMAGE_TAG} .'
                        }
                    }
                }
                stage('Inference') {
                    steps {
                        container('docker') {
                            sh 'docker build -f external_inference_service/Dockerfile -t inference:${IMAGE_TAG} .'
                        }
                    }
                }
                stage('Judge') {
                    steps {
                        container('docker') {
                            sh 'docker build -f judge_service/Dockerfile -t judge:${IMAGE_TAG} .'
                        }
                    }
                }
                stage('Redis Service') {
                    steps {
                        container('docker') {
                            sh 'docker build -f redis_service/Dockerfile -t redis-svc:${IMAGE_TAG} .'
                        }
                    }
                }
                stage('Persistence') {
                    steps {
                        container('docker') {
                            sh 'docker build -f persistence_service/Dockerfile -t persistence:${IMAGE_TAG} .'
                        }
                    }
                }
            }
        }

        stage('Unit Tests') {
            steps {
                container('docker') {
                    sh '''
                        docker run --rm \
                            -v ${WORKSPACE}:/app \
                            -w /app \
                            llm-judge-base:${IMAGE_TAG} \
                            pytest tests/unit/ \
                                --junitxml=test-results/unit-results.xml \
                                --cov=. \
                                --cov-report=xml:test-results/coverage.xml \
                                -v
                    '''
                }
            }
            post {
                always {
                    junit 'test-results/unit-results.xml'
                    publishCoverage adapters: [coberturaAdapter('test-results/coverage.xml')]
                }
            }
        }

        stage('Integration Tests') {
            when {
                anyOf {
                    branch 'develop'
                    branch pattern: 'release/.*', comparator: 'REGEXP'
                    branch 'main'
                    expression { params.RUN_INTEGRATION_TESTS == true }
                }
            }
            steps {
                container('docker') {
                    sh '''
                        # Create test network
                        docker network create llm-judge-test || true

                        # Start dependencies
                        docker run -d --name redis-test --network llm-judge-test redis:7-alpine
                        docker run -d --name mysql-test --network llm-judge-test \
                            -e MYSQL_ROOT_PASSWORD=test \
                            -e MYSQL_DATABASE=llm_judge \
                            mysql:8.0

                        # Wait for MySQL
                        sleep 30

                        # Start services in LOCAL_MODE
                        docker run -d --name gateway-test --network llm-judge-test \
                            -e LOCAL_MODE=true gateway:${IMAGE_TAG}
                        docker run -d --name redis-svc-test --network llm-judge-test \
                            -e LOCAL_MODE=true \
                            -e REDIS_HOST=redis-test \
                            redis-svc:${IMAGE_TAG}

                        # Wait for services
                        sleep 15

                        # Run integration tests
                        docker run --rm \
                            --network llm-judge-test \
                            -e LOCAL_MODE=true \
                            -e REDIS_HOST=redis-test \
                            -e MYSQL_HOST=mysql-test \
                            -v ${WORKSPACE}:/app \
                            -w /app \
                            llm-judge-base:${IMAGE_TAG} \
                            pytest tests/integration/ \
                                --junitxml=test-results/integration-results.xml \
                                -v

                        # Cleanup
                        docker stop gateway-test redis-svc-test redis-test mysql-test || true
                        docker rm gateway-test redis-svc-test redis-test mysql-test || true
                        docker network rm llm-judge-test || true
                    '''
                }
            }
            post {
                always {
                    junit 'test-results/integration-results.xml'
                }
                failure {
                    container('docker') {
                        sh '''
                            docker logs gateway-test || true
                            docker logs redis-svc-test || true
                        '''
                    }
                }
            }
        }

        stage('Push Images') {
            when {
                anyOf {
                    branch 'develop'
                    branch pattern: 'release/.*', comparator: 'REGEXP'
                    branch 'main'
                }
            }
            steps {
                container('docker') {
                    withCredentials([usernamePassword(
                        credentialsId: 'docker-registry-creds',
                        usernameVariable: 'DOCKER_USER',
                        passwordVariable: 'DOCKER_PASS'
                    )]) {
                        sh '''
                            echo $DOCKER_PASS | docker login -u $DOCKER_USER --password-stdin ${DOCKER_REGISTRY}

                            for service in gateway inference judge redis-svc persistence; do
                                docker tag ${service}:${IMAGE_TAG} ${DOCKER_REGISTRY}/${service}:${IMAGE_TAG}
                                docker push ${DOCKER_REGISTRY}/${service}:${IMAGE_TAG}

                                # Also tag as latest for develop branch
                                if [ "${BRANCH_NAME}" = "develop" ]; then
                                    docker tag ${service}:${IMAGE_TAG} ${DOCKER_REGISTRY}/${service}:latest
                                    docker push ${DOCKER_REGISTRY}/${service}:latest
                                fi
                            done
                        '''
                    }
                }
            }
        }

        stage('Deploy to Staging') {
            when {
                anyOf {
                    branch 'develop'
                    expression { params.DEPLOY_TO == 'staging' }
                }
            }
            steps {
                container('kubectl') {
                    sh '''
                        # Update image tags using kustomize or sed
                        cd local/k8s

                        for service in gateway invoke judge redis persistence; do
                            sed -i "s|image:.*${service}.*|image: ${DOCKER_REGISTRY}/${service}:${IMAGE_TAG}|g" \
                                ${service}-service.yaml
                        done

                        kubectl apply -f . -n llm-judge-staging
                        kubectl rollout status deployment -n llm-judge-staging --timeout=300s
                    '''
                }
            }
        }

        stage('Deploy to Production') {
            when {
                anyOf {
                    branch 'main'
                    expression { params.DEPLOY_TO == 'production' }
                }
            }
            steps {
                input message: 'Deploy to Production?', ok: 'Deploy'

                container('kubectl') {
                    sh '''
                        cd local/k8s

                        for service in gateway invoke judge redis persistence; do
                            sed -i "s|image:.*${service}.*|image: ${DOCKER_REGISTRY}/${service}:${IMAGE_TAG}|g" \
                                ${service}-service.yaml
                        done

                        kubectl apply -f . -n llm-judge-prod
                        kubectl rollout status deployment -n llm-judge-prod --timeout=300s
                    '''
                }
            }
        }
    }

    post {
        always {
            cleanWs()
        }
        success {
            slackSend(color: 'good', message: "✅ Build #${BUILD_NUMBER} succeeded on ${BRANCH_NAME}")
        }
        failure {
            slackSend(color: 'danger', message: "❌ Build #${BUILD_NUMBER} failed on ${BRANCH_NAME}")
        }
    }
}
```

---

## Jenkins Installation in Kubernetes

### Helm Installation

```bash
# Add Jenkins Helm repo
helm repo add jenkins https://charts.jenkins.io
helm repo update

# Create namespace
kubectl create namespace jenkins

# Create values file
cat <<EOF > jenkins-values.yaml
controller:
  serviceType: LoadBalancer  # or NodePort for local
  adminUser: admin
  adminPassword: your-secure-password

  installPlugins:
    - kubernetes:latest
    - workflow-aggregator:latest
    - git:latest
    - github:latest
    - docker-workflow:latest
    - pipeline-utility-steps:latest
    - junit:latest
    - cobertura:latest
    - slack:latest

  JCasC:
    configScripts:
      welcome-message: |
        jenkins:
          systemMessage: "LLM_Judge CI/CD Server"

agent:
  enabled: true
  # Dynamic agents in K8s
  podTemplates:
    - name: "docker"
      label: "docker"
      containers:
        - name: "docker"
          image: "docker:24-dind"
          privileged: true

persistence:
  enabled: true
  size: 20Gi

rbac:
  create: true
  readSecrets: true
EOF

# Install Jenkins
helm install jenkins jenkins/jenkins \
  --namespace jenkins \
  --values jenkins-values.yaml
```

### Get Admin Password

```bash
kubectl exec -n jenkins -it svc/jenkins -c jenkins -- /bin/cat /run/secrets/additional/chart-admin-password
```

### Access Jenkins

```bash
# Port forward
kubectl port-forward -n jenkins svc/jenkins 8080:8080

# Open http://localhost:8080
```

---

## "Click of a Button" - How It Works

### Scenario 1: Run Tests on Feature Branch

1. Open Jenkins UI → Your Pipeline
2. Click **"Build Now"**
3. Jenkins:
   - Checks out your feature branch
   - Builds base image
   - Builds all service images (parallel)
   - Runs unit tests
   - Reports results
4. You see: ✅ or ❌ with test results

### Scenario 2: Run Full Test Suite

1. Open Jenkins UI → Your Pipeline
2. Click **"Build with Parameters"**
3. Check ☑️ `RUN_INTEGRATION_TESTS`
4. Click **"Build"**
5. Jenkins:
   - All unit test steps +
   - Spins up Docker Compose test stack
   - Runs integration tests
   - Tears down stack
   - Reports all results

### Scenario 3: Deploy to Staging

1. Open Jenkins UI → Your Pipeline
2. Click **"Build with Parameters"**
3. Select `DEPLOY_TO: staging`
4. Click **"Build"**
5. Jenkins:
   - Runs tests
   - Pushes images to registry
   - Updates K8s manifests
   - Deploys to staging namespace
   - Verifies rollout

### Scenario 4: Deploy to Production

1. Merge PR to `main` branch
2. Pipeline runs automatically
3. After tests pass, pipeline **pauses**
4. You click **"Deploy"** in Jenkins UI
5. Deployment proceeds to production

---

## Summary

| Question | Answer |
|----------|--------|
| **Where does Jenkins run?** | In your K8s cluster (separate namespace) |
| **Which branch triggers builds?** | All branches on push; deploy only on develop/main |
| **How do I run tests manually?** | Click "Build Now" or "Build with Parameters" |
| **How long do tests take?** | Unit: ~3 min, Integration: ~8 min |
| **How does deployment work?** | Automatic to staging, manual approval for prod |
| **What about EKS?** | Same setup, just update kubeconfig credentials |

---

## Next Steps

1. **Install Jenkins** in your cluster using Helm
2. **Create credentials** for Docker registry and kubeconfig
3. **Add Jenkinsfile** to your repo
4. **Create pipeline** in Jenkins pointing to your repo
5. **Configure webhook** in GitHub for automatic triggers
