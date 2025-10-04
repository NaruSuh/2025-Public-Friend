# 🚀 Streamlit 배포 가이드

## 목차
1. [로컬 실행](#로컬-실행)
2. [Streamlit Cloud 배포](#streamlit-cloud-배포)
3. [Hugging Face Spaces 배포](#hugging-face-spaces-배포)
4. [기타 배포 옵션](#기타-배포-옵션)

---

## 로컬 실행

### 1. 의존성 설치

```bash
cd "/home/naru/work/2025_Vibe/2025 Druid Donum/2025 Druid Full-auto Firing"
pip install -r requirements.txt
```

### 2. 앱 실행

```bash
streamlit run app.py
```

자동으로 브라우저가 열리며 `http://localhost:8501`에서 앱에 접속할 수 있습니다.

### 3. 포트 변경 (선택사항)

```bash
streamlit run app.py --server.port 8080
```

---

## Streamlit Cloud 배포

### 📝 준비사항
- GitHub 계정
- Streamlit Cloud 계정 (https://streamlit.io/cloud)

### 단계별 가이드

#### 1. GitHub에 코드 업로드

```bash
# Git 저장소 초기화 (처음인 경우)
cd "/home/naru/work/2025_Vibe/2025 Druid Donum/2025 Druid Full-auto Firing"
git init

# 파일 추가
git add app.py main.py requirements.txt README.md prompt.md plan.md
git commit -m "Add forest bid crawler streamlit app"

# GitHub 저장소에 푸시
git remote add origin https://github.com/YOUR_USERNAME/forest-bid-crawler.git
git branch -M main
git push -u origin main
```

#### 2. Streamlit Cloud에 배포

1. https://streamlit.io/cloud 접속 및 로그인
2. **"New app"** 클릭
3. 설정:
   - **Repository**: `YOUR_USERNAME/forest-bid-crawler`
   - **Branch**: `main`
   - **Main file path**: `app.py`
4. **"Deploy"** 클릭

#### 3. 배포 완료

- 배포 URL: `https://YOUR_APP_NAME.streamlit.app`
- 자동으로 HTTPS 적용됨
- 코드 업데이트 시 자동 재배포

---

## Hugging Face Spaces 배포

### 📝 준비사항
- Hugging Face 계정 (https://huggingface.co)

### 단계별 가이드

#### 1. Space 생성

1. https://huggingface.co/spaces 접속
2. **"Create new Space"** 클릭
3. 설정:
   - **Space name**: `forest-bid-crawler`
   - **License**: MIT
   - **Space SDK**: **Streamlit**
   - **Visibility**: Public 또는 Private

#### 2. 파일 업로드

Space 생성 후 다음 파일들을 업로드:

- `app.py`
- `main.py`
- `requirements.txt`

#### 3. 배포 완료

- 배포 URL: `https://huggingface.co/spaces/YOUR_USERNAME/forest-bid-crawler`
- GPU 지원 가능 (필요시)

---

## 기타 배포 옵션

### 1. Heroku

```bash
# Procfile 생성
echo "web: streamlit run app.py --server.port $PORT" > Procfile

# runtime.txt 생성
echo "python-3.10.12" > runtime.txt

# Heroku 배포
heroku create forest-bid-crawler
git push heroku main
```

### 2. Docker 컨테이너

**Dockerfile 생성:**

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

**빌드 및 실행:**

```bash
docker build -t forest-bid-crawler .
docker run -p 8501:8501 forest-bid-crawler
```

### 3. AWS EC2

```bash
# EC2 인스턴스에서 실행
sudo apt update
sudo apt install python3-pip
pip3 install -r requirements.txt
streamlit run app.py --server.port 80
```

### 4. Google Cloud Run

```bash
# Cloud Run 배포
gcloud run deploy forest-bid-crawler \
  --source . \
  --platform managed \
  --region asia-northeast3 \
  --allow-unauthenticated
```

---

## 환경 변수 설정 (선택사항)

배포 환경에서 환경 변수로 설정 가능:

```bash
# .streamlit/secrets.toml 생성
CRAWLER_DAYS = 30
CRAWLER_DELAY = 1.0
CRAWLER_PAGE_DELAY = 2.0
```

**app.py에서 사용:**

```python
import streamlit as st

days = st.secrets.get("CRAWLER_DAYS", 30)
```

---

## 문제 해결

### Streamlit Cloud에서 메모리 부족

**해결책:** `.streamlit/config.toml` 생성

```toml
[server]
maxUploadSize = 200

[browser]
gatherUsageStats = false
```

### 크롤링 타임아웃

**해결책:** 수집 기간 제한 또는 배치 처리

```python
# app.py에서 최대 페이지 제한
if page_index > 50:  # 최대 50페이지
    break
```

### HTTPS 인증서 오류

**해결책:** `requests`에서 SSL 검증 비활성화 (개발 환경만)

```python
response = self.session.get(url, verify=False)
```

---

## 권장 배포 방법

### 🏆 **1순위: Streamlit Cloud**
- **장점**: 무료, 간단, GitHub 연동
- **단점**: 리소스 제한

### 🥈 **2순위: Hugging Face Spaces**
- **장점**: 무료, GPU 지원 가능
- **단점**: UI 커스터마이징 제한

### 🥉 **3순위: Docker + AWS/GCP**
- **장점**: 완전한 제어, 확장 가능
- **단점**: 비용 발생, 관리 필요

---

## 배포 체크리스트

- [ ] `requirements.txt` 모든 의존성 포함
- [ ] `app.py` 로컬에서 정상 작동 확인
- [ ] `.gitignore`에 불필요한 파일 제외
- [ ] README.md 업데이트
- [ ] 환경 변수 설정 (필요시)
- [ ] 보안 설정 (API 키 등)
- [ ] 배포 후 테스트

---

## 참고 링크

- [Streamlit Cloud 공식 문서](https://docs.streamlit.io/streamlit-community-cloud)
- [Hugging Face Spaces 가이드](https://huggingface.co/docs/hub/spaces)
- [Docker 공식 문서](https://docs.docker.com/)
