# 09 - System Design and Architecture

You've mastered building individual services. The next frontier is designing the *entire system* of services, data stores, and communication patterns that work together to solve a business problem. This is the discipline of System Design.

## Core Concepts

1.  **The System Design Interview Framework**: A structured way to approach a design problem, commonly used in interviews at top tech companies but also an excellent real-world tool.
2.  **Scalability Patterns**: Fundamental architectural patterns for building systems that can handle massive load.
3.  **Data-Intensive Application Design**: Principles for building systems where data is the primary challenge (volume, velocity, or variety).
4.  **Trade-offs**: System design is the art of making trade-offs. There is no single "right" answer, only answers that are more or less appropriate for a given set of constraints. The most common trade-off is between **consistency**, **availability**, and **partition tolerance** (the CAP Theorem).

---

## 1. A Framework for System Design Problems

When faced with a vague prompt like "Design a URL shortener" or "Design the Twitter timeline," use this framework to structure your thinking.

1.  **Step 1: Requirements Clarification (Functional and Non-Functional)**
    -   **Functional**: What must the system *do*? (e.g., "Users can post tweets," "Users can see a timeline of tweets from people they follow.")
    -   **Non-Functional**: What are the system's *properties*? This is the crucial part.
        -   **Scalability**: How many users? How many requests per second?
        -   **Availability**: Does the system need to be highly available (e.g., 99.99% uptime)?
        -   **Latency**: How fast must responses be? (e.g., p99 latency < 200ms).
        -   **Consistency**: Is it okay if a user sees slightly stale data? (e.g., Eventual Consistency vs. Strong Consistency).
        -   **Durability**: Must data, once written, never be lost?

2.  **Step 2: Back-of-the-Envelope Estimation**
    -   Do some quick math to estimate the scale. This will inform your technology choices.
    -   *Example for Twitter*: 300M daily active users, 2 tweets per user per day -> ~600M tweets/day. 600M / 86400s -> ~7000 writes per second (QPS). If a user follows 100 people, the read QPS for timelines will be much higher.

3.  **Step 3: High-Level System Diagram (The "Boxes and Arrows")**
    -   Draw the main components: Clients (web/mobile), Load Balancers, Web Servers (API), Databases, Caches, etc.
    -   Show the flow of a request through the system.

4.  **Step 4: Deep Dive into Components**
    -   **API Design**: What are the key API endpoints?
    -   **Database Schema / Data Model**: How will you store the data? SQL vs. NoSQL? Why? (This is often the core of the problem).
    -   **Scalability and Bottlenecks**: Identify potential bottlenecks. How will you scale the web servers? How will you scale the database (e.g., read replicas, sharding)? Where will you add caching?

5.  **Step 5: Justify and Articulate Trade-offs**
    -   For every choice, explain the "why." Why did you choose Redis for caching? Why a NoSQL database for storing tweets?
    -   Discuss the trade-offs. "I chose eventual consistency for the timeline to achieve higher availability and lower latency. It's acceptable if a user sees a new tweet a few seconds late."

---

## 2. Key Scalability Patterns

-   **Load Balancing**: Distributing incoming traffic across multiple servers.
-   **Caching**:
    -   **Client-side**: Caching in the browser.
    -   **CDN (Content Delivery Network)**: Caching static assets (images, JS, CSS) at edge locations close to users.
    -   **Application-level Cache (e.g., Redis)**: Caching database query results, API responses, etc.
-   **Database Scaling**:
    -   **Read Replicas**: Create copies of your database that are used only for read queries. This separates read and write traffic.
    -   **Sharding (Partitioning)**: Splitting your database across multiple machines. A common strategy is to shard by user ID, where all data for a given user lives on a specific shard. This is complex but allows for near-infinite horizontal scaling.
-   **Asynchronism**: Using message queues (like RabbitMQ or Kafka) to decouple services and handle background processing.

---

## 3. Designing for Data-Intensive Applications

Martin Kleppmann's book "Designing Data-Intensive Applications" is considered the bible on this topic. The key takeaways are:

-   **Reliability**: The system should work correctly, even in the face of hardware or software faults.
-   **Scalability**: The system should be able to handle growing load.
-   **Maintainability**: The system should be easy for engineers to operate and evolve.

The book provides a deep dive into the trade-offs between different data storage technologies (SQL, NoSQL, graph databases), replication methods (single-leader, multi-leader, leaderless), and data processing models (batch vs. stream).

### Example: The Twitter Timeline Problem

This is a classic system design problem that illustrates trade-offs.

-   **Initial Idea (The "Fan-out on Read" approach)**:
    1.  When a user requests their timeline, find all the people they follow.
    2.  Go to each of those users' tweet tables and get their recent tweets.
    3.  Merge them all and sort by time.
    -   **Problem**: This is very expensive at read time. For a user following hundreds of people, this is too slow.

-   **The "Fan-out on Write" approach (what Twitter actually does)**:
    1.  Each user has a dedicated "timeline" cache (e.g., a Redis list).
    2.  When a user tweets (the "write"), a background job finds all of their followers.
    3.  The new tweet is then pushed into the timeline cache of *each follower*.
    -   **Benefit**: Reading the timeline is now incredibly fast. It's just fetching a pre-computed list from Redis.
    -   **Trade-off**: Writes are much more expensive. A celebrity with millions of followers creates a "write storm." Twitter handles this with a hybrid approach, where celebrity tweets are not fanned out and are instead merged in at read time.

System design is a vast topic that requires combining knowledge from all the previous levels. It's less about knowing specific tools and more about understanding fundamental principles and being able to reason about the trade-offs between them. The best way to learn is to study classic system design problems and practice applying the framework yourself.
