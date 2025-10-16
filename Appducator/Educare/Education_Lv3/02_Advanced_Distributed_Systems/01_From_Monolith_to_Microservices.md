# 모놀리스에서 마이크로서비스로: 분산 시스템 입문

**대상 독자**: 단일 서버 애플리케이션을 만들어본 개발자가 처음으로 분산 시스템을 배우는 경우
**선행 지식**: 기본적인 웹 애플리케이션 개발 경험 (Flask/Django/Express 등)
**학습 시간**: 2-3시간

---

## 왜 분산 시스템을 배워야 할까?

### 시나리오: 성공한 스타트업의 문제

당신이 만든 간단한 블로그 서비스가 대박이 났습니다.

**초기 (사용자 100명)**
```python
# 단일 서버 Flask 앱
from flask import Flask
app = Flask(__name__)

@app.route('/posts')
def get_posts():
    posts = db.query("SELECT * FROM posts")
    return jsonify(posts)

# 하나의 서버에서 전부 처리
# ✅ 간단하고 개발 속도 빠름
# ✅ 디버깅 쉬움
```

**3개월 후 (사용자 10만명)**
```
문제 발생:
❌ 서버 CPU 사용률 95%
❌ 데이터베이스 응답 속도 3초+
❌ 새 기능 배포하면 전체 서비스 중단
❌ 이미지 업로드 하나로 전체 서버 느려짐
```

이제 "분산 시스템"이 필요한 시점입니다.

---

## 1단계: 모놀리스란 무엇인가?

### 모놀리스 (Monolith)의 정의

**모놀리스** = 모든 기능이 하나의 코드베이스, 하나의 프로세스에서 실행되는 애플리케이션

```
┌─────────────────────────────────┐
│     단일 서버 (Monolith)        │
│                                 │
│  ┌──────────────────────────┐  │
│  │  사용자 인증 코드         │  │
│  ├──────────────────────────┤  │
│  │  게시글 처리 코드         │  │
│  ├──────────────────────────┤  │
│  │  이미지 업로드 코드       │  │
│  ├──────────────────────────┤  │
│  │  결제 처리 코드           │  │
│  ├──────────────────────────┤  │
│  │  이메일 발송 코드         │  │
│  └──────────────────────────┘  │
│                                 │
│  Database                       │
└─────────────────────────────────┘
```

### 모놀리스의 장점

1. **개발이 간단함**: 모든 코드가 한 곳에 있어 함수 호출만으로 기능 사용
2. **디버깅 쉬움**: 로그가 한 곳에 모임
3. **배포 간단**: 하나의 서버에 올리면 끝
4. **트랜잭션 처리**: 데이터베이스 트랜잭션으로 일관성 유지

### 모놀리스의 한계

```python
# 문제 1: 이미지 처리가 전체 서버를 느리게 함
@app.route('/upload', methods=['POST'])
def upload_image():
    image = request.files['image']
    # CPU를 많이 사용하는 이미지 리사이징
    resize_image(image)  # 5초 소요
    # 이 동안 다른 모든 요청이 대기! 😱

# 문제 2: 작은 수정에도 전체 재배포
def fix_typo_in_email():
    return "Welcom" → "Welcome"
# 이메일 오타 하나 고치려고 전체 서비스 재시작!

# 문제 3: 팀 협업 어려움
# 10명의 개발자가 하나의 코드베이스에서 작업
# → Git 충돌 지옥
```

---

## 2단계: 마이크로서비스란?

### 마이크로서비스의 정의

**마이크로서비스** = 애플리케이션을 독립적으로 배포 가능한 작은 서비스들로 분리

```
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ 인증 서비스   │  │ 게시글 서비스 │  │ 이미지 서비스 │
│ (Node.js)    │  │ (Python)     │  │ (Go)         │
│ Port 3001    │  │ Port 3002    │  │ Port 3003    │
└──────────────┘  └──────────────┘  └──────────────┘
       │                 │                 │
       └─────────────────┴─────────────────┘
                         │
                  ┌──────────────┐
                  │  API Gateway  │
                  │  Port 80      │
                  └──────────────┘
                         │
                     사용자 요청
```

### 마이크로서비스의 핵심 원칙

1. **단일 책임**: 각 서비스는 하나의 비즈니스 기능만 담당
2. **독립 배포**: 다른 서비스에 영향 없이 배포 가능
3. **기술 독립**: 각 서비스가 다른 언어/프레임워크 사용 가능
4. **데이터 독립**: 각 서비스가 자신의 데이터베이스 소유

---

## 3단계: 실제 마이그레이션 과정

### Step 1: 모놀리스 분석

현재 코드를 기능별로 나눕니다.

```python
# 기존 모놀리스 (app.py)
from flask import Flask, request, jsonify
import bcrypt
import boto3
import stripe

app = Flask(__name__)

# 인증 관련 (100 lines)
@app.route('/login', methods=['POST'])
def login():
    # 사용자 인증 로직
    pass

@app.route('/register', methods=['POST'])
def register():
    # 회원가입 로직
    pass

# 게시글 관련 (200 lines)
@app.route('/posts', methods=['GET'])
def get_posts():
    # 게시글 목록 조회
    pass

@app.route('/posts', methods=['POST'])
def create_post():
    # 게시글 생성
    pass

# 이미지 관련 (150 lines)
@app.route('/upload', methods=['POST'])
def upload_image():
    # S3 업로드 + 리사이징
    pass

# 결제 관련 (100 lines)
@app.route('/payment', methods=['POST'])
def process_payment():
    # Stripe 결제 처리
    pass
```

**분석 결과: 4개의 서비스로 분리 가능**
- 인증 서비스 (Auth Service)
- 게시글 서비스 (Post Service)
- 이미지 서비스 (Image Service)
- 결제 서비스 (Payment Service)

### Step 2: 첫 번째 서비스 분리 (가장 독립적인 것부터)

**이미지 서비스 분리하기**

```python
# image_service.py (새로운 독립 서비스)
from flask import Flask, request, jsonify
import boto3
from PIL import Image
import io

app = Flask(__name__)
s3 = boto3.client('s3')

@app.route('/upload', methods=['POST'])
def upload_image():
    """
    이미지 업로드 및 리사이징 전담 서비스
    - 다른 서비스와 독립적으로 확장 가능
    - CPU 집약적 작업이 다른 서비스에 영향 없음
    """
    image_file = request.files['image']

    # 이미지 리사이징 (CPU 많이 사용)
    img = Image.open(image_file)
    img.thumbnail((800, 600))

    # S3 업로드
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG')
    buffer.seek(0)

    filename = f"images/{uuid.uuid4()}.jpg"
    s3.upload_fileobj(buffer, 'my-bucket', filename)

    return jsonify({
        'url': f"https://cdn.example.com/{filename}",
        'size': img.size
    })

if __name__ == '__main__':
    # 독립적인 포트에서 실행
    app.run(port=3003)
```

**기존 모놀리스에서 호출하기**

```python
# 기존 app.py (모놀리스)
import requests

@app.route('/posts', methods=['POST'])
def create_post():
    title = request.json['title']
    image = request.files.get('image')

    # 이제 이미지 처리는 별도 서비스에 위임
    if image:
        # HTTP 요청으로 이미지 서비스 호출
        response = requests.post(
            'http://image-service:3003/upload',
            files={'image': image}
        )
        image_url = response.json()['url']
    else:
        image_url = None

    # 게시글 저장
    post = {
        'title': title,
        'image_url': image_url
    }
    db.posts.insert(post)

    return jsonify(post)
```

### Step 3: 서비스 간 통신 패턴

#### 패턴 1: REST API (가장 간단)

```python
# 게시글 서비스 → 인증 서비스 호출
import requests

def get_user_info(user_id):
    # HTTP GET 요청으로 사용자 정보 조회
    response = requests.get(f'http://auth-service:3001/users/{user_id}')
    return response.json()

@app.route('/posts', methods=['POST'])
def create_post():
    # 먼저 사용자 인증 확인
    token = request.headers['Authorization']
    user = requests.post('http://auth-service:3001/verify',
                         json={'token': token}).json()

    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    # 게시글 생성
    post = {'author_id': user['id'], 'title': request.json['title']}
    db.posts.insert(post)
    return jsonify(post)
```

**장점**: 간단하고 직관적
**단점**: 동기 호출이라 느릴 수 있음 (네트워크 지연)

#### 패턴 2: 메시지 큐 (비동기)

```python
# 결제 서비스: 결제 완료 후 이벤트 발행
import pika  # RabbitMQ 클라이언트

def process_payment(user_id, amount):
    # 결제 처리
    payment_result = stripe.charge(amount)

    # 다른 서비스들에게 알림 (비동기)
    connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq'))
    channel = connection.channel()

    message = {
        'event': 'payment_completed',
        'user_id': user_id,
        'amount': amount,
        'timestamp': datetime.now().isoformat()
    }

    # 메시지 큐에 발행
    channel.basic_publish(
        exchange='events',
        routing_key='payment.completed',
        body=json.dumps(message)
    )

    return payment_result

# 이메일 서비스: 결제 완료 이벤트 구독
def on_payment_completed(ch, method, properties, body):
    message = json.loads(body)
    user_id = message['user_id']
    amount = message['amount']

    # 영수증 이메일 발송
    send_email(user_id, f"결제 완료: {amount}원")

# 메시지 큐 구독 시작
channel.basic_consume(
    queue='email_service_queue',
    on_message_callback=on_payment_completed,
    auto_ack=True
)

channel.start_consuming()
```

**장점**: 서비스 간 결합도 낮음, 한 서비스 장애가 다른 서비스에 영향 없음
**단점**: 복잡도 증가, 디버깅 어려움

---

## 4단계: 데이터베이스 분리

### 문제: 공유 데이터베이스

```
❌ 안티패턴: 모든 서비스가 하나의 DB 사용

┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ 인증 서비스   │  │ 게시글 서비스 │  │ 결제 서비스   │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                 │
       └─────────────────┴─────────────────┘
                         │
                  ┌──────────────┐
                  │  MySQL (공유) │
                  │  users 테이블 │
                  │  posts 테이블 │
                  │  payments     │
                  └──────────────┘

문제점:
- 게시글 서비스가 users 테이블 스키마 바꾸면 인증 서비스 깨짐
- 하나의 DB가 병목점
- 서비스 간 독립성 없음
```

### 해결: Database per Service 패턴

```
✅ 각 서비스가 자신의 데이터베이스 소유

┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ 인증 서비스   │  │ 게시글 서비스 │  │ 결제 서비스   │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                 │
  ┌────┴────┐      ┌─────┴─────┐     ┌────┴────┐
  │ PostgreSQL│      │   MongoDB  │     │  MySQL  │
  │  users   │      │   posts    │     │ payments│
  └──────────┘      └────────────┘     └─────────┘

장점:
✅ 서비스 간 독립성
✅ 각 서비스에 최적화된 DB 선택 가능
✅ 스키마 변경 자유로움
```

### 데이터 동기화 문제 해결

**문제**: 게시글 서비스가 작성자 이름을 표시하려면?

```python
# ❌ 안티패턴: 직접 인증 서비스 DB 접근
def get_post_with_author(post_id):
    post = posts_db.query(f"SELECT * FROM posts WHERE id={post_id}")
    # 다른 서비스의 DB에 직접 쿼리 - 절대 하지 말 것!
    author = auth_db.query(f"SELECT * FROM users WHERE id={post.author_id}")
    return {**post, 'author_name': author.name}
```

**✅ 해결 방법 1: API 호출**

```python
def get_post_with_author(post_id):
    post = posts_db.query(f"SELECT * FROM posts WHERE id={post_id}")

    # 인증 서비스의 공개 API 호출
    response = requests.get(f'http://auth-service/users/{post.author_id}')
    author = response.json()

    return {**post, 'author_name': author['name']}
```

**✅ 해결 방법 2: 데이터 복제 (더 빠름)**

```python
# 게시글 생성 시 작성자 이름을 함께 저장
@app.route('/posts', methods=['POST'])
def create_post():
    author_id = request.json['author_id']

    # 작성자 정보 조회 (1회만)
    author = requests.get(f'http://auth-service/users/{author_id}').json()

    # 게시글에 작성자 이름 함께 저장 (비정규화)
    post = {
        'title': request.json['title'],
        'author_id': author_id,
        'author_name': author['name'],  # 복제된 데이터
        'created_at': datetime.now()
    }
    posts_db.insert(post)
    return jsonify(post)

# 이제 조회할 때 API 호출 불필요
def get_post(post_id):
    post = posts_db.query(f"SELECT * FROM posts WHERE id={post_id}")
    # author_name이 이미 있음!
    return post
```

**Trade-off**: 데이터 중복 vs 성능

---

## 5단계: API Gateway 패턴

### 문제: 클라이언트가 여러 서비스 직접 호출

```javascript
// ❌ 프론트엔드에서 여러 서비스 직접 호출
async function loadPostPage(postId) {
  // 3개의 다른 서버에 요청
  const post = await fetch('http://post-service:3002/posts/' + postId);
  const author = await fetch('http://auth-service:3001/users/' + post.author_id);
  const comments = await fetch('http://comment-service:3004/comments?post=' + postId);

  // 문제:
  // - CORS 설정 3번 필요
  // - 클라이언트가 서비스 주소를 다 알아야 함
  // - 네트워크 요청 3번
}
```

### 해결: API Gateway

```
                    사용자
                      │
                      ▼
              ┌──────────────┐
              │ API Gateway   │ ← 단일 진입점
              │ (예: Kong)    │
              └──────┬───────┘
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
   ┌────────┐  ┌─────────┐  ┌─────────┐
   │ 인증    │  │ 게시글   │  │ 결제     │
   │ 서비스  │  │ 서비스   │  │ 서비스   │
   └────────┘  └─────────┘  └─────────┘
```

**API Gateway 구현 예제 (Python + FastAPI)**

```python
# api_gateway.py
from fastapi import FastAPI, Request, HTTPException
import httpx
import asyncio

app = FastAPI()

# 서비스 주소 매핑
SERVICES = {
    'auth': 'http://auth-service:3001',
    'posts': 'http://post-service:3002',
    'images': 'http://image-service:3003',
    'payments': 'http://payment-service:3004'
}

@app.get('/api/posts/{post_id}')
async def get_post_detail(post_id: int):
    """
    하나의 엔드포인트로 여러 서비스 조합
    """
    async with httpx.AsyncClient() as client:
        # 병렬로 3개 서비스 호출
        post_task = client.get(f"{SERVICES['posts']}/posts/{post_id}")
        comments_task = client.get(f"{SERVICES['posts']}/comments?post={post_id}")

        # 동시 실행 (빠름!)
        post_resp, comments_resp = await asyncio.gather(post_task, comments_task)

        post = post_resp.json()
        comments = comments_resp.json()

        # 작성자 정보 추가 조회
        author_resp = await client.get(f"{SERVICES['auth']}/users/{post['author_id']}")
        author = author_resp.json()

        # 하나의 응답으로 조합
        return {
            'post': post,
            'author': author,
            'comments': comments
        }

@app.post('/api/login')
async def login(request: Request):
    """
    라우팅: 특정 서비스로 요청 전달
    """
    body = await request.json()

    async with httpx.AsyncClient() as client:
        response = await client.post(f"{SERVICES['auth']}/login", json=body)
        return response.json()

# 이제 프론트엔드는 하나의 주소만 알면 됨!
# fetch('http://api-gateway/api/posts/123')
```

**API Gateway의 역할**

1. **라우팅**: 요청을 적절한 서비스로 전달
2. **조합 (Aggregation)**: 여러 서비스 응답을 하나로 합침
3. **인증**: 모든 요청에 대한 토큰 검증
4. **Rate Limiting**: API 사용량 제한
5. **로깅**: 모든 API 호출 기록

---

## 6단계: 서비스 디스커버리

### 문제: 하드코딩된 서비스 주소

```python
# ❌ 서비스 주소가 코드에 박혀 있음
SERVICES = {
    'auth': 'http://192.168.1.10:3001',  # 서버 IP가 바뀌면?
    'posts': 'http://192.168.1.11:3002',  # 서버 추가하면?
}
```

### 해결: 서비스 레지스트리 (Consul, Eureka)

```python
# ✅ 동적 서비스 발견
import consul

# Consul 클라이언트
consul_client = consul.Consul(host='consul-server', port=8500)

def get_service_url(service_name):
    """
    서비스 이름으로 실행 중인 인스턴스 찾기
    """
    # Consul에서 서비스 조회
    _, services = consul_client.health.service(service_name, passing=True)

    if not services:
        raise Exception(f"Service {service_name} not found")

    # 여러 인스턴스 중 하나 선택 (로드 밸런싱)
    import random
    service = random.choice(services)

    address = service['Service']['Address']
    port = service['Service']['Port']

    return f"http://{address}:{port}"

# 사용 예제
@app.get('/posts/{post_id}')
async def get_post(post_id: int):
    # 동적으로 서비스 주소 찾기
    post_service_url = get_service_url('post-service')

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{post_service_url}/posts/{post_id}")
        return response.json()
```

**서비스 등록 (각 서비스 시작 시)**

```python
# post_service.py 시작 시 자동 등록
import consul
import socket

def register_service():
    consul_client = consul.Consul()

    # 현재 서버의 IP와 포트
    hostname = socket.gethostname()
    ip = socket.gethostbyname(hostname)
    port = 3002

    # Consul에 등록
    consul_client.agent.service.register(
        name='post-service',
        service_id=f'post-service-{ip}-{port}',
        address=ip,
        port=port,
        check={
            'http': f'http://{ip}:{port}/health',
            'interval': '10s'  # 10초마다 헬스체크
        }
    )

if __name__ == '__main__':
    register_service()  # 서비스 시작 시 등록
    app.run(port=3002)
```

---

## 7단계: 장애 처리 (Resilience Patterns)

### 문제: 연쇄 장애 (Cascading Failure)

```
사용자 → API Gateway → 게시글 서비스 → 인증 서비스 (다운!)
                                            ↓
                               모든 게시글 요청 실패 😱
```

### 해결 1: Circuit Breaker (서킷 브레이커)

```python
# 전기 차단기처럼 장애 서비스로의 요청을 차단
from pybreaker import CircuitBreaker

# 서킷 브레이커 설정
auth_breaker = CircuitBreaker(
    fail_max=5,          # 5번 연속 실패하면
    timeout_duration=60  # 60초 동안 차단
)

@auth_breaker
def call_auth_service(user_id):
    """
    인증 서비스 호출 (서킷 브레이커로 보호)
    """
    response = requests.get(f'http://auth-service/users/{user_id}')
    return response.json()

@app.get('/posts/{post_id}')
def get_post(post_id: int):
    post = db.posts.get(post_id)

    try:
        # 서킷 브레이커로 보호된 호출
        author = call_auth_service(post.author_id)
        post['author_name'] = author['name']
    except Exception as e:
        # 인증 서비스 장애 시 기본값 사용
        print(f"Auth service down: {e}")
        post['author_name'] = "Unknown"

    return post

# 동작 방식:
# 1. 정상: 요청 전달
# 2. 5번 실패: 서킷 오픈 (60초간 요청 차단)
# 3. 60초 후: 반쯤 오픈 (1개 요청만 시도)
# 4. 성공하면: 서킷 닫힘 (정상 복구)
```

### 해결 2: Retry (재시도)

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),              # 최대 3번 시도
    wait=wait_exponential(multiplier=1, min=2, max=10)  # 2초, 4초, 8초 대기
)
def call_flaky_service():
    """
    불안정한 서비스 호출 (자동 재시도)
    """
    response = requests.get('http://unreliable-service/data')
    response.raise_for_status()
    return response.json()

# 1번 실패 → 2초 대기 → 재시도
# 2번 실패 → 4초 대기 → 재시도
# 3번 실패 → 예외 발생
```

### 해결 3: Timeout (타임아웃)

```python
import httpx

@app.get('/posts/{post_id}')
async def get_post(post_id: int):
    async with httpx.AsyncClient(timeout=2.0) as client:  # 2초 타임아웃
        try:
            response = await client.get(f'http://slow-service/data')
            return response.json()
        except httpx.TimeoutException:
            # 2초 안에 응답 없으면 기본값 반환
            return {"error": "Service timeout", "data": None}
```

---

## 실전 예제: 블로그 서비스 마이그레이션

### Before: 모놀리스

```python
# monolith.py (1000 lines)
from flask import Flask, request, jsonify
import bcrypt
import boto3

app = Flask(__name__)
db = Database()

@app.route('/posts', methods=['POST'])
def create_post():
    # 1. 인증 확인
    token = request.headers['Authorization']
    user = verify_token(token)
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    # 2. 이미지 업로드
    image = request.files.get('image')
    if image:
        s3 = boto3.client('s3')
        img_url = s3.upload(image)

    # 3. 게시글 저장
    post = {
        'title': request.json['title'],
        'author_id': user['id'],
        'image_url': img_url
    }
    db.posts.insert(post)

    # 4. 이메일 발송
    send_email(user['email'], "게시글이 등록되었습니다")

    return jsonify(post)

# 문제:
# - 이미지 업로드 실패 → 전체 요청 실패
# - 이메일 발송 느림 → 응답 지연
# - S3 라이브러리 업데이트 → 전체 재배포
```

### After: 마이크로서비스

```python
# ============================================
# 1. API Gateway (api_gateway.py)
# ============================================
from fastapi import FastAPI, UploadFile, Header
import httpx

app = FastAPI()

@app.post('/posts')
async def create_post(
    title: str,
    image: UploadFile = None,
    authorization: str = Header(None)
):
    async with httpx.AsyncClient() as client:
        # 1. 인증 서비스에 토큰 검증
        auth_resp = await client.post(
            'http://auth-service/verify',
            json={'token': authorization}
        )
        if auth_resp.status_code != 200:
            return {'error': 'Unauthorized'}, 401

        user = auth_resp.json()

        # 2. 이미지가 있으면 이미지 서비스에 업로드
        image_url = None
        if image:
            files = {'image': image.file}
            img_resp = await client.post(
                'http://image-service/upload',
                files=files
            )
            image_url = img_resp.json()['url']

        # 3. 게시글 서비스에 저장 요청
        post_resp = await client.post(
            'http://post-service/posts',
            json={
                'title': title,
                'author_id': user['id'],
                'author_name': user['name'],
                'image_url': image_url
            }
        )
        post = post_resp.json()

        # 4. 이메일 서비스에 비동기 이벤트 발행
        await client.post(
            'http://event-bus/publish',
            json={
                'event': 'post_created',
                'user_email': user['email'],
                'post_id': post['id']
            }
        )

        return post

# ============================================
# 2. 인증 서비스 (auth_service.py)
# ============================================
from flask import Flask, request, jsonify
import jwt

app = Flask(__name__)
db = AuthDatabase()  # 독립 DB

@app.post('/verify')
def verify_token():
    token = request.json['token']
    try:
        payload = jwt.decode(token, 'secret', algorithms=['HS256'])
        user = db.users.get(payload['user_id'])
        return jsonify(user)
    except:
        return jsonify({'error': 'Invalid token'}), 401

if __name__ == '__main__':
    app.run(port=3001)

# ============================================
# 3. 이미지 서비스 (image_service.py)
# ============================================
from flask import Flask, request, jsonify
import boto3
from PIL import Image

app = Flask(__name__)
s3 = boto3.client('s3')

@app.post('/upload')
def upload_image():
    image = request.files['image']

    # CPU 집약적 작업 (다른 서비스에 영향 없음)
    img = Image.open(image)
    img.thumbnail((800, 600))

    # S3 업로드
    filename = f"{uuid.uuid4()}.jpg"
    s3.upload(img, filename)

    return jsonify({'url': f"https://cdn.example.com/{filename}"})

if __name__ == '__main__':
    app.run(port=3003)

# ============================================
# 4. 게시글 서비스 (post_service.py)
# ============================================
from flask import Flask, request, jsonify

app = Flask(__name__)
db = PostDatabase()  # 독립 DB

@app.post('/posts')
def create_post():
    post = {
        'title': request.json['title'],
        'author_id': request.json['author_id'],
        'author_name': request.json['author_name'],  # 복제된 데이터
        'image_url': request.json.get('image_url'),
        'created_at': datetime.now()
    }
    db.posts.insert(post)
    return jsonify(post)

@app.get('/posts/<int:post_id>')
def get_post(post_id):
    # 다른 서비스 호출 없이 빠르게 조회
    post = db.posts.get(post_id)
    return jsonify(post)

if __name__ == '__main__':
    app.run(port=3002)

# ============================================
# 5. 이메일 서비스 (email_service.py)
# ============================================
import pika
import json

# RabbitMQ 연결
connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq'))
channel = connection.channel()

def on_post_created(ch, method, properties, body):
    """
    post_created 이벤트 구독
    """
    event = json.loads(body)
    send_email(
        event['user_email'],
        f"게시글 '{event['post_id']}'가 등록되었습니다"
    )

# 이벤트 구독 시작
channel.basic_consume(
    queue='email_queue',
    on_message_callback=on_post_created,
    auto_ack=True
)

print("이메일 서비스 시작...")
channel.start_consuming()
```

---

## 배포 및 운영

### Docker Compose로 로컬 실행

```yaml
# docker-compose.yml
version: '3.8'

services:
  # API Gateway
  api-gateway:
    build: ./api-gateway
    ports:
      - "80:8000"
    depends_on:
      - auth-service
      - post-service
      - image-service

  # 인증 서비스
  auth-service:
    build: ./auth-service
    ports:
      - "3001:3001"
    environment:
      - DATABASE_URL=postgresql://postgres:password@auth-db/auth
    depends_on:
      - auth-db

  # 게시글 서비스
  post-service:
    build: ./post-service
    ports:
      - "3002:3002"
    environment:
      - DATABASE_URL=mongodb://post-db:27017/posts
    depends_on:
      - post-db

  # 이미지 서비스
  image-service:
    build: ./image-service
    ports:
      - "3003:3003"
    environment:
      - AWS_ACCESS_KEY_ID=${AWS_KEY}
      - AWS_SECRET_ACCESS_KEY=${AWS_SECRET}

  # 이메일 서비스
  email-service:
    build: ./email-service
    depends_on:
      - rabbitmq

  # 데이터베이스들
  auth-db:
    image: postgres:14
    environment:
      POSTGRES_DB: auth
      POSTGRES_PASSWORD: password

  post-db:
    image: mongo:5

  # 메시지 큐
  rabbitmq:
    image: rabbitmq:3-management
    ports:
      - "5672:5672"
      - "15672:15672"  # 관리 UI

# 실행: docker-compose up
# 접속: http://localhost/posts
```

---

## 마이크로서비스의 트레이드오프

### 장점 ✅

1. **독립 배포**: 이메일 서비스 수정해도 게시글 서비스 재배포 불필요
2. **기술 독립**: 인증은 Node.js, 이미지는 Go, 게시글은 Python 가능
3. **확장성**: CPU 많이 쓰는 이미지 서비스만 서버 10대로 확장
4. **팀 자율성**: 각 팀이 자기 서비스만 책임
5. **장애 격리**: 이메일 서비스 다운되어도 게시글 조회는 정상

### 단점 ❌

1. **복잡도 증가**: 서비스 10개 → 배포 10번, 모니터링 10개
2. **네트워크 지연**: 함수 호출 (1μs) → HTTP 호출 (10ms+)
3. **데이터 일관성**: 분산 트랜잭션 어려움
4. **디버깅 어려움**: 로그가 10개 서버에 흩어짐
5. **초기 비용**: 모놀리스보다 개발 시간 2-3배

### 언제 마이크로서비스를 도입해야 할까?

**도입하지 말아야 할 때 ❌**
- 팀 크기 < 5명
- 사용자 < 1만명
- 빠른 MVP 필요
- 도메인이 계속 변화

**도입해야 할 때 ✅**
- 팀 크기 > 20명 (여러 팀)
- 트래픽이 부분적으로 급증 (예: 결제만 10배)
- 서로 다른 기술 스택 필요
- 배포 주기를 독립적으로 가져가야 함

---

## 체크리스트: 이 과정을 마스터했는가?

- [ ] 모놀리스와 마이크로서비스의 차이를 설명할 수 있다
- [ ] 모놀리스에서 첫 번째 서비스를 분리할 수 있다 (가장 독립적인 것부터)
- [ ] REST API로 서비스 간 통신을 구현할 수 있다
- [ ] 메시지 큐(RabbitMQ)로 비동기 통신을 구현할 수 있다
- [ ] Database per Service 패턴을 이해하고 데이터 중복의 trade-off를 설명할 수 있다
- [ ] API Gateway를 구현하여 여러 서비스를 조합할 수 있다
- [ ] Circuit Breaker 패턴으로 장애를 격리할 수 있다
- [ ] Docker Compose로 여러 서비스를 로컬에서 실행할 수 있다
- [ ] 마이크로서비스의 단점과 언제 도입하지 말아야 하는지 설명할 수 있다

---

## 다음 단계

1. **실습 프로젝트**: 자신의 모놀리스 프로젝트를 2-3개 서비스로 분리해보기
2. **Kubernetes 학습**: 프로덕션 환경에서 마이크로서비스 운영
3. **Service Mesh**: Istio, Linkerd로 서비스 간 통신 관리
4. **Event-Driven Architecture**: Kafka로 대용량 이벤트 스트리밍
5. **Observability**: Prometheus, Grafana, Jaeger로 모니터링

---

## 참고 자료

- **책**: "Building Microservices" by Sam Newman
- **동영상**: [Microservices Explained in 5 Minutes](https://www.youtube.com/watch?v=lL_j7ilk7rc)
- **실습**: [Microservices Demo by Google Cloud](https://github.com/GoogleCloudPlatform/microservices-demo)
- **패턴**: [Microservices.io](https://microservices.io/patterns/) - 마이크로서비스 패턴 카탈로그
