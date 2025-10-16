# 04 - CI/CD and Deployment - Lv.2: Infrastructure as Code and GitOps
# 04 - CI/CD와 배포 - Lv.2: 코드형 인프라와 GitOps

You've automated your application's build and deployment. The next level is to automate the creation and management of your *infrastructure* itself. This is known as Infrastructure as Code (IaC).
애플리케이션 빌드와 배포를 자동화했다면, 다음 단계는 인프라 자체의 생성과 관리를 자동화하는 것입니다. 이를 코드형 인프라(IaC)라고 합니다.

## Before You Begin
## 시작하기 전에
-   Confirm you can run the Level 1 CI/CD pipeline end-to-end (build → test → deploy) without manual fixes.
-   레벨 1의 CI/CD 파이프라인을 수동 수정 없이 빌드→테스트→배포까지 전체 실행할 수 있는지 확인하세요.
-   Install Terraform and make sure your cloud CLI (gcloud, aws, or az) is authenticated; IaC tooling needs valid credentials.
-   Terraform을 설치하고 gcloud, aws, az 등의 클라우드 CLI에 인증이 되어 있는지 확인하세요. IaC 도구는 유효한 자격 증명이 필수입니다.
-   Fork or create a demo cloud project so experimentation does not change production resources.
-   실험이 프로덕션 리소스에 영향을 주지 않도록 데모 클라우드 프로젝트를 포크하거나 새로 만드세요.

## Level 2 Upgrade Goals
## 레벨 2 업그레이드 목표
1.  **Express infrastructure declaratively** so teammates can review changes like regular code.
1.  **인프라를 선언적으로 표현하기** – 팀원이 일반 코드처럼 변경 사항을 리뷰할 수 있게 합니다.
2.  **Automate environment drift detection** by integrating Terraform and GitOps into your daily workflow.
2.  **환경 드리프트 감지 자동화** – Terraform과 GitOps를 일상적인 워크플로에 통합합니다.
3.  **Practice rollback-friendly deployments** by treating infrastructure changes the same as application releases.
3.  **롤백 친화적인 배포 연습** – 인프라 변경을 애플리케이션 릴리스와 동일한 프로세스로 다룹니다.

## Core Concepts
## 핵심 개념

1.  **Infrastructure as Code (IaC)**: Managing and provisioning infrastructure (servers, databases, load balancers, networks) through machine-readable definition files, rather than physical hardware configuration or interactive configuration tools.
1.  **코드형 인프라(IaC)**: 서버, 데이터베이스, 로드 밸런서, 네트워크 등을 하드웨어 설정이나 수동 도구 대신 기계가 읽을 수 있는 정의 파일로 관리하고 프로비저닝합니다.
2.  **Declarative vs. Imperative**:
2.  **선언형과 명령형 비교**:
    -   **Imperative (e.g., a shell script)**: You define the *steps* to get to the desired state.
    -   **명령형(예: 셸 스크립트)**: 원하는 상태에 도달하기 위한 *단계*를 정의합니다.
    -   **Declarative (e.g., Terraform, Kubernetes YAML)**: You define the *desired end state*, and the tool figures out how to get there. This is the preferred modern approach.
    -   **선언형(예: Terraform, Kubernetes YAML)**: *원하는 최종 상태*를 선언하면 도구가 방법을 찾아 실행합니다. 현대에는 선언형 접근이 선호됩니다.
3.  **GitOps**: A way of implementing Continuous Delivery for cloud-native applications. It uses Git as a single source of truth for both application and infrastructure code. A change to the Git repo triggers an automated process that updates the live environment.
3.  **GitOps**: 클라우드 네이티브 애플리케이션을 지속적으로 전달하는 방식으로, 애플리케이션과 인프라 코드를 위한 단일 진실 공급원으로 Git을 사용합니다. Git 저장소의 변경이 자동으로 운영 환경을 업데이트합니다.

---

## 1. Infrastructure as Code with Terraform
## 1. Terraform으로 코드형 인프라 구현하기

Terraform is the industry-standard tool for building, changing, and versioning infrastructure safely and efficiently. It uses a declarative language to describe your cloud resources.
Terraform은 인프라를 안전하고 효율적으로 구축, 변경, 버전 관리할 수 있는 업계 표준 도구입니다. 선언형 언어로 클라우드 리소스를 기술합니다.

**Why Terraform?**
**Terraform을 쓰는 이유**
-   **Platform Agnostic**: Works with AWS, Google Cloud, Azure, and many other providers.
-   **플랫폼 독립적**: AWS, Google Cloud, Azure 등 다양한 제공자에서 동작합니다.
-   **State Management**: Terraform keeps a `state file` that maps your configuration to the real-world resources, allowing it to plan and apply changes intelligently.
-   **상태 관리**: `state` 파일에 구성과 실제 리소스의 매핑을 저장해 변경 사항을 지능적으로 계획하고 적용합니다.
-   **Dry Runs**: `terraform plan` shows you exactly what will be created, changed, or destroyed before you apply it.
-   **사전 검토**: `terraform plan`으로 적용 전에 생성·변경·삭제될 항목을 정확히 확인할 수 있습니다.

### Example: Defining a Google Cloud Run Service with Terraform
### 예시: Terraform으로 Google Cloud Run 서비스 정의하기

Let's define the infrastructure for deploying your containerized FastAPI app.
컨테이너화된 FastAPI 앱을 배포하기 위한 인프라를 정의해 봅시다.

1.  **Install Terraform**: Follow the official HashiCorp instructions.
1.  **Terraform 설치**: HashiCorp 공식 문서를 참고하세요.
2.  **Create your configuration files**:
2.  **구성 파일 만들기**:

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
### Terraform 작업 흐름

1.  **Initialize**: `terraform init` (downloads the necessary provider plugins).
1.  **초기화**: `terraform init` (필요한 프로바이더 플러그인 다운로드).
2.  **Plan**: `terraform plan -var="gcp_project_id=your-gcp-project-id"`
2.  **계획**: `terraform plan -var="gcp_project_id=your-gcp-project-id"`
    -   Terraform shows you an execution plan. This is the "dry run." It will tell you what resources it's going to create, update, or delete.
    -   Terraform이 실행 계획을 보여줍니다. 일종의 “드라이런”으로, 어떤 리소스를 생성·수정·삭제할지 알려줍니다.
3.  **Apply**: `terraform apply -var="gcp_project_id=your-gcp-project-id"`
3.  **적용**: `terraform apply -var="gcp_project_id=your-gcp-project-id"`
    -   Terraform executes the plan and creates the resources in your cloud account.
    -   Terraform이 계획을 실행하여 클라우드 계정에 리소스를 생성합니다.

You can now commit these `.tf` files to your Git repository. Your infrastructure is now version-controlled, reviewable, and reproducible.
이제 `.tf` 파일을 Git 저장소에 커밋하면 인프라가 버전 관리되고 리뷰와 재현이 가능한 상태가 됩니다.

**Practice:** run `terraform plan` twice—once with the configuration above, and once after intentionally changing the memory limit or container image tag. Observe how the diff helps you reason about the impact before touching real infrastructure.
**실습:** 위 구성으로 한 번, 메모리 제한이나 이미지 태그를 일부러 변경한 뒤 한 번 `terraform plan`을 실행하여 실제 인프라를 건드리기 전에 차이를 통해 영향을 파악해 보세요.

---

## 2. GitOps with Argo CD or Flux
## 2. Argo CD 또는 Flux로 GitOps 구현하기

GitOps takes IaC a step further. The core idea is that your Git repository is the *only* source of truth. No one should be manually changing the production environment.
GitOps는 IaC를 한층 발전시킨 개념으로, Git 저장소를 단 하나의 진실 공급원으로 삼아 누구도 운영 환경을 수동으로 수정하지 않게 합니다.

**How it works**:
**동작 방식**:
1.  You have two Git repositories:
1.  Git 저장소가 두 개 필요합니다.
    -   **App Repo**: Contains your application code (Python, etc.).
    -   **앱 저장소**: 애플리케이션 코드(파이썬 등)를 저장합니다.
    -   **Infra/Config Repo**: Contains the declarative configuration for your infrastructure (Terraform, Kubernetes YAML).
    -   **인프라/구성 저장소**: Terraform, Kubernetes YAML 등 선언형 인프라 구성을 담습니다.
2.  Your CI pipeline for the **App Repo** builds a Docker image and pushes it to a registry with a new version tag (e.g., `v1.2.3`).
2.  **앱 저장소**의 CI 파이프라인이 도커 이미지를 빌드하여 새 버전 태그(예: `v1.2.3`)로 레지스트리에 푸시합니다.
3.  The CI pipeline then automatically opens a Pull Request in the **Infra Repo**, updating a file to point to the new image tag (`v1.2.3`).
3.  그러면 CI가 **인프라 저장소**에 자동으로 PR을 열어 새 이미지 태그를 가리키도록 파일을 업데이트합니다.
4.  A human reviews and merges this PR.
4.  사람이 PR을 리뷰하고 머지합니다.
5.  A **GitOps Operator** (a tool like Argo CD or Flux running in your cluster) detects the change in the Infra Repo.
5.  클러스터에서 실행 중인 **GitOps 오퍼레이터**(Argo CD, Flux 등)가 인프라 저장소의 변화를 감지합니다.
6.  The operator automatically synchronizes the live environment to match the state defined in the Git repo, pulling the new Docker image and deploying it.
6.  오퍼레이터가 Git에 정의된 상태와 운영 환경을 자동으로 동기화하면서 새 도커 이미지를 가져와 배포합니다.

**Why GitOps?**
**GitOps의 장점**
-   **Auditability**: The Git history of the Infra Repo is a perfect audit log of every change made to production.
-   **감사 가능성**: 인프라 저장소의 Git 히스토리가 모든 프로덕션 변경의 감사 로그가 됩니다.
-   **Rollbacks are Easy**: Reverting a change is as simple as reverting a commit in Git. The GitOps operator will automatically roll back the live environment.
-   **손쉬운 롤백**: Git 커밋을 되돌리는 것만으로도 변경을 롤백할 수 있으며, GitOps 오퍼레이터가 운영 환경을 자동으로 되돌립니다.
-   **Consistency**: The live environment is guaranteed to match what's defined in Git, eliminating configuration drift.
-   **일관성**: 운영 환경이 Git에 정의된 상태와 항상 일치해 구성 드리프트를 제거합니다.
-   **Enhanced Security**: Developers don't need direct access to the production environment. They just push code and merge PRs.
-   **보안 강화**: 개발자가 운영 환경에 직접 접근할 필요 없이 코드 푸시와 PR 머지만으로 배포가 진행됩니다.

While setting up a full GitOps workflow requires a container orchestration platform like Kubernetes and is a significant step up in complexity, understanding the principles is key. It represents the pinnacle of automated, reliable, and auditable deployment, and it's the direction modern cloud-native development is heading.
완전한 GitOps 워크플로를 구축하려면 쿠버네티스 같은 오케스트레이션 플랫폼이 필요해 복잡도가 증가하지만, 원리를 이해하는 것이 중요합니다. 이는 자동화되고 신뢰할 수 있으며 감사 가능한 배포의 정점이며 현대 클라우드 네이티브 개발이 지향하는 방향입니다.

**Practice:** even without Kubernetes, simulate GitOps by creating a second repo that holds Terraform variables. Update an image tag there and write a GitHub Action that runs `terraform apply` when the file changes. This mirrors the GitOps feedback loop in a simpler environment.
**실습:** 쿠버네티스가 없어도 Terraform 변수를 보관하는 두 번째 저장소를 만들어 GitOps를 모사해 보세요. 그 파일의 이미지 태그를 바꾸고, 변경 시 `terraform apply`를 실행하는 GitHub Action을 작성하면 간단한 환경에서도 GitOps 피드백 루프를 체험할 수 있습니다.

## Going Further
## 더 나아가기
-   Configure remote Terraform state (e.g., Google Cloud Storage or AWS S3) so teammates can collaborate safely.
-   Google Cloud Storage나 AWS S3에 원격 Terraform 상태를 구성해 팀이 안전하게 협업할 수 있도록 하세요.
-   Evaluate policy-as-code tools like Open Policy Agent (OPA) or HashiCorp Sentinel to enforce guardrails before `terraform apply` runs.
-   Open Policy Agent(OPA)나 HashiCorp Sentinel 같은 정책-코드 도구를 평가해 `terraform apply` 전에 가드레일을 강제하세요.
-   Study Weaveworks’ GitOps whitepaper and note two ideas you want to adopt in your deployment process this quarter.
-   Weaveworks의 GitOps 백서를 읽고 이번 분기 배포 프로세스에 도입하고 싶은 아이디어 두 가지를 기록하세요.
