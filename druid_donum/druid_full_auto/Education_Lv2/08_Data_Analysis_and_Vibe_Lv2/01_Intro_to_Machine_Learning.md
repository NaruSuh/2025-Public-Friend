# 08 - Data Analysis and Vibe - Lv.2: From Analysis to Machine Learning

You've mastered exploratory data analysis (EDA) with `pandas`. Level 2 is about using your data to make predictions and automate decisions. This is the realm of Machine Learning (ML).

## Core Concepts

1.  **The Machine Learning Workflow**: A structured process for building, deploying, and maintaining ML models.
2.  **Feature Engineering**: The art and science of creating predictive signals (features) from raw data. This is often the most important factor in a model's success.
3.  **Model Training and Evaluation**: Choosing the right algorithm, training it on your data, and rigorously evaluating its performance.
4.  **MLOps (Machine Learning Operations)**: The practice of deploying, monitoring, and retraining models in production. A model is not a one-time artifact; it's a living system that needs to be maintained.

---

## 1. The Machine Learning Workflow

A typical ML project follows these steps:
1.  **Problem Framing**: What are you trying to predict, and how will that prediction be used to drive value? (e.g., "We will predict which bids are 'high-value' to help users prioritize their efforts.")
2.  **Data Collection and Cleaning**: Same as in EDA, but with a focus on creating a reliable dataset for training.
3.  **Feature Engineering**: Create features for the model.
4.  **Model Selection**: Choose a class of models to try (e.g., logistic regression, gradient boosting).
5.  **Model Training**: Fit the model to your training data.
6.  **Model Evaluation**: Evaluate the model's performance on unseen test data using appropriate metrics.
7.  **Deployment**: Serve the trained model via an API.
8.  **Monitoring**: Track the model's performance in production and detect concept drift.

---

## 2. A Practical Example: Predicting High-Value Bids

Let's extend the analysis of your crawler data to build a predictive model.

**Problem**: We want to predict if a bid will be `is_high_value` (a binary classification problem).

### Feature Engineering
The model can't understand raw text. We need to convert our data into numbers.

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

### Model Training and Pipeline
We'll use a `Pipeline` from `scikit-learn` to chain our preprocessing and modeling steps. This is a crucial best practice that prevents data leakage.

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

### Model Evaluation
How good is our model? We need to evaluate it on the test set. For a classification problem, common metrics are:
-   **Accuracy**: Overall percentage of correct predictions. Can be misleading if classes are imbalanced.
-   **Precision**: Of the bids we predicted as "high-value," how many actually were? (Minimizes false positives).
-   **Recall**: Of all the actual "high-value" bids, how many did we find? (Minimizes false negatives).
-   **F1-Score**: The harmonic mean of precision and recall.
-   **AUC (Area Under the ROC Curve)**: A good overall measure of a classifier's ability to distinguish between classes.

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

### Serving the Model with FastAPI
Once you're happy with your model, you need to deploy it. You can save your trained `pipeline` object to a file (e.g., with `joblib`) and load it in a FastAPI application.

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
The world changes. The patterns that your model learned during training might not hold true a few months later. This is called **concept drift**.

**How to monitor for it**:
1.  **Log Predictions and Actuals**: In your production system, log both your model's predictions and the actual outcomes (when they become available).
2.  **Track Production Metrics**: Periodically (e.g., daily or weekly), recalculate your evaluation metrics (like AUC or F1-score) on the production data.
3.  **Alert on Degradation**: Set up an alert to fire if your production metrics drop below a certain threshold. This is a signal that your model is no longer performing well and needs to be retrained on more recent data.

This entire process—from data extraction to model retraining—can be automated using tools like **Kubeflow** or **MLflow**, which are designed to manage the end-to-end machine learning lifecycle.

By moving from EDA to ML, you evolve from describing the past to predicting the future. This allows you to build truly "smart" applications that can automate decisions, personalize user experiences, and unlock new forms of value from your data.
