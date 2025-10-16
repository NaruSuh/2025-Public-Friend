# 08.01 - Data Analysis with Pandas
# 08.01 - Pandas를 사용한 데이터 분석

While your primary project is a web crawler, understanding the basics of data analysis is a crucial skill for any Vibe Coder. You might need to analyze crawler performance, user behavior, or business metrics. **Pandas** is the most popular and powerful library in Python for data manipulation and analysis.
주요 프로젝트는 웹 크롤러이지만 데이터 분석의 기본을 이해하는 것은 모든 Vibe 코더에게 중요한 기술입니다. 크롤러 성능, 사용자 행동 또는 비즈니스 메트릭을 분석해야 할 수 있습니다. **Pandas**는 데이터 조작 및 분석을 위한 파이썬에서 가장 인기 있고 강력한 라이브러리입니다.

## Core Concepts
## 핵심 개념

1.  **DataFrame**: The primary data structure in Pandas. It's a two-dimensional table with labeled axes (rows and columns), much like a spreadsheet or a SQL table.
    **DataFrame**: Pandas의 기본 데이터 구조입니다. 스프레드시트나 SQL 테이블과 매우 유사한 레이블이 지정된 축(행 및 열)이 있는 2차원 테이블입니다.
2.  **Series**: A one-dimensional labeled array. Each column in a DataFrame is a Series.
    **Series**: 1차원 레이블이 지정된 배열입니다. DataFrame의 각 열은 Series입니다.
3.  **Indexing and Selection**: How to select subsets of your data (rows, columns, or both).
    **인덱싱 및 선택**: 데이터의 하위 집합(행, 열 또는 둘 다)을 선택하는 방법입니다.
4.  **Grouping and Aggregation**: The ability to group data based on some criteria and then calculate a metric for each group (e.g., `GROUP BY` in SQL).
    **그룹화 및 집계**: 일부 기준에 따라 데이터를 그룹화한 다음 각 그룹에 대한 메트릭을 계산하는 기능입니다(예: SQL의 `GROUP BY`).
5.  **Vectorization**: Pandas operations are vectorized, meaning they operate on entire arrays of data at once. This is much faster than iterating through data row by row in a Python `for` loop.
    **벡터화**: Pandas 작업은 벡터화되어 한 번에 전체 데이터 배열에 대해 작동합니다. 이것은 파이썬 `for` 루프에서 데이터를 한 줄씩 반복하는 것보다 훨씬 빠릅니다.

---

## 1. Creating and Inspecting a DataFrame
## 1. DataFrame 생성 및 검사

First, install Pandas:
먼저 Pandas를 설치합니다.
`pip install pandas`

Let's create a DataFrame from a dictionary.
사전에서 DataFrame을 만들어 보겠습니다.

```python
import pandas as pd

data = {
    'user_id': [101, 102, 103, 104, 105, 102],
    'action': ['login', 'view_page', 'login', 'add_to_cart', 'view_page', 'login'],
    'duration_ms': [100, 250, 120, 500, 300, 110],
    'platform': ['web', 'mobile', 'web', 'web', 'mobile', 'web']
}

df = pd.DataFrame(data)

# Display the first 5 rows
# 처음 5개 행 표시
print("--- Head ---")
print(df.head())

# Get a concise summary of the DataFrame
# DataFrame의 간결한 요약 정보 얻기
print("\n--- Info ---")
df.info()

# Get descriptive statistics for numerical columns
# 숫자 열에 대한 기술 통계 얻기
print("\n--- Describe ---")
print(df.describe())
```

## 2. Selection and Filtering
## 2. 선택 및 필터링

You can select data using labels (`.loc`) or integer positions (`.iloc`).
레이블(`.loc`) 또는 정수 위치(`.iloc`)를 사용하여 데이터를 선택할 수 있습니다.

```python
# Select a single column (this returns a Series)
# 단일 열 선택(Series 반환)
print(df['action'])

# Select multiple columns
# 여러 열 선택
print(df[['user_id', 'action']])

# ---
# --- Filtering with boolean indexing ---
# --- 부울 인덱싱으로 필터링 ---

# Find all rows where the action was 'login'
# 작업이 'login'인 모든 행 찾기
login_df = df[df['action'] == 'login']
print("\n--- Login Actions ---")
print(login_df)

# Find all rows where duration was greater than 200ms AND the platform was 'web'
# 기간이 200ms보다 크고 플랫폼이 'web'인 모든 행 찾기
complex_filter_df = df[(df['duration_ms'] > 200) & (df['platform'] == 'web')]
print("\n--- Complex Filter ---")
print(complex_filter_df)
```
**Note**: When combining conditions, you must use `&` (and), `|` (or), and wrap each condition in parentheses.
**참고**: 조건을 결합할 때 `&`(and), `|`(or)를 사용하고 각 조건을 괄호로 묶어야 합니다.

---

## 3. Grouping and Aggregation
## 3. 그룹화 및 집계

This is one of the most powerful features of Pandas. It's a three-step process: **Split, Apply, Combine**.
이것은 Pandas의 가장 강력한 기능 중 하나입니다. **분할, 적용, 결합**의 3단계 프로세스입니다.

Let's find the average duration and the number of actions for each user.
각 사용자의 평균 기간과 작업 수를 찾아보겠습니다.

```python
# Group the DataFrame by 'user_id'
# DataFrame을 'user_id'로 그룹화
grouped_by_user = df.groupby('user_id')

# Apply multiple aggregation functions at once
# 한 번에 여러 집계 함수 적용
user_stats = grouped_by_user.agg(
    average_duration=('duration_ms', 'mean'), # Calculate the mean of the duration_ms column
    # duration_ms 열의 평균 계산
    action_count=('action', 'count')      # Count the number of entries in the action column
    # action 열의 항목 수 계산
)

print(user_stats)
```

This would produce a new DataFrame:
그러면 새 DataFrame이 생성됩니다.
```
         average_duration  action_count
user_id                                
101                 100.0             1
102                 180.0             3
103                 120.0             1
104                 500.0             1
105                 300.0             1
```

## 4. Creating New Columns
## 4. 새 열 만들기

You can easily create new columns based on existing ones.
기존 열을 기반으로 새 열을 쉽게 만들 수 있습니다.

```python
# Convert duration from milliseconds to seconds
# 기간을 밀리초에서 초로 변환
df['duration_s'] = df['duration_ms'] / 1000

# Create a column based on a condition
# 조건을 기반으로 열 만들기
df['is_long_action'] = df['duration_ms'] > 250

print(df.head())
```

## Why is this Vibe Coding?
## 이것이 왜 Vibe 코딩인가요?

Imagine you have a log file from your crawler with millions of entries. How do you find the slowest endpoints or the most common errors?
수백만 개의 항목이 있는 크롤러의 로그 파일이 있다고 상상해 보십시오. 가장 느린 엔드포인트나 가장 일반적인 오류를 어떻게 찾습니까?

-   **Without Pandas**: You would have to write a complex Python script to read the file line by line, parse each line, use dictionaries to store counts and sums, and manually calculate averages. This would be slow to write and slow to run.
    **Pandas 없이**: 파일을 한 줄씩 읽고, 각 줄을 구문 분석하고, 사전을 사용하여 개수와 합계를 저장하고, 평균을 수동으로 계산하는 복잡한 파이썬 스크립트를 작성해야 합니다. 이것은 작성하는 데 시간이 오래 걸리고 실행하는 데 시간이 오래 걸립니다.
-   **With Pandas**: You can load the entire log file into a DataFrame with `pd.read_csv()` or `pd.read_json()`, and then use a few lines of expressive, high-performance code to get the answers you need.
    **Pandas 사용**: `pd.read_csv()` 또는 `pd.read_json()`을 사용하여 전체 로그 파일을 DataFrame으로 로드한 다음 몇 줄의 표현력 있고 고성능 코드를 사용하여 필요한 답변을 얻을 수 있습니다.

Pandas allows you to quickly explore, clean, and analyze data, turning raw information into actionable insights. This ability to quickly understand your system and your users is a core competency of a Vibe Coder.
Pandas를 사용하면 데이터를 빠르게 탐색, 정리 및 분석하여 원시 정보를 실행 가능한 통찰력으로 전환할 수 있습니다. 시스템과 사용자를 빠르게 이해하는 이 능력은 Vibe 코더의 핵심 역량입니다.