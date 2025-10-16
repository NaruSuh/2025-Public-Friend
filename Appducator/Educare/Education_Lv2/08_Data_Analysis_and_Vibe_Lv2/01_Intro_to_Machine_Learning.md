# 08 - Data Analysis and Vibe - Lv.2: From Analysis to Machine Learning
# 08 - 데이터 분석과 Vibe - Lv.2: 분석에서 머신러닝으로

You've mastered exploratory data analysis (EDA) with `pandas`. Level 2 is about using your data to make predictions and automate decisions. This is the realm of Machine Learning (ML).
`pandas`로 탐색적 데이터 분석(EDA)을 익혔다면, 레벨 2에서는 데이터를 활용해 예측하고 의사결정을 자동화하는 머신러닝(ML) 세계에 들어갑니다.

## Before You Begin
## 시작하기 전에
-   Confirm you can reproduce the Level 1 EDA notebook, including cleaning and visualizing bid data.
-   레벨 1의 EDA 노트북을 다시 실행해 입찰 데이터 정제와 시각화가 문제없이 되는지 확인하세요.
-   Install `scikit-learn`, `joblib`, and plotting libraries inside a fresh virtual environment; ML tooling can conflict with earlier dependencies.
-   새로운 가상 환경에 `scikit-learn`, `joblib`, 시각화 라이브러리를 설치하세요. ML 도구는 기존 의존성과 충돌할 수 있습니다.
-   Set aside a notebook where you document each experiment (features used, metrics achieved). This habit pays off when models multiply.
-   실험마다 사용한 피처와 성능 지표를 기록할 노트북을 준비하세요. 모델이 늘어날수록 이 습관이 큰 도움이 됩니다.

## Level 2 Upgrade Goals
## 레벨 2 업그레이드 목표
1.  **Frame ML problems responsibly** by defining business value, success metrics, and data constraints first.
1.  **책임감 있게 ML 문제 정의**: 비즈니스 가치, 성공 지표, 데이터 제약을 먼저 설정합니다.
2.  **Automate reproducible pipelines** for feature engineering, training, and evaluation.
2.  **재현 가능한 파이프라인 자동화**: 피처 엔지니어링, 학습, 평가 단계를 자동화합니다.
3.  **Operationalize models** with deployment, monitoring, and retraining loops.
3.  **모델 운영화**: 배포, 모니터링, 재학습 루프를 통해 모델을 운영 환경에 녹입니다.

## Core Concepts
## 핵심 개념

1.  **The Machine Learning Workflow**: A structured process for building, deploying, and maintaining ML models.
1.  **머신러닝 워크플로**: 모델을 구축하고 배포하며 유지보수하는 구조화된 절차입니다.
2.  **Feature Engineering**: The art and science of creating predictive signals (features) from raw data. This is often the most important factor in a model's success.
2.  **피처 엔지니어링**: 원본 데이터에서 예측 신호(피처)를 만들어 내는 기술로, 모델 성공에 결정적입니다.
3.  **Model Training and Evaluation**: Choosing the right algorithm, training it on your data, and rigorously evaluating its performance.
3.  **모델 학습과 평가**: 적절한 알고리즘을 선택하고 데이터를 학습시킨 뒤 성능을 엄격히 평가합니다.
4.  **MLOps (Machine Learning Operations)**: The practice of deploying, monitoring, and retraining models in production. A model is not a one-time artifact; it's a living system that needs to be maintained.
4.  **MLOps**: 프로덕션에서 모델을 배포·모니터링·재학습하는 실무로, 모델은 한 번 만들고 끝나는 산출물이 아니라 지속적으로 관리해야 하는 살아 있는 시스템입니다.

---

## 1. The Machine Learning Workflow
## 1. 머신러닝 워크플로

A typical ML project follows these steps:
일반적인 ML 프로젝트는 다음 단계를 따릅니다.
1.  **Problem Framing**: What are you trying to predict, and how will that prediction be used to drive value? (e.g., "We will predict which bids are 'high-value' to help users prioritize their efforts.")
1.  **문제 정의**: 무엇을 예측하고 그 예측으로 어떤 가치를 창출할지 결정합니다(예: “어떤 입찰이 고가치인지 예측해 사용자가 우선순위를 정하도록 돕는다”).
2.  **Data Collection and Cleaning**: Same as in EDA, but with a focus on creating a reliable dataset for training.
2.  **데이터 수집 및 정제**: EDA처럼 수행하되, 학습에 적합한 신뢰성 있는 데이터셋을 만드는 데 집중합니다.
3.  **Feature Engineering**: Create features for the model.
3.  **피처 엔지니어링**: 모델에 사용할 피처를 만듭니다.
4.  **Model Selection**: Choose a class of models to try (e.g., logistic regression, gradient boosting).
4.  **모델 선택**: 로지스틱 회귀, 그래디언트 부스팅 등 시도할 모델 군을 고릅니다.
5.  **Model Training**: Fit the model to your training data.
5.  **모델 학습**: 훈련 데이터로 모델을 학습시킵니다.
6.  **Model Evaluation**: Evaluate the model's performance on unseen test data using appropriate metrics.
6.  **모델 평가**: 보지 못한 테스트 데이터로 적절한 지표를 사용해 성능을 평가합니다.
7.  **Deployment**: Serve the trained model via an API.
7.  **배포**: 학습된 모델을 API 형태로 제공합니다.
8.  **Monitoring**: Track the model's performance in production and detect concept drift.
8.  **모니터링**: 프로덕션에서 모델 성능을 추적하고 개념 드리프트를 감지합니다.

**Practice:** create a “model brief” template capturing the problem statement, target metric, acceptable latency, and ethical considerations. Fill it out before touching code.
**실습:** 문제 정의, 목표 지표, 허용 지연, 윤리적 고려 사항을 담은 “모델 브리프” 템플릿을 만들고, 코드를 작성하기 전마다 채워 보세요.

---

## 2. A Practical Example: Predicting High-Value Bids
## 2. 실전 예제: 고가치 입찰 예측하기

Let's extend the analysis of your crawler data to build a predictive model.
크롤러 데이터 분석을 확장해 예측 모델을 만들어 봅시다.

**Problem**: We want to predict if a bid will be `is_high_value` (a binary classification problem).
**문제**: 입찰이 `is_high_value`인지 여부를 예측하는 이진 분류 문제입니다.

### Feature Engineering
### 피처 엔지니어링
The model can't understand raw text. We need to convert our data into numbers.
모델은 원시 텍스트를 이해하지 못하므로 숫자 형태로 변환해야 합니다.

```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier

# Assume df_clean is your cleaned dataframe from the previous guide

# Define features (X) and target (y)
X = df_clean[['department', 'post_weekday', 'has_attachment']]
y = df_clean['is_high_value']

# Split data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

# Create a preprocessor for our features
# 'department' and 'post_weekday' are categorical, so we'll one-hot encode them.
# 'has_attachment' is already boolean (numeric), so we'll just pass it through.
categorical_features = ['department', 'post_weekday']
passthrough_features = ['has_attachment']

preprocessor = ColumnTransformer(
    transformers=[
        ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features),
        ('pass', 'passthrough', passthrough_features)
    ])
```

**Practice:** experiment with at least two additional features (e.g., text length, day-of-month). Record in your notebook how each change affects validation metrics.
**실습:** 텍스트 길이, 일자 등 두 가지 이상의 추가 피처를 실험하고 검증 지표가 어떻게 변하는지 노트에 기록하세요.

### Model Training and Pipeline
### 모델 학습과 파이프라인
We'll use a `Pipeline` from `scikit-learn` to chain our preprocessing and modeling steps. This is a crucial best practice that prevents data leakage.
전처리와 모델 단계를 연결하기 위해 `scikit-learn`의 `Pipeline`을 사용합니다. 데이터 누수를 막는 중요한 모범 사례입니다.

```python
# Choose a model. A RandomForest is a great starting point.
model = RandomForestClassifier(random_state=42, class_weight='balanced')

# Create the full pipeline
pipeline = Pipeline(steps=[('preprocessor', preprocessor),
                           ('classifier', model)])

# Train the model
print("Training the model...")
pipeline.fit(X_train, y_train)
print("Training complete.")
```

**Practice:** use `GridSearchCV` or `RandomizedSearchCV` to explore hyperparameters (e.g., number of trees). Capture the best parameters and performance in your experiment log.
**실습:** `GridSearchCV`나 `RandomizedSearchCV`로 하이퍼파라미터(예: 트리 수)를 탐색하고 최적 값과 성능을 실험 노트에 기록하세요.

### Model Evaluation
### 모델 평가
How good is our model? We need to evaluate it on the test set. For a classification problem, common metrics are:
모델이 얼마나 좋은지 알아보기 위해 테스트 세트에서 평가해야 합니다. 분류 문제에서 흔히 쓰는 지표는 다음과 같습니다.
-   **Accuracy**: Overall percentage of correct predictions. Can be misleading if classes are imbalanced.
-   **정확도**: 전체 예측 중 맞춘 비율로, 클래스 불균형 시 오해를 줄 수 있습니다.
-   **Precision**: Of the bids we predicted as "high-value," how many actually were? (Minimizes false positives).
-   **정밀도**: 고가치로 예측한 것 중 실제 고가치인 비율로, 거짓 양성을 줄입니다.
-   **Recall**: Of all the actual "high-value" bids, how many did we find? (Minimizes false negatives).
-   **재현율**: 실제 고가치 중 얼마나 찾아냈는지로, 거짓 음성을 줄입니다.
-   **F1-Score**: The harmonic mean of precision and recall.
-   **F1-점수**: 정밀도와 재현율의 조화 평균입니다.
-   **AUC (Area Under the ROC Curve)**: A good overall measure of a classifier's ability to distinguish between classes.
-   **AUC**: 분류기가 클래스를 구분하는 능력을 종합적으로 나타냅니다.

```python
from sklearn.metrics import classification_report, roc_auc_score

# Make predictions on the test set
y_pred = pipeline.predict(X_test)
y_pred_proba = pipeline.predict_proba(X_test)[:, 1] # Probabilities for the positive class

print("\n--- Model Evaluation ---")
print(classification_report(y_test, y_pred))

auc_score = roc_auc_score(y_test, y_pred_proba)
print(f"AUC Score: {auc_score:.3f}")
```

---

## 3. MLOps: Deploying and Monitoring the Model
## 3. MLOps: 모델 배포와 모니터링

### Serving the Model with FastAPI
### FastAPI로 모델 제공하기
Once you're happy with your model, you need to deploy it. You can save your trained `pipeline` object to a file (e.g., with `joblib`) and load it in a FastAPI application.
모델이 만족스러우면 배포해야 합니다. 학습된 `pipeline` 객체를 `joblib` 등으로 파일에 저장하고 FastAPI 애플리케이션에서 로드할 수 있습니다.

```python
# model_server.py
import joblib
from fastapi import FastAPI
from pydantic import BaseModel

# Load the trained pipeline
pipeline = joblib.load("bid_classifier.joblib")

app = FastAPI()

class BidFeatures(BaseModel):
    department: str
    post_weekday: str
    has_attachment: bool

@app.post("/predict")
def predict(features: BidFeatures):
    # Create a DataFrame from the input
    input_df = pd.DataFrame([features.dict()])
    
    # Make a prediction
    prediction = pipeline.predict(input_df)[0]
    probability = pipeline.predict_proba(input_df)[0][1]
    
    return {
        "is_high_value_prediction": bool(prediction),
        "probability": float(probability)
    }
```

### Monitoring for Concept Drift
### 개념 드리프트 모니터링
The world changes. The patterns that your model learned during training might not hold true a few months later. This is called **concept drift**.
세계는 변합니다. 학습 당시의 패턴이 몇 달 후에는 통하지 않을 수 있는데, 이를 **개념 드리프트**라고 합니다.

**How to monitor for it**:
**감지 방법**:
1.  **Log Predictions and Actuals**: In your production system, log both your model's predictions and the actual outcomes (when they become available).
1.  **예측과 실제 결과 로깅**: 프로덕션에서 모델 예측과 실제 결과를 모두 기록합니다.
2.  **Track Production Metrics**: Periodically (e.g., daily or weekly), recalculate your evaluation metrics (like AUC or F1-score) on the production data.
2.  **프로덕션 지표 추적**: 주기적으로(A/B 테스트, 주/일 단위) AUC, F1 등 평가 지표를 다시 계산합니다.
3.  **Alert on Degradation**: Set up an alert to fire if your production metrics drop below a certain threshold. This is a signal that your model is no longer performing well and needs to be retrained on more recent data.
3.  **성능 저하 알림**: 지표가 특정 임계값 아래로 떨어지면 알림을 보내 재학습이 필요함을 알려줍니다.

This entire process—from data extraction to model retraining—can be automated using tools like **Kubeflow** or **MLflow**, which are designed to manage the end-to-end machine learning lifecycle.
데이터 추출부터 재학습까지 전 과정을 **Kubeflow**, **MLflow** 같은 도구로 자동화할 수 있습니다. 이들은 ML 라이프사이클 전체를 관리하도록 설계되었습니다.

By moving from EDA to ML, you evolve from describing the past to predicting the future. This allows you to build truly "smart" applications that can automate decisions, personalize user experiences, and unlock new forms of value from your data.
EDA에서 ML로 이동하면 과거를 설명하는 수준을 넘어 미래를 예측할 수 있습니다. 그 결과 의사결정을 자동화하고 사용자 경험을 개인화하며 데이터에서 새로운 가치를 끌어내는 “스마트” 애플리케이션을 만들 수 있습니다.

## Going Further
## 더 나아가기
-   Package the trained model with `mlflow` or `bentoml` and deploy it to a staging environment before production.
-   학습된 모델을 `mlflow`나 `bentoml`로 패키징해 프로덕션 전 스테이징 환경에 배포하세요.
-   Evaluate ethical impacts: check for class imbalance, bias across departments, and document mitigations.
-   윤리적 영향을 평가하고, 클래스 불균형과 부서별 편향을 점검해 완화책을 문서화하세요.
-   Schedule a monthly retraining job triggered by Airflow that tracks model metrics before promoting the new model.
-   Airflow로 매월 재학습 작업을 예약해 새 모델을 승격하기 전에 성능 지표를 추적하세요.
