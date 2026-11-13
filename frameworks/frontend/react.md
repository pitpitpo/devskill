# ⚛️ React Production Guide (`react.md`)

> **Framework**: React 18 / 19  
> **Classification**: Core Frontend Component Architecture  
> **Core Philosophy**: "UI is a Pure Function of State; Minimize Renders, Maximize Predictability."

---

## 1. Concurrency & Non-Blocking Transitions

React 18+ introduces concurrent rendering to keep user input responsive during expensive renders.

```typescript
import React, { useState, useTransition } from 'react';

export function SearchCatalog({ items }: { items: string[] }) {
  const [query, setQuery] = useState('');
  const [filteredItems, setFilteredItems] = useState(items);
  const [isPending, startTransition] = useTransition();

  function handleSearch(e: React.ChangeEvent<HTMLInputElement>) {
    const value = e.target.value;
    // 1. High-priority immediate update (Input keeps feeling snappy)
    setQuery(value);

    // 2. Low-priority non-blocking transition (Filtering heavy list)
    startTransition(() => {
      const results = items.filter((item) =>
        item.toLowerCase().includes(value.toLowerCase())
      );
      setFilteredItems(results);
    });
  }

  return (
    <div className="space-y-4">
      <input
        type="text"
        value={query}
        onChange={handleSearch}
        placeholder="Filter catalog..."
        className="border p-2 rounded w-full"
      />
      {isPending && <p className="text-sm text-gray-500">Updating list...</p>}
      <ul className="divide-y">
        {filteredItems.map((item) => (
          <li key={item} className="py-1">{item}</li>
        ))}
      </ul>
    </div>
  );
}
```

---

## 2. Memoization Guidelines (When to Memoize vs When Not To)

Premature memoization adds memory and comparison overhead. Follow these rules:

| Technique | When to Use | When NOT to Use |
|---|---|---|
| `React.memo` | Heavy components re-rendering frequently with identical props | Lightweight leaf components with cheap JSX |
| `useMemo` | Expensive calculations (>1,000 array iterations, complex parsing) | Simple calculations (`a + b`, short array filters) |
| `useCallback` | Callbacks passed to memoized children or hook dependency arrays | Standard event handlers passed to native elements (`<button onClick={...}>`) |

---

## 3. Production Error Boundaries

Never let an unhandled component error crash the entire application window:

```typescript
import React, { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  fallback?: ReactNode;
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = { hasError: false };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Send to Sentry, Datadog or central telemetry
    console.error('ErrorBoundary caught:', error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return (
        this.props.fallback || (
          <div className="p-4 border border-red-300 bg-red-50 rounded text-red-800">
            <h2 className="font-bold text-lg">Component Failed to Load</h2>
            <p className="text-sm">{this.state.error?.message}</p>
          </div>
        )
      );
    }
    return this.props.children;
  }
}
```

---

## 4. Anti-Patterns to Eliminate

1. ❌ **Mirroring Props in State**: Never initialize state from props (`const [val, setVal] = useState(props.val)`) unless specifically creating an editable local draft. Derive values during render instead.
2. ❌ **Effects for Data Transformation**: Never use `useEffect` to transform state when it can be calculated synchronously in the component body.
3. ❌ **Index as Key in Dynamic Lists**: Always use unique, stable IDs (`item.id`) as keys. Using array index causes state corruption when items are sorted or filtered.
