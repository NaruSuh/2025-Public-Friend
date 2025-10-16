# 09 - System Design and Architecture
# 09 - 시스템 설계와 아키텍처

You've mastered building individual services. The next frontier is designing the *entire system* of services, data stores, and communication patterns that work together to solve a business problem. This is the discipline of System Design.
개별 서비스를 만드는 데 익숙해졌다면, 다음 단계는 여러 서비스와 데이터 저장소, 통신 패턴을 결합해 비즈니스 문제를 해결하는 *전체 시스템*을 설계하는 것입니다. 이것이 바로 시스템 설계입니다.

## Before You Begin
## 시작하기 전에
-   Refresh Level 1 architecture notes (caching, API design, databases) because system design stitches all of them together.
-   레벨 1에서 배운 캐싱, API 설계, 데이터베이스 노트를 다시 복습하세요. 시스템 설계는 이 모든 요소를 엮어야 합니다.
-   Keep a whiteboard app or paper nearby—sketching diagrams is mandatory.
-   화이트보드 앱이나 종이를 준비해 두세요. 다이어그램 스케치는 필수입니다.
-   Pick a reference product (e.g., your crawler platform) so every concept has a concrete anchor instead of feeling abstract.
-   기준이 될 제품(예: 크롤러 플랫폼)을 정해 개념을 추상적이지 않고 구체적으로 연결하세요.

## Level 2 Upgrade Goals
## 레벨 2 업그레이드 목표
1.  **Structure your design conversations** using a repeatable framework.
1.  **반복 가능한 프레임워크로 설계 대화를 구조화**합니다.
2.  **Quantify scale** with back-of-the-envelope math before proposing technology.
2.  **기술 제안 전 대략적인 계산으로 규모를 정량화**합니다.
3.  **Explain trade-offs** clearly so stakeholders understand why you made each architectural choice.
3.  **트레이드오프를 명확히 설명**해 이해관계자가 아키텍처 선택 이유를 이해하도록 합니다.

## Core Concepts
## 핵심 개념

1.  **The System Design Interview Framework**: A structured way to approach a design problem, commonly used in interviews at top tech companies but also an excellent real-world tool.
1.  **시스템 설계 인터뷰 프레임워크**: 주요 기술 기업 인터뷰에서 쓰이지만 실전에서도 유용한 구조화된 접근법입니다.
2.  **Scalability Patterns**: Fundamental architectural patterns for building systems that can handle massive load.
2.  **확장성 패턴**: 대규모 부하를 처리할 수 있는 시스템을 위한 기본 아키텍처 패턴입니다.
3.  **Data-Intensive Application Design**: Principles for building systems where data is the primary challenge (volume, velocity, or variety).
3.  **데이터 집약형 애플리케이션 설계**: 데이터의 양, 속도, 다양성이 핵심 과제인 시스템을 위한 원칙입니다.
4.  **Trade-offs**: System design is the art of making trade-offs. There is no single "right" answer, only answers that are more or less appropriate for a given set of constraints. The most common trade-off is between **consistency**, **availability**, and **partition tolerance** (the CAP Theorem).
4.  **트레이드오프**: 시스템 설계는 균형의 예술입니다. 완벽한 답은 없고 주어진 제약에 더 적합한 답만 존재합니다. 가장 흔한 균형은 **일관성**, **가용성**, **분할 내성**(CAP 정리) 사이에서 이뤄집니다.

---

## 1. A Framework for System Design Problems
## 1. 시스템 설계 문제를 위한 프레임워크

When faced with a vague prompt like "Design a URL shortener" or "Design the Twitter timeline," use this framework to structure your thinking.
“URL 단축기를 설계하라”, “트위터 타임라인을 설계하라” 같은 모호한 문제를 만났을 때 아래 프레임워크로 사고를 구조화하세요.

1.  **Step 1: Requirements Clarification (Functional and Non-Functional)**
1.  **1단계: 요구사항 명확화(기능/비기능)**
    -   **Functional**: What must the system *do*? (e.g., "Users can post tweets," "Users can see a timeline of tweets from people they follow.")
    -   **기능 요구**: 시스템이 무엇을 해야 하는가? (예: “사용자는 트윗을 올릴 수 있어야 한다.” “팔로우한 사람들의 타임라인을 볼 수 있어야 한다.”)
    -   **Non-Functional**: What are the system's *properties*? This is the crucial part.
    -   **비기능 요구**: 시스템이 어떤 특성을 가져야 하는가? 매우 중요합니다.
        -   **Scalability**: How many users? How many requests per second?
        -   **확장성**: 사용자 수, 초당 요청 수는 얼마인가?
        -   **Availability**: Does the system need to be highly available (e.g., 99.99% uptime)?
        -   **가용성**: 높은 가용성(예: 99.99% 업타임)이 필요한가?
        -   **Latency**: How fast must responses be? (e.g., p99 latency < 200ms).
        -   **지연 시간**: 응답 속도는 어느 정도여야 하는가?(예: p99 < 200ms)
        -   **Consistency**: Is it okay if a user sees slightly stale data? (e.g., Eventual Consistency vs. Strong Consistency).
        -   **일관성**: 약간 오래된 데이터를 보여도 되는가?(최종 일관성 vs. 강한 일관성)
        -   **Durability**: Must data, once written, never be lost?
        -   **내구성**: 기록된 데이터가 절대 사라지면 안 되는가?

2.  **Step 2: Back-of-the-Envelope Estimation**
2.  **2단계: 대략적 규모 추산**
    -   Do some quick math to estimate the scale. This will inform your technology choices.
    -   간단한 계산으로 규모를 추정해 기술 선택에 참고하세요.
    -   *Example for Twitter*: 300M daily active users, 2 tweets per user per day -> ~600M tweets/day. 600M / 86400s -> ~7000 writes per second (QPS). If a user follows 100 people, the read QPS for timelines will be much higher.
    -   *예시*: 트위터는 일일 활성 사용자 3억 명 × 하루 2트윗 ≈ 6억 트윗/일 → 초당 약 7000건 쓰기. 사용자가 평균 100명을 팔로우한다면 읽기 QPS는 훨씬 높아집니다.

3.  **Step 3: High-Level System Diagram (The "Boxes and Arrows")**
3.  **3단계: 고수준 시스템 다이어그램(상자와 화살표)**
    -   Draw the main components: Clients (web/mobile), Load Balancers, Web Servers (API), Databases, Caches, etc.
    -   주요 구성 요소(웹·모바일 클라이언트, 로드 밸런서, 웹 서버, 데이터베이스, 캐시 등)를 그립니다.
    -   Show the flow of a request through the system.
    -   요청이 시스템을 통과하는 흐름을 표현합니다.

4.  **Step 4: Deep Dive into Components**
4.  **4단계: 구성요소 상세 설계**
    -   **API Design**: What are the key API endpoints?
    -   **API 설계**: 핵심 엔드포인트는 무엇인가?
    -   **Database Schema / Data Model**: How will you store the data? SQL vs. NoSQL? Why? (This is often the core of the problem).
    -   **데이터베이스 스키마/모델**: 데이터를 어떻게 저장할 것인가? SQL인가 NoSQL인가? 이유는 무엇인가? (문제의 핵심인 경우가 많습니다.)
    -   **Scalability and Bottlenecks**: Identify potential bottlenecks. How will you scale the web servers? How will you scale the database (e.g., read replicas, sharding)? Where will you add caching?
    -   **확장성과 병목**: 잠재적 병목을 식별하고, 웹 서버와 데이터베이스(읽기 복제, 샤딩 등)를 어떻게 확장하며, 캐시는 어디에 둘지 결정합니다.

5.  **Step 5: Justify and Articulate Trade-offs**
5.  **5단계: 트레이드오프 정당화**
    -   For every choice, explain the "why." Why did you choose Redis for caching? Why a NoSQL database for storing tweets?
    -   모든 선택에 이유를 명확히 하세요. 왜 캐시에 Redis를 썼는지, 왜 트윗 저장에 NoSQL을 택했는지 설명합니다.
    -   Discuss the trade-offs. "I chose eventual consistency for the timeline to achieve higher availability and lower latency. It's acceptable if a user sees a new tweet a few seconds late."
    -   트레이드오프를 논의합니다. “타임라인에 최종 일관성을 선택해 가용성과 지연을 개선했습니다. 몇 초 늦게 새 트윗을 보여줘도 괜찮습니다.”

**Practice:** apply this five-step framework to your current product. Write a one-page design doc and share it with a friend for critique—can they follow your reasoning?
**실습:** 현재 제품에 이 5단계 프레임워크를 적용해 한 페이지 분량의 설계 문서를 작성하고 친구에게 공유해 보세요. 상대가 논리를 따라올 수 있는지 확인하세요.

---

## 2. Key Scalability Patterns
## 2. 핵심 확장성 패턴

-   **Load Balancing**: Distributing incoming traffic across multiple servers.
-   **로드 밸런싱**: 들어오는 트래픽을 여러 서버에 분산합니다.
-   **Caching**:
-   **캐싱**:
    -   **Client-side**: Caching in the browser.
    -   **클라이언트 측**: 브라우저에서 캐시 사용.
    -   **CDN (Content Delivery Network)**: Caching static assets (images, JS, CSS) at edge locations close to users.
    -   **CDN**: 사용자와 가까운 엣지에서 정적 자산을 캐시합니다.
    -   **Application-level Cache (e.g., Redis)**: Caching database query results, API responses, etc.
    -   **애플리케이션 레벨 캐시**(예: Redis): 데이터베이스 쿼리 결과, API 응답 등을 캐시합니다.
-   **Database Scaling**:
-   **데이터베이스 확장**:
    -   **Read Replicas**: Create copies of your database that are used only for read queries. This separates read and write traffic.
    -   **읽기 복제본**: 읽기 전용 복제본을 만들어 읽기와 쓰기 트래픽을 분리합니다.
    -   **Sharding (Partitioning)**: Splitting your database across multiple machines. A common strategy is to shard by user ID, where all data for a given user lives on a specific shard. This is complex but allows for near-infinite horizontal scaling.
    -   **샤딩**: 데이터베이스를 여러 머신에 분할합니다. 사용자 ID로 샤딩하는 전략이 흔하며, 복잡하지만 거의 무한한 수평 확장을 가능케 합니다.
-   **Asynchronism**: Using message queues (like RabbitMQ or Kafka) to decouple services and handle background processing.
-   **비동기 처리**: RabbitMQ, Kafka 같은 메시지 큐로 서비스를 분리하고 백그라운드 작업을 처리합니다.

---

## 3. Designing for Data-Intensive Applications
## 3. 데이터 집약 시스템 설계하기

Martin Kleppmann's book "Designing Data-Intensive Applications" is considered the bible on this topic. The key takeaways are:
마틴 클렙만의 『Designing Data-Intensive Applications』는 이 분야의 바이블로 여겨집니다. 핵심 요약은 다음과 같습니다.

-   **Reliability**: The system should work correctly, even in the face of hardware or software faults.
-   **신뢰성**: 하드웨어나 소프트웨어 오류에도 시스템이 정확히 동작해야 합니다.
-   **Scalability**: The system should be able to handle growing load.
-   **확장성**: 증가하는 부하를 감당할 수 있어야 합니다.
-   **Maintainability**: The system should be easy for engineers to operate and evolve.
-   **유지보수성**: 엔지니어가 운영하고 발전시키기 쉬워야 합니다.

The book provides a deep dive into the trade-offs between different data storage technologies (SQL, NoSQL, graph databases), replication methods (single-leader, multi-leader, leaderless), and data processing models (batch vs. stream).
이 책은 다양한 데이터 저장 기술(SQL, NoSQL, 그래프 DB), 복제 방식(싱글 리더, 다중 리더, 리더리스), 데이터 처리 모델(배치 vs. 스트림) 간의 트레이드오프를 깊이 있게 다룹니다.

### Example: The Twitter Timeline Problem
### 예시: 트위터 타임라인 문제

This is a classic system design problem that illustrates trade-offs.
트레이드오프를 보여주는 대표적인 시스템 설계 문제입니다.

-   **Initial Idea (The "Fan-out on Read" approach)**:
-   **초기 아이디어(읽기 시 팬아웃)**:
    1.  When a user requests their timeline, find all the people they follow.
    1.  사용자가 타임라인을 요청하면 팔로우한 모든 사람을 찾습니다.
    2.  Go to each of those users' tweet tables and get their recent tweets.
    2.  각 사용자의 트윗 테이블에서 최신 트윗을 가져옵니다.
    3.  Merge them all and sort by time.
    3.  모두 합쳐 시간순으로 정렬합니다.
    -   **Problem**: This is very expensive at read time. For a user following hundreds of people, this is too slow.
    -   **문제점**: 읽기 시 비용이 너무 커져 수백 명을 팔로우하는 사용자는 타임라인이 매우 느려집니다.

-   **The "Fan-out on Write" approach (what Twitter actually does)**:
-   **쓰기 시 팬아웃(트위터의 실제 방식)**:
    1.  Each user has a dedicated "timeline" cache (e.g., a Redis list).
    1.  각 사용자는 전용 “타임라인” 캐시(예: Redis 리스트)를 가집니다.
    2.  When a user tweets (the "write"), a background job finds all of their followers.
    2.  사용자가 트윗하면 백그라운드 작업이 모든 팔로워를 찾습니다.
    3.  The new tweet is then pushed into the timeline cache of *each follower*.
    3.  새 트윗을 *모든 팔로워*의 타임라인 캐시에 푸시합니다.
    -   **Benefit**: Reading the timeline is now incredibly fast. It's just fetching a pre-computed list from Redis.
    -   **장점**: 타임라인 읽기가 매우 빨라집니다. 미리 계산해둔 리스트를 Redis에서 가져오면 됩니다.
    -   **Trade-off**: Writes are much more expensive. A celebrity with millions of followers creates a "write storm." Twitter handles this with a hybrid approach, where celebrity tweets are not fanned out and are instead merged in at read time.
    -   **트레이드오프**: 쓰기 비용이 크게 늘어 유명인의 트윗은 “쓰기 폭풍”을 일으킵니다. 트위터는 하이브리드 방식을 사용해 유명인 트윗은 읽기 시 병합합니다.

System design is a vast topic that requires combining knowledge from all the previous levels. It's less about knowing specific tools and more about understanding fundamental principles and being able to reason about the trade-offs between them. The best way to learn is to study classic system design problems and practice applying the framework yourself.
시스템 설계는 이전 단계에서 배운 모든 지식을 통합해야 하는 방대한 주제입니다. 특정 도구를 아는 것보다 기본 원리를 이해하고 그 사이의 트레이드오프를 논리적으로 설명할 수 있는지가 더 중요합니다. 고전적인 시스템 설계 문제를 공부하고 프레임워크를 직접 적용해 보는 것이 가장 좋은 학습 방법입니다.

## Going Further
## 더 나아가기
-   Record yourself walking through a design problem in 30 minutes, then watch it back to spot missing steps or weak explanations.
-   30분 안에 설계 문제를 풀어 설명하는 모습을 녹화했다가 다시 보며 빠뜨린 단계나 부족한 설명을 찾아보세요.
-   Study real-world architecture blogs (Netflix, Uber, Pinterest) and map their systems onto the framework above.
-   Netflix, Uber, Pinterest 같은 실제 아키텍처 블로그를 읽고 위 프레임워크에 맞춰 구조를 매핑해 보세요.
-   Lead a mini design review with teammates using a smaller feature (e.g., notification service) to practice productive feedback loops.
-   알림 서비스 같은 소규모 기능을 주제로 팀원들과 미니 설계 리뷰를 진행해 생산적인 피드백 루프를 연습하세요.
