# 08.01 - Data Analysis with Pandas and Vibe

Your `druid_full_auto` project scrapes data, but the ultimate goal is to derive insights from that data. This is where data analysis comes in. `pandas` is the cornerstone of data analysis in Python. This guide will walk you through the "Vibe" approach to data analysis: being question-driven, iterative, and focused on clear communication.

## Core Concepts of Vibe Data Analysis

1.  **Start with a Question, Not with the Data**: What are you trying to figure out? What decision are you trying to make? A clear question guides your entire analysis.
2.  **Data Cleaning is 80% of the Work**: Raw data is always messy. Your crawler data will have missing values, incorrect types, and inconsistencies. A robust cleaning process is essential.
3.  **Explore and Visualize**: Before you model, you must explore. Use summary statistics and visualizations to understand the shape, distribution, and relationships in your data.
4.  **Iterate and Refine**: Your first analysis will likely lead to more questions. Analysis is a cycle of questioning, exploring, and refining.
5.  **Communicate Clearly**: The final output of an analysis is not a number; it's a decision or a story. Use clear visualizations and simple language to communicate your findings.

---

## A Practical Walkthrough: Analyzing Your Crawler Data

Let's assume your crawler has produced an Excel file, `bids.xlsx`, with columns like `post_date`, `title`, `department`, `views`, and `has_attachment`.

**Goal/Question**: "Which departments post the most high-value bids, and when do they post them?" ("High-value" could be defined by views or other metrics).

### 1. Setup and Data Loading

We'll use `pandas` for data manipulation, `matplotlib` and `seaborn` for plotting.

```python
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Set some display options for better viewing
pd.set_option('display.max_columns', 50)
pd.set_option('display.width', 1000)

# Load the data
try:
    df = pd.read_excel("bids.xlsx")
    print("Data loaded successfully.")
    print(df.info())
except FileNotFoundError:
    print("Error: bids.xlsx not found. Please run the crawler first.")
    # Create a dummy dataframe for demonstration
    data = {'post_date': pd.to_datetime(['2025-09-01', '2025-09-02', None, '2025-09-03']),
            'title': ['Project A', 'Project B', 'Project C', 'Project D'],
            'department': ['Finance', 'IT', 'Finance', 'HR'],
            'views': [150, '500', 200, 'N/A'],
            'has_attachment': [True, False, True, True]}
    df = pd.DataFrame(data)

```

### 2. Data Cleaning and Preprocessing

This is the most critical step.

```python
# --- Step 2: Clean the data ---
print("\n--- Cleaning Data ---")

# Copy the dataframe to avoid modifying the original
df_clean = df.copy()

# a) Handle data types
# Convert 'post_date' to datetime, coercing errors to NaT (Not a Time)
df_clean['post_date'] = pd.to_datetime(df_clean['post_date'], errors='coerce')

# Convert 'views' to numeric, coercing errors to NaN (Not a Number)
df_clean['views'] = pd.to_numeric(df_clean['views'], errors='coerce')

# b) Handle missing values
print(f"\nMissing values before cleaning:\n{df_clean.isnull().sum()}")

# For 'views', a common strategy is to fill missing values with the median or mean.
# Median is generally safer as it's less affected by outliers.
median_views = df_clean['views'].median()
df_clean['views'].fillna(median_views, inplace=True)

# For 'post_date', we might not have a sensible default, so we can drop rows where it's missing.
df_clean.dropna(subset=['post_date'], inplace=True)

print(f"\nMissing values after cleaning:\n{df_clean.isnull().sum()}")

# c) Feature Engineering: Create new columns from existing ones.
# This is where you add your domain knowledge.
df_clean['post_weekday'] = df_clean['post_date'].dt.day_name()
df_clean['post_month'] = df_clean['post_date'].dt.month
df_clean['post_hour'] = df_clean['post_date'].dt.hour # If you have time information

# Define what "high value" means. Let's use views > 90th percentile.
high_view_threshold = df_clean['views'].quantile(0.90)
df_clean['is_high_value'] = df_clean['views'] > high_view_threshold

print("\nCleaned and enriched data sample:")
print(df_clean.head())
```

### 3. Exploratory Data Analysis (EDA)

Now that the data is clean, let's explore it.

```python
# --- Step 3: Exploratory Data Analysis ---
print("\n--- Exploring Data ---")

# a) Summary statistics for numeric columns
print("\nSummary statistics:")
print(df_clean[['views']].describe())

# b) Value counts for categorical columns
print("\nDepartment counts:")
print(df_clean['department'].value_counts())

# c) Grouping and Aggregations: This is the heart of analysis.
# Let's find the average views per department.
avg_views_by_dept = df_clean.groupby('department')['views'].mean().sort_values(ascending=False)
print("\nAverage views by department:")
print(avg_views_by_dept)

# Let's count the number of high-value bids per department.
high_value_counts = df_clean[df_clean['is_high_value']]['department'].value_counts()
print("\nHigh-value bid counts by department:")
print(high_value_counts)
```

### 4. Visualization for Communication

A plot is worth a thousand words. Use `seaborn` for beautiful and informative plots.

```python
# --- Step 4: Visualize the Findings ---
print("\n--- Generating Visualizations ---")
sns.set_theme(style="whitegrid")

# a) Which departments post the most bids?
plt.figure(figsize=(12, 6))
sns.countplot(y='department', data=df_clean, order=df_clean['department'].value_counts().index, palette='viridis')
plt.title('Total Number of Bids by Department')
plt.xlabel('Number of Bids')
plt.ylabel('Department')
plt.tight_layout()
plt.savefig("bids_by_department.png")
# plt.show()

# b) Which departments post the highest-view bids?
plt.figure(figsize=(12, 6))
sns.barplot(x=avg_views_by_dept.values, y=avg_views_by_dept.index, palette='plasma')
plt.title('Average Views by Department')
plt.xlabel('Average Views')
plt.ylabel('Department')
plt.tight_layout()
plt.savefig("avg_views_by_department.png")
# plt.show()

# c) When are bids posted during the week?
plt.figure(figsize=(10, 5))
weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
sns.countplot(x='post_weekday', data=df_clean, order=weekday_order, palette='magma')
plt.title('Bid Posting Frequency by Day of the Week')
plt.xlabel('Day of the Week')
plt.ylabel('Number of Bids')
plt.tight_layout()
plt.savefig("bids_by_weekday.png")
# plt.show()

print("\nVisualizations saved to .png files.")
```

### 5. Drawing Conclusions (The "Vibe" part)

Based on the analysis, you can now answer your original question.

**Example Conclusion**:
"Our analysis shows that while the **Finance department** posts the highest *volume* of bids, the **IT department** consistently posts bids with the highest *average views*, making them a key source of 'high-value' opportunities. Furthermore, the majority of all bids are posted between **Tuesday and Thursday**, with a significant drop-off on Mondays and Fridays. To maximize our chances of seeing high-value bids early, we should focus our attention on IT department postings from Tuesday to Thursday."

This conclusion is actionable, data-driven, and directly answers the initial question. This is the goal of any Vibe Data Analysis.
