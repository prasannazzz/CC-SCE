# Hello Flask K8s

A simple, production-ready Flask application designed for Kubernetes deployment with a complete GitHub Actions CI/CD pipeline.

## What the project does

This project is a minimal, containerized Flask web application that serves a welcoming message along with the underlying Kubernetes pod hostname. It's packaged with a Dockerfile for straightforward containerization using Gunicorn, and includes Kubernetes manifests (`deployment.yaml` and `service.yaml`) for deploying the application to a cluster with a RollingUpdate strategy and a NodePort service.

## Why the project is useful

- **Production-Ready Server**: Utilizes Gunicorn as the WSGI HTTP Server for production deployment.
- **Containerized**: Fully Dockerized for easy distribution and consistent environments across different stages.
- **Kubernetes Native**: Includes `Deployment` and `Service` manifests with robust availability configurations (multiple replicas, rolling updates).
- **Automated CI/CD**: Built-in GitHub Actions workflow (`deploy.yml`) automatically builds and pushes Docker images to Docker Hub upon pushing to the `main` branch.
- **Easy Customization**: Built with simplicity in mind, acting as a great boilerplate or reference architecture for more complex Python web microservices.

## How users can get started

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) installed.
- [Kubernetes/kubectl](https://kubernetes.io/docs/tasks/tools/) deployed (Minikube, kind, EKS, etc.).
- Python 3.11+.

### Local Development

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd my-flask-app   # Navigate to the flask app directory
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application locally:**
   ```bash
   python app.py
   ```
   Access the app at `http://localhost:5000`.

### Docker Deployment

1. **Build the Docker image:**
   ```bash
   docker build -t hello-flask-k8s:latest .
   ```

2. **Run the container:**
   ```bash
   docker run -p 5000:5000 hello-flask-k8s:latest
   ```

### Kubernetes Deployment

1. **Apply the Kubernetes manifests:**
   ```bash
   kubectl apply -f deployment.yaml
   kubectl apply -f service.yaml
   ```

2. **Access the application in the cluster:**
   The `service.yaml` configures a NodePort exposing the app on port `30008` (configurable).
   You can access it at `http://<Node-IP>:30008`.

## Where users can get help

- For issues regarding the application setup, feel free to open a GitHub Issue in the repository.
- [Flask Official Documentation](https://flask.palletsprojects.com/)
- [Kubernetes Deployment Guides](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)

## Who maintains and contributes

This application is maintained by Prasanna (prasannapatil91). Contributions are very welcome! If you're interested in making this starter project better, feel free to open a Pull Request. For significant rewrites or feature additions, please open an issue first to discuss the exact capabilities you'd like to integrate.
