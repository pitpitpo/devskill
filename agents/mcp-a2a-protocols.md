# 🔌 Model Context Protocol (MCP) & Agent2Agent (A2A) Interoperability (`agents/mcp-a2a-protocols.md`)

> **Standard Identifier**: `AGENT-MCP-A2A-001`  
> **Status**: Mandatory / Production Standard  
> **Target Audience**: AI Systems Engineers, Platform Architects, Multi-Agent Orchestrator Builders, Security Engineers  
> **Classification**: Level 5 Interoperable Agentic Systems Standard  
> **Governing Standards**: MCP 2026 Stateless Core & Streamable HTTP Spec, A2A Protocol (Linux Foundation AAIF), OAuth 2.1 + RFC 8707 Resource Indicators, OWASP Top 10 for Agentic Applications (ASI01–ASI10), OWASP Agentic Skills Top 10 (AST10)  
> **Governing Rules**: [RULES.md](../RULES.md) (R-060, R-062, R-078, R-171–R-178, R-191–R-200, R-228, R-229, R-234, R-235)  
> **Last Updated**: 2026-11-19

---

## 1. Scope & Division of Labor

Modern production agent architectures separate **Agent-to-Tool** integration from **Agent-to-Agent** delegation. Both standards are maintained under neutral open governance (Linux Foundation Agentic AI Foundation / AAIF):

| Protocol | Direction | Primary Purpose | Core Primitive | Discovery Mechanism |
|---|---|---|---|---|
| **MCP** (Model Context Protocol) | Vertical (Agent → Tool / Data) | Standardized invocation of tools, prompts, and structured resources | Tools, Resources, Prompts, Elicitation | Server capability negotiation (`tools/list`, `resources/list`) |
| **A2A** (Agent2Agent Protocol) | Horizontal (Agent → Peer Agent) | Cross-vendor, opaque, asynchronous multi-agent task delegation | Tasks, Artifacts, Messages, Streaming Events | `GET /.well-known/agent-card.json` |
| **Agent Skills** (`SKILL.md` / `AGENTS.md`) | Cognitive (Repo → Agent) | Progressive-disclosure procedural expertise & verifiable scripts | Frontmatter metadata + on-demand references | Directory scan (`SKILL.md`, `AGENTS.md`) |

```
                          ENTERPRISE AGENTIC PROTOCOL STACK

   [User / Client App]
            │
            ▼
   ┌────────────────────────────────────────────────────────────┐
   │  LEAD ORCHESTRATOR AGENT (AGENTS.md + SKILL.md Routing)    │
   └──────────────┬──────────────────────────────┬──────────────┘
                  │ A2A (JSON-RPC / SSE)         │ MCP (Streamable HTTP + OAuth 2.1)
                  │ /.well-known/agent-card.json │ RFC 8707 Resource Indicators
                  ▼                              ▼
   ┌─────────────────────────────┐  ┌──────────────────────────────┐
   │ SPECIALIST PEER AGENT       │  │ STATELESS MCP TOOL SERVER    │
   │ - Opaque internal reasoning │  │ - Strict Zod/Pydantic schemas│
   │ - Long-running Task state   │  │ - Least-agency scoped tokens │
   │ - Signed Artifact handoff   │  │ - Idempotent mutations       │
   └──────────────┬──────────────┘  └──────────────┬───────────────┘
                  │ MCP                            │
                  ▼                                ▼
         [Domain Data / APIs]             [PostgreSQL / Internal APIs]
```

---

## 2. Core Philosophy / Golden Rule

> **"MCP Connects Agents Downward to Typed, Scoped Tools; A2A Connects Agents Horizontally as Opaque Task Services; Every Call Enforces Least Agency, Stateless Transport, and Audience-Bound OAuth 2.1."**

### The Five Non-Negotiable Invariants

1. **Stateless Core & Streamable HTTP (MCP 2026)**: Remote production MCP servers MUST use the **Streamable HTTP** transport with per-request stateless context rather than legacy long-lived SSE-only sessions. This enables horizontal scaling behind load balancers, edge gateways, and serverless platforms. Reserve `stdio` strictly for local developer CLI subprocesses.
2. **OAuth 2.1 + RFC 8707 Resource Indicators (R-229)**: Remote MCP servers MUST NEVER rely on shared static API keys or pass-through user super-tokens. Clients MUST authenticate via OAuth 2.1 (PKCE required) with explicit `resource` audience binding (RFC 8707) so tokens issued for one MCP server cannot be replayed against another downstream API (preventing confused-deputy / ASI03 privilege abuse).
3. **Least Agency & Tool Sandboxing (OWASP ASI02 / ASI03 / R-228)**: Expose the minimum set of read/write tools required for the workflow. Separate read-only tools from state-mutating tools, declare explicit tool annotations (`readOnlyHint`, `destructiveHint`, `idempotentHint`), and require human-in-the-loop (HITL) elicitation or confirmation tokens for destructive mutations (R-200).
4. **Input Schema Validation & Untrusted Output Quarantine (OWASP ASI01 / ASI06)**: Validate every tool argument against strict JSON Schema / Zod / Pydantic models before execution. Treat all tool outputs, external documents, and A2A peer artifacts as **untrusted data** — never concatenate them raw into system instructions.
5. **Signed Identity & Replay-Protected A2A Delegation (OWASP ASI07)**: Inter-agent A2A calls MUST verify peer Agent Cards over TLS 1.3, enforce explicit authentication schemes (`oauth2`, `mtls`, or signed JWT assertions), bound task recursion depth (preventing ASI08 cascading failures), and attach W3C Trace Context (`traceparent`) across every hop.

---

## 3. Production Implementation Blueprints

### 3.1 Hardened Stateless MCP Server (TypeScript + Zod + RFC 8707 Audience Check)

```typescript
import { z } from "zod";
import { jwtVerify, createRemoteJWKSet } from "jose";

const EXPECTED_RESOURCE_URI = "https://mcp.internal.example.com/v1";
const JWKS = createRemoteJWKSet(
  new URL("https://auth.internal.example.com/.well-known/jwks.json")
);

const GetInvoiceInputSchema = z.object({
  invoiceId: z.string().regex(/^inv_[a-zA-Z0-9]{16,32}$/),
});

export interface VerifiedMcpPrincipal {
  readonly subject: string;
  readonly tenantId: string;
  readonly scopes: ReadonlySet<string>;
}

/**
 * Verifies OAuth 2.1 Bearer JWT with strict RFC 8707 audience binding.
 * Fails closed on missing token, expired token, or mismatched audience.
 */
export async function verifyMcpAccessToken(
  authorizationHeader: string | undefined
): Promise<VerifiedMcpPrincipal> {
  if (!authorizationHeader?.startsWith("Bearer ")) {
    throw new Error("UNAUTHORIZED: Missing Bearer token");
  }
  const token = authorizationHeader.slice("Bearer ".length).trim();

  const { payload } = await jwtVerify(token, JWKS, {
    issuer: "https://auth.internal.example.com",
    audience: EXPECTED_RESOURCE_URI, // RFC 8707 strict resource binding
    algorithms: ["RS256", "EdDSA"],
  });

  const subject = typeof payload.sub === "string" ? payload.sub : "";
  const tenantId = typeof payload["tenant_id"] === "string" ? payload["tenant_id"] : "";
  const scopeStr = typeof payload["scope"] === "string" ? payload["scope"] : "";

  if (!subject || !tenantId) {
    throw new Error("FORBIDDEN: Token missing required identity claims");
  }

  return {
    subject,
    tenantId,
    scopes: new Set(scopeStr.split(/\s+/).filter(Boolean)),
  };
}

/**
 * Read-only MCP tool handler with strict schema validation, scope enforcement,
 * and tenant-isolated data access (OWASP A01:2025 + ASI02 + ASI03).
 */
export async function handleGetInvoiceTool(
  rawArgs: unknown,
  principal: VerifiedMcpPrincipal,
  loadInvoice: (tenantId: string, invoiceId: string) => Promise<Record<string, unknown> | null>
): Promise<{ content: Array<{ type: "text"; text: string }>; isError?: boolean }> {
  if (!principal.scopes.has("invoices:read")) {
    return {
      isError: true,
      content: [{ type: "text", text: "Forbidden: missing required scope invoices:read" }],
    };
  }

  const parsed = GetInvoiceInputSchema.safeParse(rawArgs);
  if (!parsed.success) {
    return {
      isError: true,
      content: [{ type: "text", text: `Invalid arguments: ${parsed.error.message}` }],
    };
  }

  const invoice = await loadInvoice(principal.tenantId, parsed.data.invoiceId);
  if (!invoice) {
    return {
      isError: true,
      content: [{ type: "text", text: "Invoice not found in caller tenant scope" }],
    };
  }

  return {
    content: [{ type: "text", text: JSON.stringify(invoice) }],
  };
}
```

### 3.2 A2A Agent Card (`/.well-known/agent-card.json`)

```json
{
  "name": "security-audit-agent",
  "description": "Performs deterministic SAST, dependency SCA, and threat-model verification on pull request diffs.",
  "url": "https://agents.internal.example.com/security-audit/a2a",
  "version": "1.0.0",
  "capabilities": {
    "streaming": true,
    "pushNotifications": false,
    "stateTransitionHistory": true
  },
  "authentication": {
    "schemes": ["oauth2"],
    "credentials": "https://auth.internal.example.com/.well-known/oauth-authorization-server"
  },
  "defaultInputModes": ["application/json", "text/plain"],
  "defaultOutputModes": ["application/json"],
  "skills": [
    {
      "id": "audit-pr-diff",
      "name": "Audit Pull Request Diff",
      "description": "Scans a scoped git diff for OWASP Top 10:2025 and ASI01-ASI10 risks and returns structured SARIF findings.",
      "tags": ["security", "owasp", "sast", "code-review"]
    }
  ]
}
```

---

## 4. OWASP Agentic Security Hardening (ASI01–ASI10 & AST10)

| Risk ID | Threat Vector | Mandatory Engineering Control |
|---|---|---|
| **ASI01** | Agent Goal Hijack (indirect prompt injection via tool output/web content) | Isolate untrusted content in structured data fields; enforce declarative authorization outside the LLM context window. |
| **ASI02** | Tool Misuse & Exploitation | Strict JSON Schema validation, allowlisted command/URL arguments, rate limits per tool, explicit `destructiveHint` gating. |
| **ASI03** | Identity & Privilege Abuse (token pass-through / over-scoped credentials) | OAuth 2.1 with RFC 8707 audience binding, short-lived scoped tokens (≤ 15m), zero ambient admin credentials. |
| **ASI04** | Agentic Supply Chain Vulnerabilities (malicious MCP server / skill / plugin) | Pin MCP server versions/digests, verify checksums/signatures, audit `SKILL.md` scripts before execution, ban dynamic remote code loading. |
| **ASI05** | Unexpected Code Execution | Execute agent-generated code exclusively inside ephemeral, network-restricted sandboxes (containers/microVMs) with non-root UID and CPU/RAM caps. |
| **ASI06** | Memory & Context Poisoning | Sign/version persistent memory entries, apply TTLs, validate RAG chunk provenance, separate per-tenant vector namespaces. |
| **ASI07** | Insecure Inter-Agent Communication | Enforce TLS 1.3 + mTLS or OAuth 2.1 on A2A links; verify Agent Card origin and task correlation IDs. |
| **ASI08** | Cascading Failures | Enforce max recursion/hop depth (`maxHops <= 3`), per-task token/time budgets, circuit breakers, and Saga rollbacks (R-194–R-197). |
| **ASI09** | Human-Agent Trust Exploitation | Present raw command diffs, target resources, and impact summaries (not persuasive prose) in HITL approval prompts. |
| **ASI10** | Rogue Agents | Immutable audit logs of every tool call (`tool_name`, `principal`, `args_hash`, `exit_code`, `trace_id`), kill-switch revocation, deterministic harness hooks (`PreToolUse`/`Stop`). |

---

## 5. Common Anti-Patterns

- **Token Passthrough Anti-Pattern**: Forwarding a user's broad session JWT directly from an MCP server to an upstream API without token exchange and RFC 8707 audience scoping.
- **Unbounded Tool Surface**: Exposing raw SQL execution (`run_sql(query)`) or unconstrained shell execution (`exec(cmd)`) over a remote MCP endpoint instead of narrow, parameterized domain tools.
- **Stateful In-Memory Session Pinning**: Storing MCP session state only in local process RAM, causing random failures behind multi-replica Kubernetes Ingress or serverless autoscalers.
- **Unbounded A2A Fan-Out**: Allowing Agent A → Agent B → Agent A cycles without hop limits, fencing tokens (R-193), or cost ceilings.

---

## 6. Verification Checklist

- [ ] **Transport**: Remote MCP server implements Streamable HTTP with stateless request handling.
- [ ] **AuthZ**: OAuth 2.1 Bearer JWT verified with strict `iss`, `aud` (RFC 8707 resource URI), `exp`, and fine-grained `scope` checks.
- [ ] **Schemas**: 100% of tool parameters validated via Zod/Pydantic; unknown fields rejected (`strict()`).
- [ ] **Least Agency**: Destructive tools separated from read-only tools and gated behind explicit confirmation/HITL policy.
- [ ] **Observability**: Every MCP tool call and A2A task emits OpenTelemetry GenAI spans with `traceparent` propagation and scrubbed arguments.
- [ ] **Supply Chain**: All third-party MCP servers and skills pinned by immutable version/digest and audited before deployment.
