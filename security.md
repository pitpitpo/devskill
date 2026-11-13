# 🔒 Production Security Standards (`security.md`)

> **Classification**: Production Security Baseline  
> **Applicability**: All services, APIs, web applications, and database layers  
> **Compliance Targets**: OWASP Top 10, SOC 2 Type II, ISO 27001, GDPR, HIPAA

---

## 1. Core Security Principles

1. **Zero Trust Architecture**:
   - Never trust network locality. Authenticate and authorize every request, whether incoming from the public internet or an internal VPC microservice.
   - Mutual TLS (mTLS) for all service-to-service communication within service meshes.
2. **Defense in Depth**:
   - Implement overlapping security controls at the Edge (WAF, DDoS mitigation), Transport (TLS 1.3), Application (Schema validation, RBAC/ABAC), and Data layers (Encryption at rest, column masking).
3. **Fail Closed**:
   - If an authorization service, rate limiter, or signature check fails or times out, the request MUST be rejected (`401 Unauthorized` or `503 Service Unavailable`), never permitted by default.
4. **Least Privilege**:
   - IAM roles, service accounts, and database users must have the bare minimum permissions required for their specific function.

---

## 2. OWASP Top 10 Mitigation Matrix & Code Guidelines

### A01: Broken Access Control
- **Risk**: Unauthorized users accessing objects, endpoints, or data belonging to other tenants/users (IDOR - Insecure Direct Object Reference).
- **Rule**: Never trust client-supplied entity IDs without verifying ownership or tenancy in the authorization context.
- **Pattern**:
  ```python
  # BAD: IDOR vulnerability
  @app.get("/invoices/{invoice_id}")
  async def get_invoice(invoice_id: str, db: Session = Depends(get_db)):
      return db.query(Invoice).filter(Invoice.id == invoice_id).first()

  # GOOD: Tenant-scoped lookup
  @app.get("/invoices/{invoice_id}")
  async def get_invoice(
      invoice_id: str, 
      current_user: User = Depends(get_current_active_user),
      db: Session = Depends(get_db)
  ):
      invoice = db.query(Invoice).filter(
          Invoice.id == invoice_id, 
          Invoice.organization_id == current_user.org_id
      ).first()
      if not invoice:
          raise HTTPException(status_code=404, detail="Invoice not found")
      return invoice
  ```

### A02: Cryptographic Failures
- **Risk**: Weak algorithms, plaintext passwords, unencrypted sensitive data at rest or in transit.
- **Rules**:
  - Passwords: Hash using **Argon2id** (memory: 64MB, iterations: 3, parallelism: 4) or **bcrypt** (work factor ≥ 12). Never use MD5, SHA-1, or plain SHA-256.
  - Symmetric Encryption: Use **AES-256-GCM** or **ChaCha20-Poly1305** (authenticated encryption with associated data).
  - Transit: Enforce **TLS 1.3** (minimum TLS 1.2 with strong cipher suites). Strict Transport Security (`HSTS: max-age=63072000; includeSubDomains; preload`).

### A03: Injection (SQL, Command, LDAP, NoSQL)
- **Risk**: Untrusted user inputs concatenated into query interpreters.
- **Rule**: Parameterized queries only. Zero dynamic string concatenation.
- **Pattern**:
  ```typescript
  // BAD: SQL Injection
  const user = await db.query(`SELECT * FROM users WHERE email = '${email}'`);

  // GOOD: Parameterized query
  const user = await db.query(
    'SELECT id, email, role FROM users WHERE email = $1', 
    [email]
  );
  ```

### A04: Insecure Design & Threat Modeling
- **Risk**: Omitting security considerations during architecture design.
- **Requirement**: Use **STRIDE** (Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege) threat modeling on all new system architecture diagrams.
- Rate limit all authentication endpoints (Max 5 failed attempts per 15-minute window with IP/account throttling).

### A05: Security Misconfiguration
- **Headers to Enforce on Every HTTP Response**:
  ```http
  Strict-Transport-Security: max-age=63072000; includeSubDomains; preload
  X-Content-Type-Options: nosniff
  X-Frame-Options: DENY
  Referrer-Policy: strict-origin-when-cross-origin
  Permissions-Policy: geolocation=(), microphone=(), camera=()
  Content-Security-Policy: default-src 'self'; script-src 'self'; object-src 'none';
  ```
- Disable directory listing, suppress server identification headers (`Server:`, `X-Powered-By:`), and disable debug modes in production (`DEBUG=False`).

### A06: Vulnerable and Outdated Components
- Pin all dependency versions using lockfiles (`package-lock.json`, `poetry.lock`, `Cargo.lock`, `go.sum`).
- Integrate automated CVE scanning in CI/CD via `trivy`, `snyk`, or `cargo audit`. Block builds on CVSS score ≥ 7.0 (High/Critical).

### A07: Identification & Authentication Failures
- Enforce Multi-Factor Authentication (MFA) via TOTP or WebAuthn/FIDO2.
- Session Management:
  - Session cookies must be `HttpOnly; Secure; SameSite=Strict; Path=/`.
  - Max session lifetime: 8 hours; Idle timeout: 30 minutes.
- JWT Standards:
  - Sign tokens with asymmetric keys (**RS256** or **Ed25519**). Reject the `none` algorithm explicitly.
  - Short-lived Access Tokens (5–15 minutes).
  - Refresh Tokens must be stored hashed in the database and rotated on each use with automatic reuse detection.

### A08: Software & Data Integrity Failures
- Protect against untrusted deserialization: Never use Python `pickle`, Java native deserialization, or PHP `unserialize` on user input. Use JSON or Protocol Buffers.
- Verify software artifact hashes and sign container images using `Cosign`.

### A09: Security Logging & Monitoring Failures
- Log all security events: login attempts (success and failure), password resets, permission changes, administrative actions, and high-value data exports.
- Centralize logs into a SIEM (Datadog, Splunk, Elastic) with automated alerts on suspicious anomalies (e.g., 20+ failed logins across multiple IPs in 1 minute).

### A10: Server-Side Request Forgery (SSRF)
- **Risk**: Application fetches a remote URL provided by the user, enabling attackers to scan internal VPC networks, query AWS metadata (`http://169.254.169.254`), or hit local loopback services.
- **Mitigation**:
  - Restrict user-provided URLs to an explicit allowlist of schemes (`https` only) and domains.
  - Resolve DNS before request and explicitly reject private IP ranges:
    - Loopback: `127.0.0.0/8`, `::1`
    - RFC 1918 Private: `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`
    - Link-Local / Cloud Metadata: `169.254.0.0/16`

---

## 3. Secrets Management & Cryptography

1. **Vault & Cloud KMS Integration**:
   - Production secrets must never reside in source code or `.env` files checked into git.
   - Use centralized Secret Vaults (HashiCorp Vault, AWS Secrets Manager, GCP Secret Manager) with automatic rotation every 90 days.
2. **Envelope Encryption Pattern**:
   - Encrypt sensitive database columns (SSN, credit card tokens, health records) using a Data Encryption Key (DEK) protected by a Key Encryption Key (KEK) inside a hardware security module (HSM).
3. **Environment Isolation**:
   - Staging and development environments must NEVER have access to production databases, third-party production credentials, or real customer data.

---

## 4. Supply Chain & Container Security

1. **Non-Root Containers**:
   ```dockerfile
   # Example secure non-root Dockerfile snippet
   FROM alpine:3.20 AS builder
   # ... build steps ...
   
   FROM alpine:3.20
   RUN addgroup -S appgroup && adduser -S appuser -G appgroup
   USER appuser
   EXPOSE 8080
   CMD ["./service"]
   ```
2. **Minimal Base Images**:
   - Use Distroless (`gcr.io/distroless/static-debian12`) or Alpine minimal images to minimize attack surface and OS-level vulnerabilities.
3. **Software Bill of Materials (SBOM)**:
   - Generate an SBOM during build (`syft`) and scan against current vulnerability databases (`grype`).

---

## 5. Security Verification Checklist

| Security Gate | Criteria | Verification Tool |
|---|---|---|
| **Static Code Analysis** | Zero High/Critical findings | Semgrep / SonarQube |
| **Dependency Audit** | Zero vulnerable dependencies (CVSS ≥ 7) | Snyk / Trivy / Dependabot |
| **Secret Detection** | Zero credentials or private keys in git | Gitleaks / GitGuardian |
| **Container Image Scan** | Zero OS or library vulnerabilities | Trivy image scanner |
| **Dynamic API Scan** | Input fuzzing, injection checks | OWASP ZAP / DAST |
| **Permission Audit** | Non-root container, minimal IAM roles | Kube-linter / Checkov |
| **Security Headers** | A+ rating on securityheaders.com | curl / automated test suite |
