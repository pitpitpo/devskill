# 🐹 Go Production Standard (`golang.md`)

> **Language**: Go 1.22+  
> **Classification**: Systems Programming & High-Throughput Microservices  
> **Core Philosophy**: "Clear is Better Than Clever; Explicit Error Handling; Concurrency via Channels."

---

## 1. Project Layout & Package Architecture

Follow the standard Go application layout:
```
myproject/
├── cmd/
│   └── server/
│       └── main.go
├── internal/          # Code private to this repository (cannot be imported externally)
│   ├── domain/
│   ├── repository/
│   └── service/
├── pkg/               # Public reusable packages
├── go.mod
└── go.sum
```

---

## 2. Explicit Error Wrapping (`%w`)

Never discard errors. Wrap errors with contextual information:

```go
package service

import (
	"errors"
	"fmt"
)

var ErrUserNotFound = errors.New("user not found")

func (s *UserService) GetUserEmail(id string) (string, error) {
	user, err := s.repo.FindByID(id)
	if err != nil {
		if errors.Is(err, ErrUserNotFound) {
			return "", ErrUserNotFound
		}
		// Wrap with context using %w to preserve error chain
		return "", fmt.Errorf("failed to fetch user %s from repository: %w", id, err)
	}
	return user.Email, nil
}
```

---

## 3. Concurrency & Context Cancellation

Always accept `context.Context` as the first argument in I/O operations and respect cancellation:

```go
func (p *WorkerPool) ProcessTasks(ctx context.Context, tasks <-chan Task) {
	for {
		select {
		case <-ctx.Done():
			// Gracefully terminate worker on signal or timeout
			return
		case task, ok := <-tasks:
			if !ok {
				return // Channel closed
			}
			p.execute(ctx, task)
		}
	}
}
```

---

## 4. Interface Rules

- **Accept interfaces, return structs**: Functions should receive interfaces for loose coupling and return concrete structs for clarity.
- Keep interfaces small (Single-method interfaces like `io.Reader`, `io.Writer`).
