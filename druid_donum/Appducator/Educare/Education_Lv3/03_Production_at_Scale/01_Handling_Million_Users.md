# 백만 사용자 대응하기: 스케일링의 실전

**대상 독자**: 소규모 서비스를 만들어봤지만 대규모 트래픽 처리 경험이 없는 개발자
**선행 지식**: 기본적인 웹 개발, 데이터베이스 사용 경험
**학습 시간**: 3-4시간

---

## 시작: 당신의 서비스가 대박났다

### Day 1: 100명의 사용자

```python
# 간단한 Flask 앱
from flask import Flask, jsonify
import sqlite3

app = Flask(__name__)

@app.route('/users/<int:user_id>')
def get_user(user_id):
    conn = sqlite3.connect('app.db')
    user = conn.execute('SELECT * FROM users WHERE id=?', (user_id,)).fetchone()
    conn.close()
    return jsonify(user)

if __name__ == '__main__':
    app.run()

# 응답 시간: 50ms
# CPU 사용률: 5%
# 모든 것이 완벽! ✅
```

### Day 30: 10,000명의 사용자

```
문제 발생:
⚠️ 응답 시간: 50ms → 500ms (10배 증가)
⚠️ CPU 사용률: 5% → 60%
⚠️ 데이터베이스 연결 오류 빈발
```

### Day 60: 100,000명의 사용자

```
심각한 문제:
❌ 응답 시간: 5초+
❌ CPU 사용률: 95%+
❌ 서버 다운 (하루 3번)
❌ 사용자 이탈률 급증
```

### Day 90: 1,000,000명의 사용자 (목표)

```
필요한 것:
✅ 응답 시간 < 100ms (언제나)
✅ 99.9% 가용성 (한 달에 43분 이하 다운타임)
✅ 동시 접속자 100,000명 처리
✅ 데이터베이스 조회/쓰기 초당 10,000건
```

이 가이드는 **Day 1 → Day 90으로 가는 여정**을 단계별로 안내합니다.

---

## 단계 1: 데이터베이스 최적화

### 문제: N+1 쿼리

```python
# ❌ 성능 재앙: N+1 쿼리
@app.route('/posts')
def get_posts():
    posts = db.execute('SELECT * FROM posts LIMIT 100').fetchall()

    result = []
    for post in posts:  # 100번 반복
        # 매번 DB 쿼리! (100번 추가 쿼리)
        author = db.execute('SELECT * FROM users WHERE id=?', (post['author_id'],)).fetchone()
        post['author_name'] = author['name']
        result.append(post)

    return jsonify(result)

# 총 쿼리 수: 1 (posts) + 100 (authors) = 101번
# 응답 시간: 1초+ 😱
```

### 해결: JOIN 사용

```python
# ✅ 해결 1: JOIN으로 한 번에 조회
@app.route('/posts')
def get_posts():
    query = '''
        SELECT
            posts.*,
            users.name AS author_name,
            users.avatar AS author_avatar
        FROM posts
        JOIN users ON posts.author_id = users.id
        LIMIT 100
    '''
    posts = db.execute(query).fetchall()
    return jsonify(posts)

# 총 쿼리 수: 1번
# 응답 시간: 50ms ✅
```

### 인덱스 추가

```python
# ✅ 인덱스로 조회 속도 향상
# 인덱스 없을 때: Full Table Scan (모든 행 확인)
# 인덱스 있을 때: B-Tree 검색 (로그 시간)

# 마이그레이션 파일
CREATE INDEX idx_posts_author_id ON posts(author_id);
CREATE INDEX idx_posts_created_at ON posts(created_at);
CREATE INDEX idx_users_email ON users(email);

# Before: SELECT * FROM posts WHERE author_id = 123
# → 100만 행 전체 스캔 (3초)

# After: 인덱스로 즉시 찾기 (10ms)
```

**인덱스 사용 전후 비교**

```sql
-- 인덱스 없을 때
EXPLAIN SELECT * FROM posts WHERE author_id = 123;
-- Seq Scan on posts (cost=0.00..18334.52 rows=1000 width=100)

-- 인덱스 있을 때
EXPLAIN SELECT * FROM posts WHERE author_id = 123;
-- Index Scan using idx_posts_author_id (cost=0.29..8.31 rows=1 width=100)
-- 2000배 빠름!
```

---

## 단계 2: 캐싱 (Caching)

### 원리: 자주 사용하는 데이터를 메모리에 저장

```
캐시 없을 때:
사용자 요청 → 데이터베이스 조회 (50ms)
사용자 요청 → 데이터베이스 조회 (50ms)
사용자 요청 → 데이터베이스 조회 (50ms)
... 매번 DB 부하

캐시 있을 때:
사용자 요청 → Redis 조회 (1ms) ✅
사용자 요청 → Redis 조회 (1ms) ✅
사용자 요청 → Redis 조회 (1ms) ✅
... DB 부하 거의 없음
```

### 실전: Redis 캐시 적용

```python
# ✅ Redis로 인기 게시글 캐싱
import redis
import json

cache = redis.Redis(host='localhost', port=6379, decode_responses=True)

@app.route('/posts/popular')
def get_popular_posts():
    # 1. 캐시 확인
    cached = cache.get('popular_posts')
    if cached:
        print("캐시 히트! 🎯")
        return cached  # 1ms 만에 응답

    # 2. 캐시 미스: DB 조회
    print("캐시 미스... DB 조회")
    posts = db.execute('''
        SELECT * FROM posts
        ORDER BY views DESC
        LIMIT 20
    ''').fetchall()

    result = json.dumps(posts)

    # 3. 캐시에 저장 (10분간 유효)
    cache.setex('popular_posts', 600, result)

    return result

# 첫 번째 요청: DB 조회 (50ms)
# 이후 10분간: Redis 조회 (1ms) × 10,000 요청
# → DB 부하 99% 감소!
```

### 캐시 무효화 전략

```python
# 문제: 게시글이 업데이트되어도 캐시는 그대로
# 해결: 게시글 수정 시 캐시 삭제

@app.route('/posts/<int:post_id>', methods=['PUT'])
def update_post(post_id):
    # 1. 게시글 업데이트
    db.execute(
        'UPDATE posts SET title=?, content=? WHERE id=?',
        (title, content, post_id)
    )

    # 2. 관련 캐시 삭제
    cache.delete(f'post:{post_id}')
    cache.delete('popular_posts')  # 인기 게시글 목록도 갱신
    cache.delete(f'user_posts:{author_id}')  # 작성자 게시글 목록도 갱신

    return jsonify({'message': 'Updated'})
```

### Cache-Aside 패턴 (권장)

```python
def get_user(user_id):
    """
    캐시 우선, 없으면 DB 조회 후 캐시 저장
    """
    cache_key = f'user:{user_id}'

    # 1. 캐시 확인
    cached_user = cache.get(cache_key)
    if cached_user:
        return json.loads(cached_user)

    # 2. DB 조회
    user = db.execute('SELECT * FROM users WHERE id=?', (user_id,)).fetchone()

    if user:
        # 3. 캐시 저장 (1시간)
        cache.setex(cache_key, 3600, json.dumps(user))

    return user
```

---

## 단계 3: 수평 확장 (Horizontal Scaling)

### 수직 확장 vs 수평 확장

```
수직 확장 (Scale Up): 서버를 더 좋은 것으로 교체
┌─────────────┐      ┌─────────────┐
│  2 CPU      │  →   │  32 CPU     │
│  4GB RAM    │      │  128GB RAM  │
│  $100/월    │      │  $2,000/월  │
└─────────────┘      └─────────────┘

한계:
❌ 비용이 기하급수적으로 증가
❌ 물리적 한계 (세상에서 가장 좋은 서버도 한계가 있음)
❌ 단일 장애점 (서버 하나 죽으면 전체 다운)

수평 확장 (Scale Out): 서버를 더 많이 추가
┌─────────┐           ┌─────────┐ ┌─────────┐ ┌─────────┐
│ 2 CPU   │     →     │ 2 CPU   │ │ 2 CPU   │ │ 2 CPU   │
│ 4GB RAM │           │ 4GB RAM │ │ 4GB RAM │ │ 4GB RAM │
│ $100/월 │           │ $100/월 │ │ $100/월 │ │ $100/월 │
└─────────┘           └─────────┘ └─────────┘ └─────────┘
                           3배 성능, 3배 비용 (선형)

장점:
✅ 비용 효율적 (선형 증가)
✅ 무한 확장 가능
✅ 고가용성 (하나 죽어도 나머지가 처리)
```

### 로드 밸런서 추가

```
사용자 요청
    ↓
┌───────────────┐
│ Load Balancer │ ← nginx, HAProxy, AWS ELB
│  (Nginx)      │
└───────┬───────┘
        │
  ┌─────┼─────┐
  ↓     ↓     ↓
┌────┐┌────┐┌────┐
│App1││App2││App3│ ← 동일한 애플리케이션 3개
└────┘└────┘└────┘
  │     │     │
  └─────┼─────┘
        ↓
   ┌─────────┐
   │Database │
   └─────────┘
```

**Nginx 설정 예제**

```nginx
# /etc/nginx/nginx.conf
upstream app_servers {
    # 라운드로빈: 순서대로 분배
    server app1.example.com:8000;
    server app2.example.com:8000;
    server app3.example.com:8000;
}

server {
    listen 80;

    location / {
        proxy_pass http://app_servers;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

# 트래픽 분배:
# 요청 1 → app1
# 요청 2 → app2
# 요청 3 → app3
# 요청 4 → app1 (순환)
```

**가중치 기반 로드 밸런싱**

```nginx
upstream app_servers {
    server app1.example.com:8000 weight=3;  # 더 좋은 서버
    server app2.example.com:8000 weight=1;  # 구형 서버
    server app3.example.com:8000 weight=1;

    # app1이 60%의 트래픽 처리
}
```

### 세션 관리 문제

```python
# ❌ 문제: 서버별로 다른 세션
# 사용자 로그인 → app1에 저장
session['user_id'] = 123

# 다음 요청 → app2로 라우팅
# app2는 세션 정보 없음! → 로그인 풀림 😱
```

**해결 1: Sticky Session (권장하지 않음)**

```nginx
upstream app_servers {
    ip_hash;  # 같은 IP는 같은 서버로
    server app1.example.com:8000;
    server app2.example.com:8000;
}

# 단점: 특정 서버에 부하 집중 가능
```

**해결 2: 중앙 세션 저장소 (권장) ✅**

```python
# Flask 세션을 Redis에 저장
from flask import Flask, session
from flask_session import Session
import redis

app = Flask(__name__)
app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_REDIS'] = redis.Redis(host='redis-server', port=6379)
Session(app)

@app.route('/login', methods=['POST'])
def login():
    # 세션 정보가 Redis에 저장됨
    session['user_id'] = 123
    # 어느 app 서버로 가도 Redis에서 조회 가능!
    return 'Logged in'

# app1, app2, app3 모두 같은 Redis 사용
# → 세션 공유 완료! ✅
```

---

## 단계 4: 데이터베이스 스케일링

### 4-1. Read Replica (읽기 복제본)

```
문제: 데이터베이스가 병목
- 쓰기: 10% (INSERT, UPDATE, DELETE)
- 읽기: 90% (SELECT)

해결: 읽기 전용 복제본 추가

         ┌─────────────────┐
         │  Primary DB     │ ← 쓰기 (Master)
         │  (Write)        │
         └────────┬────────┘
                  │ 복제
         ┌────────┴────────┐
         ↓                 ↓
    ┌─────────┐      ┌─────────┐
    │Replica 1│      │Replica 2│ ← 읽기 전용
    │(Read)   │      │(Read)   │
    └─────────┘      └─────────┘
```

**Python 코드 예제**

```python
import random
from sqlalchemy import create_engine

# Primary DB (쓰기)
primary_db = create_engine('postgresql://primary-db:5432/app')

# Replica DBs (읽기)
replica_dbs = [
    create_engine('postgresql://replica1-db:5432/app'),
    create_engine('postgresql://replica2-db:5432/app'),
]

def get_read_db():
    """읽기용 DB를 랜덤하게 선택 (로드 밸런싱)"""
    return random.choice(replica_dbs)

# 읽기 쿼리
@app.route('/posts')
def get_posts():
    db = get_read_db()  # Replica 사용
    posts = db.execute('SELECT * FROM posts LIMIT 100').fetchall()
    return jsonify(posts)

# 쓰기 쿼리
@app.route('/posts', methods=['POST'])
def create_post():
    db = primary_db  # Primary 사용
    db.execute('INSERT INTO posts (title) VALUES (?)', (title,))
    db.commit()
    return jsonify({'message': 'Created'})

# 결과:
# - 읽기 부하 90% → Replica 2대가 분산 처리
# - 쓰기 부하 10% → Primary 1대가 처리
# → 전체 DB 처리량 3배 증가!
```

### 4-2. 샤딩 (Sharding)

```
문제: 데이터가 너무 많아서 하나의 DB로 감당 불가
- 사용자: 1억명
- 게시글: 10억개
- 한 DB 용량 한계

해결: 데이터를 여러 DB로 분산

      사용자 ID로 샤딩
      ┌──────────────────┐
      │  User ID % 3     │
      └─────────┬────────┘
                │
      ┌─────────┼─────────┐
      ↓         ↓         ↓
  ┌───────┐┌───────┐┌───────┐
  │Shard 0││Shard 1││Shard 2│
  │ID%3=0 ││ID%3=1 ││ID%3=2 │
  │       ││       ││       │
  │User 3 ││User 1 ││User 2 │
  │User 6 ││User 4 ││User 5 │
  │User 9 ││User 7 ││User 8 │
  └───────┘└───────┘└───────┘
```

**샤딩 구현**

```python
# 샤드 매핑
shards = [
    create_engine('postgresql://shard0:5432/app'),
    create_engine('postgresql://shard1:5432/app'),
    create_engine('postgresql://shard2:5432/app'),
]

def get_shard(user_id):
    """사용자 ID로 샤드 선택"""
    shard_index = user_id % len(shards)
    return shards[shard_index]

@app.route('/users/<int:user_id>')
def get_user(user_id):
    # 올바른 샤드에서 조회
    db = get_shard(user_id)
    user = db.execute('SELECT * FROM users WHERE id=?', (user_id,)).fetchone()
    return jsonify(user)

@app.route('/users', methods=['POST'])
def create_user():
    # 새 사용자 ID 생성 (중앙 ID 생성기 사용)
    user_id = id_generator.generate()

    # 해당 샤드에 저장
    db = get_shard(user_id)
    db.execute(
        'INSERT INTO users (id, name, email) VALUES (?, ?, ?)',
        (user_id, name, email)
    )

    return jsonify({'user_id': user_id})
```

**샤딩의 어려움**

```python
# ❌ 문제 1: JOIN이 어려움
# 사용자는 Shard 0에, 게시글은 Shard 1에 있으면
# 한 번의 쿼리로 JOIN 불가능

# ✅ 해결: 애플리케이션 레벨 조인
def get_user_with_posts(user_id):
    user_shard = get_shard(user_id)
    user = user_shard.execute('SELECT * FROM users WHERE id=?', (user_id,))

    # 별도 쿼리로 게시글 조회 (게시글도 user_id로 샤딩되어 있다고 가정)
    post_shard = get_shard(user_id)
    posts = post_shard.execute('SELECT * FROM posts WHERE author_id=?', (user_id,))

    return {'user': user, 'posts': posts}

# ❌ 문제 2: 트랜잭션이 어려움
# 두 개의 샤드에 걸친 원자적 업데이트 어려움

# ✅ 해결: 2-Phase Commit (복잡) 또는 Saga 패턴
```

---

## 단계 5: CDN (Content Delivery Network)

### 문제: 전 세계 사용자에게 빠른 응답

```
서버가 서울에 있을 때:
- 서울 사용자: 10ms ✅
- 도쿄 사용자: 50ms ✅
- LA 사용자: 200ms ⚠️
- 런던 사용자: 300ms ❌

물리적 거리 = 지연 시간
```

### 해결: CDN으로 전 세계 캐싱

```
         사용자 (LA)
              ↓
    ┌──────────────────┐
    │ CDN Edge (LA)    │ ← 10ms (가까움!)
    │ (Cloudflare)     │
    └─────────┬────────┘
              │ 첫 요청 시에만
              ↓
    ┌──────────────────┐
    │ Origin (서울)     │ ← 200ms (멀지만 한 번만)
    └──────────────────┘

첫 번째 LA 사용자: 200ms (Origin에서 가져옴)
이후 LA 사용자들: 10ms (CDN 캐시에서 응답) ✅
```

### 정적 파일 CDN 배포

```python
# Before: 서버에서 직접 제공
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_file(f'static/{filename}')

# 문제: 이미지 100개 → 서버 부하 100배

# ✅ After: CDN 사용
# HTML에서 CDN URL 사용
<img src="https://cdn.example.com/images/logo.png">
# → 서버 부하 0! CDN이 전담

# S3 + CloudFront 예제
import boto3

s3 = boto3.client('s3')

@app.route('/upload', methods=['POST'])
def upload_image():
    image = request.files['image']

    # S3에 업로드
    filename = f'images/{uuid.uuid4()}.jpg'
    s3.upload_fileobj(image, 'my-bucket', filename)

    # CloudFront CDN URL 반환
    cdn_url = f'https://d1234abcd.cloudfront.net/{filename}'
    return jsonify({'url': cdn_url})

# 전 세계 사용자가 10-50ms 안에 이미지 로드!
```

### 동적 콘텐츠도 CDN 캐싱

```python
# API 응답도 CDN에 캐싱 가능
@app.route('/api/posts/popular')
def get_popular_posts():
    # Cache-Control 헤더 추가
    response = jsonify(get_popular_posts_from_db())
    response.headers['Cache-Control'] = 'public, max-age=300'  # 5분간 캐싱
    return response

# CDN(Cloudflare, Fastly 등)이 이 응답을 5분간 캐싱
# → 전 세계 사용자가 동일한 데이터를 빠르게 조회
```

---

## 단계 6: 비동기 처리 (Task Queue)

### 문제: 느린 작업이 응답 지연

```python
# ❌ 동기 처리: 사용자가 5초 대기
@app.route('/signup', methods=['POST'])
def signup():
    # 1. 사용자 생성 (100ms)
    user = create_user(email, password)

    # 2. 환영 이메일 발송 (2초) ← 느림!
    send_welcome_email(user.email)

    # 3. 추천 친구 계산 (3초) ← 매우 느림!
    calculate_friend_recommendations(user.id)

    return jsonify({'message': 'Welcome!'})

# 총 응답 시간: 5초+ 😱
# 사용자: "왜 이렇게 느려?"
```

### 해결: 백그라운드 작업 큐

```python
# ✅ 비동기 처리: 사용자는 100ms만 대기
from celery import Celery

# Celery 설정 (Redis를 메시지 브로커로 사용)
celery = Celery('tasks', broker='redis://localhost:6379/0')

# 백그라운드 작업 정의
@celery.task
def send_welcome_email(email):
    """백그라운드에서 실행될 작업"""
    time.sleep(2)  # 이메일 발송 (느림)
    print(f"Email sent to {email}")

@celery.task
def calculate_friend_recommendations(user_id):
    """백그라운드에서 실행될 작업"""
    time.sleep(3)  # 추천 계산 (매우 느림)
    print(f"Recommendations calculated for user {user_id}")

@app.route('/signup', methods=['POST'])
def signup():
    # 1. 사용자 생성 (100ms)
    user = create_user(email, password)

    # 2. 이메일 발송 (비동기로 예약만)
    send_welcome_email.delay(user.email)  # delay() = 백그라운드 실행

    # 3. 추천 계산 (비동기로 예약만)
    calculate_friend_recommendations.delay(user.id)

    # 즉시 응답 반환!
    return jsonify({'message': 'Welcome!'})

# 총 응답 시간: 100ms ✅
# 이메일/추천은 백그라운드에서 천천히 처리
```

**Celery Worker 실행**

```bash
# 터미널 1: Flask 앱 실행
$ python app.py

# 터미널 2: Celery Worker 실행
$ celery -A app.celery worker --loglevel=info

# Worker가 Redis에서 작업을 가져와 처리
[2025-10-06 10:00:00] Task send_welcome_email received
[2025-10-06 10:00:02] Email sent to user@example.com
```

---

## 단계 7: 모니터링 & 알림

### 문제: 서버가 다운되어도 모름

```
03:00 AM: 데이터베이스 다운
03:01 AM: 사용자들 "사이트 안 돼요" (트위터에 불평)
09:00 AM: 개발자 출근 후 확인 😱
09:30 AM: 서버 재시작
→ 6시간 다운타임!
```

### 해결: 실시간 모니터링

```python
# ✅ Prometheus + Grafana로 모니터링
from prometheus_flask_exporter import PrometheusMetrics

app = Flask(__name__)
metrics = PrometheusMetrics(app)

# 자동으로 측정되는 메트릭:
# - 요청 수
# - 응답 시간
# - 에러율

# 커스텀 메트릭
from prometheus_client import Counter, Histogram

# 게시글 생성 수 추적
posts_created = Counter('posts_created_total', 'Total posts created')

# 이미지 처리 시간 추적
image_processing_time = Histogram('image_processing_seconds', 'Time to process images')

@app.route('/posts', methods=['POST'])
def create_post():
    # 게시글 생성
    create_post_in_db()

    # 메트릭 증가
    posts_created.inc()

    return jsonify({'message': 'Created'})

@app.route('/upload', methods=['POST'])
def upload_image():
    with image_processing_time.time():  # 시간 측정
        process_image()

    return jsonify({'message': 'Uploaded'})
```

**Grafana 대시보드 구성**

```
┌─────────────────────────────────────────┐
│  API 응답 시간                          │
│  ████████░░░░░░ 95th percentile: 120ms │
│  ████████████░░ 50th percentile: 50ms  │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│  초당 요청 수 (RPS)                     │
│  ▁▂▃▅▇█▇▅▃▂▁ 평균: 1,500 RPS          │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│  에러율                                 │
│  ▁▁▁▁▁▁▁▁▁▁▁ 0.05%                    │
└─────────────────────────────────────────┘
```

### 알림 설정 (Alertmanager)

```yaml
# alertmanager.yml
groups:
- name: api_alerts
  rules:
  # 에러율이 1% 넘으면 알림
  - alert: HighErrorRate
    expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.01
    annotations:
      summary: "에러율이 1%를 초과했습니다!"
      description: "5분간 에러율: {{ $value }}%"

  # 응답 시간이 500ms 넘으면 알림
  - alert: SlowResponse
    expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 0.5
    annotations:
      summary: "API 응답이 느립니다"

  # 데이터베이스 연결 실패
  - alert: DatabaseDown
    expr: up{job="postgresql"} == 0
    annotations:
      summary: "데이터베이스가 다운되었습니다!"

# Slack으로 알림 받기
receivers:
- name: 'slack'
  slack_configs:
  - api_url: 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
    channel: '#alerts'
    text: '⚠️ {{ .CommonAnnotations.summary }}'
```

---

## 실전 시나리오: 100만 사용자 아키텍처

### 최종 아키텍처

```
                        인터넷
                           │
                           ↓
                    ┌──────────────┐
                    │   CDN        │ ← 정적 파일 (이미지, CSS, JS)
                    │(CloudFront)  │
                    └──────────────┘
                           │
                           ↓
                    ┌──────────────┐
                    │Load Balancer │ ← AWS ELB
                    │   (Nginx)    │
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              ↓            ↓            ↓
        ┌─────────┐  ┌─────────┐  ┌─────────┐
        │  App 1  │  │  App 2  │  │  App 3  │ ← Auto Scaling (3-20대)
        └────┬────┘  └────┬────┘  └────┬────┘
             │            │            │
             └────────────┼────────────┘
                          │
              ┌───────────┼───────────┐
              ↓           ↓           ↓
        ┌─────────┐ ┌──────────┐ ┌──────────┐
        │ Redis   │ │PostgreSQL│ │ Celery   │
        │(Cache)  │ │(Primary) │ │(Queue)   │
        └─────────┘ └────┬─────┘ └──────────┘
                         │
                    ┌────┴────┐
                    ↓         ↓
              ┌──────────┐┌──────────┐
              │Replica 1 ││Replica 2 │
              └──────────┘└──────────┘
```

### 비용 계산 (AWS 기준, 월 예상)

```
로드 밸런서 (ELB): $20
앱 서버 3대 (t3.medium): $100 × 3 = $300
Redis (ElastiCache): $50
PostgreSQL Primary (db.r5.large): $150
PostgreSQL Replica 2대: $150 × 2 = $300
CloudFront (CDN): $100
S3 (이미지 저장): $50
CloudWatch (모니터링): $30

총 비용: 약 $1,000/월

처리 가능:
✅ 동시 접속자: 100,000명
✅ 초당 요청: 10,000 RPS
✅ 가용성: 99.9%
```

---

## 성능 최적화 체크리스트

### 데이터베이스

- [ ] N+1 쿼리를 JOIN으로 변경했는가?
- [ ] 자주 조회하는 컬럼에 인덱스를 추가했는가?
- [ ] EXPLAIN으로 쿼리 플랜을 확인했는가?
- [ ] Connection Pool을 사용하는가? (매번 연결 생성하지 않기)
- [ ] 읽기 복제본(Read Replica)을 사용하는가?

### 캐싱

- [ ] 자주 조회되는 데이터를 캐싱했는가?
- [ ] 캐시 TTL을 적절히 설정했는가?
- [ ] 데이터 변경 시 캐시를 무효화하는가?
- [ ] Cache-Control 헤더를 설정했는가?

### 서버

- [ ] 로드 밸런서를 사용하는가?
- [ ] Auto Scaling을 설정했는가? (부하에 따라 자동 증설)
- [ ] 세션을 중앙 저장소(Redis)에 저장하는가?
- [ ] Health Check 엔드포인트가 있는가?

### 비동기 처리

- [ ] 느린 작업(이메일, 이미지 처리)을 백그라운드로 처리하는가?
- [ ] Task Queue(Celery, RabbitMQ)를 사용하는가?

### CDN

- [ ] 정적 파일(이미지, CSS, JS)을 CDN에서 제공하는가?
- [ ] 동적 API 응답도 적절히 캐싱되는가?

### 모니터링

- [ ] 에러율, 응답 시간, RPS를 실시간 모니터링하는가?
- [ ] 임계값 초과 시 알림을 받는가?
- [ ] 로그 중앙화(ELK, CloudWatch Logs)를 사용하는가?

---

## 다음 단계

1. **Kubernetes**: 컨테이너 오케스트레이션으로 더 나은 Auto Scaling
2. **Microservices**: 서비스를 기능별로 분리하여 독립 배포
3. **Global Infrastructure**: 다중 리전 배포로 전 세계 저지연
4. **Chaos Engineering**: 장애 시뮬레이션으로 시스템 강건성 테스트

---

## 참고 자료

- **책**: "Designing Data-Intensive Applications" by Martin Kleppmann
- **코스**: [System Design Primer (GitHub)](https://github.com/donnemartin/system-design-primer)
- **도구**: [Locust](https://locust.io/) - 부하 테스트 도구
- **블로그**: [AWS Architecture Blog](https://aws.amazon.com/blogs/architecture/)
