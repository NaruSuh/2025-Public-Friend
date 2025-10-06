# 07 - Security - Lv.2: Proactive Security and DevSecOps
# 07 - 보안 - Lv.2: 선제적 보안과 DevSecOps

You've mastered the basics of securing your application. Level 2 is about shifting from a defensive posture to a proactive one. This means integrating security into every step of your development lifecycle (DevSecOps) and adopting advanced security practices.
애플리케이션 보안의 기초를 익혔다면, 레벨 2에서는 수동적인 방어에서 벗어나 선제적으로 움직여야 합니다. 즉, 개발 생애주기의 모든 단계에 보안을 통합(DevSecOps)하고 고급 보안 기법을 도입한다는 뜻입니다.

## Before You Begin
## 시작하기 전에
-   Revisit the Level 1 security checklist and ensure items like HTTPS everywhere, input validation, and secret management are already in place.
-   레벨 1의 보안 체크리스트를 다시 확인하여 HTTPS 적용, 입력 검증, 시크릿 관리 등이 모두 갖춰져 있는지 점검하세요.
-   Enable Docker Desktop or another container runtime—you’ll run security scanners and Falco locally while learning.
-   학습 중 보안 스캐너와 Falco를 로컬에서 실행할 수 있도록 Docker Desktop 등 컨테이너 런타임을 준비하세요.
-   Create a private wiki or README where you can record threat models, scanner output, and mitigation decisions as you go.
-   위협 모델, 스캐너 결과, 완화 결정을 기록할 개인 위키나 README를 만들어 두세요.

## Level 2 Upgrade Goals
## 레벨 2 업그레이드 목표
1.  **Make security continuous:** every commit, build, and deploy should run automated security controls.
1.  **보안의 상시화**: 커밋, 빌드, 배포마다 자동화된 보안 검사를 실행합니다.
2.  **Design first, defend first:** use threat modeling to influence architecture before code exists.
2.  **설계 단계에서 방어 설계**: 코드 작성 전에 위협 모델링으로 아키텍처에 보안을 반영합니다.
3.  **Monitor the runtime:** detect and respond to attacks that slip past your preventative measures.
3.  **런타임 모니터링**: 예방 조치를 우회한 공격을 감지하고 대응합니다.

## Core Concepts
## 핵심 개념

1.  **DevSecOps**: The philosophy of "shifting left" on security. Instead of security being a final gate before release, it's an automated, integral part of the development process.
1.  **DevSecOps**: 보안을 개발 초기 단계로 “이동”시키는 철학으로, 보안을 출시 직전의 마지막 관문이 아니라 개발 과정에 자동으로 녹여 넣습니다.
2.  **Threat Modeling**: A structured process for identifying potential threats and vulnerabilities in your system *before* you write any code.
2.  **위협 모델링**: 코드를 작성하기 전에 시스템의 잠재적 위협과 취약점을 구조적으로 식별하는 과정입니다.
3.  **Identity and Access Management (IAM)**: Moving beyond simple user authentication to a centralized and fine-grained control system for both users and services.
3.  **IAM(신원 및 접근 관리)**: 단순 사용자 인증을 넘어 사용자와 서비스 모두를 세밀하게 제어하는 중앙화 시스템입니다.
4.  **Runtime Security**: Detecting and responding to threats in your running, production environment.
4.  **런타임 보안**: 운영 중인 환경에서 위협을 감지하고 대응하는 역량입니다.

---

## 1. Threat Modeling: Thinking Like an Attacker
## 1. 위협 모델링: 공격자처럼 생각하기

Threat modeling is a proactive exercise you should do at the design stage of any new feature or service. A common framework is **STRIDE**:
위협 모델링은 새로운 기능이나 서비스를 설계할 때 반드시 수행해야 할 선제적 활동입니다. 대표적인 프레임워크는 **STRIDE**입니다.

-   **S**poofing: Can an attacker pretend to be someone or something they're not? (e.g., impersonating another user).
-   **S**poofing: 공격자가 다른 사용자로 위장할 수 있는가?
-   **T**ampering: Can an attacker modify data in transit or at rest? (e.g., changing the price of an item in an API call).
-   **T**ampering: 데이터가 전송되거나 저장될 때 조작될 수 있는가?
-   **R**epudiation: Can a user deny having performed an action? (e.g., "I never authorized that payment!").
-   **R**epudiation: 사용자가 수행한 행동을 부인할 수 있는가?
-   **I**nformation Disclosure: Can an attacker access data they shouldn't? (e.g., leaking user profiles).
-   **I**nformation Disclosure: 공격자가 접근해서는 안 될 데이터를 볼 수 있는가?
-   **D**enial of Service (DoS): Can an attacker crash or disable your service? (e.g., by sending a malformed request that causes an unhandled exception).
-   **D**enial of Service: 공격자가 서비스 장애를 일으킬 수 있는가?
-   **E**levation of Privilege: Can a regular user gain admin privileges?
-   **E**levation of Privilege: 일반 사용자가 관리자 권한을 획득할 수 있는가?

**How to do it**:
**진행 방법**:
1.  Draw a diagram of your system, showing user entry points, services, and data stores.
1.  시스템 다이어그램을 그려 사용자 진입점, 서비스, 데이터 저장소를 표시합니다.
2.  For each component and data flow, go through the STRIDE checklist and brainstorm potential attacks.
2.  각 구성 요소와 데이터 흐름에 STRIDE 체크리스트를 적용해 가능한 공격을 브레인스토밍합니다.
3.  For each threat, identify potential mitigations (e.g., "To prevent tampering with payment data, we will sign the payload with a secret key").
3.  위협마다 완화 방안을 정의합니다(예: 결제 데이터 조작 방지를 위해 페이로드에 서명을 추가).
4.  Prioritize the threats and turn the mitigations into development tasks.
4.  위협의 우선순위를 정하고 완화책을 개발 작업으로 전환합니다.

**Practice:** run a threat-modeling workshop with yourself (or a teammate) before shipping the next feature. Capture the diagram and mitigation list in your wiki—this becomes living documentation you can update as the system changes.
**실습:** 다음 기능을 출시하기 전에 혼자 또는 팀원과 위협 모델링 워크숍을 진행하고, 다이어그램과 완화 목록을 위키에 기록해 시스템 변화에 따라 갱신 가능한 문서로 만드세요.

---

## 2. Automating Security in CI/CD (The "Sec" in DevSecOps)
## 2. CI/CD에서 보안 자동화하기 (DevSecOps의 “Sec”)

Your CI/CD pipeline is your most powerful tool for automating security.
CI/CD 파이프라인은 보안을 자동화할 수 있는 가장 강력한 도구입니다.

### Static Application Security Testing (SAST)
### 정적 애플리케이션 보안 테스트(SAST)
-   **What it is**: Tools that scan your source code for potential security vulnerabilities.
-   **정의**: 소스 코드를 스캔해 잠재적 취약점을 찾는 도구입니다.
-   **Example Tool**: `Bandit`. It's a linter for security. Many of its rules are also integrated into `Ruff`, which you may already be using!
-   **예시 도구**: `Bandit` – 보안 전용 린터입니다.
-   **Integration**: Add a `lint:security` step to your GitHub Actions workflow.
-   **통합 방법**: GitHub Actions 워크플로에 `lint:security` 단계를 추가하세요.

```yaml
- name: Run Bandit SAST Scan
  run: |
    pip install bandit
    bandit -r src/ -ll -c pyproject.toml
```
This will fail the build if it finds high-confidence, high-severity issues like hardcoded passwords or the use of `pickle`.
하드코딩된 비밀번호, `pickle` 사용 등 심각도가 높은 문제를 발견하면 빌드가 실패합니다.

**Practice:** extend your CI pipeline to upload Bandit results as build artifacts (JUnit or SARIF). Review the findings, suppress false positives with comments, and document why each suppression is safe.
**실습:** CI 파이프라인에서 Bandit 결과를 빌드 아티팩트(JUnit 또는 SARIF)로 업로드하도록 확장하고, 결과를 검토해 오탐은 주석으로 제외하며 그 이유를 문서화하세요.

### Dynamic Application Security Testing (DAST)
### 동적 애플리케이션 보안 테스트(DAST)
-   **What it is**: Tools that attack your *running* application to find vulnerabilities, just like a real attacker would.
-   **정의**: 실제 공격자처럼 실행 중인 애플리케이션을 공격해 취약점을 찾는 도구입니다.
-   **Example Tool**: OWASP ZAP (Zed Attack Proxy).
-   **예시 도구**: OWASP ZAP.
-   **Integration**: This is more complex. A common pattern is to have your CI pipeline deploy your application to a temporary "staging" environment and then run a ZAP scan against that environment.
-   **통합 방법**: 다소 복잡하지만, CI 파이프라인이 임시 스테이징 환경에 앱을 배포하고 그 환경을 대상으로 ZAP 스캔을 수행하는 방식이 일반적입니다.

### Software Composition Analysis (SCA)
### 소프트웨어 구성 분석(SCA)
This is what you're already doing with `Dependabot`—scanning your dependencies for known vulnerabilities. This is a critical part of DevSecOps.
이는 `Dependabot`으로 이미 수행 중인 작업으로, 의존성의 알려진 취약점을 스캔하는 DevSecOps의 핵심 활동입니다.

**Practice:** configure Dependabot (or Renovate) to group security fixes weekly. Schedule a recurring task to review and merge them, noting any manual testing you perform.
**실습:** Dependabot(또는 Renovate)이 보안 패치를 주간 단위로 묶도록 설정하고, 이를 검토·머지하며 진행한 수동 테스트를 기록하는 반복 작업을 일정에 넣으세요.

---

## 3. Advanced Identity Management: OAuth2 and OIDC
## 3. 고급 신원 관리: OAuth2와 OIDC

As your system grows, you might need to allow third-party applications to access your API on behalf of a user, or you might want to use "Sign in with Google/GitHub." This is where OAuth2 and OpenID Connect (OIDC) come in.
시스템이 성장하면 서드파티 앱이 사용자 대신 API를 호출하도록 허용하거나, “구글/깃허브 로그인” 같은 기능을 제공해야 할 수도 있습니다. 그때 필요한 것이 OAuth2와 OIDC입니다.

-   **OAuth2**: An **authorization** framework. It defines how a user can grant a third-party app limited access to their data without giving them their password. It's all about "scopes" (e.g., `read:profile`, `write:posts`).
-   **OAuth2**: **권한 부여** 프레임워크로, 사용자가 비밀번호를 공유하지 않고도 서드파티 앱에 제한된 접근 권한(스코프)을 줄 수 있게 합니다.
-   **OpenID Connect (OIDC)**: An **authentication** layer built on top of OAuth2. It provides a standard way to get an `id_token` that proves who the user is. "Sign in with Google" is OIDC.
-   **OpenID Connect(OIDC)**: OAuth2 위에 구축된 **인증** 계층으로, 사용자를 증명하는 `id_token`을 표준 방식으로 제공합니다. “구글 로그인”이 대표적인 예입니다.

Implementing an OAuth2 provider is complex and full of security pitfalls. It's highly recommended to use a third-party Identity as a Service (IDaaS) provider like **Auth0**, **Okta**, or a cloud-native one like **AWS Cognito** or **Google Identity Platform**. They handle the complexity of login forms, multi-factor authentication (MFA), password resets, and token issuance for you.
OAuth2 제공자를 직접 구현하면 복잡하고 보안 함정이 많습니다. **Auth0**, **Okta** 같은 IDaaS나 **AWS Cognito**, **Google Identity Platform** 같은 클라우드 서비스 사용을 강력 추천합니다. 로그인 폼, MFA, 비밀번호 재설정, 토큰 발급 등의 복잡성을 대신 처리해 줍니다.

---

## 4. Runtime Security with Falco
## 4. Falco로 런타임 보안 강화하기

How do you know if something malicious is happening inside your running containers? Runtime security tools can detect anomalous behavior.
실행 중인 컨테이너 안에서 악의적인 일이 벌어지는지 어떻게 알 수 있을까요? 런타임 보안 도구가 이상 행동을 감지해 줍니다.

**Falco** is a popular open-source tool for runtime threat detection for cloud-native platforms. It uses eBPF (a powerful Linux kernel technology) to observe system calls and can detect suspicious activity based on a set of rules.
**Falco**는 클라우드 네이티브 환경에서 런타임 위협을 탐지하는 인기 오픈소스 도구로, 강력한 리눅스 커널 기술인 eBPF를 사용해 시스템 호출을 관찰하고 규칙 기반으로 의심스러운 활동을 감지합니다.

**Example Falco Rules**:
**Falco 규칙 예시**:
-   "A shell was run inside a container." (This is often a sign of an attacker who has gained initial access).
-   “컨테이너 내부에서 셸이 실행됨” – 초기에 침투한 공격자 징후입니다.
-   "A process tried to write to a sensitive file like `/etc/passwd`."
-   “프로세스가 `/etc/passwd` 같은 민감 파일에 쓰려고 함”.
-   "An outbound network connection was made to a known malicious IP address."
-   “알려진 악성 IP 주소로 아웃바운드 연결이 생성됨”.

When Falco detects a violation, it can send an alert to your monitoring system. This provides a crucial layer of defense for detecting and responding to attacks that have bypassed your initial security controls.
Falco가 규칙 위반을 감지하면 모니터링 시스템으로 알림을 전송할 수 있어 초기에 보안을 뚫고 들어온 공격에 대응할 마지막 방어선을 제공합니다.

By embracing these Level 2 concepts, you move from a reactive "patching vulnerabilities" mindset to a proactive "building a secure system" culture. You start to think like an attacker, automate your defenses, and gain visibility into the security of your running systems.
이러한 레벨 2 개념을 받아들이면 “취약점을 때우는” 수동적 사고에서 벗어나 “안전한 시스템을 구축하는” 선제적 문화로 전환할 수 있습니다. 공격자처럼 생각하고 방어를 자동화하며 런타임 보안 가시성을 확보하게 됩니다.

## Going Further
## 더 나아가기
-   Adopt Infrastructure as Code security scanners (tfsec, Checkov) and gate Terraform plans on their results.
-   tfsec, Checkov 같은 코드형 인프라 보안 스캐너를 도입해 Terraform 계획을 그 결과에 따라 제한하세요.
-   Explore identity federation by integrating your app with an external IdP; document the token flow and refresh logic.
-   외부 IdP와 연동해 신원 연합을 실험하고 토큰 흐름과 갱신 로직을 문서화하세요.
-   Run a tabletop incident response drill: simulate a leaked API key and walk through detection, mitigation, and postmortem steps.
-   테이블탑 사고 대응 훈련을 진행해 API 키 유출을 가정하고 탐지·대응·사후 분석 과정을 연습하세요.
