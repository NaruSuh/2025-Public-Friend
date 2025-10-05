# 07.01 - Web Application Security Essentials (OWASP Top 10)

Security is not a feature; it's a prerequisite. For a Vibe Coder building real-world applications, understanding web security fundamentals is non-negotiable. This guide provides a practical overview based on the OWASP (Open Web Application Security Project) Top 10, the industry-standard awareness document for web application security.

---

## The OWASP Top 10 (2021) - A Vibe Coder's Interpretation

### 1. A01:2021 - Broken Access Control

**What it is**: Users being able to access things they shouldn't. This is the most common and critical vulnerability.

**Example**: An API endpoint `GET /api/v1/users/{user_id}/profile` that lets you view a user's profile. If you can change `user_id` in the URL to someone else's ID and see their data, you have broken access control.

**Prevention**:
-   **Never trust user input for authorization decisions.**
-   In your endpoint logic, always verify that the *authenticated* user has the right to access the requested resource.
-   **Centralize access control logic.**

```python
# FastAPI Example
from fastapi import Depends, HTTPException, status
from . import models, auth # Your auth functions

@router.get("/orders/{order_id}")
def get_order(order_id: int, current_user: models.User = Depends(auth.get_current_user)):
    order = db.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # THE CRITICAL CHECK:
    if order.owner_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
        
    return order
```

### 2. A02:2021 - Cryptographic Failures

**What it is**: Mishandling of sensitive data, like passwords, credit cards, or personal information, leading to its exposure.

**Prevention**:
-   **Store passwords hashed and salted**, never in plain text. Use a strong, adaptive algorithm like `bcrypt` or `Argon2`. The `passlib` library is excellent for this.
-   **Encrypt all data in transit** using TLS (i.e., use HTTPS everywhere).
-   **Encrypt sensitive data at rest** (in the database) if required by compliance or business needs.
-   **Don't roll your own cryptography.** Use well-vetted libraries.

### 3. A03:2021 - Injection

**What it is**: Untrusted user data being sent to an interpreter as part of a command or query. The classic example is SQL Injection.

**Prevention**:
-   **Use an ORM (like SQLAlchemy) or parameterized queries (prepared statements).** This is the single most important defense against SQL injection. The database driver treats the query structure and the user data separately.

**Safe (SQLAlchemy ORM):**
```python
# User input is treated as a value, not part of the SQL command.
db.query(models.User).filter(models.User.name == user_supplied_name).first()
```

**Unsafe (Raw SQL with string formatting - NEVER DO THIS):**
```python
# DANGEROUS! A user could supply a name like: 'admin'; DROP TABLE users; --'
cursor.execute(f"SELECT * FROM users WHERE name = '{user_supplied_name}'")
```

### 4. A05:2021 - Security Misconfiguration

**What it is**: Default configurations, verbose error messages, or insecure cloud service settings.

**Prevention**:
-   **Harden your infrastructure**: Change default passwords, disable unnecessary services.
-   **Minimalist `Dockerfile`**: Use minimal base images and don't include debug tools in production images.
-   **Don't leak information in error messages**: In production, return generic error messages, not full stack traces. FastAPI does this by default.
-   **Configure cloud services securely**: Use tools like Terraform to codify and review your cloud security group rules, IAM policies, and S3 bucket policies.

### 5. A06:2021 - Vulnerable and Outdated Components

**What it is**: Using libraries or frameworks with known security vulnerabilities. Your `requirements.txt` can be a huge security risk.

**Prevention**:
-   **Automate dependency scanning**: Use tools like `Dependabot` (free on GitHub), `Snyk`, or `pyup`. They will automatically open pull requests to update vulnerable dependencies.
-   **Pin your dependencies**: Use a `requirements.txt` or `poetry.lock` file to ensure you are using known, vetted versions of your dependencies in production.

### 6. A08:2021 - Software and Data Integrity Failures

**What it is**: Trusting software or data without verifying its integrity. This includes insecure deserialization.

**Prevention**:
-   **Never use `pickle`, `pyyaml`'s `yaml.load()`, or `eval()` on untrusted data.** These can lead to arbitrary code execution.
-   **Use safe serialization formats** like JSON. When you need more complex object deserialization, use a library like Pydantic that validates the data against a strict schema.
-   **Verify signatures of software updates** or data from external sources if provided.

---

## A Vibe Coder's Security Checklist

Before deploying any feature, run through this mental checklist:

1.  **Access Control**: Does this endpoint verify that the logged-in user is authorized to perform this action on this specific resource?
2.  **Data Handling**: Am I handling any sensitive data? If so, is it being encrypted in transit (HTTPS) and stored securely (hashed passwords)?
3.  **Input**: Am I using an ORM or parameterized queries for all database access? Am I validating all user input with Pydantic or similar?
4.  **Dependencies**: Have I run a dependency scan? Are there any known critical vulnerabilities in my libraries?
5.  **Secrets**: Are all my API keys, database passwords, and other secrets stored in a secure secrets manager (like HashiCorp Vault or AWS Secrets Manager) and not in my code or environment variables in plain text?
6.  **Error Messages**: Are my production error messages generic and uninformative to an attacker?
7.  **Deserialization**: Am I avoiding `pickle` and other unsafe deserialization methods on any data that originated from a user?

Security is a process, not a destination. By integrating these principles into your development workflow, you build a strong security posture from the ground up.
