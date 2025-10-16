# 07.01 - Web Application Security Essentials
# 07.01 - 웹 애플리케이션 보안 필수 사항

Security is not a feature; it's a fundamental requirement. A single vulnerability can compromise your entire system and your users' data. A Vibe Coder builds security into their workflow from the very beginning. This guide covers the most common web vulnerabilities and how to prevent them.
보안은 기능이 아닙니다. 근본적인 요구 사항입니다. 단일 취약점은 전체 시스템과 사용자 데이터를 손상시킬 수 있습니다. Vibe 코더는 처음부터 워크플로에 보안을 구축합니다. 이 가이드는 가장 일반적인 웹 취약점과 이를 방지하는 방법을 다룹니다.

This guide is based on the **OWASP Top 10**, a standard awareness document for web application security.
이 가이드는 웹 애플리케이션 보안에 대한 표준 인식 문서인 **OWASP Top 10**을 기반으로 합니다.

## 1. Injection (e.g., SQL Injection)
## 1. 주입(예: SQL 주입)

**What it is**: An attacker sends malicious data to your application, which is then interpreted and executed as a command or query. The most famous example is SQL Injection.
**정의**: 공격자가 애플리케이션에 악성 데이터를 보내면 해당 데이터가 명령이나 쿼리로 해석되어 실행됩니다. 가장 유명한 예는 SQL 주입입니다.

**Bad (Vulnerable) Code**:
**나쁜 (취약한) 코드**:
```python
# NEVER DO THIS
# 절대 이렇게 하지 마세요
def get_user(email: str):
    query = f"SELECT * FROM users WHERE email = '{email}'" # The email is directly put into the query string
    # 이메일이 쿼리 문자열에 직접 삽입됩니다.
    db.execute(query)
```
An attacker could provide the email `' OR 1=1; --`. The final query would become `SELECT * FROM users WHERE email = '' OR 1=1; --'`, which would return all users in the database.
공격자는 `' OR 1=1; --` 이메일을 제공할 수 있습니다. 최종 쿼리는 `SELECT * FROM users WHERE email = '' OR 1=1; --'`이 되어 데이터베이스의 모든 사용자를 반환합니다.

**How to Prevent It (The Vibe Way)**:
**예방 방법(Vibe 방식)**:
-   **Use an ORM with Parameterized Queries**: This is the most important defense. Libraries like SQLAlchemy automatically and safely separate the query logic from the user-provided data.
    **매개변수화된 쿼리와 함께 ORM 사용**: 이것이 가장 중요한 방어책입니다. SQLAlchemy와 같은 라이브러리는 쿼리 로직을 사용자가 제공한 데이터와 자동으로 안전하게 분리합니다.
    ```python
    # SQLAlchemy does this correctly by default
    # SQLAlchemy는 기본적으로 이 작업을 올바르게 수행합니다.
    def get_user(db: Session, email: str):
        # The ORM creates a parameterized query. The email is treated as data, not a command.
        # ORM은 매개변수화된 쿼리를 생성합니다. 이메일은 명령이 아닌 데이터로 처리됩니다.
        return db.query(User).filter(User.email == email).first()
    ```

## 2. Broken Authentication
## 2. 손상된 인증

**What it is**: Flaws in how you manage user identity, authentication, and sessions. This can allow an attacker to impersonate legitimate users.
**정의**: 사용자 신원, 인증 및 세션을 관리하는 방법의 결함입니다. 이를 통해 공격자는 합법적인 사용자를 사칭할 수 있습니다.

**How to Prevent It**:
**예방 방법**:
-   **Never Store Passwords in Plain Text**: Always hash and salt passwords using a strong, modern algorithm like **bcrypt** or **Argon2**.
    **비밀번호를 일반 텍스트로 저장하지 마십시오**: 항상 **bcrypt** 또는 **Argon2**와 같은 강력하고 현대적인 알고리즘을 사용하여 비밀번호를 해시하고 솔트 처리하십시오.
    ```python
    from passlib.context import CryptContext

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def get_password_hash(password):
        return pwd_context.hash(password)

    def verify_password(plain_password, hashed_password):
        return pwd_context.verify(plain_password, hashed_password)
    ```
-   **Implement Rate Limiting**: Prevent brute-force attacks on your login endpoints.
    **속도 제한 구현**: 로그인 엔드포인트에 대한 무차별 대입 공격을 방지합니다.
-   **Use Secure Session Management**: Don't roll your own. Use stateless JWTs or a framework's built-in, secure session handling.
    **안전한 세션 관리 사용**: 직접 만들지 마십시오. 상태 비저장 JWT 또는 프레임워크의 내장된 안전한 세션 처리를 사용하십시오.

## 3. Sensitive Data Exposure
## 3. 민감한 데이터 노출

**What it is**: Failing to properly protect sensitive data, both in transit (over the network) and at rest (in the database).
**정의**: 전송 중(네트워크를 통해) 및 저장 시(데이터베이스에서) 민감한 데이터를 제대로 보호하지 못하는 것입니다.

**How to Prevent It**:
**예방 방법**:
-   **Use HTTPS Everywhere**: Encrypt all data in transit with TLS. In production, your load balancer or reverse proxy (like Nginx) should handle this.
    **어디서나 HTTPS 사용**: 전송 중인 모든 데이터를 TLS로 암호화합니다. 프로덕션에서는 로드 밸런서나 리버스 프록시(예: Nginx)가 이를 처리해야 합니다.
-   **Don't Log Sensitive Data**: Never log passwords, API keys, or credit card numbers.
    **민감한 데이터를 기록하지 마십시오**: 비밀번호, API 키 또는 신용카드 번호를 절대 기록하지 마십시오.
-   **Encrypt Data at Rest**: For extremely sensitive data, consider encrypting it even in the database.
    **저장 데이터 암호화**: 매우 민감한 데이터의 경우 데이터베이스에서도 암호화하는 것을 고려하십시오.
-   **Minimize Data Exposure**: Only return the data that the client absolutely needs. For example, never send the user's `hashed_password` in an API response. Use Pydantic response models to control what data is serialized.
    **데이터 노출 최소화**: 클라이언트가 절대적으로 필요한 데이터만 반환합니다. 예를 들어, API 응답에 사용자의 `hashed_password`를 절대 보내지 마십시오. Pydantic 응답 모델을 사용하여 직렬화되는 데이터를 제어합니다.

## 4. Insecure Design
## 4. 안전하지 않은 설계

**What it is**: A new category in the 2021 OWASP Top 10, this refers to flaws in the design and architecture of your application. Security needs to be a consideration from the beginning.
**정의**: 2021 OWASP Top 10의 새로운 카테고리로, 애플리케이션의 설계 및 아키텍처의 결함을 의미합니다. 보안은 처음부터 고려해야 합니다.

**How to Prevent It**:
**예방 방법**:
-   **Threat Modeling**: For a new feature, think like an attacker. What are the different ways this feature could be abused? What are the assets we need to protect?
    **위협 모델링**: 새로운 기능에 대해 공격자처럼 생각하십시오. 이 기능이 악용될 수 있는 다양한 방법은 무엇입니까? 보호해야 할 자산은 무엇입니까?
-   **Principle of Least Privilege**: A user or a service should only have the minimum level of access or permissions that it needs to perform its function.
    **최소 권한의 원칙**: 사용자나 서비스는 기능을 수행하는 데 필요한 최소한의 액세스 수준이나 권한만 가져야 합니다.
-   **Defense in Depth**: Don't rely on a single security control. Use multiple layers of defense (e.g., input validation, ORM, firewall, authentication).
    **심층 방어**: 단일 보안 제어에 의존하지 마십시오. 여러 계층의 방어(예: 입력 유효성 검사, ORM, 방화벽, 인증)를 사용하십시오.

## 5. Security Misconfiguration
## 5. 보안 구성 오류

**What it is**: Failing to implement all security controls, or implementing them incorrectly. This includes things like:
**정의**: 모든 보안 제어를 구현하지 못하거나 잘못 구현하는 것입니다. 여기에는 다음과 같은 것들이 포함됩니다.
-   Running with debug mode enabled in production.
    프로덕션에서 디버그 모드를 활성화한 상태로 실행합니다.
-   Having verbose error messages that leak information about your stack.
    스택에 대한 정보를 유출하는 장황한 오류 메시지가 있습니다.
-   Not changing default passwords for admin accounts.
    관리자 계정의 기본 비밀번호를 변경하지 않습니다.
-   Leaving cloud storage buckets publicly accessible.
    클라우드 스토리지 버킷을 공개적으로 액세스할 수 있도록 둡니다.

**How to Prevent It**:
**예방 방법**:
-   **Automate Your Deployments**: Use CI/CD and Infrastructure as Code (IaC) to create a repeatable, secure deployment process. This reduces the risk of manual configuration errors.
    **배포 자동화**: CI/CD 및 코드형 인프라(IaC)를 사용하여 반복 가능하고 안전한 배포 프로세스를 만듭니다. 이렇게 하면 수동 구성 오류의 위험이 줄어듭니다.
-   **Use Separate Configurations**: Have different configuration files or environment variables for development, staging, and production.
    **별도 구성 사용**: 개발, 스테이징 및 프로덕션을 위한 다른 구성 파일이나 환경 변수를 사용합니다.
-   **Regularly Scan and Audit**: Use automated tools to scan your dependencies for known vulnerabilities (`pip-audit`, `Snyk`, GitHub Dependabot) and your infrastructure for misconfigurations.
    **정기적으로 스캔 및 감사**: 자동화된 도구를 사용하여 알려진 취약점(`pip-audit`, `Snyk`, GitHub Dependabot)에 대해 종속성을 스캔하고 잘못된 구성에 대해 인프라를 스캔합니다.

Security is a continuous process, not a one-time checklist. By integrating these principles into your daily development habits, you build a strong security posture that protects your application and your users. This is the Vibe Coder way.
보안은 일회성 체크리스트가 아니라 지속적인 프로세스입니다. 이러한 원칙을 일상적인 개발 습관에 통합함으로써 애플리케이션과 사용자를 보호하는 강력한 보안 태세를 구축합니다. 이것이 Vibe 코더의 방식입니다.