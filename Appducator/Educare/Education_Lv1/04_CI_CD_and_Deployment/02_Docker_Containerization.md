# 04.02 - Containerizing Applications with Docker
# 04.02 - Docker로 애플리케이션 컨테이너화하기

Docker allows you to package your application, along with all its dependencies, into a standardized unit called a container. This solves the classic "it works on my machine" problem and is a fundamental skill for modern development and deployment.
Docker를 사용하면 애플리케이션과 모든 종속성을 컨테이너라는 표준화된 단위로 패키징할 수 있습니다. 이것은 고전적인 "내 컴퓨터에서는 작동하는데" 문제를 해결하고 현대적인 개발 및 배포를 위한 기본 기술입니다.

## Core Concepts
## 핵심 개념

1.  **Image**: A lightweight, standalone, executable package that includes everything needed to run a piece of software, including the code, a runtime, libraries, environment variables, and config files. Images are built from a `Dockerfile`.
    **이미지**: 코드, 런타임, 라이브러리, 환경 변수 및 구성 파일을 포함하여 소프트웨어를 실행하는 데 필요한 모든 것을 포함하는 가볍고 독립적인 실행 가능 패키지입니다. 이미지는 `Dockerfile`에서 빌드됩니다.
2.  **Container**: A running instance of an image. You can run many containers from the same image.
    **컨테이너**: 이미지의 실행 중인 인스턴스입니다. 동일한 이미지에서 많은 컨테이너를 실행할 수 있습니다.
3.  **Dockerfile**: A text file that contains instructions for building a Docker image.
    **Dockerfile**: Docker 이미지를 빌드하기 위한 지침이 포함된 텍스트 파일입니다.
4.  **Layer**: Each instruction in a `Dockerfile` creates a layer in the image. Docker caches layers, which makes subsequent builds much faster if the underlying instructions haven't changed.
    **레이어**: `Dockerfile`의 각 명령어는 이미지에 레이어를 생성합니다. Docker는 레이어를 캐시하므로 기본 명령어가 변경되지 않은 경우 후속 빌드가 훨씬 빨라집니다.
5.  **Registry**: A place to store and distribute Docker images (e.g., Docker Hub, GitHub Container Registry, Google Artifact Registry).
    **레지스트리**: Docker 이미지를 저장하고 배포하는 장소입니다(예: Docker Hub, GitHub Container Registry, Google Artifact Registry).

---

## Creating a `Dockerfile` for a Python Web Application
## 파이썬 웹 애플리케이션용 `Dockerfile` 생성

Let's create a production-ready `Dockerfile` for a FastAPI application. We'll use a **multi-stage build**, which is a best practice for creating small, secure images.
FastAPI 애플리케이션을 위한 프로덕션 준비가 된 `Dockerfile`을 만들어 보겠습니다. 작고 안전한 이미지를 만들기 위한 모범 사례인 **다단계 빌드**를 사용합니다.

**Why multi-stage?**
**왜 다단계인가?**
The "builder" stage will have all our build-time dependencies (like `pip-tools`), but the final "runner" stage will only contain our application code and its runtime dependencies. This results in a much smaller and more secure final image because it doesn't contain unnecessary build tools.
"빌더" 단계에는 모든 빌드 시간 종속성(예: `pip-tools`)이 포함되지만 최종 "러너" 단계에는 애플리케이션 코드와 런타임 종속성만 포함됩니다. 이렇게 하면 불필요한 빌드 도구가 포함되지 않으므로 최종 이미지가 훨씬 작고 안전해집니다.

Create a file named `Dockerfile` in your project root.
프로젝트 루트에 `Dockerfile`이라는 파일을 만듭니다.

```dockerfile
# -----------------
# Builder Stage
# -----------------
# Use a specific Python version for reproducibility.
# Use a specific, recent Python version for reproducibility.
FROM python:3.12-slim-bookworm as builder

# Apply security updates to the base image
RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Set environment variables
# PYTHONDONTWRITEBYTECODE: Prevents Python from writing .pyc files.
# PYTHONUNBUFFERED: Ensures that print statements and logs are sent straight to the terminal.
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install build-time dependencies (pip-tools)
RUN pip install --no-cache-dir pip-tools

# Copy only the requirements files first to leverage Docker's layer caching.
# If these files don't change, Docker won't re-run the next step.
COPY requirements.in requirements.txt ./
COPY dev-requirements.in dev-requirements.txt ./

# Install application dependencies into a virtual environment.
# This isolates dependencies and makes the final image cleaner.
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Compile and install dependencies
RUN pip-compile requirements.in -o requirements.txt && \
    pip install --no-cache-dir -r requirements.txt

# -----------------
# Runner Stage
# -----------------
# Use the same base image for the final stage.
FROM python:3.12-slim-bookworm

# Set the working directory
WORKDIR /app

# Create a non-root user for security.
# Running containers as root is a security risk.
RUN addgroup --system app && adduser --system --group app
USER app

# Copy the virtual environment from the builder stage.
COPY --from=builder /opt/venv /opt/venv

# Copy the application code.
COPY ./src ./src

# Make the virtual environment's Python the default.
ENV PATH="/opt/venv/bin:$PATH"

# Expose the port the app runs on.
EXPOSE 8000

# The command to run the application.
# Use gunicorn for a production-ready web server.
# You'll need to add 'gunicorn' to your requirements.in
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "-w", "4", "-b", "0.0.0.0:8000", "src.main:app"]
```

### Key Best Practices in this `Dockerfile`:
### 이 `Dockerfile`의 주요 모범 사례:

1.  **Use Specific Base Images**: `python:3.10-slim` is better than `python:latest` for reproducibility. `slim` versions are smaller.
    **특정 기본 이미지 사용**: 재현성을 위해 `python:latest`보다 `python:3.10-slim`이 더 좋습니다. `slim` 버전이 더 작습니다.
2.  **Leverage Layer Caching**: We `COPY` the requirements files and install dependencies *before* copying the application code. This means if you only change your app code (`src`), Docker can reuse the expensive dependency installation layer, making builds much faster.
    **레이어 캐싱 활용**: 애플리케이션 코드를 복사하기 *전에* 요구 사항 파일을 `COPY`하고 종속성을 설치합니다. 즉, 앱 코드(`src`)만 변경하면 Docker가 비용이 많이 드는 종속성 설치 레이어를 재사용하여 빌드 속도를 훨씬 빠르게 할 수 있습니다.
3.  **Run as a Non-Root User**: `RUN adduser...` and `USER app` significantly improve security by limiting the container's privileges.
    **루트가 아닌 사용자로 실행**: `RUN adduser...` 및 `USER app`은 컨테이너의 권한을 제한하여 보안을 크게 향상시킵니다.
4.  **Use a Production-Ready Server**: `uvicorn` alone is great for development, but `gunicorn` is a battle-tested process manager that can run multiple `uvicorn` workers for better performance and reliability.
    **프로덕션 준비 서버 사용**: `uvicorn`만으로도 개발에 훌륭하지만 `gunicorn`은 더 나은 성능과 안정성을 위해 여러 `uvicorn` 작업자를 실행할 수 있는 검증된 프로세스 관리자입니다.
5.  **Multi-Stage Build**: The final image doesn't contain `pip-tools` or any other build-time cruft.
    **다단계 빌드**: 최종 이미지에는 `pip-tools` 또는 기타 빌드 시간 찌꺼기가 포함되지 않습니다.

---

## Building and Running the Container
## 컨테이너 빌드 및 실행

1.  **Build the image**:
    **이미지 빌드**:
    ```bash
    # The -t flag tags the image with a name (e.g., my-vibe-app)
    # -t 플래그는 이미지에 이름(예: my-vibe-app)으로 태그를 지정합니다.
    docker build -t my-vibe-app .
    ```

2.  **Run the container**:
    **컨테이너 실행**:
    ```bash
    # -p 8000:8000 maps port 8000 on your host machine to port 8000 in the container.
    # -p 8000:8000은 호스트 시스템의 8000번 포트를 컨테이너의 8000번 포트에 매핑합니다.
    # --rm automatically removes the container when it exits.
    # --rm은 컨테이너가 종료될 때 자동으로 컨테이너를 제거합니다.
    docker run --rm -p 8000:8000 my-vibe-app
    ```
    You should now be able to access your API at `http://localhost:8000`.
    이제 `http://localhost:8000`에서 API에 액세스할 수 있습니다.

3.  **Pushing to a Registry**:
    **레지스트리에 푸시**:
    Once your image is built, you can push it to a registry to be used in your CI/CD pipeline or by a cloud provider.
    이미지가 빌드되면 CI/CD 파이프라인이나 클라우드 제공업체에서 사용할 수 있도록 레지스트리에 푸시할 수 있습니다.

    ```bash
    # 1. Tag the image for your registry (e.g., GitHub Container Registry)
    #    Format: ghcr.io/YOUR_USERNAME/IMAGE_NAME:TAG
    # 1. 레지스트리에 대한 이미지 태그 지정(예: GitHub Container Registry)
    #    형식: ghcr.io/사용자이름/이미지이름:태그
    docker tag my-vibe-app ghcr.io/narusuh/my-vibe-app:v0.1.0

    # 2. Log in to the registry
    # 2. 레지스트리에 로그인
    docker login ghcr.io -u YOUR_USERNAME -p YOUR_PAT # Use a Personal Access Token
    # docker login ghcr.io -u 사용자이름 -p 개인용액세스토큰 # 개인용 액세스 토큰 사용

    # 3. Push the image
    # 3. 이미지 푸시
    docker push ghcr.io/narusuh/my-vibe-app:v0.1.0
    ```

By containerizing your application, you create a portable, reproducible, and scalable unit of software. This is the foundation for deploying applications consistently across different environments, from your local machine to a massive cloud-native cluster. It's a non-negotiable skill for a modern Vibe Coder.
애플리케이션을 컨테이너화함으로써 이식 가능하고 재현 가능하며 확장 가능한 소프트웨어 단위를 만듭니다. 이것은 로컬 컴퓨터에서 대규모 클라우드 네이티브 클러스터에 이르기까지 다양한 환경에 일관되게 애플리케이션을 배포하기 위한 기반입니다. 현대 Vibe 코더에게는 타협할 수 없는 기술입니다.