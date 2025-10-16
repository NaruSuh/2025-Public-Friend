# 보안 아키텍처: 처음부터 제대로 설계하기

**대상 독자**: 웹 애플리케이션을 만들어봤지만 보안을 체계적으로 배운 적 없는 개발자
**선행 지식**: 기본적인 웹 개발 (HTTP, 세션, 데이터베이스)
**학습 시간**: 3-4시간

---

## 왜 보안이 중요한가?

### 실제 사례

```
2017년 Equifax 해킹:
- 1억 4천만명 개인정보 유출
- 원인: Apache Struts 취약점 패치 안 함
- 손해: $700M (약 8천억원)

2021년 Codecov 공급망 공격:
- 수백 개 기업의 CI/CD 환경 침해
- 원인: Docker 이미지에 악성코드 삽입
- 영향: Google, HashiCorp 등

당신의 서비스도 예외가 아닙니다.
```

### 보안의 원칙: Defense in Depth (다층 방어)

```
❌ 단일 방어선 (쉽게 뚫림)
┌─────────────┐
│   방화벽     │ ← 이것만 뚫리면 끝
└──────┬──────┘
       ↓
   전체 시스템 노출

✅ 다층 방어 (여러 겹의 보호)
┌─────────────┐
│   WAF       │ ← 1차 방어
└──────┬──────┘
┌──────┴──────┐
│   방화벽     │ ← 2차 방어
└──────┬──────┘
┌──────┴──────┐
│ 인증/인가    │ ← 3차 방어
└──────┬──────┘
┌──────┴──────┐
│ 입력 검증    │ ← 4차 방어
└──────┬──────┘
┌──────┴──────┐
│암호화된 DB  │ ← 5차 방어
└─────────────┘

한 층이 뚫려도 나머지가 보호
```

---

## 1단계: 인증 (Authentication) - "너 누구야?"

### 잘못된 인증

```python
# ❌ 절대 하지 말 것 #1: 평문 비밀번호 저장
@app.route('/register', methods=['POST'])
def register():
    password = request.json['password']
    # 데이터베이스에 그대로 저장 😱
    db.execute('INSERT INTO users (email, password) VALUES (?, ?)',
               (email, password))
    # 해커가 DB 탈취하면 모든 비밀번호 노출!

# ❌ 절대 하지 말 것 #2: MD5/SHA1 해싱
password_hash = hashlib.md5(password.encode()).hexdigest()
# MD5는 1초에 수십억 번 연산 가능 → 무차별 대입 공격에 취약
```

### 올바른 비밀번호 저장: bcrypt

```python
# ✅ bcrypt 사용 (느린 해시 = 안전)
import bcrypt

@app.route('/register', methods=['POST'])
def register():
    password = request.json['password']

    # bcrypt로 해싱 (자동으로 salt 추가)
    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    # 결과: $2b$12$N9qo8uLOickgx2ZMRZoMye... (60자)

    db.execute('INSERT INTO users (email, password_hash) VALUES (?, ?)',
               (email, password_hash))

    return jsonify({'message': 'Registered'})

@app.route('/login', methods=['POST'])
def login():
    email = request.json['email']
    password = request.json['password']

    # DB에서 사용자 조회
    user = db.execute('SELECT * FROM users WHERE email=?', (email,)).fetchone()

    if not user:
        return jsonify({'error': 'Invalid credentials'}), 401

    # bcrypt로 비밀번호 검증
    if bcrypt.checkpw(password.encode(), user['password_hash']):
        # 비밀번호 일치!
        session['user_id'] = user['id']
        return jsonify({'message': 'Logged in'})
    else:
        return jsonify({'error': 'Invalid credentials'}), 401

# bcrypt의 장점:
# - 1번 해싱에 약 0.1초 소요 (의도적으로 느림)
# - 무차별 대입 공격: 1초에 10개만 시도 가능
# - MD5: 1초에 10억 개 시도 가능
# → bcrypt가 1억 배 안전!
```

### JWT (JSON Web Token)으로 stateless 인증

```python
# ✅ JWT 사용 (서버에 세션 저장 불필요)
import jwt
from datetime import datetime, timedelta

SECRET_KEY = 'your-secret-key-keep-it-safe'

@app.route('/login', methods=['POST'])
def login():
    # 사용자 인증 (위와 동일)
    user = authenticate(email, password)

    if not user:
        return jsonify({'error': 'Invalid credentials'}), 401

    # JWT 토큰 생성
    payload = {
        'user_id': user['id'],
        'email': user['email'],
        'exp': datetime.utcnow() + timedelta(hours=24)  # 24시간 유효
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')

    return jsonify({'token': token})

# 클라이언트는 이후 요청에 토큰 포함
# Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

@app.route('/profile')
def get_profile():
    # 요청 헤더에서 토큰 추출
    token = request.headers.get('Authorization', '').replace('Bearer ', '')

    try:
        # 토큰 검증
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        user_id = payload['user_id']

        # 사용자 정보 조회
        user = db.execute('SELECT * FROM users WHERE id=?', (user_id,)).fetchone()
        return jsonify(user)

    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Token expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Invalid token'}), 401

# JWT 장점:
# ✅ 서버에 세션 저장 불필요 (stateless)
# ✅ 마이크로서비스에 적합 (서비스 간 토큰 공유 가능)
# ✅ 모바일 앱에 적합

# JWT 단점:
# ❌ 토큰 무효화 어려움 (로그아웃 구현 복잡)
# ❌ 토큰 크기 큼 (세션 ID보다)
```

### 2FA (2-Factor Authentication)

```python
# ✅ TOTP (Time-based One-Time Password) 구현
import pyotp
import qrcode
from io import BytesIO

@app.route('/enable-2fa', methods=['POST'])
def enable_2fa():
    user_id = session['user_id']

    # 사용자별 secret 생성
    secret = pyotp.random_base32()

    # DB에 저장
    db.execute('UPDATE users SET totp_secret=? WHERE id=?',
               (secret, user_id))

    # QR 코드 생성 (Google Authenticator 앱에서 스캔)
    totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
        name=user['email'],
        issuer_name='MyApp'
    )

    qr = qrcode.make(totp_uri)
    buffer = BytesIO()
    qr.save(buffer, format='PNG')

    return send_file(buffer, mimetype='image/png')

@app.route('/verify-2fa', methods=['POST'])
def verify_2fa():
    user_id = session['user_id']
    code = request.json['code']  # 사용자가 입력한 6자리 코드

    user = db.execute('SELECT * FROM users WHERE id=?', (user_id,)).fetchone()

    # TOTP 검증
    totp = pyotp.TOTP(user['totp_secret'])
    if totp.verify(code):
        session['2fa_verified'] = True
        return jsonify({'message': '2FA verified'})
    else:
        return jsonify({'error': 'Invalid code'}), 401

# 로그인 흐름:
# 1. 이메일/비밀번호 입력 → 인증
# 2. 6자리 코드 입력 (Google Authenticator) → 2FA 검증
# → 두 단계를 모두 통과해야 로그인 완료
```

---

## 2단계: 인가 (Authorization) - "너 이거 할 수 있어?"

### 잘못된 인가

```python
# ❌ 클라이언트를 믿지 마세요
@app.route('/posts/<int:post_id>', methods=['DELETE'])
def delete_post(post_id):
    # 현재 사용자가 이 게시글의 작성자인지 확인 안 함!
    db.execute('DELETE FROM posts WHERE id=?', (post_id,))
    return jsonify({'message': 'Deleted'})

# 공격:
# DELETE /posts/123 → 다른 사람 글 삭제 가능! 😱
```

### 올바른 인가: 소유권 확인

```python
# ✅ 소유권 검증
@app.route('/posts/<int:post_id>', methods=['DELETE'])
def delete_post(post_id):
    user_id = session.get('user_id')

    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    # 게시글 조회
    post = db.execute('SELECT * FROM posts WHERE id=?', (post_id,)).fetchone()

    if not post:
        return jsonify({'error': 'Not found'}), 404

    # 소유권 확인
    if post['author_id'] != user_id:
        return jsonify({'error': 'Forbidden'}), 403

    # 소유자만 삭제 가능
    db.execute('DELETE FROM posts WHERE id=?', (post_id,))
    return jsonify({'message': 'Deleted'})
```

### RBAC (Role-Based Access Control)

```python
# ✅ 역할 기반 권한 관리
# 역할 정의
ROLES = {
    'admin': ['read', 'write', 'delete', 'manage_users'],
    'editor': ['read', 'write', 'delete'],
    'viewer': ['read']
}

def require_permission(permission):
    """데코레이터: 권한 확인"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_id = session.get('user_id')
            if not user_id:
                return jsonify({'error': 'Unauthorized'}), 401

            user = db.execute('SELECT * FROM users WHERE id=?', (user_id,)).fetchone()
            user_role = user['role']

            # 역할에 권한이 있는지 확인
            if permission not in ROLES.get(user_role, []):
                return jsonify({'error': 'Forbidden'}), 403

            return f(*args, **kwargs)
        return decorated_function
    return decorator

# 사용 예제
@app.route('/users', methods=['GET'])
@require_permission('manage_users')
def list_users():
    # admin만 접근 가능
    users = db.execute('SELECT * FROM users').fetchall()
    return jsonify(users)

@app.route('/posts', methods=['POST'])
@require_permission('write')
def create_post():
    # editor 이상만 접근 가능
    # ...
```

### 객체 수준 인가 (IDOR 방지)

```python
# ❌ IDOR (Insecure Direct Object Reference) 취약점
@app.route('/api/orders/<int:order_id>')
def get_order(order_id):
    # 주문 번호만으로 조회 → 다른 사람 주문 조회 가능!
    order = db.execute('SELECT * FROM orders WHERE id=?', (order_id,)).fetchone()
    return jsonify(order)

# 공격:
# GET /api/orders/1 → 내 주문
# GET /api/orders/2 → 다른 사람 주문 😱
# GET /api/orders/3 → 다른 사람 주문 😱

# ✅ 해결: 사용자 확인
@app.route('/api/orders/<int:order_id>')
def get_order(order_id):
    user_id = session.get('user_id')

    # 주문 번호 + 사용자 ID로 조회
    order = db.execute(
        'SELECT * FROM orders WHERE id=? AND user_id=?',
        (order_id, user_id)
    ).fetchone()

    if not order:
        # 주문이 없거나, 다른 사람의 주문
        return jsonify({'error': 'Not found'}), 404

    return jsonify(order)
```

---

## 3단계: 입력 검증 (Input Validation)

### SQL Injection 방지

```python
# ❌ SQL Injection 취약점
@app.route('/search')
def search():
    keyword = request.args.get('keyword')

    # 사용자 입력을 직접 쿼리에 삽입 😱
    query = f"SELECT * FROM posts WHERE title LIKE '%{keyword}%'"
    results = db.execute(query).fetchall()

    return jsonify(results)

# 공격:
# GET /search?keyword=test' OR '1'='1
# → 쿼리: SELECT * FROM posts WHERE title LIKE '%test' OR '1'='1%'
# → 모든 게시글 노출!

# GET /search?keyword=test'; DROP TABLE posts; --
# → 게시글 테이블 삭제! 😱

# ✅ 해결: Parameterized Query (Prepared Statement)
@app.route('/search')
def search():
    keyword = request.args.get('keyword')

    # 플레이스홀더(?) 사용 → SQL Injection 불가능
    query = "SELECT * FROM posts WHERE title LIKE ?"
    results = db.execute(query, (f'%{keyword}%',)).fetchall()

    return jsonify(results)

# 공격 시도:
# GET /search?keyword=test' OR '1'='1
# → 쿼리: SELECT * FROM posts WHERE title LIKE ?
# → 파라미터: "test' OR '1'='1" (문자열로 처리됨)
# → 공격 실패 ✅
```

### XSS (Cross-Site Scripting) 방지

```python
# ❌ XSS 취약점
@app.route('/posts/<int:post_id>')
def view_post(post_id):
    post = db.execute('SELECT * FROM posts WHERE id=?', (post_id,)).fetchone()

    # 사용자가 입력한 HTML을 그대로 렌더링 😱
    return f'''
        <h1>{post['title']}</h1>
        <p>{post['content']}</p>
    '''

# 공격:
# 게시글 내용: <script>alert(document.cookie)</script>
# → 페이지 방문자의 쿠키 탈취 가능!

# ✅ 해결 1: HTML 이스케이핑 (Jinja2 자동 처리)
from flask import render_template_string

@app.route('/posts/<int:post_id>')
def view_post(post_id):
    post = db.execute('SELECT * FROM posts WHERE id=?', (post_id,)).fetchone()

    # Jinja2가 자동으로 HTML 이스케이프
    return render_template_string('''
        <h1>{{ post.title }}</h1>
        <p>{{ post.content }}</p>
    ''', post=post)

# 입력: <script>alert('XSS')</script>
# 출력: &lt;script&gt;alert('XSS')&lt;/script&gt;
# → 스크립트 실행 안 됨 ✅

# ✅ 해결 2: Content Security Policy (CSP)
@app.after_request
def set_csp(response):
    response.headers['Content-Security-Policy'] = \
        "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'"
    # 외부 스크립트 실행 차단
    return response
```

### Command Injection 방지

```python
# ❌ Command Injection 취약점
import os

@app.route('/ping')
def ping():
    host = request.args.get('host')

    # 사용자 입력을 쉘 명령어에 사용 😱
    result = os.popen(f'ping -c 4 {host}').read()
    return result

# 공격:
# GET /ping?host=google.com; cat /etc/passwd
# → 시스템 파일 노출!

# ✅ 해결 1: subprocess로 안전하게 실행
import subprocess

@app.route('/ping')
def ping():
    host = request.args.get('host')

    # 입력 검증
    if not re.match(r'^[a-zA-Z0-9.-]+$', host):
        return jsonify({'error': 'Invalid host'}), 400

    # 쉘 없이 직접 실행 (shell=False)
    result = subprocess.run(
        ['ping', '-c', '4', host],
        capture_output=True,
        text=True,
        timeout=10
    )

    return result.stdout

# ✅ 해결 2: 화이트리스트 사용
ALLOWED_HOSTS = ['google.com', 'cloudflare.com', 'localhost']

@app.route('/ping')
def ping():
    host = request.args.get('host')

    if host not in ALLOWED_HOSTS:
        return jsonify({'error': 'Host not allowed'}), 400

    # 안전한 호스트만 실행
    result = subprocess.run(['ping', '-c', '4', host], capture_output=True)
    return result.stdout
```

---

## 4단계: 데이터 보호 (Data Protection)

### 전송 중 암호화: HTTPS

```nginx
# ✅ Nginx에서 HTTPS 강제
server {
    listen 80;
    server_name example.com;

    # HTTP → HTTPS 리다이렉트
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name example.com;

    # Let's Encrypt 인증서
    ssl_certificate /etc/letsencrypt/live/example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;

    # 보안 설정
    ssl_protocols TLSv1.2 TLSv1.3;  # TLS 1.0/1.1 비활성화
    ssl_ciphers HIGH:!aNULL:!MD5;

    # HSTS (HTTP Strict Transport Security)
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    location / {
        proxy_pass http://localhost:8000;
    }
}
```

### 저장 데이터 암호화

```python
# ✅ 민감한 데이터 암호화 저장
from cryptography.fernet import Fernet

# 암호화 키 생성 (환경 변수에 저장)
# ENCRYPTION_KEY=b'your-32-byte-key-keep-it-very-safe='
encryption_key = os.environ['ENCRYPTION_KEY']
cipher = Fernet(encryption_key)

@app.route('/cards', methods=['POST'])
def add_credit_card():
    user_id = session['user_id']
    card_number = request.json['card_number']

    # 카드 번호 암호화
    encrypted_card = cipher.encrypt(card_number.encode())

    # 암호화된 데이터를 DB에 저장
    db.execute(
        'INSERT INTO credit_cards (user_id, encrypted_number) VALUES (?, ?)',
        (user_id, encrypted_card)
    )

    return jsonify({'message': 'Card added'})

@app.route('/cards')
def get_cards():
    user_id = session['user_id']

    cards = db.execute(
        'SELECT * FROM credit_cards WHERE user_id=?',
        (user_id,)
    ).fetchall()

    # 복호화
    decrypted_cards = []
    for card in cards:
        decrypted_number = cipher.decrypt(card['encrypted_number']).decode()
        # 마지막 4자리만 보여주기
        masked_number = '**** **** **** ' + decrypted_number[-4:]
        decrypted_cards.append({'number': masked_number})

    return jsonify(decrypted_cards)

# 해커가 DB를 탈취해도 암호화 키가 없으면 복호화 불가능!
```

### 민감 정보 로그 제외

```python
# ❌ 로그에 비밀번호 노출
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    logging.info(f"Login attempt: {data}")  # 😱 비밀번호 로그에 기록!

# ✅ 민감 정보 마스킹
import copy

SENSITIVE_FIELDS = ['password', 'credit_card', 'ssn']

def mask_sensitive_data(data):
    """민감한 필드를 마스킹"""
    safe_data = copy.deepcopy(data)
    for field in SENSITIVE_FIELDS:
        if field in safe_data:
            safe_data[field] = '***REDACTED***'
    return safe_data

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    logging.info(f"Login attempt: {mask_sensitive_data(data)}")
    # 로그: {"email": "user@example.com", "password": "***REDACTED***"}
```

---

## 5단계: API 보안

### Rate Limiting (속도 제한)

```python
# ✅ Flask-Limiter로 무차별 대입 공격 방지
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,  # IP 주소 기준
    default_limits=["200 per day", "50 per hour"]
)

@app.route('/login', methods=['POST'])
@limiter.limit("5 per minute")  # 1분에 5번만 시도 가능
def login():
    # 로그인 로직
    pass

# 공격자가 비밀번호 무차별 대입 시도:
# 1분에 5번만 시도 가능 → 100만 개 비밀번호 테스트 = 3,800년 소요 😎

@app.route('/api/expensive-operation', methods=['POST'])
@limiter.limit("10 per hour")  # 비용이 큰 작업은 더 제한
def expensive_operation():
    # 복잡한 계산
    pass
```

### CORS (Cross-Origin Resource Sharing) 설정

```python
# ✅ 허용된 도메인만 API 접근 가능
from flask_cors import CORS

app = Flask(__name__)

# ❌ 모든 도메인 허용 (위험)
# CORS(app, origins='*')

# ✅ 특정 도메인만 허용
CORS(app, origins=[
    'https://myapp.com',
    'https://www.myapp.com'
])

# 이제 다른 도메인에서 API 호출 시 브라우저가 차단
# 예: https://evil.com에서 fetch('https://api.myapp.com/users')
# → 브라우저: "CORS policy 위반" 에러
```

### API 키 인증

```python
# ✅ API 키로 외부 서비스 접근 제어
import secrets

def generate_api_key():
    """안전한 API 키 생성"""
    return secrets.token_urlsafe(32)

@app.route('/api-keys', methods=['POST'])
def create_api_key():
    user_id = session['user_id']

    # API 키 생성
    api_key = generate_api_key()

    db.execute(
        'INSERT INTO api_keys (user_id, key, created_at) VALUES (?, ?, ?)',
        (user_id, api_key, datetime.now())
    )

    return jsonify({'api_key': api_key})

def require_api_key(f):
    """API 키 검증 데코레이터"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')

        if not api_key:
            return jsonify({'error': 'API key required'}), 401

        # API 키 검증
        key_record = db.execute(
            'SELECT * FROM api_keys WHERE key=?',
            (api_key,)
        ).fetchone()

        if not key_record:
            return jsonify({'error': 'Invalid API key'}), 401

        # 요청 컨텍스트에 사용자 정보 저장
        g.user_id = key_record['user_id']

        return f(*args, **kwargs)
    return decorated_function

@app.route('/api/data')
@require_api_key
def get_data():
    user_id = g.user_id
    # 사용자별 데이터 반환
    data = db.execute('SELECT * FROM data WHERE user_id=?', (user_id,))
    return jsonify(data)

# 사용:
# curl -H "X-API-Key: your-api-key-here" https://api.example.com/data
```

---

## 6단계: 공급망 보안 (Supply Chain Security)

### 의존성 취약점 스캔

```bash
# ✅ Python 의존성 취약점 확인
$ pip install safety

$ safety check
# 결과:
# ╔═══════════════════════════════════════════════════════════════╗
# ║                                                               ║
# ║                 /$$$$$$            /$$                        ║
# ║                /$$__  $$          | $$                        ║
# ║               | $$  \__/  /$$$$$$ | $$$$$$                   ║
# ║               |  $$$$$$  |____  $$| $$_  $$                  ║
# ║                \____  $$  /$$$$$$$| $$ \ $$                  ║
# ║                /$$  \ $$ /$$__  $$| $$ | $$                  ║
# ║               |  $$$$$$/|  $$$$$$$| $$ | $$                  ║
# ║                \______/  \_______/|__/ |__/                  ║
# ║                                                               ║
# ╚═══════════════════════════════════════════════════════════════╝
#
# +==============================================================================+
# | REPORT                                                                       |
# +============================+===========+==========================+==========+
# | package                    | installed | affected                 | ID       |
# +============================+===========+==========================+==========+
# | jinja2                     | 2.11.0    | <2.11.3                  | 38834    |
# +============================+===========+==========================+==========+

# ✅ requirements.txt에 버전 고정
flask==2.3.0  # ❌ flask (버전 미지정)
jinja2==3.1.2  # ✅ 안전한 버전
requests>=2.28.0,<3.0.0  # ✅ 범위 지정
```

### 의존성 최소화

```python
# ❌ 불필요한 라이브러리 설치
# requirements.txt
django  # 사용 안 하는데 설치
tensorflow  # 사용 안 하는데 설치
pillow
requests
...
# → 공격 표면 증가 (더 많은 취약점 가능성)

# ✅ 필요한 것만 설치
# requirements.txt
pillow==9.5.0
requests==2.28.2

# 미사용 패키지 확인
$ pip install pip-autoremove
$ pip-autoremove -l  # 사용하지 않는 패키지 나열
```

### Docker 이미지 보안

```dockerfile
# ❌ 취약한 Dockerfile
FROM python:latest  # 'latest' 태그는 예측 불가능

USER root  # root 사용자로 실행 (위험!)

COPY . /app
WORKDIR /app

RUN pip install -r requirements.txt

CMD ["python", "app.py"]

# ✅ 안전한 Dockerfile
FROM python:3.11-slim-bullseye  # 구체적 버전 명시

# 보안 업데이트 적용
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 비root 사용자 생성
RUN useradd -m -u 1000 appuser

WORKDIR /app

# 의존성만 먼저 복사 (캐시 활용)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY --chown=appuser:appuser . .

# 비root 사용자로 전환
USER appuser

# 헬스체크 추가
HEALTHCHECK --interval=30s --timeout=3s \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "app:app"]
```

### 이미지 스캔

```bash
# ✅ Trivy로 Docker 이미지 취약점 스캔
$ docker run aquasec/trivy image myapp:latest

# 결과:
# myapp:latest (debian 11.6)
# ==========================
# Total: 23 (CRITICAL: 5, HIGH: 10, MEDIUM: 8, LOW: 0)
#
# ┌─────────────────┬────────────────┬──────────┬─────────────────┐
# │    Library      │ Vulnerability  │ Severity │ Installed Ver   │
# ├─────────────────┼────────────────┼──────────┼─────────────────┤
# │ openssl         │ CVE-2023-1234  │ CRITICAL │ 1.1.1n          │
# │ libc6           │ CVE-2023-5678  │ HIGH     │ 2.31-13         │
# └─────────────────┴────────────────┴──────────┴─────────────────┘
```

---

## 7단계: 모니터링 & 사고 대응

### 보안 이벤트 로깅

```python
# ✅ 의심스러운 활동 로깅
import logging

security_logger = logging.getLogger('security')
security_logger.setLevel(logging.WARNING)

@app.route('/login', methods=['POST'])
def login():
    email = request.json['email']
    password = request.json['password']
    ip = request.remote_addr

    user = authenticate(email, password)

    if not user:
        # 실패한 로그인 시도 기록
        security_logger.warning(
            f"Failed login attempt - Email: {email}, IP: {ip}"
        )
        return jsonify({'error': 'Invalid credentials'}), 401

    # 성공한 로그인 기록
    security_logger.info(
        f"Successful login - Email: {email}, IP: {ip}"
    )

    return jsonify({'token': create_token(user)})

# 분석: 같은 IP에서 100번 실패 → 무차별 대입 공격 탐지
```

### 이상 탐지 (Anomaly Detection)

```python
# ✅ 비정상 활동 탐지
from datetime import datetime, timedelta
import redis

redis_client = redis.Redis()

def check_anomaly(user_id, action):
    """사용자 행동 이상 탐지"""
    key = f"user:{user_id}:{action}"
    window = 60  # 1분 윈도우

    # 1분간 행동 횟수 증가
    count = redis_client.incr(key)
    redis_client.expire(key, window)

    # 임계값 확인
    thresholds = {
        'login': 5,          # 1분에 5번 이상 로그인 시도
        'post_create': 10,   # 1분에 10개 이상 게시글 작성
        'api_call': 100      # 1분에 100번 이상 API 호출
    }

    if count > thresholds.get(action, 100):
        # 알림 발송
        security_logger.critical(
            f"Anomaly detected - User: {user_id}, Action: {action}, Count: {count}"
        )

        # 사용자 일시 차단
        redis_client.setex(f"blocked:{user_id}", 300, "1")  # 5분 차단

        return True

    return False

@app.route('/posts', methods=['POST'])
def create_post():
    user_id = session['user_id']

    # 이상 행동 확인
    if check_anomaly(user_id, 'post_create'):
        return jsonify({'error': 'Too many requests'}), 429

    # 정상 처리
    create_post_in_db()
    return jsonify({'message': 'Created'})
```

### 침해 사고 대응 플랜

```python
# ✅ 비상 대응 엔드포인트 (관리자 전용)
@app.route('/admin/emergency/revoke-all-sessions', methods=['POST'])
@require_role('admin')
def revoke_all_sessions():
    """모든 사용자 세션 무효화 (토큰 유출 시)"""
    # JWT secret 변경 → 모든 기존 토큰 무효화
    new_secret = secrets.token_urlsafe(32)
    db.execute('UPDATE config SET jwt_secret=?', (new_secret,))

    security_logger.critical("All sessions revoked by admin")

    return jsonify({'message': 'All sessions revoked'})

@app.route('/admin/emergency/block-ip', methods=['POST'])
@require_role('admin')
def block_ip():
    """악성 IP 차단"""
    ip = request.json['ip']

    # Redis에 차단 IP 저장
    redis_client.sadd('blocked_ips', ip)

    security_logger.warning(f"IP blocked: {ip}")

    return jsonify({'message': f'Blocked {ip}'})

# 미들웨어: 차단된 IP 확인
@app.before_request
def check_blocked_ip():
    ip = request.remote_addr
    if redis_client.sismember('blocked_ips', ip):
        abort(403)
```

---

## 보안 체크리스트

### 인증/인가
- [ ] 비밀번호를 bcrypt로 해싱하여 저장하는가?
- [ ] JWT 토큰에 만료 시간이 설정되어 있는가?
- [ ] 중요한 작업에 2FA를 사용하는가?
- [ ] 모든 API 엔드포인트에 인증이 필요한가?
- [ ] 객체 수준 권한 확인(IDOR 방지)을 하는가?

### 입력 검증
- [ ] SQL Injection 방지를 위해 Parameterized Query를 사용하는가?
- [ ] XSS 방지를 위해 HTML 이스케이핑을 하는가?
- [ ] Command Injection 방지를 위해 입력을 검증하는가?
- [ ] 파일 업로드 시 확장자와 내용을 검증하는가?

### 데이터 보호
- [ ] HTTPS를 강제하는가? (HTTP → HTTPS 리다이렉트)
- [ ] 민감한 데이터(카드 번호 등)를 암호화하여 저장하는가?
- [ ] 로그에 비밀번호/토큰이 기록되지 않는가?
- [ ] 데이터베이스 백업이 암호화되는가?

### API 보안
- [ ] Rate Limiting이 설정되어 있는가?
- [ ] CORS가 적절히 설정되어 있는가? (모든 origin 허용 금지)
- [ ] API 키가 안전하게 생성/저장되는가?

### 공급망 보안
- [ ] 의존성 취약점을 정기적으로 스캔하는가?
- [ ] requirements.txt에 버전이 고정되어 있는가?
- [ ] Docker 이미지를 스캔하는가?
- [ ] 비root 사용자로 컨테이너를 실행하는가?

### 모니터링
- [ ] 실패한 로그인 시도를 로깅하는가?
- [ ] 비정상 활동을 탐지하는가?
- [ ] 보안 이벤트 알림이 설정되어 있는가?
- [ ] 침해 사고 대응 플랜이 있는가?

---

## 다음 단계

1. **OWASP Top 10**: 웹 애플리케이션 10대 취약점 학습
2. **Penetration Testing**: Burp Suite, OWASP ZAP으로 보안 테스트
3. **Secure SDLC**: 개발 라이프사이클에 보안 통합
4. **Bug Bounty**: HackerOne, Bugcrowd에서 실전 경험

---

## 참고 자료

- **OWASP Top 10**: https://owasp.org/www-project-top-ten/
- **웹 보안 학습**: https://portswigger.net/web-security (무료 실습 랩)
- **책**: "Web Application Security" by Andrew Hoffman
- **도구**: https://github.com/Netflix/security_monkey (보안 모니터링)
