# Python Flask Application CI-CD Pipeline Deployment on AWS EC2 using Docker, Kubernates and Github Actions.

A minimal, production-ready Flask web application designed for Kubernetes deployment, complete with a fully automated GitHub Actions CI/CD pipeline. The application serves a live response including the underlying pod hostname, making it ideal as a reference architecture or boilerplate for Python microservices running on Kubernetes.

---

## Table of Contents

- [What the Project Does](#what-the-project-does)
- [Architecture Overview](#architecture-overview)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Getting Started](#getting-started)
  - [Local Development](#local-development)
  - [Docker Deployment](#docker-deployment)
  - [Kubernetes Deployment](#kubernetes-deployment)
- [Application Details](#application-details)
- [Docker Configuration](#docker-configuration)
- [Kubernetes Manifests](#kubernetes-manifests)
  - [Deployment](#deployment)
  - [Service](#service)
- [CI/CD Pipeline](#cicd-pipeline)
  - [Pipeline Stages](#pipeline-stages)
  - [Required GitHub Secrets](#required-github-secrets)
  - [Image Versioning Strategy](#image-versioning-strategy)
- [Configuration Reference](#configuration-reference)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [Maintainer](#maintainer)

---

## What the Project Does

This project provides a containerized Flask web application that returns a simple HTML response containing:

- A static welcome message
- The `HOSTNAME` environment variable, which Kubernetes automatically sets to the pod name

The hostname display is intentional — it demonstrates that traffic is being load-balanced across multiple pod replicas, making it straightforward to verify that the deployment, service, and rolling update strategy are functioning correctly.

---

## Architecture Overview

```
Developer Machine
      |
      | git push (main branch)
      v
GitHub Repository (CC-SCE)
      |
      | triggers
      v
GitHub Actions Workflow (deploy.yml)
      |
      |-- docker build
      |-- docker push :latest
      |-- docker push :<commit-sha>
      |-- SSH into EC2
      v
Docker Hub (prasannapatil91/hello-flask-k8s)
      |
      | kubectl set image (via SSH)
      v
AWS EC2 Instance (Ubuntu 22.04, t3.micro)
      |
      | K3s Kubernetes Cluster
      |-- Deployment: flask-app (2 replicas, RollingUpdate)
      |       |-- Pod 1 (Container: Flask + Gunicorn, Port 5000)
      |       |-- Pod 2 (Container: Flask + Gunicorn, Port 5000)
      |
      |-- Service: flask-service (NodePort: 30008 -> 5000)
      v
Browser: http://<EC2-PUBLIC-IP>:30008
```

---

## Project Structure

```
CC-SCE/
├── .github/
│   └── workflows/
│       └── deploy.yml          # GitHub Actions CI/CD pipeline definition
└── my-flask-app/
    ├── app.py                  # Flask application entrypoint
    ├── requirements.txt        # Python dependencies (Flask, Gunicorn)
    ├── Dockerfile              # Multi-stage container definition
    ├── deployment.yaml         # Kubernetes Deployment manifest
    ├── service.yaml            # Kubernetes Service manifest (NodePort)
    └── CCSCEKEY.pem            # EC2 SSH key — never commit to version control
```

> **Important:** Add `CCSCEKEY.pem` to your `.gitignore` immediately. Committing private keys to a repository is a critical security vulnerability. Store the key contents in a GitHub Secret (`EC2_KEY`) for use in the pipeline.

---

## Prerequisites

Before getting started, ensure the following are available on your system:

| Requirement | Minimum Version | Purpose |
|---|---|---|
| Python | 3.11+ | Running the application locally |
| Docker | 24.x+ | Building and running the container |
| kubectl | 1.28+ | Interacting with the Kubernetes cluster |
| A Kubernetes cluster | Any | Minikube, kind, K3s, EKS, GKE, AKS |
| Docker Hub account | — | Storing and pulling images |
| GitHub account | — | Source control and Actions runner |

For the full cloud deployment as described in this guide, you will also need an AWS account with an EC2 instance running Ubuntu 22.04 and K3s installed.

---

## Getting Started

### Local Development

Clone the repository and navigate to the application directory:

```bash
git clone <repository-url>
cd my-flask-app
```

Install the Python dependencies:

```bash
pip install -r requirements.txt
```

Run the application using Flask's built-in development server:

```bash
python app.py
```

The application will be available at `http://localhost:5000`.

Note: The built-in Flask server is suitable for local development only. It is single-threaded, not fault-tolerant, and not designed for concurrent traffic. Use Gunicorn for any deployment environment.

---

### Docker Deployment

Build the Docker image from the project root (where the Dockerfile is located):

```bash
docker build -t hello-flask-k8s:latest .
```

Run the container, mapping the container's port 5000 to your host:

```bash
docker run -p 5000:5000 hello-flask-k8s:latest
```

The application will be accessible at `http://localhost:5000`.

To run the container in detached mode:

```bash
docker run -d -p 5000:5000 --name flask-app hello-flask-k8s:latest
```

To stop and remove the container:

```bash
docker stop flask-app && docker rm flask-app
```

---

### Kubernetes Deployment

Ensure your `kubectl` context is pointed at the correct cluster before applying manifests:

```bash
kubectl config current-context
```

Apply the deployment and service manifests:

```bash
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
```

Verify the deployment rolled out successfully:

```bash
kubectl rollout status deployment/flask-app
```

Confirm both pods are in a `Running` state:

```bash
kubectl get pods -o wide
```

Confirm the service is created with the correct NodePort:

```bash
kubectl get svc flask-service
```

Access the application at:

```
http://<Node-IP>:30008
```

Replace `<Node-IP>` with the external IP of your node. On AWS EC2, this is the Public IPv4 address visible in the AWS Console. Note that the IP changes every time an EC2 instance is stopped and restarted unless an Elastic IP is assigned.

---

## Application Details

**`app.py`**

```python
from flask import Flask
import os

app = Flask(__name__)

@app.route('/')
def hello():
    hostname = os.environ.get('HOSTNAME', 'unknown')
    return f'''
    <h1>Hello World!</h1>
    <p>Running on Kubernetes</p>
    <p>Pod: {hostname}</p>
    '''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

The application binds to `0.0.0.0` rather than `127.0.0.1` so that it is reachable from outside the container. The `HOSTNAME` environment variable is injected automatically by Kubernetes at pod creation time and corresponds to the pod's name (e.g., `flask-app-5459cb8657-cdfh9`).

**`requirements.txt`**

```
flask==3.0.0
gunicorn==21.2.0
```

Dependencies are pinned to exact versions to ensure reproducible builds. Flask is the web framework, and Gunicorn is the production-grade WSGI HTTP server that handles concurrent requests and process management.

---

## Docker Configuration

**`Dockerfile`**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
```

Key decisions in this Dockerfile:

- **`python:3.11-slim`** — Uses the slim variant of the official Python image to minimize the final image size by excluding development tools and documentation that are unnecessary at runtime.
- **Dependency layer first** — `requirements.txt` is copied and installed before the application source code. Docker caches layers, so if only `app.py` changes, the dependency installation layer is reused, significantly speeding up subsequent builds.
- **`--no-cache-dir`** — Prevents pip from storing downloaded packages locally inside the image, reducing image size.
- **Gunicorn as the CMD** — The container starts Gunicorn directly, bypassing Flask's development server entirely. Gunicorn manages multiple worker processes and handles the WSGI protocol between the HTTP request and the Flask application.

---

## Kubernetes Manifests

### Deployment

**`deployment.yaml`**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: flask-app
spec:
  replicas: 2
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1
      maxSurge: 1
  selector:
    matchLabels:
      app: flask-app
  template:
    metadata:
      labels:
        app: flask-app
    spec:
      containers:
      - name: flask-app
        image: prasannapatil91/hello-flask-k8s:latest
        imagePullPolicy: Always
        ports:
        - containerPort: 5000
```

Key configuration decisions:

- **`replicas: 2`** — Runs two pod instances simultaneously. If one pod crashes or is evicted, the other continues serving traffic while Kubernetes reconciles the desired state by scheduling a replacement.
- **`RollingUpdate` strategy** — Ensures zero-downtime deployments. With `maxUnavailable: 1` and `maxSurge: 1`, Kubernetes brings one new pod up before taking one old pod down, so at least one pod is always serving traffic during the update.
- **`imagePullPolicy: Always`** — Forces the container runtime to check Docker Hub for a newer image every time a pod starts. This is critical when using mutable tags like `:latest`. For immutable tags (commit SHAs), `IfNotPresent` is more efficient.
- **`matchLabels`** — The `selector.matchLabels` must exactly match the `template.metadata.labels`. Kubernetes uses this to associate pods with the deployment controller.

**Scaling the deployment:**

```bash
# Scale up to 4 replicas
kubectl scale deployment flask-app --replicas=4

# Scale back down
kubectl scale deployment flask-app --replicas=2
```

**Rolling back a failed deployment:**

```bash
kubectl rollout undo deployment/flask-app
```

**Viewing rollout history:**

```bash
kubectl rollout history deployment/flask-app
```

---

### Service

**`service.yaml`**

```yaml
apiVersion: v1
kind: Service
metadata:
  name: flask-service
spec:
  type: NodePort
  selector:
    app: flask-app
  ports:
  - port: 5000
    targetPort: 5000
    nodePort: 30008
```

Key configuration decisions:

- **`type: NodePort`** — Exposes the service on a static port on every node in the cluster. This is the simplest way to expose a service externally without a cloud load balancer. The valid NodePort range is `30000-32767`.
- **`selector: app: flask-app`** — The service routes traffic only to pods whose labels match `app: flask-app`. This decouples the service from specific pod identities — Kubernetes automatically updates the endpoint list as pods are created and destroyed.
- **Port mapping** — External traffic hits `<Node-IP>:30008`, the service forwards it to port `5000` inside the cluster (`port: 5000`), and the container receives it on port `5000` (`targetPort: 5000`).

For production workloads, consider replacing `NodePort` with a `LoadBalancer` type service (on cloud providers) or an `Ingress` resource to handle TLS termination, hostname-based routing, and path-based routing.

---

## CI/CD Pipeline

The pipeline is defined in `.github/workflows/deploy.yml` and runs automatically on every push to the `main` branch.

**`deploy.yml`**

```yaml
name: CI/CD Pipeline

on:
  push:
    branches:
      - main

jobs:
  build-and-push:
    runs-on: ubuntu-latest

    defaults:
      run:
        working-directory: my-flask-app

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Login to Docker Hub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}

      - name: Build Docker image
        run: |
          docker build -t ${{ secrets.DOCKER_USERNAME }}/hello-flask-k8s:latest .
          docker tag ${{ secrets.DOCKER_USERNAME }}/hello-flask-k8s:latest \
            ${{ secrets.DOCKER_USERNAME }}/hello-flask-k8s:${{ github.sha }}

      - name: Push Docker image
        run: |
          docker push ${{ secrets.DOCKER_USERNAME }}/hello-flask-k8s:latest
          docker push ${{ secrets.DOCKER_USERNAME }}/hello-flask-k8s:${{ github.sha }}

      - name: Deploy to EC2 via SSH
        uses: appleboy/ssh-action@v1.0.3
        with:
          host: ${{ secrets.EC2_HOST }}
          username: ubuntu
          key: ${{ secrets.EC2_KEY }}
          script: |
            kubectl set image deployment/flask-app \
              flask-app=${{ secrets.DOCKER_USERNAME }}/hello-flask-k8s:${{ github.sha }}
            kubectl rollout status deployment/flask-app
```

---

### Pipeline Stages

**1. Checkout**
Uses `actions/checkout@v4` (Node.js 24 compatible) to pull the repository contents onto the runner. The `defaults.run.working-directory` setting ensures all subsequent `run` steps execute inside `my-flask-app/`, where the Dockerfile is located.

**2. Login to Docker Hub**
Uses `docker/login-action@v3` with credentials stored in GitHub Secrets. This authenticates the runner to Docker Hub so it can push images to the repository.

**3. Build Docker image**
Builds the image from the Dockerfile in the working directory and applies two tags:
- `:latest` — a mutable, always-current tag for convenience
- `:<commit-sha>` — an immutable tag tied to the exact commit that triggered the build, enabling precise traceability and rollback

**4. Push Docker image**
Pushes both tags to Docker Hub. The commit SHA tag creates a permanent, auditable record of every image that was ever built.

**5. Deploy to EC2 via SSH**
Uses `appleboy/ssh-action@v1.0.3` to open an SSH connection to the EC2 instance using the private key stored in `EC2_KEY`. It then runs `kubectl set image` using the commit SHA tag (not `:latest`) to update the deployment. This is critical — Kubernetes only triggers a pod restart when the image reference changes. Using `:latest` repeatedly does not trigger a restart because the image string does not change.

---

### Required GitHub Secrets

Navigate to your repository on GitHub, then go to **Settings > Secrets and variables > Actions** and create the following secrets:

| Secret Name | Description |
|---|---|
| `DOCKER_USERNAME` | Your Docker Hub username (e.g., `prasannapatil91`) |
| `DOCKER_PASSWORD` | A Docker Hub Access Token with Read/Write permissions. Generate one under Account Settings > Security > New Access Token. Do not use your account password. |
| `EC2_HOST` | The public IPv4 address of your EC2 instance. This must be updated every time the instance is stopped and restarted, as AWS assigns a new IP unless an Elastic IP is configured. |
| `EC2_KEY` | The full contents of your `.pem` private key file, including the header and footer lines (`-----BEGIN RSA PRIVATE KEY-----` ... `-----END RSA PRIVATE KEY-----`). |

---

### Image Versioning Strategy

Two tags are pushed on every pipeline run:

| Tag | Value | Characteristics |
|---|---|---|
| `:latest` | Always points to the most recent build | Mutable — overwritten on every push. Useful for pulling the current version quickly but not reliable for reproducibility. |
| `:<commit-sha>` | Example: `:a3f9c12b...` | Immutable — unique per commit. Used by the pipeline for deployments and rollbacks. Provides a complete audit trail. |

To roll back to a specific previous version:

```bash
kubectl set image deployment/flask-app \
  flask-app=prasannapatil91/hello-flask-k8s:<previous-commit-sha>

kubectl rollout status deployment/flask-app
```

---

## Configuration Reference

| Parameter | Location | Default | Description |
|---|---|---|---|
| Flask port | `app.py` | `5000` | Port the Flask/Gunicorn process listens on inside the container |
| Container port | `Dockerfile` | `5000` | Exposed port declared in the image |
| Replica count | `deployment.yaml` | `2` | Number of pod replicas to maintain |
| NodePort | `service.yaml` | `30008` | External port exposed on the node. Must be in range 30000-32767 |
| Python version | `Dockerfile` | `3.11-slim` | Base Python image version |
| Flask version | `requirements.txt` | `3.0.0` | Pinned Flask version |
| Gunicorn version | `requirements.txt` | `21.2.0` | Pinned Gunicorn version |

---

## Troubleshooting

**Pods are not restarting after a pipeline run**

This occurs when the deployment is updated with `:latest` instead of a commit SHA. Since the image string does not change, Kubernetes considers the deployment unchanged and does not restart pods. The pipeline in this project uses `${{ github.sha }}` to ensure every deployment references a unique image tag.

```bash
# Force a restart without changing the image reference
kubectl rollout restart deployment/flask-app
```

---

**GitHub Actions fails with "Dockerfile not found"**

This happens when the `working-directory` is not set and the runner looks for a Dockerfile in the repository root instead of `my-flask-app/`. Ensure the following block is present in `deploy.yml`:

```yaml
defaults:
  run:
    working-directory: my-flask-app
```

---

**SSH deploy step fails after EC2 restart**

AWS assigns a new public IP address every time an EC2 instance starts (unless an Elastic IP is configured). Update the `EC2_HOST` secret in GitHub with the new IP address before re-running the pipeline.

To avoid this issue entirely, assign an Elastic IP to your EC2 instance from the AWS Console under EC2 > Elastic IPs. This provides a static IP that persists across stops and restarts.

---

**`kubectl` hangs or returns a TLS timeout**

K3s may not have fully started after an EC2 restart. Allow 60 seconds after starting the instance, then:

```bash
sudo systemctl restart k3s
sudo systemctl status k3s
kubectl get nodes
```

---

**Image pull error in pod (`ErrImagePull` or `ImagePullBackOff`)**

Verify the image name and tag match exactly what was pushed to Docker Hub:

```bash
kubectl describe pod <pod-name>
```

Check the `Events` section at the bottom of the output for the specific error. Common causes are a mismatched Docker Hub username in `deployment.yaml` or a private Docker Hub repository without pull credentials configured in the cluster.

---

**`kubectl` permission denied on `k3s.yaml`**

```bash
sudo chmod 644 /etc/rancher/k3s/k3s.yaml
```

---

**SSH key permission denied locally**

```bash
chmod 400 ~/CCSCEKEY.pem
```

---

## Contributing

Contributions are welcome. To contribute:

1. Open an issue first to discuss the change, particularly for significant feature additions or architectural changes. This avoids wasted effort if the direction does not align with the project's goals.
2. Fork the repository and create a feature branch from `main`.
3. Make your changes with clear, descriptive commit messages.
4. Ensure the application runs correctly locally and the Docker build succeeds before opening a pull request.
5. Open a pull request against `main` with a description of what was changed and why.

For bug reports, include the output of `kubectl describe pod <pod-name>` and the relevant GitHub Actions run log if the issue is pipeline-related.

---

## Maintainer

Maintained by **Prasanna** ([prasannapatil91](https://hub.docker.com/u/prasannapatil91)).

- Docker Hub: [prasannapatil91/hello-flask-k8s](https://hub.docker.com/r/prasannapatil91/hello-flask-k8s)
- Flask Documentation: https://flask.palletsprojects.com
- Kubernetes Deployment Reference: https://kubernetes.io/docs/concepts/workloads/controllers/deployment/
- GitHub Actions Documentation: https://docs.github.com/en/actions
- K3s Documentation: https://docs.k3s.io
