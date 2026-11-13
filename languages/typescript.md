# 🟦 TypeScript Production Standard (`typescript.md`)

> **Language**: TypeScript 5.4+  
> **Classification**: Idiomatic Type-Safe Development  
> **Core Philosophy**: "If It Compiles with Strict Mode and Zod Parsers, It Does Not Crash at Runtime."

---

## 1. Non-Negotiable `tsconfig.json` Compiler Baseline

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true,
    "strictFunctionTypes": true,
    "strictBindCallApply": true,
    "strictPropertyInitialization": true,
    "noImplicitThis": true,
    "alwaysStrict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true,
    "forceConsistentCasingInFileNames": true,
    "skipLibCheck": true
  }
}
```

---

## 2. The Zero-`any` Policy & Type Narrowing

Never use `any`. When dealing with unknown payloads (API responses, event data), use `unknown` combined with custom type predicates or schema validation:

```typescript
// Custom Type Predicate
function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

// Discriminated Union Pattern (Exhaustive Type Checking)
type PaymentState =
  | { status: 'PENDING'; initiatedAt: Date }
  | { status: 'SUCCEEDED'; transactionId: string; amount: number }
  | { status: 'FAILED'; errorCode: string; retryCount: number };

function handlePayment(state: PaymentState) {
  switch (state.status) {
    case 'PENDING':
      return `Waiting since ${state.initiatedAt.toISOString()}`;
    case 'SUCCEEDED':
      return `Charged $${state.amount} (Tx: ${state.transactionId})`;
    case 'FAILED':
      return `Failed with code ${state.errorCode}`;
    default: {
      // Compile-time exhaustiveness check: causes compilation error if a new state is added!
      const _exhaustiveCheck: never = state;
      throw new Error(`Unhandled payment state: ${_exhaustiveCheck}`);
    }
  }
}
```

---

## 3. Runtime Parsing with Zod

```typescript
import { z } from 'zod';

export const UserSchema = z.object({
  id: z.string().uuid(),
  email: z.string().email(),
  role: z.enum(['ADMIN', 'MEMBER', 'VIEWER']),
  metadata: z.record(z.string(), z.unknown()).optional(),
});

// Infer static TypeScript type directly from runtime schema
export type User = z.infer<typeof UserSchema>;

export function parseIncomingUser(raw: unknown): User {
  return UserSchema.parse(raw);
}
```
