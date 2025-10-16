# 데이터 파이프라인 구축: ETL부터 실시간 스트리밍까지

**대상 독자**: 데이터베이스를 다뤄봤지만 대규모 데이터 처리 경험이 없는 개발자
**선행 지식**: SQL, Python, 기본적인 데이터 구조
**학습 시간**: 3-4시간

---

## 데이터 파이프라인이란?

### 정의

**데이터 파이프라인** = 데이터를 수집 → 변환 → 저장 → 분석하는 자동화된 프로세스

### 왜 필요한가?

```
수동 처리 (파이프라인 없을 때):
09:00 - 개발자가 5개 소스에서 CSV 다운로드
09:30 - Excel로 데이터 정제
10:00 - 포맷 변환
10:30 - 데이터베이스에 업로드
11:00 - 분석가에게 전달
→ 매일 2시간 소요, 실수 가능성 높음

자동 처리 (파이프라인 있을 때):
02:00 - 자동으로 데이터 수집
02:05 - 자동으로 정제 및 변환
02:10 - 데이터베이스에 자동 업로드
02:15 - 대시보드 자동 업데이트
09:00 - 분석가가 최신 데이터로 작업 시작
→ 자동화, 오류 없음, 시간 절약
```

---

## 1단계: ETL 기초 (Extract, Transform, Load)

### Extract (추출): 데이터 수집

```python
# ✅ 여러 소스에서 데이터 수집
import requests
import psycopg2
from pymongo import MongoClient

class DataExtractor:
    """다양한 소스에서 데이터 추출"""

    def extract_from_api(self, url):
        """REST API에서 데이터 추출"""
        response = requests.get(url)
        response.raise_for_status()
        return response.json()

    def extract_from_postgres(self, query):
        """PostgreSQL에서 데이터 추출"""
        conn = psycopg2.connect(
            host='localhost',
            database='sales_db',
            user='user',
            password='password'
        )

        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()

        return rows

    def extract_from_mongodb(self, collection_name, query):
        """MongoDB에서 데이터 추출"""
        client = MongoClient('mongodb://localhost:27017/')
        db = client['analytics']
        collection = db[collection_name]

        documents = list(collection.find(query))
        client.close()

        return documents

    def extract_from_csv(self, file_path):
        """CSV 파일에서 데이터 추출"""
        import pandas as pd
        df = pd.read_csv(file_path)
        return df.to_dict('records')

# 사용 예제
extractor = DataExtractor()

# API에서 사용자 데이터
users = extractor.extract_from_api('https://api.example.com/users')

# DB에서 주문 데이터
orders = extractor.extract_from_postgres(
    'SELECT * FROM orders WHERE created_at >= NOW() - INTERVAL \'1 day\''
)

# MongoDB에서 로그 데이터
logs = extractor.extract_from_mongodb(
    'user_events',
    {'timestamp': {'$gte': datetime.now() - timedelta(days=1)}}
)
```

### Transform (변환): 데이터 정제 및 가공

```python
# ✅ 데이터 변환 및 정제
import pandas as pd
from datetime import datetime

class DataTransformer:
    """데이터 정제 및 변환"""

    def clean_data(self, data):
        """결측치 처리, 중복 제거"""
        df = pd.DataFrame(data)

        # 결측치 처리
        df['email'].fillna('unknown@example.com', inplace=True)
        df['age'].fillna(df['age'].median(), inplace=True)

        # 중복 제거
        df.drop_duplicates(subset=['user_id'], inplace=True)

        return df.to_dict('records')

    def normalize_data(self, data):
        """데이터 정규화"""
        df = pd.DataFrame(data)

        # 날짜 형식 통일
        df['created_at'] = pd.to_datetime(df['created_at'])

        # 문자열 소문자 변환
        df['email'] = df['email'].str.lower()

        # 전화번호 형식 통일 (010-1234-5678 → 01012345678)
        df['phone'] = df['phone'].str.replace('-', '')

        return df.to_dict('records')

    def enrich_data(self, orders, users):
        """데이터 결합 및 보강"""
        df_orders = pd.DataFrame(orders)
        df_users = pd.DataFrame(users)

        # 주문 데이터에 사용자 정보 결합
        enriched = df_orders.merge(
            df_users,
            left_on='user_id',
            right_on='id',
            how='left'
        )

        # 파생 변수 생성
        enriched['order_year'] = enriched['created_at'].dt.year
        enriched['order_month'] = enriched['created_at'].dt.month

        # 나이 그룹 분류
        enriched['age_group'] = pd.cut(
            enriched['age'],
            bins=[0, 18, 30, 50, 100],
            labels=['Youth', 'Young Adult', 'Middle Age', 'Senior']
        )

        return enriched.to_dict('records')

# 사용 예제
transformer = DataTransformer()

# 1. 정제
clean_users = transformer.clean_data(users)

# 2. 정규화
normalized_users = transformer.normalize_data(clean_users)

# 3. 보강
enriched_orders = transformer.enrich_data(orders, normalized_users)
```

### Load (적재): 데이터 저장

```python
# ✅ 변환된 데이터를 목적지에 저장
class DataLoader:
    """데이터 적재"""

    def load_to_postgres(self, data, table_name):
        """PostgreSQL에 데이터 적재"""
        import psycopg2
        from psycopg2.extras import execute_batch

        conn = psycopg2.connect(
            host='warehouse-db',
            database='analytics',
            user='etl_user',
            password='password'
        )

        cursor = conn.cursor()

        # 테이블 생성 (없으면)
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {table_name} (
                id SERIAL PRIMARY KEY,
                user_id INT,
                email VARCHAR(255),
                age INT,
                created_at TIMESTAMP
            )
        ''')

        # 데이터 삽입
        insert_query = f'''
            INSERT INTO {table_name} (user_id, email, age, created_at)
            VALUES (%(user_id)s, %(email)s, %(age)s, %(created_at)s)
        '''

        execute_batch(cursor, insert_query, data)

        conn.commit()
        cursor.close()
        conn.close()

    def load_to_s3(self, data, bucket, key):
        """S3에 Parquet 파일로 저장"""
        import boto3
        import pandas as pd
        from io import BytesIO

        df = pd.DataFrame(data)

        # Parquet 형식으로 변환 (압축률 높음, 쿼리 빠름)
        buffer = BytesIO()
        df.to_parquet(buffer, engine='pyarrow', compression='snappy')
        buffer.seek(0)

        # S3 업로드
        s3 = boto3.client('s3')
        s3.upload_fileobj(buffer, bucket, key)

    def load_to_bigquery(self, data, dataset, table):
        """Google BigQuery에 적재"""
        from google.cloud import bigquery
        import pandas as pd

        client = bigquery.Client()

        df = pd.DataFrame(data)
        table_id = f'{dataset}.{table}'

        # 데이터 적재
        job = client.load_table_from_dataframe(df, table_id)
        job.result()  # 완료 대기

# 사용 예제
loader = DataLoader()

# PostgreSQL 데이터 웨어하우스에 적재
loader.load_to_postgres(enriched_orders, 'fact_orders')

# S3에 백업
loader.load_to_s3(enriched_orders, 'my-data-lake', 'orders/2025-10-06.parquet')
```

---

## 2단계: 전체 ETL 파이프라인 구성

### Airflow로 파이프라인 오케스트레이션

```python
# ✅ Apache Airflow DAG (Directed Acyclic Graph)
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

# DAG 정의
default_args = {
    'owner': 'data-team',
    'depends_on_past': False,
    'start_date': datetime(2025, 1, 1),
    'email': ['data-team@example.com'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 3,  # 실패 시 3번 재시도
    'retry_delay': timedelta(minutes=5)
}

dag = DAG(
    'daily_sales_etl',
    default_args=default_args,
    description='일일 매출 데이터 ETL',
    schedule_interval='0 2 * * *',  # 매일 오전 2시 실행 (크론 표현식)
    catchup=False
)

# Task 1: 데이터 추출
def extract_task():
    extractor = DataExtractor()

    users = extractor.extract_from_api('https://api.example.com/users')
    orders = extractor.extract_from_postgres(
        'SELECT * FROM orders WHERE created_at >= NOW() - INTERVAL \'1 day\''
    )

    # XCom에 저장 (Task 간 데이터 전달)
    return {'users': users, 'orders': orders}

extract = PythonOperator(
    task_id='extract_data',
    python_callable=extract_task,
    dag=dag
)

# Task 2: 데이터 변환
def transform_task(**context):
    # 이전 Task에서 데이터 받기
    ti = context['ti']
    data = ti.xcom_pull(task_ids='extract_data')

    transformer = DataTransformer()

    clean_users = transformer.clean_data(data['users'])
    normalized_users = transformer.normalize_data(clean_users)
    enriched_orders = transformer.enrich_data(data['orders'], normalized_users)

    return enriched_orders

transform = PythonOperator(
    task_id='transform_data',
    python_callable=transform_task,
    provide_context=True,
    dag=dag
)

# Task 3: 데이터 적재
def load_task(**context):
    ti = context['ti']
    enriched_orders = ti.xcom_pull(task_ids='transform_data')

    loader = DataLoader()
    loader.load_to_postgres(enriched_orders, 'fact_orders')
    loader.load_to_s3(
        enriched_orders,
        'my-data-lake',
        f'orders/{datetime.now().strftime("%Y-%m-%d")}.parquet'
    )

load = PythonOperator(
    task_id='load_data',
    python_callable=load_task,
    provide_context=True,
    dag=dag
)

# Task 의존성 정의
extract >> transform >> load  # extract 완료 → transform 실행 → load 실행

# Airflow UI에서 시각화:
# ┌─────────┐     ┌───────────┐     ┌──────────┐
# │ Extract │ --> │ Transform │ --> │  Load    │
# └─────────┘     └───────────┘     └──────────┘
```

### 파이프라인 모니터링

```python
# ✅ 데이터 품질 검증 Task 추가
def validate_data_quality(**context):
    """데이터 품질 검증"""
    ti = context['ti']
    data = ti.xcom_pull(task_ids='transform_data')

    df = pd.DataFrame(data)

    # 검증 1: 결측치 확인
    null_percentage = df.isnull().sum() / len(df) * 100
    if (null_percentage > 5).any():  # 5% 이상 결측치
        raise ValueError(f"Too many null values: {null_percentage}")

    # 검증 2: 중복 확인
    duplicates = df.duplicated(subset=['order_id']).sum()
    if duplicates > 0:
        raise ValueError(f"Found {duplicates} duplicate orders")

    # 검증 3: 데이터 범위 확인
    if (df['amount'] < 0).any():
        raise ValueError("Found negative order amounts")

    # 검증 4: 예상 레코드 수 확인
    if len(df) < 100:  # 하루에 최소 100건은 있어야 함
        raise ValueError(f"Too few records: {len(df)}")

    print(f"Data quality check passed: {len(df)} records")

validate = PythonOperator(
    task_id='validate_quality',
    python_callable=validate_data_quality,
    provide_context=True,
    dag=dag
)

# 의존성 업데이트
extract >> transform >> validate >> load
# 품질 검증 실패 시 load 실행 안 됨
```

---

## 3단계: 실시간 스트리밍 파이프라인

### Kafka를 이용한 실시간 데이터 처리

```python
# ✅ Kafka Producer: 이벤트 발행
from kafka import KafkaProducer
import json

producer = KafkaProducer(
    bootstrap_servers=['localhost:9092'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# 사용자 클릭 이벤트 발행
def track_user_click(user_id, page, product_id):
    event = {
        'event_type': 'click',
        'user_id': user_id,
        'page': page,
        'product_id': product_id,
        'timestamp': datetime.now().isoformat()
    }

    # Kafka 토픽에 이벤트 전송
    producer.send('user_events', value=event)
    producer.flush()

# 웹 애플리케이션에서 호출
@app.route('/track/click', methods=['POST'])
def track_click():
    data = request.json
    track_user_click(
        user_id=data['user_id'],
        page=data['page'],
        product_id=data.get('product_id')
    )
    return jsonify({'status': 'tracked'})

# ✅ Kafka Consumer: 이벤트 소비 및 처리
from kafka import KafkaConsumer
import redis

consumer = KafkaConsumer(
    'user_events',
    bootstrap_servers=['localhost:9092'],
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    group_id='analytics-group'
)

redis_client = redis.Redis()

# 실시간 이벤트 처리
for message in consumer:
    event = message.value

    # 실시간 카운터 업데이트
    if event['event_type'] == 'click':
        product_id = event['product_id']

        # Redis에 클릭 수 증가
        redis_client.hincrby('product_clicks', product_id, 1)

        # 최근 1시간 클릭 수 (Sliding Window)
        key = f"product:{product_id}:clicks:hourly"
        redis_client.zadd(
            key,
            {event['timestamp']: event['timestamp']}
        )
        redis_client.zremrangebyscore(
            key,
            '-inf',
            (datetime.now() - timedelta(hours=1)).timestamp()
        )

        # 1시간 클릭 수 조회
        hourly_clicks = redis_client.zcard(key)

        # 인기 상품 알림 (1시간에 100회 이상 클릭)
        if hourly_clicks >= 100:
            send_alert(f"Product {product_id} is trending! {hourly_clicks} clicks/hour")

    # 데이터베이스에 저장 (배치 처리)
    save_to_db(event)
```

### Spark Streaming으로 대규모 처리

```python
# ✅ PySpark로 실시간 데이터 분석
from pyspark.sql import SparkSession
from pyspark.sql.functions import window, col, count

spark = SparkSession.builder \
    .appName("RealTimeAnalytics") \
    .getOrCreate()

# Kafka에서 스트림 읽기
df = spark \
    .readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "localhost:9092") \
    .option("subscribe", "user_events") \
    .load()

# JSON 파싱
from pyspark.sql.functions import from_json
from pyspark.sql.types import StructType, StructField, StringType, TimestampType

schema = StructType([
    StructField("event_type", StringType()),
    StructField("user_id", StringType()),
    StructField("product_id", StringType()),
    StructField("timestamp", TimestampType())
])

events = df.selectExpr("CAST(value AS STRING)") \
    .select(from_json("value", schema).alias("data")) \
    .select("data.*")

# 5분 윈도우로 상품별 클릭 수 집계
product_clicks = events \
    .groupBy(
        window(col("timestamp"), "5 minutes"),  # 5분 윈도우
        col("product_id")
    ) \
    .agg(count("*").alias("click_count")) \
    .orderBy(col("click_count").desc())

# 실시간 결과를 콘솔에 출력
query = product_clicks \
    .writeStream \
    .outputMode("complete") \
    .format("console") \
    .start()

query.awaitTermination()

# 출력:
# +------------------------------------------+----------+-----------+
# |window                                    |product_id|click_count|
# +------------------------------------------+----------+-----------+
# |{2025-10-06 10:00:00, 2025-10-06 10:05:00}|P12345    |523        |
# |{2025-10-06 10:00:00, 2025-10-06 10:05:00}|P67890    |412        |
# +------------------------------------------+----------+-----------+
```

---

## 4단계: 데이터 레이크 vs 데이터 웨어하우스

### 데이터 레이크 (Data Lake)

```
특징:
✅ 원본 데이터를 그대로 저장 (Schema-on-Read)
✅ 정형/비정형 데이터 모두 저장 가능
✅ 저렴한 스토리지 (S3, GCS)
✅ 유연성 높음

적합한 경우:
- 머신러닝 학습 데이터
- 로그 파일, 이미지, 동영상
- 탐색적 분석

도구: AWS S3, Azure Data Lake, Google Cloud Storage
```

**데이터 레이크 구조 예제**

```
s3://my-data-lake/
├── raw/                     # 원본 데이터 (변환 전)
│   ├── orders/
│   │   ├── 2025-10-01.json
│   │   ├── 2025-10-02.json
│   ├── logs/
│   │   ├── 2025-10-01.log.gz
│   ├── images/
│       ├── product_123.jpg
│
├── processed/               # 정제된 데이터
│   ├── orders/
│   │   ├── 2025-10-01.parquet
│   │   ├── 2025-10-02.parquet
│
└── curated/                 # 분석용 데이터
    ├── daily_sales/
        ├── 2025-10-01.parquet
```

### 데이터 웨어하우스 (Data Warehouse)

```
특징:
✅ 구조화된 데이터만 저장 (Schema-on-Write)
✅ 분석 최적화 (집계 쿼리 빠름)
✅ 비용 높음
✅ SQL 쿼리 가능

적합한 경우:
- BI 대시보드
- 정기 리포트
- SQL 분석

도구: Snowflake, BigQuery, Redshift
```

**데이터 웨어하우스 스키마 (Star Schema)**

```sql
-- ✅ Fact Table (측정 가능한 이벤트)
CREATE TABLE fact_orders (
    order_id BIGINT PRIMARY KEY,
    user_id BIGINT,              -- Foreign Key
    product_id BIGINT,            -- Foreign Key
    date_id INT,                  -- Foreign Key
    amount DECIMAL(10, 2),        -- 측정값
    quantity INT,                 -- 측정값
    shipping_cost DECIMAL(10, 2)  -- 측정값
);

-- Dimension Tables (설명 정보)
CREATE TABLE dim_users (
    user_id BIGINT PRIMARY KEY,
    email VARCHAR(255),
    age INT,
    country VARCHAR(50)
);

CREATE TABLE dim_products (
    product_id BIGINT PRIMARY KEY,
    name VARCHAR(255),
    category VARCHAR(100),
    price DECIMAL(10, 2)
);

CREATE TABLE dim_date (
    date_id INT PRIMARY KEY,
    date DATE,
    year INT,
    month INT,
    day INT,
    quarter INT,
    is_weekend BOOLEAN
);

-- 분석 쿼리 (매우 빠름)
SELECT
    d.year,
    d.month,
    p.category,
    SUM(f.amount) AS total_sales,
    COUNT(DISTINCT f.user_id) AS unique_customers
FROM fact_orders f
JOIN dim_date d ON f.date_id = d.date_id
JOIN dim_products p ON f.product_id = p.product_id
WHERE d.year = 2025
GROUP BY d.year, d.month, p.category
ORDER BY total_sales DESC;
```

---

## 5단계: 증분 처리 (Incremental Processing)

### 문제: 매번 전체 데이터 처리는 비효율

```python
# ❌ 매번 전체 데이터 처리 (느림, 비용 높음)
def daily_etl():
    # 전체 데이터 조회 (테이블에 10억 행이 있으면?)
    all_orders = db.execute('SELECT * FROM orders').fetchall()

    # 전체 데이터 변환 및 적재 (매일 10억 행 처리)
    transform_and_load(all_orders)

# ✅ 증분 처리: 변경된 데이터만 처리
def incremental_etl():
    # 마지막 처리 시점 조회
    last_run = db.execute(
        'SELECT MAX(last_processed_at) FROM etl_metadata'
    ).fetchone()[0]

    # 변경된 데이터만 조회 (하루에 10만 행)
    new_orders = db.execute(
        'SELECT * FROM orders WHERE updated_at > ?',
        (last_run,)
    ).fetchall()

    # 변경 데이터만 처리
    transform_and_load(new_orders)

    # 처리 시점 기록
    db.execute(
        'UPDATE etl_metadata SET last_processed_at = ?',
        (datetime.now(),)
    )

# 성능 비교:
# 전체 처리: 10억 행 × 10ms = 2,777시간
# 증분 처리: 10만 행 × 10ms = 16분
# → 10,000배 빠름!
```

### CDC (Change Data Capture)

```python
# ✅ Debezium으로 실시간 변경 감지
# PostgreSQL의 변경 사항을 Kafka로 스트리밍

# Debezium 설정 (docker-compose.yml)
"""
services:
  debezium:
    image: debezium/connect
    environment:
      - BOOTSTRAP_SERVERS=kafka:9092
      - CONFIG_STORAGE_TOPIC=debezium_config
      - OFFSET_STORAGE_TOPIC=debezium_offset
"""

# Debezium Connector 등록
import requests

connector_config = {
    "name": "orders-connector",
    "config": {
        "connector.class": "io.debezium.connector.postgresql.PostgresConnector",
        "database.hostname": "postgres",
        "database.port": "5432",
        "database.user": "debezium",
        "database.password": "password",
        "database.dbname": "production",
        "table.include.list": "public.orders",
        "topic.prefix": "dbserver1"
    }
}

requests.post(
    'http://debezium:8083/connectors',
    json=connector_config
)

# 이제 orders 테이블의 INSERT/UPDATE/DELETE가 실시간으로 Kafka로 전송됨!

# Consumer에서 변경 사항 처리
from kafka import KafkaConsumer

consumer = KafkaConsumer('dbserver1.public.orders')

for message in consumer:
    change = json.loads(message.value)

    if change['op'] == 'c':  # Create (INSERT)
        handle_new_order(change['after'])
    elif change['op'] == 'u':  # Update
        handle_updated_order(change['before'], change['after'])
    elif change['op'] == 'd':  # Delete
        handle_deleted_order(change['before'])
```

---

## 6단계: 데이터 품질 및 테스팅

### Great Expectations로 데이터 검증

```python
# ✅ Great Expectations: 데이터 품질 보장
import great_expectations as gx

context = gx.get_context()

# 데이터 소스 연결
datasource = context.sources.add_pandas("my_datasource")
data_asset = datasource.add_dataframe_asset(name="orders")

# Expectation Suite 생성
suite = context.add_expectation_suite("orders_quality")

# 기대값 정의
validator = context.get_validator(
    batch_request=data_asset.build_batch_request(),
    expectation_suite_name="orders_quality"
)

# 검증 규칙
validator.expect_column_values_to_not_be_null("order_id")
validator.expect_column_values_to_be_unique("order_id")
validator.expect_column_values_to_be_between("amount", min_value=0, max_value=1000000)
validator.expect_column_values_to_be_in_set("status", ["pending", "completed", "cancelled"])
validator.expect_column_values_to_match_regex("email", r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

# 검증 실행
results = validator.validate()

if not results['success']:
    print("Data quality check failed!")
    for result in results['results']:
        if not result['success']:
            print(f"Failed: {result['expectation_config']['expectation_type']}")
    raise ValueError("Data quality issues detected")
```

### 데이터 파이프라인 유닛 테스트

```python
# ✅ pytest로 변환 로직 테스트
import pytest
from transformer import DataTransformer

def test_clean_data_removes_duplicates():
    """중복 제거 테스트"""
    transformer = DataTransformer()

    input_data = [
        {'user_id': 1, 'email': 'test@example.com'},
        {'user_id': 1, 'email': 'test@example.com'},  # 중복
        {'user_id': 2, 'email': 'test2@example.com'}
    ]

    result = transformer.clean_data(input_data)

    assert len(result) == 2  # 중복 제거됨

def test_normalize_email_lowercases():
    """이메일 소문자 변환 테스트"""
    transformer = DataTransformer()

    input_data = [
        {'user_id': 1, 'email': 'TEST@EXAMPLE.COM'}
    ]

    result = transformer.normalize_data(input_data)

    assert result[0]['email'] == 'test@example.com'

def test_enrich_data_adds_user_info():
    """데이터 결합 테스트"""
    transformer = DataTransformer()

    orders = [{'order_id': 1, 'user_id': 123, 'amount': 100}]
    users = [{'id': 123, 'name': 'John Doe', 'age': 30}]

    result = transformer.enrich_data(orders, users)

    assert result[0]['name'] == 'John Doe'
    assert result[0]['age'] == 30
```

---

## 실전 예제: e커머스 데이터 파이프라인

### 요구사항

```
목표: 실시간 상품 추천 시스템

데이터 소스:
- 사용자 클릭 (Kafka)
- 주문 내역 (PostgreSQL)
- 상품 정보 (MongoDB)
- 재고 (Redis)

처리:
- 실시간: 클릭 스트림 분석 (Kafka + Spark)
- 배치: 일일 판매 집계 (Airflow + Snowflake)

출력:
- 추천 API (실시간)
- 판매 대시보드 (Tableau)
```

### 아키텍처

```
┌──────────────┐
│ 웹 앱        │ → 클릭 이벤트
└──────┬───────┘
       ↓
┌──────────────┐
│ Kafka        │ → 이벤트 스트림
└──────┬───────┘
       ↓
┌──────────────┐
│ Spark        │ → 실시간 분석
│ Streaming    │
└──────┬───────┘
       ↓
┌──────────────┐
│ Redis        │ → 추천 캐시
└──────────────┘
       ↑
┌──────┴───────┐
│ 추천 API     │ ← 사용자 요청
└──────────────┘

(별도)
┌──────────────┐
│ Airflow      │ → 매일 새벽 2시
└──────┬───────┘
       ↓
┌──────────────┐
│ PostgreSQL   │ → 주문 추출
└──────┬───────┘
       ↓
┌──────────────┐
│ Transform    │ → 집계 및 정제
└──────┬───────┘
       ↓
┌──────────────┐
│ Snowflake    │ → 데이터 웨어하우스
└──────┬───────┘
       ↓
┌──────────────┐
│ Tableau      │ → 대시보드
└──────────────┘
```

---

## 데이터 엔지니어링 체크리스트

### 파이프라인 설계
- [ ] 데이터 소스가 명확히 정의되어 있는가?
- [ ] 데이터 변환 로직이 문서화되어 있는가?
- [ ] 배치 vs 실시간 처리 선택이 적절한가?
- [ ] 증분 처리로 효율성을 높였는가?

### 데이터 품질
- [ ] 결측치, 중복, 이상치를 처리하는가?
- [ ] 데이터 검증 규칙이 있는가? (Great Expectations)
- [ ] 변환 로직에 유닛 테스트가 있는가?
- [ ] 데이터 품질 메트릭을 모니터링하는가?

### 성능
- [ ] 파티셔닝으로 쿼리 속도를 높였는가?
- [ ] 압축 형식(Parquet, ORC)을 사용하는가?
- [ ] 불필요한 전체 스캔을 피하는가?
- [ ] 병렬 처리를 활용하는가?

### 운영
- [ ] 파이프라인이 자동으로 실행되는가? (Airflow)
- [ ] 실패 시 알림이 오는가?
- [ ] 재시도 로직이 있는가?
- [ ] 처리 이력이 기록되는가?

### 비용
- [ ] 스토리지 비용을 최적화했는가? (수명 주기 정책)
- [ ] 불필요한 데이터 복사를 피하는가?
- [ ] 컴퓨팅 리소스를 적절히 사용하는가?

---

## 다음 단계

1. **dbt (data build tool)**: SQL 기반 데이터 변환 및 테스팅
2. **Delta Lake**: ACID 트랜잭션이 가능한 데이터 레이크
3. **Flink**: 초저지연 실시간 스트림 처리
4. **Data Mesh**: 분산 데이터 아키텍처

---

## 참고 자료

- **책**: "Fundamentals of Data Engineering" by Joe Reis & Matt Housley
- **코스**: [Data Engineering Zoomcamp](https://github.com/DataTalksClub/data-engineering-zoomcamp)
- **도구**: [Apache Airflow 튜토리얼](https://airflow.apache.org/docs/apache-airflow/stable/tutorial.html)
- **블로그**: [Databricks Engineering Blog](https://databricks.com/blog/category/engineering)
