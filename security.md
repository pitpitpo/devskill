# 🔒 Production Security Standards (`security.md`)

> **Classification**: Production Security Baseline (v2.0.0)  
> **Applicability**: All services, APIs, web applications, database layers, CI/CD pipelines, and agentic AI systems  
> **Compliance Targets**: OWASP Top 10:2025, OWASP Top 10 for Agentic Applications (ASI01–ASI10), OWASP Agentic Skills Top 10 (AST10), NIST SP 800-63B-4 (2025), NIST PQC (FIPS 203/204/205), NIST SP 800-207 (Zero Trust), SOC 2 Type II, ISO 27001, GDPR  
> **Last Updated**: 2026-11-19

---

## 1. Core Security Principles

1. **Zero Trust Architecture (NIST SP 800-207)**:
   - Never trust network locality. Authenticate and authorize every request, whether arriving from the public internet or an internal cluster mesh.
   - Enforce Mutual TLS (mTLS) with TLS 1.3 (hybrid post-quantum key exchange where supported) for all service-to-service traffic.
2. **Defense in Depth**:
   - Layer independent security controls across Edge (WAF, rate limits), Transport (TLS 1.3 + HSTS), Application (strict boundary schemas, RBAC/ABAC, CSP), Data (envelope encryption, PostgreSQL RLS, column masking), and Agentic Harness (`PreToolUse` / OAuth 2.1 RFC 8707 audience scoping).
3. **Fail Closed (OWASP A10:2025 / R-232)**:
   - If an authorization service, signature verifier, rate limiter, schema parser, or dependency times out or throws an unexpected exception, the system MUST reject the request (`401`/`403`/`503`) and leave state unchanged — never fail open.
4. **Least Privilege & Least Agency (R-067, R-228)**:
   - Grant IAM roles, DB accounts, MCP servers, and autonomous agents the bare minimum permissions and tool capabilities needed for their exact task.

---

## 2. OWASP Top 10:2025 Mitigation Matrix & Code Guidelines

### A01:2025 – Broken Access Control *(Includes SSRF)*
- **Risk**: Unauthorized users accessing objects belonging to other tenants/users (IDOR), privilege escalation, missing function-level access control, or Server-Side Request Forgery (SSRF) probing internal VPCs/metadata endpoints.
- **Rules**:
  - Verify ownership or tenant membership on every object lookup (`WHERE id = $1 AND tenant_id = $2` or PostgreSQL Row-Level Security).
  - For any server-side outbound URL fetch, allowlist `https` scheme + explicit domains, resolve DNS prior to connect (blocking DNS rebinding), and reject loopback (`127.0.0.0/8`, `::1`), RFC 1918 private networks (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), and link-local/cloud metadata (`169.254.0.0/16`, `fd00::/8`).
- **Pattern**:
  ```python
  # BAD: IDOR vulnerability (no tenant check)
  @app.get("/invoices/{invoice_id}")
  async def get_invoice(invoice_id: str, db: Session = Depends(get_db)):
      return db.query(Invoice).filter(Invoice.id == invoice_id).first()

  # GOOD: Tenant-scoped lookup failing closed with 404
  @app.get("/invoices/{invoice_id}")
  async def get_invoice(
      invoice_id: str,
      current_user: User = Depends(get_current_active_user),
      db: Session = Depends(get_db),
  ):
      invoice = (
          db.query(Invoice)
          .filter(
              Invoice.id == invoice_id,
              Invoice.organization_id == current_user.org_id,
          )
          .first()
      )
      if not invoice:
          raise HTTPException(status_code=404, detail="Invoice not found")
      return invoice
  ```

### A02:2025 – Security Misconfiguration
- **Mandatory HTTP Security Headers**:
  ```http
  Strict-Transport-Security: max-age=63072000; includeSubDomains; preload
  X-Content-Type-Options: nosniff
  X-Frame-Options: DENY
  Referrer-Policy: strict-origin-when-cross-origin
  Permissions-Policy: geolocation=(), microphone=(), camera=()
  Content-Security-Policy: default-src 'self'; script-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'
  ```
- Disable debug flags (`DEBUG=False`), directory listings, verbose error pages, and server version headers (`Server`, `X-Powered-By`). Never return `Access-Control-Allow-Origin: *` alongside `Access-Control-Allow-Credentials: true` (R-079).

### A03:2025 – Software Supply Chain Failures
- **Risk**: Compromised transitive packages, malicious install hooks, slopsquatted AI-hallucinated packages, unverified container layers, and poisoned CI actions.
- **Rules**:
  - Commit lockfiles and enforce frozen installs (`npm ci --ignore-scripts`, `uv sync --frozen`, `cargo fetch --locked`) (R-117–R-119).
  - Pin container base images and GitHub Actions by full **SHA-256 / commit SHA** digest rather than mutable tags (R-156).
  - Generate CycloneDX/SPDX SBOMs (`syft`), scan via `trivy`/`grype`/`cargo-audit`/`pip-audit` blocking CVSS ≥ 7.0, and sign release artifacts with **Cosign / Sigstore + SLSA Provenance Level 3** (R-120, R-124, R-125).
  - Verify package provenance, download velocity, maintainer reputation, and license before adding any dependency (R-007, R-126).

### A04:2025 – Cryptographic Failures
- **Password Hashing**: **Argon2id** (RFC 9106: 64 MiB memory, 3 iterations, parallelism 4) or bcrypt (cost ≥ 12). MD5, SHA-1, SHA-256, and DES are strictly banned for password storage (R-065).
- **Symmetric Encryption**: Authenticated encryption only — **AES-256-GCM** or **ChaCha20-Poly1305** with unique CSPRNG nonces (R-066, R-082).
- **Asymmetric & Post-Quantum Readiness (NIST FIPS 203/204/205 & NISTIR 8547 / R-231)**:
  - Classical baseline: **Ed25519** / **ECDSA P-256+** / **RSA-3072+**.
  - **Hybrid Post-Quantum TLS**: Enable hybrid key exchange (`X25519MLKEM768` per FIPS 203 ML-KEM) on edge gateways, ingress controllers, and TLS 1.3 stacks to mitigate *harvest-now, decrypt-later* threats.
  - **Crypto-Agility**: Abstract cipher/key-exchange suites behind configuration interfaces and maintain a Cryptographic Bill of Materials (CBOM) tracking transition readiness toward FIPS 203 (ML-KEM), FIPS 204 (ML-DSA), and FIPS 205 (SLH-DSA).
- **Constant-Time Verification**: Always compare HMACs, API keys, and tokens using `crypto.timingSafeEqual` / `hmac.compare_digest` after checking equal byte lengths (R-076).

### A05:2025 – Injection (SQL, NoSQL, Command, LDAP, Template, Prompt)
- **Rule**: 100% parameterized queries and safe structured templates (e.g., Python 3.14 PEP 750 `t`-strings with parameterized processors, prepared SQL statements). Zero string interpolation into interpreters or shells (R-061).
- **Pattern**:
  ```typescript
  // BAD: SQL Injection
  const user = await db.query(`SELECT * FROM users WHERE email = '${email}'`);

  // GOOD: Parameterized query
  const user = await db.query(
    "SELECT id, email, role FROM users WHERE email = $1",
    [email]
  );
  ```

### A06:2025 – Insecure Design
- Perform **STRIDE** threat modeling (Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege) on every new architecture diagram or sensitive workflow.
- Enforce distributed rate limiting (Redis Token/Leaky Bucket) on auth, password reset, OTP, and expensive endpoints (R-068).
- Design business invariants into database constraints, atomic transactions, idempotency keys, and state machines rather than relying on UI checks.

### A07:2025 – Authentication Failures (Aligned with NIST SP 800-63B-4, July 2025)
- **NIST SP 800-63B-4 Password Policy (R-230)**:
  - **Minimum length**: **≥ 15 characters** when used as a single factor; **≥ 8 characters** when combined with MFA.
  - **Maximum length**: Support **≥ 64 characters**, all printable ASCII, spaces, and Unicode (supporting passphrases and password managers).
  - **PROHIBITED**: Do NOT enforce arbitrary composition rules (mandatory uppercase/symbol mixes) and do NOT force periodic password rotation (e.g., every 90 days) absent compromise evidence.
  - **REQUIRED**: Screen every new/changed password against dynamic breach/compromised-credential blocklists and context-specific terms; allow copy-and-paste in password fields; cap consecutive failed attempts (max 100 with exponential throttling).
- **Phishing-Resistant MFA (AAL2+)**: Offer **WebAuthn / FIDO2 Passkeys** as a primary phishing-resistant authenticator alongside TOTP.
- **Sessions & JWTs**:
  - Cookies: `HttpOnly; Secure; SameSite=Strict` (or `Lax` where cross-site GET navigation requires it); explicit idle + absolute expiration.
  - JWTs: Asymmetric signing (`EdDSA`/`RS256`), explicitly reject `alg: none`, short-lived access tokens (5–15 min), and hashed single-use rotating refresh tokens with reuse detection.

### A08:2025 – Software or Data Integrity Failures
- Ban unsafe deserialization (`pickle.loads`, `yaml.load`, Java native serialization, `eval()`). Use strictly validated JSON or Protocol Buffers (R-081).
- Verify webhook HMAC-SHA256 signatures with a ≤ 300s timestamp replay window (R-185).
- Verify artifact digests and Cosign signatures before production deployment.

### A09:2025 – Security Logging and Alerting Failures
- Emit immutable, append-only structured JSON audit logs for auth successes/failures, MFA changes, privilege escalations, administrative actions, and bulk exports (R-083, R-142, R-152).
- Scrub all PII, passwords, Bearer tokens, and secrets prior to emission (R-144).
- Route security logs to a SIEM with automated symptom-based alerting on credential stuffing, impossible travel, or authorization spike anomalies.

### A10:2025 – Mishandling of Exceptional Conditions
- **Risk**: Catch blocks that silently return `true`, bypass auth checks, leak stack traces/SQL schemas, leave partial uncommitted transactions, or crash without releasing locks/connections.
- **Rules (R-046, R-057, R-059, R-232)**:
  - Every `try/catch` MUST fail closed, preserve root causes (`cause` / `%w`), release resources deterministically (`finally`/`defer`/`using`), and return standardized RFC 9457 `application/problem+json` without internal traces.
  - Never fall back to permissive defaults when a policy engine, feature flag store, or JWT JWKS endpoint is unreachable.

---

## 3. OWASP Top 10 for Agentic Applications (ASI01–ASI10) & Skills (AST10)

When building AI agents, tool servers (MCP), or multi-agent pipelines (A2A), enforce [`agents/mcp-a2a-protocols.md`](agents/mcp-a2a-protocols.md) and these controls:

| ID | Risk | Mandatory Mitigation |
|---|---|---|
| **ASI01** | Agent Goal Hijack | Separate untrusted user/document data from system instructions; enforce authorization deterministically outside the LLM. |
| **ASI02** | Tool Misuse & Exploitation | Narrow domain-specific tool schemas (Zod/Pydantic `.strict()`); ban generic raw-SQL/shell tools on remote MCP servers. |
| **ASI03** | Identity & Privilege Abuse | Enforce **OAuth 2.1 + RFC 8707 Resource Indicators** per MCP server; never pass through ambient user admin tokens (R-229). |
| **ASI04** | Agentic Supply Chain Vulnerabilities | Pin MCP servers, model endpoints, and `SKILL.md` dependencies by immutable hash/version; audit scripts (AST10) before running. |
| **ASI05** | Unexpected Code Execution | Sandbox all dynamic code execution in ephemeral, non-root, network-isolated containers/microVMs with CPU/RAM/timeout bounds. |
| **ASI06** | Memory & Context Poisoning | Isolate RAG/vector indexes by `tenant_id`, track source provenance, expire stale memory with TTLs, and sanitize retrieved text. |
| **ASI07** | Insecure Inter-Agent Communication | Authenticate A2A peers via mTLS or OAuth 2.1, verify `/.well-known/agent-card.json` over TLS 1.3, propagate `traceparent`. |
| **ASI08** | Cascading Failures | Bound worker fan-out ($K \le 4$), cycle ceilings ($\le 3$ rounds), hop limits, timeouts, and Saga rollbacks (R-194–R-197). |
| **ASI09** | Human-Agent Trust Exploitation | Display raw diffs, exact target commands, and concrete blast radius in HITL prompts — never persuasive summaries alone. |
| **ASI10** | Rogue Agents | Enforce deterministic harness hooks (`PreToolUse`/`Stop` Exit Code 2), immutable tool-call audit logs, and instant token revocation. |

---

## 4. Secrets Management, Cryptography & Container Hardening

1. **Centralized Vault & KMS**: Never commit secrets to git or `.env` files in VCS. Use AWS Secrets Manager, GCP Secret Manager, or HashiCorp Vault with automated rotation and short-lived OIDC workload identities (zero static CI cloud keys).
2. **Envelope Encryption**: Encrypt sensitive columns (PII, payment tokens, PHI) with per-record/per-tenant DEKs wrapped by cloud HSM KEKs.
3. **Environment Isolation**: Development and staging MUST NEVER connect to production databases or use real customer PII.
4. **Hardened Non-Root Containers (R-154–R-156, R-162)**:
   ```dockerfile
   # Pin base images by immutable SHA-256 digest in production
   FROM cgr.dev/chainguard/static:latest@sha256:<pinned-digest>
   USER 10001:10001
   COPY --from=builder --chown=10001:10001 /app/service /service
   EXPOSE 8080
   ENTRYPOINT ["/service"]
   ```
   Mount root filesystem read-only (`readOnlyRootFilesystem: true`), drop all Linux capabilities (`capabilities.drop: ["ALL"]`), and disallow privilege escalation (`allowPrivilegeEscalation: false`).

---

## 5. Security Verification Checklist

| Security Gate | Criteria | Verification Tool |
|---|---|---|
| **Static Code Analysis (SAST)** | Zero High/Critical findings | Semgrep / CodeQL |
| **Supply Chain & SCA (A03:2025)** | Zero CVSS ≥ 7.0 vulns; CycloneDX SBOM + Cosign attestation | Trivy / Grype / Syft / Cosign |
| **Secret Detection** | Zero credentials or private keys in git history or diff | Gitleaks / TruffleHog / `./scripts/ci-gate.sh` |
| **Container Image Hardening** | Non-root UID, digest-pinned, read-only rootfs, 0 Critical CVEs | Trivy image / Kube-linter / Checkov |
| **Dynamic API Scan (DAST)** | Input fuzzing, IDOR/SSRF/injection checks, RFC 9457 error hygiene | OWASP ZAP / Nuclei |
| **Auth & Crypto Compliance** | NIST SP 800-63B-4 blocklist + 15-char single-factor, Argon2id, TLS 1.3 hybrid PQC | Auth integration suite / `testssl.sh` |
| **Agentic & MCP Audit (ASI/AST10)** | RFC 8707 audience check, strict tool schemas, sandboxed execution | MCP contract tests / prompt-injection evals |
