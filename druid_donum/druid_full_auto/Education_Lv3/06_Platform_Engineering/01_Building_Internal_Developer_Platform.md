# 내부 개발자 플랫폼 구축: 개발자 경험 향상하기

**대상 독자**: 여러 팀이 있는 조직에서 개발 인프라 개선을 고민하는 개발자
**선행 지식**: Docker, Kubernetes 기초, CI/CD 경험
**학습 시간**: 3-4시간

---

## 플랫폼 엔지니어링이란?

### 문제: 개발자가 인프라에 시간을 낭비

```
현실:
- 백엔드 개발자: "Kubernetes YAML 작성법을 3일째 공부 중..."
- 프론트엔드 개발자: "CI/CD 파이프라인이 왜 안 돌아가지?"
- 데이터 과학자: "GPU 서버 접근 권한 받는 데 2주 걸렸어요"
- CTO: "개발자 10명인데 왜 인프라 관리만 하고 있죠?"

시간 낭비:
- 환경 설정: 주당 5시간
- 배포 문제 해결: 주당 3시간
- 인프라 학습: 주당 4시간
→ 실제 개발: 주 40시간 중 28시간만!
```

### 해결: Internal Developer Platform (IDP)

```
플랫폼 엔지니어링 = 개발자를 위한 셀프서비스 플랫폼 구축

목표:
✅ 개발자가 인프라를 신경 쓰지 않고 코드에 집중
✅ 배포를 버튼 클릭 한 번으로
✅ 모니터링, 로깅, 보안이 자동으로
✅ 일관된 개발 경험 제공

결과:
- 환경 설정: 5분 (자동화)
- 배포: 1분 (원클릭)
- 인프라 학습: 0시간 (추상화됨)
→ 실제 개발: 주 40시간 모두!
```

---

## 1단계: 개발 환경 표준화

### 문제: "내 컴퓨터에서는 되는데요?"

```bash
# ❌ 각 개발자가 다른 환경
개발자 A: Python 3.8, PostgreSQL 12, Redis 5
개발자 B: Python 3.11, PostgreSQL 15, Redis 7
개발자 C: Python 3.9, MySQL 8 (???)

# 결과:
# - 로컬에서는 작동, 프로덕션에서 에러
# - 새 팀원 온보딩에 3일 소요
# - 의존성 충돌 디버깅에 시간 낭비
```

### 해결 1: Dev Container (VS Code)

```json
// ✅ .devcontainer/devcontainer.json
{
  "name": "MyApp Development",
  "dockerComposeFile": "docker-compose.yml",
  "service": "app",
  "workspaceFolder": "/workspace",

  // 자동으로 설치될 VS Code 확장
  "extensions": [
    "ms-python.python",
    "ms-python.vscode-pylance",
    "ms-azuretools.vscode-docker",
    "eamodio.gitlens"
  ],

  // 컨테이너 생성 후 실행
  "postCreateCommand": "pip install -r requirements.txt && pre-commit install",

  // 포트 포워딩
  "forwardPorts": [8000, 5432, 6379],

  // 환경 변수
  "remoteEnv": {
    "DATABASE_URL": "postgresql://postgres:password@db:5432/myapp"
  }
}
```

```yaml
# .devcontainer/docker-compose.yml
version: '3.8'

services:
  app:
    build:
      context: ..
      dockerfile: .devcontainer/Dockerfile
    volumes:
      - ..:/workspace:cached
    command: sleep infinity  # 컨테이너 유지

  db:
    image: postgres:15
    environment:
      POSTGRES_PASSWORD: password
      POSTGRES_DB: myapp

  redis:
    image: redis:7-alpine
```

```dockerfile
# .devcontainer/Dockerfile
FROM python:3.11-slim

# 개발 도구 설치
RUN apt-get update && apt-get install -y \
    git \
    curl \
    vim \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Python 도구
RUN pip install --no-cache-dir \
    black \
    flake8 \
    pytest \
    ipython

WORKDIR /workspace
```

**사용법**

```
1. VS Code에서 프로젝트 열기
2. "Reopen in Container" 클릭
3. 모든 환경이 자동으로 설정됨!

신입 개발자 온보딩:
- Before: 3일 (수동 설치, 트러블슈팅)
- After: 5분 (Dev Container 실행)
```

### 해결 2: GitHub Codespaces (클라우드 개발 환경)

```yaml
# ✅ .devcontainer/devcontainer.json (Codespaces용)
{
  "name": "Cloud Development",
  "image": "mcr.microsoft.com/devcontainers/python:3.11",

  // Codespaces에 할당할 리소스
  "hostRequirements": {
    "cpus": 4,
    "memory": "8gb",
    "storage": "32gb"
  },

  "postCreateCommand": "make setup"
}
```

**장점**

```
✅ 로컬 머신 성능 무관 (클라우드에서 실행)
✅ iPad에서도 개발 가능
✅ 브라우저만 있으면 OK
✅ 팀원 간 환경 100% 동일
```

---

## 2단계: 배포 자동화 (Self-Service Deployment)

### 문제: 복잡한 배포 프로세스

```bash
# ❌ 수동 배포 (14단계, 30분 소요)
1. 코드 커밋
2. Dockerfile 작성
3. Docker 빌드
4. Docker Hub에 푸시
5. Kubernetes YAML 작성 (100줄+)
6. ConfigMap 업데이트
7. Secret 생성
8. kubectl apply
9. Deployment 상태 확인
10. 로그 확인
11. 에러 발생 → YAML 수정
12. 다시 kubectl apply
13. Ingress 설정
14. DNS 업데이트

# 개발자의 멘탈: 💔
```

### 해결: Platform Orchestrator (Backstage)

```yaml
# ✅ Backstage 앱 템플릿
apiVersion: scaffolder.backstage.io/v1beta3
kind: Template
metadata:
  name: python-service
  title: Create a Python Service
  description: 클릭 몇 번으로 새 Python 서비스 생성

spec:
  parameters:
    - title: Service Information
      properties:
        serviceName:
          type: string
          description: 서비스 이름
        description:
          type: string
          description: 서비스 설명
        owner:
          type: string
          description: 팀 이름
          ui:field: OwnerPicker

  steps:
    # 1. GitHub 저장소 생성
    - id: create-repo
      name: Create GitHub Repository
      action: publish:github
      input:
        repoUrl: github.com?owner=myorg&repo=${{ parameters.serviceName }}

    # 2. 템플릿 코드 복사
    - id: fetch-template
      name: Fetch Template
      action: fetch:template
      input:
        url: ./template
        values:
          serviceName: ${{ parameters.serviceName }}
          owner: ${{ parameters.owner }}

    # 3. Kubernetes 리소스 생성
    - id: create-k8s-resources
      name: Create Kubernetes Resources
      action: kubernetes:create
      input:
        manifest: |
          apiVersion: apps/v1
          kind: Deployment
          metadata:
            name: ${{ parameters.serviceName }}
          spec:
            replicas: 2
            template:
              spec:
                containers:
                - name: app
                  image: myregistry/${{ parameters.serviceName }}:latest
                  resources:
                    requests:
                      memory: "256Mi"
                      cpu: "250m"
                    limits:
                      memory: "512Mi"
                      cpu: "500m"

    # 4. CI/CD 파이프라인 생성
    - id: create-pipeline
      name: Create CI/CD Pipeline
      action: github:actions:create
      input:
        repoUrl: github.com?owner=myorg&repo=${{ parameters.serviceName }}
        workflowPath: .github/workflows/deploy.yml

  output:
    links:
      - title: Repository
        url: ${{ steps.create-repo.output.remoteUrl }}
      - title: Pipeline
        url: ${{ steps.create-pipeline.output.workflowUrl }}
```

**개발자 경험**

```
Before (30분):
1. GitHub 저장소 수동 생성
2. Dockerfile 작성
3. K8s YAML 100줄 작성
4. CI/CD 설정
5. 문서 읽으며 트러블슈팅

After (2분):
1. Backstage UI 접속
2. "Create Python Service" 클릭
3. 서비스 이름 입력
4. "Create" 버튼 클릭
→ 완료! 🎉
```

---

## 3단계: 통합 로깅 & 모니터링

### 문제: 분산된 로그

```
개발자: "사용자가 500 에러 봤다는데 로그가 어디 있죠?"

현실:
- 앱 로그: CloudWatch Logs
- 웹서버 로그: S3
- 데이터베이스 로그: RDS Logs
- Kubernetes 로그: kubectl logs
→ 5개 시스템을 뒤져야 함 😱
```

### 해결: ELK Stack (Elasticsearch, Logstash, Kibana)

```yaml
# ✅ 모든 로그를 중앙 집중화
# docker-compose.yml
version: '3.8'

services:
  elasticsearch:
    image: elasticsearch:8.10.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
    ports:
      - 9200:9200

  logstash:
    image: logstash:8.10.0
    volumes:
      - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf
    depends_on:
      - elasticsearch

  kibana:
    image: kibana:8.10.0
    ports:
      - 5601:5601
    depends_on:
      - elasticsearch
```

```conf
# logstash.conf
input {
  # Kubernetes 로그
  file {
    path => "/var/log/containers/*.log"
    type => "kubernetes"
  }

  # 애플리케이션 로그 (Filebeat에서 전송)
  beats {
    port => 5044
  }
}

filter {
  # JSON 로그 파싱
  if [type] == "app" {
    json {
      source => "message"
    }
  }

  # Kubernetes 메타데이터 추가
  if [type] == "kubernetes" {
    grok {
      match => { "message" => "%{GREEDYDATA:log}" }
    }
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "logs-%{+YYYY.MM.dd}"
  }
}
```

**애플리케이션에서 구조화된 로그 전송**

```python
# ✅ 구조화된 로그 (JSON)
import structlog
import logging

# structlog 설정
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer()
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
)

logger = structlog.get_logger()

@app.route('/orders', methods=['POST'])
def create_order():
    user_id = session['user_id']
    amount = request.json['amount']

    # 구조화된 로그
    logger.info(
        "order_created",
        user_id=user_id,
        amount=amount,
        currency="USD",
        ip_address=request.remote_addr
    )

    # 출력 (JSON):
    # {
    #   "event": "order_created",
    #   "user_id": 123,
    #   "amount": 99.99,
    #   "currency": "USD",
    #   "ip_address": "192.168.1.1",
    #   "timestamp": "2025-10-06T10:30:00Z"
    # }
```

**Kibana에서 로그 검색**

```
이제 Kibana UI에서:
- "user_id: 123" → 특정 사용자의 모든 활동
- "level: ERROR" → 모든 에러 로그
- "event: order_created AND amount > 1000" → 고액 주문
→ 클릭 몇 번으로 찾기! ✅
```

### 통합 메트릭: Grafana

```yaml
# ✅ prometheus.yml
scrape_configs:
  # 애플리케이션 메트릭
  - job_name: 'my-app'
    static_configs:
      - targets: ['app:8000']

  # Kubernetes 메트릭
  - job_name: 'kubernetes'
    kubernetes_sd_configs:
      - role: pod
```

```python
# 애플리케이션에서 메트릭 노출
from prometheus_flask_exporter import PrometheusMetrics

app = Flask(__name__)
metrics = PrometheusMetrics(app)

# 자동 측정:
# - http_request_duration_seconds
# - http_request_total
# - http_request_exceptions_total

# 커스텀 메트릭
from prometheus_client import Counter, Gauge

order_total = Counter('orders_total', 'Total orders created')
active_users = Gauge('active_users', 'Currently active users')

@app.route('/orders', methods=['POST'])
def create_order():
    order_total.inc()  # 카운터 증가
    # ...
```

**Grafana 대시보드 (JSON)**

```json
{
  "dashboard": {
    "title": "Application Overview",
    "panels": [
      {
        "title": "Requests per Second",
        "targets": [
          {
            "expr": "rate(http_request_total[5m])"
          }
        ]
      },
      {
        "title": "95th Percentile Latency",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))"
          }
        ]
      },
      {
        "title": "Error Rate",
        "targets": [
          {
            "expr": "rate(http_request_total{status=~\"5..\"}[5m]) / rate(http_request_total[5m])"
          }
        ]
      }
    ]
  }
}
```

---

## 4단계: Secrets 관리

### 문제: 하드코딩된 비밀번호

```python
# ❌ 절대 하지 말 것
DATABASE_URL = "postgresql://admin:password123@db.example.com/prod"
AWS_SECRET_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"

# 문제:
# 1. Git에 커밋되면 영구히 남음 (삭제해도 히스토리에 있음)
# 2. 개발자 모두가 프로덕션 비밀번호 알게 됨
# 3. 비밀번호 변경 시 코드 수정 필요
```

### 해결: Vault (HashiCorp)

```bash
# ✅ Vault 서버 실행
$ docker run -d --name=vault \
  -p 8200:8200 \
  vault server -dev

# Vault에 시크릿 저장
$ vault kv put secret/myapp/database \
  username=admin \
  password=super-secret-password

$ vault kv put secret/myapp/aws \
  access_key=AKIAIOSFODNN7EXAMPLE \
  secret_key=wJalrXUtnFEMI/K7MDENG/bPxRfiCY
```

**애플리케이션에서 Vault 사용**

```python
# ✅ Vault에서 시크릿 조회
import hvac

# Vault 클라이언트
client = hvac.Client(url='http://vault:8200')
client.token = os.environ['VAULT_TOKEN']  # 환경 변수로 토큰 전달

# 시크릿 조회
secret = client.secrets.kv.v2.read_secret_version(path='myapp/database')
db_password = secret['data']['data']['password']

# 데이터베이스 연결
DATABASE_URL = f"postgresql://admin:{db_password}@db.example.com/prod"
```

**Kubernetes에서 Vault 통합**

```yaml
# ✅ Vault Agent Injector로 자동 주입
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
spec:
  template:
    metadata:
      annotations:
        vault.hashicorp.com/agent-inject: "true"
        vault.hashicorp.com/role: "myapp"
        vault.hashicorp.com/agent-inject-secret-database: "secret/myapp/database"
    spec:
      containers:
      - name: app
        image: myapp:latest
        env:
        - name: DATABASE_PASSWORD
          value: /vault/secrets/database  # Vault Agent가 파일로 제공

# Pod 시작 시 자동으로 시크릿이 파일에 저장됨
# /vault/secrets/database:
# {
#   "username": "admin",
#   "password": "super-secret-password"
# }
```

### 동적 시크릿 (더 안전)

```bash
# ✅ Vault가 임시 DB 계정 생성
$ vault write database/roles/myapp-role \
  db_name=postgres \
  creation_statements="CREATE ROLE \"{{name}}\" WITH LOGIN PASSWORD '{{password}}' VALID UNTIL '{{expiration}}';" \
  default_ttl="1h" \
  max_ttl="24h"

# 애플리케이션이 요청하면 1시간 유효한 계정 생성
$ vault read database/creds/myapp-role
# Key: username, Value: v-token-myapp-role-x7f9s2k3
# Key: password, Value: A1a-random-password-B2b

# 1시간 후 자동으로 계정 삭제
# → 비밀번호 유출되어도 1시간만 유효!
```

---

## 5단계: GitOps로 인프라 관리

### 문제: 수동 kubectl 명령어

```bash
# ❌ 개발자가 직접 프로덕션에 배포
$ kubectl apply -f deployment.yaml

# 문제:
# - 누가 언제 무엇을 변경했는지 추적 불가
# - 실수로 잘못된 설정 적용 가능
# - 롤백 어려움
# - 환경별(dev/stage/prod) 일관성 보장 안 됨
```

### 해결: ArgoCD (GitOps)

```yaml
# ✅ Git 저장소가 단일 진실 공급원 (Single Source of Truth)
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: app
        image: myregistry/myapp:v1.2.3
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
```

**ArgoCD Application 정의**

```yaml
# argocd/application.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: myapp-production
  namespace: argocd
spec:
  project: default

  # Git 저장소
  source:
    repoURL: https://github.com/myorg/k8s-manifests
    targetRevision: main
    path: k8s/production

  # 배포할 클러스터
  destination:
    server: https://kubernetes.default.svc
    namespace: production

  # 자동 동기화
  syncPolicy:
    automated:
      prune: true       # Git에서 삭제된 리소스는 클러스터에서도 삭제
      selfHeal: true    # 수동 변경 감지 시 Git 상태로 복원
```

**워크플로우**

```
1. 개발자가 k8s/deployment.yaml 수정
2. GitHub에 Pull Request 생성
3. 팀원이 리뷰 & 승인
4. main 브랜치에 머지
5. ArgoCD가 자동으로 변경 감지
6. Kubernetes에 자동 배포
→ 모든 변경이 Git에 기록됨! ✅

롤백:
$ git revert abc123
$ git push
→ ArgoCD가 자동으로 이전 버전 배포
```

**ArgoCD UI**

```
대시보드에서 확인 가능:
- 현재 배포된 버전
- Git 커밋 해시
- 동기화 상태 (Synced / Out of Sync)
- 배포 히스토리
- 리소스 상태 (Pod, Service, Ingress)

버튼 클릭으로:
- 수동 동기화
- 롤백
- 차이점 확인 (Diff)
```

---

## 6단계: 개발자 포털 (Backstage)

### 모든 것을 한곳에

```yaml
# ✅ Backstage catalog-info.yaml
apiVersion: backstage.io/v1alpha1
kind: Component
metadata:
  name: payment-service
  description: 결제 처리 서비스
  annotations:
    github.com/project-slug: myorg/payment-service
    circleci.com/project-slug: github/myorg/payment-service
    pagerduty.com/service-id: PXYZ123

spec:
  type: service
  lifecycle: production
  owner: payments-team

  # 시스템 의존성
  dependsOn:
    - component:database-postgres
    - component:redis-cache
    - component:notification-service

  # API 문서
  providesApis:
    - payment-api

---
apiVersion: backstage.io/v1alpha1
kind: API
metadata:
  name: payment-api
spec:
  type: openapi
  lifecycle: production
  owner: payments-team
  definition:
    $text: https://github.com/myorg/payment-service/blob/main/openapi.yaml
```

**Backstage UI에서 한눈에 보기**

```
개발자 포털 접속: https://backstage.mycompany.com

[Payment Service]
├─ Overview
│  ├─ 설명: 결제 처리 서비스
│  ├─ 소유자: payments-team
│  └─ 생명주기: production
│
├─ CI/CD
│  ├─ 최근 빌드: ✅ 성공 (5분 전)
│  └─ 배포 상태: v1.2.3 (production)
│
├─ API Docs
│  └─ OpenAPI Spec (자동 생성된 문서)
│
├─ Dependencies
│  ├─ PostgreSQL (정상)
│  ├─ Redis (정상)
│  └─ Notification Service (정상)
│
├─ Monitoring
│  ├─ Grafana 대시보드 → [링크]
│  ├─ Kibana 로그 → [링크]
│  └─ PagerDuty 알림 → [링크]
│
└─ Incidents
   ├─ 활성: 0
   └─ 지난 30일: 2

모든 정보를 한 페이지에서!
```

---

## 플랫폼 엔지니어링 성숙도 모델

### Level 0: 수동 (Manual)

```
- kubectl 명령어 직접 실행
- SSH로 서버 접속하여 수동 배포
- 로그는 각 서버에서 tail -f
- 비밀번호는 .env 파일에

개발자 시간 낭비: 50%
```

### Level 1: 자동화 (Automated)

```
- CI/CD 파이프라인 있음
- Docker 컨테이너 사용
- 중앙 로깅 (ELK)
- 환경 변수로 설정 관리

개발자 시간 낭비: 30%
```

### Level 2: 셀프서비스 (Self-Service)

```
- 개발자 포털 (Backstage)
- 원클릭 배포
- GitOps (ArgoCD)
- Vault로 시크릿 관리
- 통합 모니터링 (Grafana)

개발자 시간 낭비: 10%
```

### Level 3: 플랫폼 (Platform)

```
- Golden Path Templates (모범 사례 자동화)
- Policy as Code (보안/컴플라이언스 자동 검증)
- Cost Optimization (리소스 최적화 권장)
- Developer Metrics (DORA 메트릭 추적)
- Self-Healing (자동 복구)

개발자 시간 낭비: 5%
개발 속도: 3배 증가 🚀
```

---

## 실전 예제: 스타트업 → 100명 조직

### Phase 1: 스타트업 (10명)

```
인프라:
- Heroku 또는 AWS Elastic Beanstalk
- GitHub Actions CI/CD
- CloudWatch Logs

비용: $500/월
관리 시간: 주 5시간

이 단계에서는 플랫폼 불필요 (오버엔지니어링)
```

### Phase 2: 성장기 (50명)

```
문제 발생:
- 배포 충돌 (5개 팀이 동시에 배포)
- 로그 찾기 어려움
- 환경 설정 불일치

해결:
✅ Kubernetes (GKE/EKS)
✅ ArgoCD (GitOps)
✅ ELK Stack
✅ Vault

비용: $5,000/월
플랫폼 팀: 2명
개발 속도: 1.5배 증가
```

### Phase 3: 확장기 (100명+)

```
문제:
- 신입 온보딩 느림
- 서비스 간 의존성 불명확
- 인프라 지식 격차

해결:
✅ Backstage (개발자 포털)
✅ Service Catalog
✅ Golden Path Templates
✅ Policy as Code (OPA)

비용: $20,000/월
플랫폼 팀: 5명
개발 속도: 3배 증가
ROI: $200,000/월 (개발자 생산성 향상)
```

---

## 플랫폼 엔지니어링 체크리스트

### 개발자 경험 (Developer Experience)
- [ ] 신입 개발자가 1일 안에 첫 배포를 할 수 있는가?
- [ ] 배포가 10분 이내에 완료되는가?
- [ ] 로그/메트릭을 한곳에서 볼 수 있는가?
- [ ] 문서가 코드와 함께 자동 업데이트되는가?

### 자동화
- [ ] CI/CD 파이프라인이 모든 서비스에 적용되어 있는가?
- [ ] 인프라 변경이 Git으로 관리되는가? (GitOps)
- [ ] 배포 롤백이 자동화되어 있는가?

### 보안
- [ ] 비밀번호/API 키가 코드에 없는가?
- [ ] Secrets 관리 도구를 사용하는가? (Vault, AWS Secrets Manager)
- [ ] Policy as Code로 보안 규칙을 강제하는가?

### 관찰성 (Observability)
- [ ] 모든 서비스의 메트릭을 모니터링하는가?
- [ ] 로그가 구조화되어 있는가? (JSON)
- [ ] 분산 추적(Tracing)을 사용하는가? (Jaeger, Zipkin)

### 셀프서비스
- [ ] 개발자가 플랫폼 팀 없이 배포할 수 있는가?
- [ ] 서비스 템플릿이 제공되는가?
- [ ] 개발자 포털이 있는가?

---

## 다음 단계

1. **Crossplane**: Kubernetes로 클라우드 인프라 관리
2. **Terraform**: Infrastructure as Code
3. **OPA (Open Policy Agent)**: Policy as Code
4. **DORA Metrics**: 개발 성과 측정

---

## 참고 자료

- **책**: "Team Topologies" by Matthew Skelton & Manuel Pais
- **웹사이트**: [platformengineering.org](https://platformengineering.org/)
- **도구**: [Backstage.io](https://backstage.io/)
- **블로그**: [Spotify Engineering Blog](https://engineering.atspotify.com/)
