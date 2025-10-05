# 07 - Security - Lv.2: Proactive Security and DevSecOps

You've mastered the basics of securing your application. Level 2 is about shifting from a defensive posture to a proactive one. This means integrating security into every step of your development lifecycle (DevSecOps) and adopting advanced security practices.

## Core Concepts

1.  **DevSecOps**: The philosophy of "shifting left" on security. Instead of security being a final gate before release, it's an automated, integral part of the development process.
2.  **Threat Modeling**: A structured process for identifying potential threats and vulnerabilities in your system *before* you write any code.
3.  **Identity and Access Management (IAM)**: Moving beyond simple user authentication to a centralized and fine-grained control system for both users and services.
4.  **Runtime Security**: Detecting and responding to threats in your running, production environment.

---

## 1. Threat Modeling: Thinking Like an Attacker

Threat modeling is a proactive exercise you should do at the design stage of any new feature or service. A common framework is **STRIDE**:

-   **S**poofing: Can an attacker pretend to be someone or something they're not? (e.g., impersonating another user).
-   **T**ampering: Can an attacker modify data in transit or at rest? (e.g., changing the price of an item in an API call).
-   **R**epudiation: Can a user deny having performed an action? (e.g., "I never authorized that payment!").
-   **I**nformation Disclosure: Can an attacker access data they shouldn't? (e.g., leaking user profiles).
-   **D**enial of Service (DoS): Can an attacker crash or disable your service? (e.g., by sending a malformed request that causes an unhandled exception).
-   **E**levation of Privilege: Can a regular user gain admin privileges?

**How to do it**:
1.  Draw a diagram of your system, showing user entry points, services, and data stores.
2.  For each component and data flow, go through the STRIDE checklist and brainstorm potential attacks.
3.  For each threat, identify potential mitigations (e.g., "To prevent tampering with payment data, we will sign the payload with a secret key").
4.  Prioritize the threats and turn the mitigations into development tasks.

---

## 2. Automating Security in CI/CD (The "Sec" in DevSecOps)

Your CI/CD pipeline is your most powerful tool for automating security.

### Static Application Security Testing (SAST)
-   **What it is**: Tools that scan your source code for potential security vulnerabilities.
-   **Example Tool**: `Bandit`. It's a linter for security.
-   **Integration**: Add a `lint:security` step to your GitHub Actions workflow.

```yaml
- name: Run Bandit SAST Scan
  run: |
    pip install bandit
    bandit -r src/ -ll -c pyproject.toml
```
This will fail the build if it finds high-confidence, high-severity issues like hardcoded passwords or the use of `pickle`.

### Dynamic Application Security Testing (DAST)
-   **What it is**: Tools that attack your *running* application to find vulnerabilities, just like a real attacker would.
-   **Example Tool**: OWASP ZAP (Zed Attack Proxy).
-   **Integration**: This is more complex. A common pattern is to have your CI pipeline deploy your application to a temporary "staging" environment and then run a ZAP scan against that environment.

### Software Composition Analysis (SCA)
This is what you're already doing with `Dependabot`—scanning your dependencies for known vulnerabilities. This is a critical part of DevSecOps.

---

## 3. Advanced Identity Management: OAuth2 and OIDC

As your system grows, you might need to allow third-party applications to access your API on behalf of a user, or you might want to use "Sign in with Google/GitHub." This is where OAuth2 and OpenID Connect (OIDC) come in.

-   **OAuth2**: An **authorization** framework. It defines how a user can grant a third-party app limited access to their data without giving them their password. It's all about "scopes" (e.g., `read:profile`, `write:posts`).
-   **OpenID Connect (OIDC)**: An **authentication** layer built on top of OAuth2. It provides a standard way to get an `id_token` that proves who the user is. "Sign in with Google" is OIDC.

Implementing an OAuth2 provider is complex and full of security pitfalls. It's highly recommended to use a third-party Identity as a Service (IDaaS) provider like **Auth0**, **Okta**, or a cloud-native one like **AWS Cognito** or **Google Identity Platform**. They handle the complexity of login forms, multi-factor authentication (MFA), password resets, and token issuance for you.

---

## 4. Runtime Security with Falco

How do you know if something malicious is happening inside your running containers? Runtime security tools can detect anomalous behavior.

**Falco** is a popular open-source tool for runtime threat detection for cloud-native platforms. It uses eBPF (a powerful Linux kernel technology) to observe system calls and can detect suspicious activity based on a set of rules.

**Example Falco Rules**:
-   "A shell was run inside a container." (This is often a sign of an attacker who has gained initial access).
-   "A process tried to write to a sensitive file like `/etc/passwd`."
-   "An outbound network connection was made to a known malicious IP address."

When Falco detects a violation, it can send an alert to your monitoring system. This provides a crucial layer of defense for detecting and responding to attacks that have bypassed your initial security controls.

By embracing these Level 2 concepts, you move from a reactive "patching vulnerabilities" mindset to a proactive "building a secure system" culture. You start to think like an attacker, automate your defenses, and gain visibility into the security of your running systems.
