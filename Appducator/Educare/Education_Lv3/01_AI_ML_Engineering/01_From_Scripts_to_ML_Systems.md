# 01.01 - From Scripts to ML Systems (스크립트에서 ML 시스템으로)

## 🎯 이 문서의 목적

**"AI/ML을 처음 접하는 엔지니어"**가 **"프로덕션 ML 시스템을 설계·운영하는 전문가"**로 성장하기 위한 첫 단계입니다.

**전제 조건:** Python 기초, API 개발 경험 (Lv1~Lv2 완료)

---

## 📚 목차

1. [ML이 뭐고 왜 필요한가?](#ml이-뭐고-왜-필요한가)
2. [스크립트 vs ML 시스템](#스크립트-vs-ml-시스템)
3. [ML 워크플로우 전체 그림](#ml-워크플로우-전체-그림)
4. [첫 ML 프로젝트: 실습](#첫-ml-프로젝트-실습)
5. [프로덕션으로 가는 길](#프로덕션으로-가는-길)

---

## ML이 뭐고 왜 필요한가?

### 🤔 전통적인 프로그래밍의 한계

**문제: 룰 기반 로직의 복잡도 폭발**

```python
# 예: 스팸 필터 (전통적 방식)
def is_spam(email):
    spam_words = ['free', 'winner', '!!!', 'click here']

    if any(word in email.lower() for word in spam_words):
        return True

    if email.count('!') > 3:
        return True

    if 'viagra' in email or 'lottery' in email:
        return True

    # 100개, 1000개 규칙 추가...
    # → 유지보수 불가능!
```

**한계:**
- 새로운 스팸 패턴마다 코드 수정 필요
- 규칙이 수백 개가 되면 관리 불가
- 미묘한 패턴 감지 어려움 (예: "F.R.E.E" 같은 변형)

---

### ✨ Machine Learning의 등장

**핵심 아이디어: "규칙을 직접 작성하지 말고, 데이터에서 학습하게 하자"**

```python
# ML 방식
from sklearn.naive_bayes import MultinomialNB
from sklearn.feature_extraction.text import CountVectorizer

# 1. 데이터 준비
emails = [
    ("Win free iPhone now!!!", "spam"),
    ("Meeting at 3pm today", "ham"),
    ("Congratulations! You won lottery", "spam"),
    ("Can you review my PR?", "ham"),
    # ... 수천 개의 예시
]

X_train = [email for email, _ in emails]
y_train = [label for _, label in emails]

# 2. 모델 학습 (자동으로 패턴 학습!)
vectorizer = CountVectorizer()
X_vec = vectorizer.fit_transform(X_train)

model = MultinomialNB()
model.fit(X_vec, y_train)

# 3. 새로운 이메일 분류 (규칙 없이!)
new_email = "F.R.E.E iPhone"
prediction = model.predict(vectorizer.transform([new_email]))
# → "spam" (자동으로 변형 패턴도 인식!)
```

**장점:**
- ✅ 데이터만 추가하면 자동으로 개선
- ✅ 복잡한 패턴도 스스로 발견
- ✅ 유지보수 간단 (모델 재학습만 하면 됨)

---

### 🎯 언제 ML을 쓸까?

**ML이 적합한 경우:**
- ✅ **패턴이 복잡**해서 규칙으로 표현 어려움 (이미지 인식, 음성 인식)
- ✅ **지속적으로 변화**하는 환경 (사기 탐지, 추천 시스템)
- ✅ **대량의 데이터**가 있고 라벨링 가능 (로그 분석, 수요 예측)

**ML이 부적합한 경우:**
- ❌ 규칙이 명확하고 단순함 (세금 계산, 주소 검증)
- ❌ 데이터가 극소량 (< 100개)
- ❌ 설명 가능성이 필수 (의료, 법률 - 단, Explainable AI 발전 중)

---

## 스크립트 vs ML 시스템

### 📜 스크립트 단계 (Jupyter Notebook)

**특징: 탐색과 실험**

```python
# notebook.ipynb
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

# 데이터 로드
df = pd.read_csv('data.csv')

# 전처리
df = df.dropna()
X = df[['feature1', 'feature2']]
y = df['label']

# 학습
X_train, X_test, y_train, y_test = train_test_split(X, y)
model = RandomForestClassifier()
model.fit(X_train, y_train)

# 평가
print(f"Accuracy: {model.score(X_test, y_test)}")
```

**장점:**
- 빠른 실험
- 시각화 쉬움
- 대화형 개발

**문제:**
- 재현 불가능 (셀 실행 순서 의존)
- 버전 관리 어려움
- 프로덕션 배포 불가

---

### 🏗️ ML 시스템 (Production)

**특징: 자동화와 안정성**

```python
# ml_pipeline.py
from dataclasses import dataclass
from pathlib import Path
import joblib

@dataclass
class Config:
    data_path: Path
    model_path: Path
    features: list[str]

class DataPipeline:
    def load(self, path: Path) -> pd.DataFrame:
        return pd.read_csv(path)

    def preprocess(self, df: pd.DataFrame) -> pd.DataFrame:
        # 재현 가능한 전처리
        df = df.copy()
        df = df.dropna()
        return df

class ModelTrainer:
    def __init__(self, config: Config):
        self.config = config

    def train(self, X, y):
        model = RandomForestClassifier(
            n_estimators=100,
            random_state=42  # 재현성!
        )
        model.fit(X, y)
        return model

    def save(self, model, path: Path):
        joblib.dump(model, path)

# CLI 실행
if __name__ == "__main__":
    config = Config(...)
    pipeline = DataPipeline()
    trainer = ModelTrainer(config)

    df = pipeline.load(config.data_path)
    df = pipeline.preprocess(df)

    model = trainer.train(df[config.features], df['label'])
    trainer.save(model, config.model_path)
```

**장점:**
- ✅ 재현 가능 (같은 입력 → 같은 결과)
- ✅ 버전 관리 가능 (Git)
- ✅ 자동화 가능 (CI/CD)
- ✅ 테스트 가능

---

## ML 워크플로우 전체 그림

### 🔄 MLOps 파이프라인

```
1. 데이터 수집
   ↓
2. 탐색적 데이터 분석 (EDA)
   ↓
3. 데이터 전처리 & Feature Engineering
   ↓
4. 모델 학습 & 실험
   ↓
5. 모델 평가 & 검증
   ↓
6. 모델 배포
   ↓
7. 모니터링 & 피드백
   ↓
(1번으로 다시 - 지속적 개선)
```

---

### 🧩 각 단계 상세

#### 1단계: 데이터 수집

```python
# data_collector.py
import requests
from datetime import datetime
from pathlib import Path

class DataCollector:
    """크롤링, API, DB에서 데이터 수집"""

    def collect_from_api(self, url: str) -> list[dict]:
        response = requests.get(url)
        return response.json()

    def save_raw_data(self, data: list[dict], version: str):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = Path(f"data/raw/{version}_{timestamp}.json")
        path.parent.mkdir(parents=True, exist_ok=True)

        import json
        with open(path, 'w') as f:
            json.dump(data, f)

        return path

# 사용
collector = DataCollector()
data = collector.collect_from_api("https://api.example.com/data")
path = collector.save_raw_data(data, version="v1")
```

**핵심:**
- 원본 데이터 보존 (버전별로 저장)
- 재수집 가능하도록 로직 분리

---

#### 2단계: EDA (탐색적 데이터 분석)

```python
# eda.py
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

class EDA:
    def __init__(self, df: pd.DataFrame):
        self.df = df

    def basic_stats(self):
        """기본 통계"""
        print(self.df.describe())
        print(self.df.info())

    def check_missing(self):
        """결측치 확인"""
        missing = self.df.isnull().sum()
        print(missing[missing > 0])

    def plot_distributions(self):
        """분포 시각화"""
        self.df.hist(figsize=(12, 8))
        plt.tight_layout()
        plt.savefig('dist.png')

    def check_correlations(self):
        """상관관계 분석"""
        corr = self.df.corr()
        sns.heatmap(corr, annot=True)
        plt.savefig('corr.png')

# 사용
df = pd.read_json(path)
eda = EDA(df)
eda.basic_stats()
eda.check_missing()
```

**목적:**
- 데이터 이해
- 문제점 발견 (결측치, 이상치, 불균형)
- Feature 선택 힌트 얻기

---

#### 3단계: Feature Engineering

```python
# features.py
from sklearn.preprocessing import StandardScaler, LabelEncoder

class FeatureEngineer:
    """피처 생성 및 변환"""

    def create_time_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """시간 데이터에서 피처 추출"""
        df = df.copy()
        df['hour'] = pd.to_datetime(df['timestamp']).dt.hour
        df['day_of_week'] = pd.to_datetime(df['timestamp']).dt.dayofweek
        df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
        return df

    def encode_categories(self, df: pd.DataFrame, cols: list[str]):
        """카테고리 인코딩"""
        for col in cols:
            le = LabelEncoder()
            df[col] = le.fit_transform(df[col])
        return df

    def scale_features(self, X: pd.DataFrame) -> pd.DataFrame:
        """스케일링 (0-1 정규화)"""
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        return pd.DataFrame(X_scaled, columns=X.columns)
```

**핵심 개념:**
- **피처(Feature)**: 모델의 입력 변수
- **좋은 피처 = 성능 향상의 80%**
- 도메인 지식이 중요!

---

#### 4단계: 모델 학습

```python
# train.py
from sklearn.model_selection import cross_val_score
from sklearn.ensemble import RandomForestClassifier
import mlflow  # 실험 추적 도구

class Trainer:
    def train_and_evaluate(self, X, y):
        model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )

        # Cross Validation (과적합 방지)
        scores = cross_val_score(model, X, y, cv=5)
        print(f"CV Scores: {scores}")
        print(f"Mean: {scores.mean():.3f} (+/- {scores.std():.3f})")

        # 전체 데이터로 최종 학습
        model.fit(X, y)

        # MLflow로 실험 기록
        with mlflow.start_run():
            mlflow.log_param("n_estimators", 100)
            mlflow.log_param("max_depth", 10)
            mlflow.log_metric("cv_score", scores.mean())
            mlflow.sklearn.log_model(model, "model")

        return model
```

**핵심:**
- **Cross Validation**: 과적합 방지, 일반화 성능 측정
- **실험 추적**: 어떤 설정이 잘 작동했는지 기록

---

#### 5단계: 모델 평가

```python
# evaluate.py
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report
)

class Evaluator:
    def evaluate_classification(self, y_true, y_pred):
        """분류 모델 평가"""

        print("=== Classification Report ===")
        print(classification_report(y_true, y_pred))

        print("\n=== Confusion Matrix ===")
        print(confusion_matrix(y_true, y_pred))

        metrics = {
            'accuracy': accuracy_score(y_true, y_pred),
            'precision': precision_score(y_true, y_pred, average='weighted'),
            'recall': recall_score(y_true, y_pred, average='weighted'),
            'f1': f1_score(y_true, y_pred, average='weighted')
        }

        return metrics

# 사용
evaluator = Evaluator()
metrics = evaluator.evaluate_classification(y_test, y_pred)
print(f"F1 Score: {metrics['f1']:.3f}")
```

**중요 메트릭:**
- **Accuracy**: 전체 정확도 (불균형 데이터에선 부적합)
- **Precision**: 양성 예측의 정확도 (FP 중요할 때)
- **Recall**: 실제 양성의 탐지율 (FN 중요할 때)
- **F1 Score**: Precision과 Recall의 조화평균

---

## 첫 ML 프로젝트: 실습

### 🎯 프로젝트: 크롤러 결과 자동 분류기

**문제:** 크롤링한 입찰 공고를 카테고리별로 자동 분류

**데이터:**
- 입력: 공고 제목, 내용
- 출력: 카테고리 (건설, IT, 용역, 물품 등)

---

### 📝 Step 1: 데이터 준비

```python
# prepare_data.py
import pandas as pd

def load_crawled_data():
    """크롤링 결과를 학습 데이터로 변환"""

    # 크롤링 결과 (Excel)
    df = pd.read_excel("crawled_bids.xlsx")

    # 필요한 컬럼만 선택
    df = df[['title', 'content', 'category']]

    # 결측치 제거
    df = df.dropna()

    # 텍스트 결합 (제목 + 내용)
    df['text'] = df['title'] + " " + df['content']

    # 저장
    df.to_csv("ml_data.csv", index=False)

    print(f"총 {len(df)}개 데이터 준비 완료")
    print(f"카테고리 분포:\n{df['category'].value_counts()}")

if __name__ == "__main__":
    load_crawled_data()
```

---

### 📝 Step 2: 모델 학습

```python
# train_classifier.py
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
import joblib

def train():
    # 데이터 로드
    df = pd.read_csv("ml_data.csv")

    X = df['text']
    y = df['category']

    # 학습/테스트 분리
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # 파이프라인 생성
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(max_features=5000)),
        ('clf', MultinomialNB())
    ])

    # 학습
    pipeline.fit(X_train, y_train)

    # 평가
    score = pipeline.score(X_test, y_test)
    print(f"Test Accuracy: {score:.3f}")

    # 저장
    joblib.dump(pipeline, "bid_classifier.pkl")
    print("모델 저장 완료: bid_classifier.pkl")

if __name__ == "__main__":
    train()
```

---

### 📝 Step 3: 실시간 예측 API

```python
# api.py
from fastapi import FastAPI
import joblib

app = FastAPI()

# 모델 로드 (서버 시작 시 1번만)
model = joblib.load("bid_classifier.pkl")

@app.post("/predict")
async def predict(text: str):
    """입찰 공고 카테고리 예측"""

    prediction = model.predict([text])[0]
    probabilities = model.predict_proba([text])[0]

    # 확률 상위 3개
    top3_idx = probabilities.argsort()[-3:][::-1]
    top3 = [
        {
            "category": model.classes_[idx],
            "probability": float(probabilities[idx])
        }
        for idx in top3_idx
    ]

    return {
        "prediction": prediction,
        "confidence": float(probabilities.max()),
        "top3": top3
    }

# 실행: uvicorn api:app --reload
```

**사용:**
```bash
curl -X POST "http://localhost:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{"text": "도로 포장 공사 입찰"}'

# 결과:
{
  "prediction": "건설",
  "confidence": 0.89,
  "top3": [
    {"category": "건설", "probability": 0.89},
    {"category": "용역", "probability": 0.08},
    {"category": "물품", "probability": 0.03}
  ]
}
```

---

## 프로덕션으로 가는 길

### 🚀 스크립트 → 시스템 전환 체크리스트

#### 1. 재현성 확보
```python
# ❌ 나쁜 예
model = RandomForestClassifier()  # random_state 없음!

# ✅ 좋은 예
model = RandomForestClassifier(random_state=42)

# 버전 고정
# requirements.txt
scikit-learn==1.5.0  # 명확한 버전
pandas==2.2.2
```

#### 2. 설정 외부화
```python
# config.yaml
model:
  type: RandomForestClassifier
  params:
    n_estimators: 100
    max_depth: 10
    random_state: 42

data:
  train_path: data/train.csv
  test_path: data/test.csv

# 코드에서 사용
import yaml

with open('config.yaml') as f:
    config = yaml.safe_load(f)

model_params = config['model']['params']
model = RandomForestClassifier(**model_params)
```

#### 3. 로깅 추가
```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def train():
    logger.info("학습 시작")
    logger.info(f"데이터 크기: {len(df)}")

    model.fit(X_train, y_train)

    score = model.score(X_test, y_test)
    logger.info(f"Test Score: {score:.3f}")

    logger.info("모델 저장 완료")
```

#### 4. 에러 핸들링
```python
class ModelLoadError(Exception):
    pass

def load_model(path: Path):
    try:
        model = joblib.load(path)
        logger.info(f"모델 로드 성공: {path}")
        return model
    except FileNotFoundError:
        raise ModelLoadError(f"모델 파일 없음: {path}")
    except Exception as e:
        raise ModelLoadError(f"모델 로드 실패: {e}")
```

#### 5. 테스트 작성
```python
# test_model.py
import pytest

def test_model_prediction():
    model = joblib.load("bid_classifier.pkl")

    # 알려진 입력 → 예상 출력
    text = "도로 포장 공사"
    prediction = model.predict([text])[0]

    assert prediction == "건설"

def test_model_confidence():
    model = joblib.load("bid_classifier.pkl")

    proba = model.predict_proba(["명확한 IT 프로젝트 입찰"])[0]

    # 확신도가 0.8 이상이어야 함
    assert proba.max() > 0.8
```

---

## 🎓 다음 단계

### Lv3에서 배울 내용:

1. **MLOps 파이프라인 자동화**
   - Airflow로 학습 자동화
   - MLflow로 실험 추적
   - DVC로 데이터 버전 관리

2. **모델 서빙 & 스케일링**
   - TensorFlow Serving, TorchServe
   - 배치 예측 vs 실시간 예측
   - GPU 활용

3. **모니터링 & A/B 테스트**
   - 모델 성능 drift 감지
   - 새 모델 vs 기존 모델 비교
   - 자동 롤백

---

## 📚 추천 학습 순서

1. **기초 다지기** (2주)
   - scikit-learn 공식 튜토리얼
   - Kaggle "Titanic" 대회 완주

2. **실전 프로젝트** (4주)
   - 자신의 크롤러 데이터로 분류기 만들기
   - API로 서빙하기
   - Docker 컨테이너화

3. **MLOps 입문** (4주)
   - MLflow 실험 추적
   - GitHub Actions로 자동 학습
   - Monitoring 대시보드 구축

---

## ✅ 체크리스트

학습 완료 후 다음을 할 수 있어야 합니다:

- [ ] Jupyter Notebook에서 간단한 ML 모델 학습
- [ ] 학습 코드를 Python 스크립트로 변환
- [ ] 모델을 pickle/joblib로 저장·로드
- [ ] FastAPI로 예측 API 만들기
- [ ] 기본 모델 평가 메트릭 이해 (Accuracy, F1)
- [ ] 재현 가능한 파이프라인 구축

---

**다음 문서:** `02_MLOps_Pipeline_Automation.md`
