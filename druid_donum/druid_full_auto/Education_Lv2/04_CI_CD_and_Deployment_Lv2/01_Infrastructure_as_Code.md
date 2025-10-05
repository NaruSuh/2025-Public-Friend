# 04 - CI/CD and Deployment - Lv.2: Infrastructure as Code and GitOps

You've automated your application's build and deployment. The next level is to automate the creation and management of your *infrastructure* itself. This is known as Infrastructure as Code (IaC).

## Core Concepts

1.  **Infrastructure as Code (IaC)**: Managing and provisioning infrastructure (servers, databases, load balancers, networks) through machine-readable definition files, rather than physical hardware configuration or interactive configuration tools.
2.  **Declarative vs. Imperative**:
    -   **Imperative (e.g., a shell script)**: You define the *steps* to get to the desired state.
    -   **Declarative (e.g., Terraform, Kubernetes YAML)**: You define the *desired end state*, and the tool figures out how to get there. This is the preferred modern approach.
3.  **GitOps**: A way of implementing Continuous Delivery for cloud-native applications. It uses Git as a single source of truth for both application and infrastructure code. A change to the Git repo triggers an automated process that updates the live environment.

---

## 1. Infrastructure as Code with Terraform

Terraform is the industry-standard tool for building, changing, and versioning infrastructure safely and efficiently. It uses a declarative language to describe your cloud resources.

**Why Terraform?**
-   **Platform Agnostic**: Works with AWS, Google Cloud, Azure, and many other providers.
-   **State Management**: Terraform keeps a `state file` that maps your configuration to the real-world resources, allowing it to plan and apply changes intelligently.
-   **Dry Runs**: `terraform plan` shows you exactly what will be created, changed, or destroyed before you apply it.

### Example: Defining a Google Cloud Run Service with Terraform

Let's define the infrastructure for deploying your containerized FastAPI app.

1.  **Install Terraform**: Follow the official HashiCorp instructions.
2.  **Create your configuration files**:

**`main.tf`**:
```terraform
# Configure the Google Cloud provider
provider "google" {
  project = var.gcp_project_id
  region  = "us-central1"
}

# Enable the necessary APIs
resource "google_project_service" "run_api" {
  service = "run.googleapis.com"
}
resource "google_project_service" "artifacts_api" {
  service = "artifactregistry.googleapis.com"
}

# Create a Google Artifact Registry to store your Docker images
resource "google_artifact_registry_repository" "primary" {
  location      = "us-central1"
  repository_id = "my-vibe-app-repo"
  format        = "DOCKER"
  depends_on = [google_project_service.artifacts_api]
}

# Define the Cloud Run service
resource "google_cloud_run_v2_service" "default" {
  name     = "my-vibe-app-service"
  location = "us-central1"

  template {
    containers {
      # This points to the Docker image you pushed in the CI/CD pipeline
      image = "us-central1-docker.pkg.dev/${var.gcp_project_id}/${google_artifact_registry_repository.primary.repository_id}/my-vibe-app:latest"
      
      ports {
        container_port = 8000
      }
    }
  }

  # Allow unauthenticated access to the service
  iam_policy {
    policy_data = data.google_iam_policy.noauth.policy_data
  }

  depends_on = [google_project_service.run_api]
}

# A data source to generate the public access policy
data "google_iam_policy" "noauth" {
  binding {
    role = "roles/run.invoker"
    members = [
      "allUsers",
    ]
  }
}

# Output the URL of the deployed service
output "service_url" {
  value = google_cloud_run_v2_service.default.uri
}
```

**`variables.tf`**:
```terraform
variable "gcp_project_id" {
  description = "The GCP project ID to deploy to."
  type        = string
}
```

### The Terraform Workflow

1.  **Initialize**: `terraform init` (downloads the necessary provider plugins).
2.  **Plan**: `terraform plan -var="gcp_project_id=your-gcp-project-id"`
    -   Terraform shows you an execution plan. This is the "dry run." It will tell you what resources it's going to create, update, or delete.
3.  **Apply**: `terraform apply -var="gcp_project_id=your-gcp-project-id"`
    -   Terraform executes the plan and creates the resources in your cloud account.

You can now commit these `.tf` files to your Git repository. Your infrastructure is now version-controlled, reviewable, and reproducible.

---

## 2. GitOps with Argo CD or Flux

GitOps takes IaC a step further. The core idea is that your Git repository is the *only* source of truth. No one should be manually changing the production environment.

**How it works**:
1.  You have two Git repositories:
    -   **App Repo**: Contains your application code (Python, etc.).
    -   **Infra/Config Repo**: Contains the declarative configuration for your infrastructure (Terraform, Kubernetes YAML).
2.  Your CI pipeline for the **App Repo** builds a Docker image and pushes it to a registry with a new version tag (e.g., `v1.2.3`).
3.  The CI pipeline then automatically opens a Pull Request in the **Infra Repo**, updating a file to point to the new image tag (`v1.2.3`).
4.  A human reviews and merges this PR.
5.  A **GitOps Operator** (a tool like Argo CD or Flux running in your cluster) detects the change in the Infra Repo.
6.  The operator automatically synchronizes the live environment to match the state defined in the Git repo, pulling the new Docker image and deploying it.

**Why GitOps?**
-   **Auditability**: The Git history of the Infra Repo is a perfect audit log of every change made to production.
-   **Rollbacks are Easy**: Reverting a change is as simple as reverting a commit in Git. The GitOps operator will automatically roll back the live environment.
-   **Consistency**: The live environment is guaranteed to match what's defined in Git, eliminating configuration drift.
-   **Enhanced Security**: Developers don't need direct access to the production environment. They just push code and merge PRs.

While setting up a full GitOps workflow requires a container orchestration platform like Kubernetes and is a significant step up in complexity, understanding the principles is key. It represents the pinnacle of automated, reliable, and auditable deployment, and it's the direction modern cloud-native development is heading.
