# 04.02 - Containerizing Applications with Docker

Docker allows you to package your application, along with all its dependencies, into a standardized unit called a container. This solves the classic "it works on my machine" problem and is a fundamental skill for modern development and deployment.

## Core Concepts

1.  **Image**: A lightweight, standalone, executable package that includes everything needed to run a piece of software, including the code, a runtime, libraries, environment variables, and config files. Images are built from a `Dockerfile`.
2.  **Container**: A running instance of an image. You can run many containers from the same image.
3.  **Dockerfile**: A text file that contains instructions for building a Docker image.
4.  **Layer**: Each instruction in a `Dockerfile` creates a layer in the image. Docker caches layers, which makes subsequent builds much faster if the underlying instructions haven't changed.
5.  **Registry**: A place to store and distribute Docker images (e.g., Docker Hub, GitHub Container Registry, Google Artifact Registry).

---

## Creating a `Dockerfile` for a Python Web Application

Let's create a production-ready `Dockerfile` for a FastAPI application. We'll use a **multi-stage build**, which is a best practice for creating small, secure images.

**Why multi-stage?**
The "builder" stage will have all our build-time dependencies (like `pip-tools`), but the final "runner" stage will only contain our application code and its runtime dependencies. This results in a much smaller and more secure final image because it doesn't contain unnecessary build tools.

Create a file named `Dockerfile` in your project root.

```dockerfile
# -----------------
# Builder Stage
# -----------------
# Use a specific Python version for reproducibility.
FROM python:3.10-slim as builder

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
FROM python:3.10-slim

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

1.  **Use Specific Base Images**: `python:3.10-slim` is better than `python:latest` for reproducibility. `slim` versions are smaller.
2.  **Leverage Layer Caching**: We `COPY` the requirements files and install dependencies *before* copying the application code. This means if you only change your app code (`src`), Docker can reuse the expensive dependency installation layer, making builds much faster.
3.  **Run as a Non-Root User**: `RUN adduser...` and `USER app` significantly improve security by limiting the container's privileges.
4.  **Use a Production-Ready Server**: `uvicorn` alone is great for development, but `gunicorn` is a battle-tested process manager that can run multiple `uvicorn` workers for better performance and reliability.
5.  **Multi-Stage Build**: The final image doesn't contain `pip-tools` or any other build-time cruft.

---

## Building and Running the Container

1.  **Build the image**:
    ```bash
    # The -t flag tags the image with a name (e.g., my-vibe-app)
    docker build -t my-vibe-app .
    ```

2.  **Run the container**:
    ```bash
    # -p 8000:8000 maps port 8000 on your host machine to port 8000 in the container.
    # --rm automatically removes the container when it exits.
    docker run --rm -p 8000:8000 my-vibe-app
    ```
    You should now be able to access your API at `http://localhost:8000`.

3.  **Pushing to a Registry**:
    Once your image is built, you can push it to a registry to be used in your CI/CD pipeline or by a cloud provider.

    ```bash
    # 1. Tag the image for your registry (e.g., GitHub Container Registry)
    #    Format: ghcr.io/YOUR_USERNAME/IMAGE_NAME:TAG
    docker tag my-vibe-app ghcr.io/narusuh/my-vibe-app:v0.1.0

    # 2. Log in to the registry
    docker login ghcr.io -u YOUR_USERNAME -p YOUR_PAT # Use a Personal Access Token

    # 3. Push the image
    docker push ghcr.io/narusuh/my-vibe-app:v0.1.0
    ```

By containerizing your application, you create a portable, reproducible, and scalable unit of software. This is the foundation for deploying applications consistently across different environments, from your local machine to a massive cloud-native cluster. It's a non-negotiable skill for a modern Vibe Coder.
