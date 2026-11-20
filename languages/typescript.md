# 🟦 TypeScript Production Standard (`typescript.md`)

> **Standard**: TypeScript 5.8–6.0 / 7.0 (`tsgo` Native Compiler, Strict Type System, ECMAScript 2024+ Target)  
> **Tooling Stack**: NodeNext / Bundler Resolution, Zod v4 / Valibot v1, `tsgo` / `tsc`, Vitest  
> **Classification**: Strict Compile-Time Invariance, Idiomatic Type Systems, & Enterprise Web/Node Architecture  
> **Applicability**: Fullstack Engineers, Platform Architects, API Gateway & Core Backend Developers  
> **Prerequisites**: Structural Typing Mechanics, Type Lattice Theory, JavaScript Event Loop & Prototype Model  

---

## 1. Title, Metadata & Scope

TypeScript has evolved from a convenient JavaScript superset into an enterprise-grade type system capable of modeling complex distributed architectures, compile-time invariants, and runtime boundary contracts. However, without rigorous compiler governance and idiomatic discipline, production TypeScript systems routinely degenerate into "Type Soup":
1. **The `any` Contagion**: Pervasive use of `any` and unconstrained type assertions (`as unknown as T`) that subvert compiler checks and lead to runtime `TypeError: Cannot read properties of undefined`.
2. **Runtime Contract Decoupling**: Static types that drift from actual JSON payloads across REST, GraphQL, and message queue boundaries due to missing schema validation.
3. **Exception-Driven Control Flow**: Unchecked thrown exceptions bubbling across asynchronous call stacks, causing unhandled promise rejections and crashing Node.js processes.
4. **Permissive Compiler Configurations**: Legacy `tsconfig.json` baselines that permit implicit anys, unchecked indexed access, and lenient nullability.
5. **Slow Typecheck Cycles**: Poorly tuned project references and unbounded generic recursive types that degrade developer feedback loops and CI build times.

This standard establishes a non-negotiable engineering manual for writing high-performance, strictly typed TypeScript 5.5+ applications. It covers strict compiler settings, advanced type narrowing, generic abstractions, mapped and conditional types, schema validation with Zod and Valibot, functional `Result<T, E>` error handling, and memory-conscious compiler tuning.

---

## 2. Core Philosophy & Golden Rules

> **"If It Compiles Under Strict Invariance and Parses Through Runtime Schemas, It Cannot Crash at Runtime."**

Every TypeScript codebase under this standard must adhere to five foundational golden rules:

1. **Zero Tolerance for `any`**: The `any` keyword disables the type checker. Any dynamic, untyped, or external data must be typed as `unknown` and subsequently narrowed using type predicates or parsed using validated schemas.
2. **Total Boundary Validation**: Never trust incoming external data (HTTP bodies, query strings, environmental variables, database query results, Redis caches). Every boundary must be guarded by runtime parsers (Zod or Valibot) that act as single sources of truth.
3. **Explicit, Checked Errors as Values**: Avoid throwing untyped runtime exceptions for expected business failures. Expected failures must be returned as typed values using the `Result<T, E>` pattern, forcing callers to exhaustively handle success and failure branches.
4. **Exhaustive Control Flow**: Switch statements and discriminated union evaluations must always enforce compile-time exhaustiveness via the `never` type check to guarantee that new domain variants cannot be forgotten.
5. **No Blind Type Assertions (`as`)**: The `as` operator is a compiler escape hatch. Avoid type assertions except at the most constrained low-level driver boundaries where type narrowing cannot prove correctness.

---

## 3. Architecture & Type System Internals

To write performant TypeScript and avoid compiler bottlenecks, engineers must understand the compiler's underlying mechanics.

### 3.1 Structural Typing vs. Nominal Typing & Nominal Brand Invariants

TypeScript's type system is **structural** (duck-typed): if two types share the same shape, they are mutually assignable. While flexible, this leads to the **primitive obsession** vulnerability, where distinct domain concepts (e.g., `UserId`, `AccountId`, `EmailAddress`) become interchangeable strings or numbers.

```
                  TypeScript Structural vs Nominal Brands
                  
   ┌─────────────────────────────────────────────────────────┐
   │ Structural Equivalence (Dangerous Domain Interchange)   │
   │                                                         │
   │   type UserId = string;                                 │
   │   type AccountId = string;                              │
   │                                                         │
   │   const user: UserId = "usr_123";                       │
   │   const acc: AccountId = user; // ❌ Valid! Compiles!   │
   └────────────────────────────┬────────────────────────────┘
                                │
                                ▼
   ┌─────────────────────────────────────────────────────────┐
   │ Nominal Branding (Compile-Time Invariant Enforcement)   │
   │                                                         │
   │   type Brand<K, T> = K & { readonly __brand: T };       │
   │   type UserId = Brand<string, "UserId">;                │
   │   type AccountId = Brand<string, "AccountId">;          │
   │                                                         │
   │   const user: UserId = makeUserId("usr_123");           │
   │   const acc: AccountId = user; // ⛔ Compile Error!     │
   └─────────────────────────────────────────────────────────┘
```

Branding enforces nominal separation with zero runtime memory overhead: the `__brand` property exists purely in the compiler's type checker and is stripped during emit.

### 3.2 The Type Lattice: `unknown` vs `any` vs `never`

The TypeScript type hierarchy forms a mathematical lattice:
- **`unknown` (Top Type)**: The set of all possible values. Any value can be assigned to `unknown`, but no properties or methods can be accessed on an `unknown` value without prior narrowing.
- **`any` (Escape Hatch)**: Both top and bottom type simultaneously. Disables type safety and bypasses the lattice. Prohibited in production.
- **`never` (Bottom Type / Empty Set)**: Represents values that can never occur. Nothing can be assigned to `never` (except `never` itself). It is used to prove exhaustiveness in dead code branches.

```
                           unknown (Top Type)
                                  ▲
                                  │
                   ┌──────────────┴──────────────┐
                   │                             │
                string        number         boolean ...
                   │                             │
                   └──────────────┬──────────────┘
                                  │
                                  ▼
                            never (Bottom Type)
```

---

## 4. Concrete Production Code & Patterns

### 4.1 Non-Negotiable `tsconfig.json` Strict Tuning

A production `tsconfig.json` must activate all strictness flags, modern module resolution, and path mappings.

```json
{
  "$schema": "https://json.schemastore.org/tsconfig",
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["ES2022"],
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "rootDir": "./src",
    "outDir": "./dist",
    
    /* Strict Type-Checking Options */
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true,
    "strictFunctionTypes": true,
    "strictBindCallApply": true,
    "strictPropertyInitialization": true,
    "noImplicitThis": true,
    "alwaysStrict": true,
    
    /* Additional Error-Detection Checks */
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "exactOptionalPropertyTypes": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true,
    "noUncheckedIndexedAccess": true,
    "noImplicitOverride": true,
    "noPropertyAccessFromIndexSignature": true,
    "allowUnusedLabels": false,
    "allowUnreachableCode": false,
    
    /* Module and Emit Rules */
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true,
    "removeComments": true,
    "isolatedModules": true,
    "verbatimModuleSyntax": true,
    "forceConsistentCasingInFileNames": true,
    "skipLibCheck": true
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist", "**/*.spec.ts", "**/*.test.ts"]
}
```

---

### 4.2 Nominal Typing, Discriminated Unions & Exhaustiveness

```typescript
// src/domain/types.ts

// 1. Nominal Branding Utility
declare const brandSymbol: unique symbol;
export type Brand<T, B extends string> = T & { readonly [brandSymbol]: B };

export type UserId = Brand<string, 'UserId'>;
export type OrderId = Brand<string, 'OrderId'>;
export type Cents = Brand<number, 'Cents'>;

export function makeUserId(raw: string): UserId {
  if (!/^usr_[a-zA-Z0-9]{16}$/.test(raw)) {
    throw new Error(`Invalid UserId format: ${raw}`);
  }
  return raw as UserId;
}

export function makeCents(raw: number): Cents {
  if (!Number.isInteger(raw) || raw < 0) {
    throw new Error(`Monetary amount in cents must be non-negative integer: ${raw}`);
  }
  return raw as Cents;
}

// 2. Discriminated Union Event Hierarchy
export type PaymentMethod =
  | { readonly type: 'CREDIT_CARD'; readonly cardLast4: string; readonly expMonth: number; readonly expYear: number }
  | { readonly type: 'BANK_TRANSFER'; readonly iban: string; readonly bic: string }
  | { readonly type: 'CRYPTO'; readonly walletAddress: string; readonly network: 'MAINNET' | 'POLYGON' };

export type OrderEvent =
  | { readonly kind: 'ORDER_CREATED'; readonly orderId: OrderId; readonly userId: UserId; readonly amount: Cents }
  | { readonly kind: 'ORDER_PAID'; readonly orderId: OrderId; readonly paymentMethod: PaymentMethod; readonly paidAt: Date }
  | { readonly kind: 'ORDER_CANCELLED'; readonly orderId: OrderId; readonly reason: string; readonly cancelledAt: Date };

// 3. Exhaustiveness Checking via Bottom Type (never)
export function assertNever(x: never, customMessage?: string): never {
  throw new Error(customMessage ?? `Unhandled discriminated union member: ${JSON.stringify(x)}`);
}

export function formatOrderAuditLog(event: OrderEvent): string {
  switch (event.kind) {
    case 'ORDER_CREATED':
      return `[CREATED] Order ${event.orderId} for User ${event.userId} (Amount: $${(event.amount / 100).toFixed(2)})`;
    case 'ORDER_PAID':
      return `[PAID] Order ${event.orderId} via ${event.paymentMethod.type} at ${event.paidAt.toISOString()}`;
    case 'ORDER_CANCELLED':
      return `[CANCELLED] Order ${event.orderId}: ${event.reason}`;
    default:
      // If a new event is added to OrderEvent, compiler will throw a type error here!
      return assertNever(event);
  }
}
```

---

### 4.3 Advanced Generics, Conditional Types & Mapped Types

```typescript
// src/types/metaprogramming.ts

// 1. Deep Readonly Mapped Type (Recursively prevents mutation)
export type DeepReadonly<T> = T extends Function | boolean | number | string | symbol | null | undefined
  ? T
  : T extends Array<infer U>
    ? ReadonlyArray<DeepReadonly<U>>
    : T extends Map<infer K, infer V>
      ? ReadonlyMap<DeepReadonly<K>, DeepReadonly<V>>
      : T extends Set<infer M>
        ? ReadonlySet<DeepReadonly<M>>
        : { readonly [P in keyof T]: DeepReadonly<T[P]> };

// 2. Nested Key Paths Extractor
export type NestedKeyOf<ObjectType extends object> = {
  [Key in keyof ObjectType & (string | number)]: ObjectType[Key] extends object
    ? `${Key}` | `${Key}.${NestedKeyOf<ObjectType[Key]>}`
    : `${Key}`;
}[keyof ObjectType & (string | number)];

// 3. Conditional Type Filtering by Value Type
export type SubType<Base, Condition> = Pick<
  Base,
  { [Key in keyof Base]: Base[Key] extends Condition ? Key : never }[keyof Base]
>;

// Example usage:
interface ServerConfiguration {
  host: string;
  port: number;
  maxConnections: number;
  ssl: {
    enabled: boolean;
    certPath: string;
  };
}

export type StringConfigPaths = SubType<ServerConfiguration, string>; // { host: string }
export type ConfigDotPaths = NestedKeyOf<ServerConfiguration>; 
// "host" | "port" | "maxConnections" | "ssl" | "ssl.enabled" | "ssl.certPath"
```

---

### 4.4 Result<T, E> Functional Error Handling Pattern

Instead of throwing untyped runtime errors that can bubble unexpectedly, use an explicit `Result` container:

```typescript
// src/core/result.ts

export type Result<T, E = Error> =
  | { readonly ok: true; readonly value: T }
  | { readonly ok: false; readonly error: E };

export const Result = {
  ok<T>(value: T): Result<T, never> {
    return { ok: true, value };
  },

  fail<E>(error: E): Result<never, E> {
    return { ok: false, error };
  },

  map<T, U, E>(result: Result<T, E>, fn: (val: T) => U): Result<U, E> {
    return result.ok ? Result.ok(fn(result.value)) : result;
  },

  flatMap<T, U, E, F>(
    result: Result<T, E>,
    fn: (val: T) => Result<U, F>
  ): Result<U, E | F> {
    return result.ok ? fn(result.value) : result;
  },

  async fromAsync<T, E = Error>(
    promise: Promise<T>,
    onError: (err: unknown) => E
  ): Promise<Result<T, E>> {
    try {
      const data = await promise;
      return Result.ok(data);
    } catch (err) {
      return Result.fail(onError(err));
    }
  },
};
```

#### Real-World Service Using `Result<T, E>`
```typescript
// src/services/account-service.ts
import { Result } from '../core/result.js';
import { Cents, makeCents, UserId } from '../domain/types.js';

export interface InsufficientFundsError {
  readonly code: 'INSUFFICIENT_FUNDS';
  readonly required: Cents;
  readonly available: Cents;
}

export interface AccountNotFoundError {
  readonly code: 'ACCOUNT_NOT_FOUND';
  readonly userId: UserId;
}

export type DebitError = InsufficientFundsError | AccountNotFoundError;

export class AccountService {
  private readonly ledger = new Map<UserId, Cents>();

  public getBalance(id: UserId): Result<Cents, AccountNotFoundError> {
    const balance = this.ledger.get(id);
    if (balance === undefined) {
      return Result.fail({ code: 'ACCOUNT_NOT_FOUND', userId: id });
    }
    return Result.ok(balance);
  }

  public debit(
    userId: UserId,
    amount: Cents
  ): Result<{ newBalance: Cents }, DebitError> {
    const balanceResult = this.getBalance(userId);
    if (!balanceResult.ok) {
      return balanceResult;
    }

    const currentBalance = balanceResult.value;
    if (currentBalance < amount) {
      return Result.fail({
        code: 'INSUFFICIENT_FUNDS',
        required: amount,
        available: currentBalance,
      });
    }

    const newBalance = makeCents(currentBalance - amount);
    this.ledger.set(userId, newBalance);
    return Result.ok({ newBalance });
  }
}
```

---

### 4.5 Boundary Runtime Schema Validation (Zod & Valibot)

#### 1. Zod Industrial-Grade Validation
```typescript
// src/schemas/user-schema.ts
import { z } from 'zod';
import { makeCents, makeUserId, UserId } from '../domain/types.js';

export const UserRegistrationSchema = z.object({
  email: z.string().email().max(255).toLowerCase().trim(),
  password: z
    .string()
    .min(12, 'Password must be at least 12 characters')
    .regex(/[A-Z]/, 'Must contain at least one uppercase letter')
    .regex(/[0-9]/, 'Must contain at least one number')
    .regex(/[^A-Za-z0-9]/, 'Must contain at least one special character'),
  role: z.enum(['ADMIN', 'ENGINEER', 'ANALYST']).default('ENGINEER'),
  initialDepositCents: z
    .number()
    .int()
    .nonnegative()
    .transform((val) => makeCents(val)),
  preferences: z
    .object({
      theme: z.enum(['LIGHT', 'DARK', 'SYSTEM']).default('SYSTEM'),
      marketingOptIn: z.boolean().default(false),
    })
    .default({}),
});

export type UserRegistrationInput = z.input<typeof UserRegistrationSchema>;
export type UserRegistrationDTO = z.infer<typeof UserRegistrationSchema>;
```

#### 2. Valibot Ultra-Lightweight Zero-Overhead Validation
Valibot provides modular, tree-shakeable validation, reducing client and serverless bundle sizes by over 90% compared to Zod.

```typescript
// src/schemas/valibot-schema.ts
import * as v from 'valibot';

export const ApiKeyHeaderSchema = v.object({
  'x-api-key': v.pipe(
    v.string('Header x-api-key is required'),
    v.regex(/^live_sec_[a-zA-Z0-9]{32}$/, 'Invalid live secret API key format')
  ),
  'x-client-timestamp': v.pipe(
    v.string(),
    v.transform((val) => Number.parseInt(val, 10)),
    v.number(),
    v.check(
      (ts) => Math.abs(Date.now() - ts) < 300_000,
      'Timestamp drift exceeds 5-minute skew window'
    )
  ),
});

export type ApiKeyHeader = v.InferOutput<typeof ApiKeyHeaderSchema>;
```


### 4.6 Advanced Type Narrowing & Custom Type Predicates

Type predicates (`value is Type`) and assertion functions (`asserts value is Type`) allow safe runtime type discrimination across heterogeneous data.

```typescript
// src/utils/narrowing.ts

/**
 * Validates whether an unknown value is a non-null object record.
 */
export function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

/**
 * Validates whether an unknown value is a non-empty string.
 */
export function isNonEmptyString(value: unknown): value is string {
  return typeof value === 'string' && value.trim().length > 0;
}

/**
 * Safe object key check that preserves type narrowing on the target record.
 */
export function hasProperty<T extends object, K extends PropertyKey>(
  obj: T,
  prop: K
): obj is T & Record<K, unknown> {
  return Object.prototype.hasOwnProperty.call(obj, prop);
}

/**
 * Runtime assertion function that throws if the condition is not met.
 * Narrowing takes effect across the remainder of the containing function scope.
 */
export function assertCondition(
  condition: boolean,
  message: string
): asserts condition {
  if (!condition) {
    throw new TypeError(`Assertion failure: ${message}`);
  }
}

// Example usage:
export function processRawApiResponse(payload: unknown): { id: string; count: number } {
  assertCondition(isRecord(payload), 'Payload must be an object');
  assertCondition(hasProperty(payload, 'id') && isNonEmptyString(payload.id), 'Payload must have valid id');
  assertCondition(hasProperty(payload, 'count') && typeof payload.count === 'number', 'Payload must have valid count');
  
  // Here, TypeScript has successfully narrowed `payload` to contain `id: string` and `count: number`
  return {
    id: payload.id,
    count: payload.count,
  };
}
```

---

### 4.7 Testing Strictly-Typed Systems with Vitest & Type Testing

Modern test suites must verify both runtime behavior and compile-time type assignments:

```typescript
// src/services/account-service.spec.ts
import { describe, expect, expectTypeOf, it } from 'vitest';
import { Result } from '../core/result.js';
import { makeCents, makeUserId } from '../domain/types.js';
import { AccountService } from './account-service.js';

describe('AccountService Strict Type Tests', () => {
  it('should verify return type signatures at compile time', () => {
    const service = new AccountService();
    const userId = makeUserId('usr_1234567890abcdef');
    
    const balanceResult = service.getBalance(userId);
    
    // Vitest compile-time type verification
    expectTypeOf(balanceResult).toEqualTypeOf<
      Result<ReturnType<typeof makeCents>, { readonly code: 'ACCOUNT_NOT_FOUND'; readonly userId: ReturnType<typeof makeUserId> }>
    >();
  });

  it('should prevent debit when balance is insufficient', () => {
    const service = new AccountService();
    const userId = makeUserId('usr_1234567890abcdef');
    
    // Pre-deposit via internal ledger mutation for testing
    // Debit attempt exceeding balance
    const debitResult = service.debit(userId, makeCents(5000));
    
    expect(debitResult.ok).toBe(false);
    if (!debitResult.ok) {
      expect(debitResult.error.code).toBe('ACCOUNT_NOT_FOUND');
    }
  });
});
```

---

## 5. Security & Performance Considerations

### 5.1 Security Guardrails in TypeScript Applications

1. **Prototype Pollution Protection**:
   Parsing untrusted JSON or recursively merging objects can allow attackers to inject malicious properties into `Object.prototype`.
   - Never use naive recursive merges (`target[k] = source[k]`).
   - Validate input against explicit schemas (`z.object()`) with strict keys.
   - Use `Object.create(null)` for in-memory dictionary maps to eliminate prototype inheritance.
2. **ReDoS (Regular Expression Denial of Service)**:
   Never run unchecked user input through complex nested backtracking regular expressions.
   ```typescript
   // ❌ VULNERABLE: Catastrophic backtracking on "aaaaaaaaaaaaaaaaaaaaaaaaaaaa!"
   const badRegex = /^([a-zA-Z0-9]+)*$/;

   // ✅ SAFE: Linear complexity or bounded length check first
   function safeValidate(input: string): boolean {
     if (input.length > 64) return false;
     return /^[a-zA-Z0-9]+$/.test(input);
   }
   ```
3. **Preventing Information Leakage via Serializers**:
   Internal domain entities often contain sensitive attributes (`passwordHash`, `ssn`, `salt`). Enforce projection types:
   ```typescript
   type PublicUser = Omit<UserEntity, 'passwordHash' | 'mfaSecret'>;
   ```
4. **Const Assertions (`as const`) for Immutable Literals**:
   Always use `as const` on static lookup tables to preserve literal types and enforce immutability:
   ```typescript
   export const HTTP_STATUS = {
     OK: 200,
     BAD_REQUEST: 400,
     UNAUTHORIZED: 401,
     FORBIDDEN: 403,
     NOT_FOUND: 404,
     INTERNAL_SERVER_ERROR: 500,
   } as const;

   export type HttpStatus = typeof HTTP_STATUS[keyof typeof HTTP_STATUS];
   ```

### 5.2 Compiler Tuning & Performance Optimization

1. **Eliminate Recursive Union Explosion**:
   Deeply nested conditional types can cause the TypeScript compiler (`tsc`) to consume gigabytes of memory and crash with `RangeError: Maximum call stack size exceeded`.
   - Prefer interfaces over type aliases for large object shapes; interfaces are cached internally by the compiler based on shape identity.
   - Avoid infinite recursive tuples or deeply nested JSON types without recursion termination depth counters.
2. **Project References and Incremental Builds**:
   For monorepos, split monolithic packages into independent `tsconfig.json` modules with `"composite": true` and `"incremental": true`. This enables `tsc --build` to recompile only modified modules.
3. **TS-Reset for Correct Standard Library Types**:
   Default TypeScript lib types contain unsound historical quirks (e.g., `JSON.parse` returns `any`, `fetch().json()` returns `any`, `Array.includes` is overly restrictive). Integrate `@total-typescript/ts-reset` in your root entry point to make built-ins return `unknown`.

---

## 6. Common Pitfalls & Anti-Patterns

### 6.1 The Dangerous Type Assertion (`as any` / `as T`)
```typescript
// ❌ BAD: Blind assertion disables all safety checks. Crashes at runtime!
const response = await fetch('/api/user');
const user = (await response.json()) as User;
console.log(user.profile.avatarUrl.toLowerCase()); 

// ✅ GOOD: Safely parse with Zod or type predicate
const rawData: unknown = await response.json();
const parsedResult = UserSchema.safeParse(rawData);
if (!parsedResult.success) {
  throw new Error(`Data corruption from API: ${parsedResult.error.message}`);
}
const user = parsedResult.data;
```

### 6.2 The Unchecked Non-Null Assertion Operator (`!`)
```typescript
// ❌ BAD: Assuming map contains key causes runtime null dereference
const user = userMap.get(id)!;
user.sendNotification();

// ✅ GOOD: Handle undefined explicitly
const user = userMap.get(id);
if (!user) {
  throw new EntityNotFoundError(`User ${id} not found in cache`);
}
user.sendNotification();
```

### 6.3 Using `Function` or `object` as Parameter Types
```typescript
// ❌ BAD: 'Function' allows any callable; 'object' permits any non-primitive
function execute(callback: Function, config: object) {
  callback();
}

// ✅ GOOD: Explicit signatures and generic constraints
function execute<TConfig extends Record<string, unknown>>(
  callback: (ctx: ExecutionContext) => Promise<void>,
  config: TConfig
): Promise<void> {
  // ...
}
```

### 6.4 Enums vs Const Object Unions
```typescript
// ❌ BAD: Numeric enums generate bloated IIFE JavaScript runtime code and allow reverse mapping leaks
enum UserRoleEnum {
  ADMIN,
  USER
}

// ✅ GOOD: Const object with union type. Emits zero JS overhead!
export const USER_ROLES = {
  ADMIN: 'ADMIN',
  USER: 'USER',
} as const;

export type UserRole = (typeof USER_ROLES)[keyof typeof USER_ROLES];
```

---

## 7. TypeScript 6.0 / 7.0 Native Compiler (`tsgo`) & 2026 Migration Rules

TypeScript 6.0 serves as the strict alignment bridge to TypeScript 7.0 (`tsgo`, the native Go-ported compiler delivering 8–12× faster cold type-checking and multi-core project builds).

- **Adopt `tsgo` in CI & Monorepos**: Run `tsgo --noEmit` (or `tsgo --build` with composite project references) for rapid feedback loops. Tune parallelism explicitly on constrained CI runners using `--checkers`, `--builders`, or `--singleThreaded` when memory ceilings are tight.
- **Eliminate Legacy 5.x Deprecations**:
  - Remove `moduleResolution: "node"` (Node10) in favor of `"NodeNext"` (backend/libraries) or `"Bundler"` (Vite/Next.js/Turbopack apps).
  - Avoid relying on standalone `"baseUrl": "."`; specify relative `./` prefixes directly in `"paths"` entries or prefer package.json `"imports"` (`#internal/*`) so Node.js, bundlers, and `tsgo` agree without custom resolvers.
  - Enable `"erasableSyntaxOnly": true` for Node.js 24 native TypeScript stripping compatibility where applicable (preferring `as const` objects over runtime `enum` and parameter properties).
- **Explicit Strictness**: Even though TypeScript 6.0+ defaults `"strict": true`, continue declaring `"noUncheckedIndexedAccess": true` and `"exactOptionalPropertyTypes": true` explicitly in `tsconfig.base.json`.

---

## 8. Verification Checklist

Before deploying TypeScript code to production, ensure every gate in this checklist is verified:

- [ ] **Compiler Strictness**: `tsc --noEmit` (or `tsgo --noEmit`) runs with 0 errors under `strict: true` and `noUncheckedIndexedAccess: true`.
- [ ] **Zero `any` Occurrences**: `eslint` rule `@typescript-eslint/no-explicit-any` is configured as `error` with no global overrides.
- [ ] **Runtime Boundary Verification**: Every HTTP endpoint, environment variable, and message handler decodes payloads using `Zod` or `Valibot`.
- [ ] **Exhaustive Unions**: All `switch` statements over discriminated unions contain an exhaustive `default: assertNever(val)` branch.
- [ ] **Explicit Domain Branding**: IDs and financial values use nominal brands (`Brand<string, "Id">`) to prevent primitive obsession.
- [ ] **Functional Error Handling**: Critical domain workflows return `Result<T, E>` rather than throwing untyped runtime exceptions.
- [ ] **Prototype Pollution Guard**: Dynamic object merges are validated against strict schemas or run on `Object.create(null)` maps.
- [ ] **Build Time Verification**: `tsc --build` / `tsgo --build` completes within the established CI timeout without unbounded memory growth.
