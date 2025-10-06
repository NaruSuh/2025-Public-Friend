# 01.01 - Basic Python for Beginners
# 01.01 - 초보자를 위한 기본 파이썬

This guide is for those who are completely new to programming or Python. We'll cover the absolute fundamentals needed to start your Vibe Coding journey.
이 가이드는 프로그래밍이나 파이썬을 처음 접하는 분들을 위한 것입니다. Vibe Coding 여정을 시작하는 데 필요한 절대적인 기본 사항을 다룹니다.

## Core Concepts
## 핵심 개념

1.  **Variables**: Named containers for storing data.
    **변수**: 데이터 저장을 위한 이름이 지정된 컨테이너입니다.
2.  **Data Types**: The type of data a variable can hold (e.g., text, numbers, lists).
    **데이터 유형**: 변수가 보유할 수 있는 데이터 유형입니다(예: 텍스트, 숫자, 목록).
3.  **Collections**: Ways to group multiple data items together (e.g., lists, dictionaries).
    **컬렉션**: 여러 데이터 항목을 함께 그룹화하는 방법입니다(예: 목록, 사전).
4.  **Control Flow**: How to make decisions and repeat actions in your code (e.g., `if` statements, `for` loops).
    **제어 흐름**: 코드에서 결정을 내리고 작업을 반복하는 방법입니다(예: `if` 문, `for` 루프).
5.  **Functions**: Reusable blocks of code that perform a specific task.
    **함수**: 특정 작업을 수행하는 재사용 가능한 코드 블록입니다.

---

## 1. Variables and Basic Data Types
## 1. 변수 및 기본 데이터 유형

Think of a variable as a labeled box where you can store something.
변수를 무언가를 저장할 수 있는 레이블이 붙은 상자라고 생각하십시오.

```python
# A variable named 'greeting' that holds a string (text)
# 문자열(텍스트)을 담는 'greeting'이라는 변수
greeting = "Hello, Vibe Coder!"

# A variable named 'project_year' that holds an integer (whole number)
# 정수(정수)를 담는 'project_year'라는 변수
project_year = 2025

# A variable named 'pi_approx' that holds a float (decimal number)
# 부동 소수점(소수)을 담는 'pi_approx'라는 변수
pi_approx = 3.14

# A variable named 'is_learning' that holds a boolean (True or False)
# 부울(참 또는 거짓)을 담는 'is_learning'이라는 변수
is_learning = True

# You can print the contents of a variable to the screen
# 변수의 내용을 화면에 인쇄할 수 있습니다.
print(greeting)
print(project_year)
```

## 2. Collections: Lists and Dictionaries
## 2. 컬렉션: 목록 및 사전

Often, you need to work with groups of data.
종종 데이터 그룹으로 작업해야 합니다.

### Lists
### 목록
A list is an ordered collection of items. You can access items by their position (index), which starts at 0.
목록은 순서가 있는 항목 모음입니다. 0에서 시작하는 위치(인덱스)로 항목에 액세스할 수 있습니다.

```python
# A list of strings
# 문자열 목록
tools = ["Git", "Python", "VSCode", "Docker"]

# Access the first item (index 0)
# 첫 번째 항목(인덱스 0)에 액세스
print(tools[0])  # Output: Git

# Add an item to the end of the list
# 목록 끝에 항목 추가
tools.append("FastAPI")
print(tools)

# Loop through all items in the list
# 목록의 모든 항목을 반복합니다.
for tool in tools:
    print(f"I am learning {tool}!")
```

### Dictionaries
### 사전
A dictionary is a collection of key-value pairs. It's like a real-world dictionary where you look up a word (the key) to find its definition (the value).
사전은 키-값 쌍의 모음입니다. 단어(키)를 찾아 정의(값)를 찾는 실제 사전과 같습니다.

```python
# A dictionary representing a project
# 프로젝트를 나타내는 사전
project = {
    "name": "Druid Full Auto",
    "language": "Python",
    "year": 2025,
    "is_awesome": True
}

# Access a value by its key
# 키로 값에 액세스
print(project["name"])  # Output: Druid Full Auto

# Add a new key-value pair
# 새 키-값 쌍 추가
project["status"] = "In Progress"
print(project)

# Loop through the keys and values
# 키와 값을 반복합니다.
for key, value in project.items():
    print(f"Project {key} is {value}")
```

---

## 3. Control Flow: `if` Statements and `for` Loops
## 3. 제어 흐름: `if` 문 및 `for` 루프

### `if` Statements
### `if` 문
`if` statements allow your code to make decisions.
`if` 문을 사용하면 코드가 결정을 내릴 수 있습니다.

```python
language = "Python"

if language == "Python":
    print("This is a Vibe Coding project!")
elif language == "Java":
    print("This is a different kind of project.")
else:
    print("What language is this?")
```

### `for` Loops
### `for` 루프
`for` loops allow you to repeat an action for each item in a collection.
`for` 루프를 사용하면 컬렉션의 각 항목에 대해 작업을 반복할 수 있습니다.

```python
# We already saw this with lists and dictionaries!
# 우리는 이미 목록과 사전에서 이것을 보았습니다!

# You can also loop a specific number of times with range()
# range()를 사용하여 특정 횟수만큼 반복할 수도 있습니다.
for i in range(5):  # Loops from 0 to 4
    print(f"This is loop number {i}")
```

---

## 4. Functions
## 4. 함수

A function is a named, reusable block of code that performs a specific action. Functions are the building blocks of any application.
함수는 특정 작업을 수행하는 이름이 지정된 재사용 가능한 코드 블록입니다. 함수는 모든 애플리케이션의 구성 요소입니다.

```python
# A simple function that takes one argument (name)
# 하나의 인수(이름)를 사용하는 간단한 함수
def greet(name):
    """This is a docstring. It explains what the function does."""
    return f"Hello, {name}! Welcome to Vibe Coding."

# Call the function and store its result in a variable
# 함수를 호출하고 그 결과를 변수에 저장합니다.
welcome_message = greet("Naru")
print(welcome_message)

# A function with a default argument
# 기본 인수가 있는 함수
def create_project(name, language="Python"):
    print(f"Creating project: {name} in {language}")

# Call the function with both arguments
# 두 인수를 모두 사용하여 함수 호출
create_project("My New App", "JavaScript")

# Call the function with only the required argument
# 필수 인수만 사용하여 함수 호출
create_project("My Vibe App") # language will default to "Python"
```

This is just the beginning. The key to learning is to **build things**. Take these concepts and try to write small scripts. For example:
이것은 시작에 불과합니다. 학습의 핵심은 **만드는 것**입니다. 이러한 개념을 가지고 작은 스크립트를 작성해 보십시오. 예를 들어:
-   A script that prints out your favorite tools from a list.
    목록에서 좋아하는 도구를 인쇄하는 스크립트입니다.
-   A script that takes your name as input and prints a personalized greeting.
    이름을 입력으로 받아 개인화된 인사말을 인쇄하는 스크립트입니다.

Happy coding!
즐거운 코딩 되세요!