# Accessibility (a11y) — Production Guide

> Building inclusive applications that work for everyone. WCAG 2.2 AA compliance as the baseline.  
> **Core Philosophy**: "Web Accessibility (WCAG 2.2 AA) is non-negotiable human inclusion and legal compliance. Semantic HTML first, ARIA only when semantics fall short, and test every interaction via keyboard alone."

---

## Security & Performance Considerations

| Area | Focus | Standard Protocol |
| :--- | :--- | :--- |
| **Focus Hijacking & Trap Attacks** | Security | Modal dialogs must trap focus securely; closing the modal must restore focus to the trigger element without executing arbitrary script |
| **DOM Tree Bloat** | Performance | Deep nested trees degrade screen reader virtual navigation; maintain shallow semantic hierarchies |
| **Dynamic Announcement Saturation** | UX & Screen Reader Performance | Use `aria-live="polite"` for non-critical status updates to prevent interrupting assistive technology audio streams |

---

## Table of Contents

- [Why Accessibility Matters](#why-accessibility-matters)
- [WCAG 2.2 Principles](#wcag-22-principles)
- [Semantic HTML](#semantic-html)
- [ARIA Patterns](#aria-patterns)
- [Keyboard Navigation](#keyboard-navigation)
- [Forms & Validation](#forms--validation)
- [Color & Contrast](#color--contrast)
- [Images & Media](#images--media)
- [Dynamic Content](#dynamic-content)
- [Focus Management](#focus-management)
- [Testing](#testing)
- [React Component Patterns](#react-component-patterns)
- [Common Mistakes](#common-mistakes)
- [Checklist](#checklist)

---

## Why Accessibility Matters

1. **Legal requirement** — ADA, Section 508, EAA (EU), AODA (Canada)
2. **Market size** — 1.3 billion people globally live with disabilities
3. **SEO benefit** — Screen readers and search engines parse similar structures
4. **Better UX for everyone** — Captions help in noisy environments, keyboard nav helps power users

---

## WCAG 2.2 Principles

### POUR Framework

| Principle | Meaning | Key Guidelines |
|-----------|---------|---------------|
| **Perceivable** | Content can be perceived by all senses | Text alternatives, captions, contrast |
| **Operable** | UI can be operated by all users | Keyboard, timing, seizures, navigation |
| **Understandable** | Content and UI are understandable | Readable, predictable, error prevention |
| **Robust** | Works with current and future tech | Valid HTML, ARIA, name/role/value |

### Conformance Levels

| Level | Description | Required For |
|-------|-------------|-------------|
| **A** | Minimum accessibility | Basic compliance |
| **AA** | Addresses major barriers | **Most legal requirements** |
| **AAA** | Highest accessibility | Specialized applications |

---

## Semantic HTML

### Use Native Elements First

```html
<!-- ❌ BAD: div soup -->
<div class="button" onclick="submit()">Submit</div>
<div class="nav">
  <div class="link" onclick="navigate('/')">Home</div>
</div>
<div class="input-wrapper">
  <div class="label">Email</div>
  <div class="input" contenteditable="true"></div>
</div>

<!-- ✅ GOOD: semantic HTML -->
<button type="submit">Submit</button>
<nav>
  <a href="/">Home</a>
</nav>
<label for="email">Email</label>
<input type="email" id="email" required />
```

### Document Structure

```html
<!-- Proper heading hierarchy -->
<main>
  <h1>Page Title</h1>             <!-- Only ONE h1 per page -->

  <section aria-labelledby="section1">
    <h2 id="section1">Section</h2>
    <h3>Subsection</h3>           <!-- Never skip levels -->
  </section>

  <section aria-labelledby="section2">
    <h2 id="section2">Another Section</h2>
  </section>
</main>

<!-- Landmark regions -->
<header role="banner">...</header>
<nav role="navigation" aria-label="Main">...</nav>
<main role="main">...</main>
<aside role="complementary">...</aside>
<footer role="contentinfo">...</footer>
```

### HTML Elements Reference

| Need | Use | Not |
|------|-----|-----|
| Clickable action | `<button>` | `<div onclick>` |
| Navigation | `<a href>` | `<span onclick>` |
| List of items | `<ul>/<ol>/<li>` | `<div>` with bullets |
| Data grid | `<table>` with `<th>` | `<div>` grid |
| Form field label | `<label for>` | `<span>` near input |
| Required context | `<details>/<summary>` | JS-only accordion |
| Time/date | `<time datetime>` | Plain text |
| Abbreviation | `<abbr title>` | Plain text |

---

## ARIA Patterns

### The First Rule of ARIA

> **Don't use ARIA if you can use native HTML.** ARIA is a supplement, not a replacement.

### Common ARIA Attributes

```html
<!-- Labels -->
<button aria-label="Close dialog">×</button>
<nav aria-label="Main navigation">...</nav>
<section aria-labelledby="heading-id">
  <h2 id="heading-id">Products</h2>
</section>
<input aria-describedby="help-text" />
<p id="help-text">Password must be 8+ characters</p>

<!-- States -->
<button aria-expanded="false" aria-controls="menu1">Menu</button>
<div id="menu1" aria-hidden="true">...</div>

<button aria-pressed="true">Bold</button>
<input aria-invalid="true" aria-errormessage="email-error" />
<span id="email-error" role="alert">Invalid email address</span>

<!-- Live regions -->
<div aria-live="polite">        <!-- For non-urgent updates -->
  3 items in cart
</div>
<div aria-live="assertive">     <!-- For urgent alerts -->
  Error: Payment failed
</div>
<div role="status">             <!-- Implicit aria-live="polite" -->
  Saving...
</div>
<div role="alert">              <!-- Implicit aria-live="assertive" -->
  Session expired
</div>
```

### Modal Dialog Pattern

```html
<div
  role="dialog"
  aria-modal="true"
  aria-labelledby="dialog-title"
  aria-describedby="dialog-desc"
>
  <h2 id="dialog-title">Confirm Deletion</h2>
  <p id="dialog-desc">This action cannot be undone.</p>
  <button>Cancel</button>
  <button>Delete</button>
</div>
```

```typescript
// Focus trap for modals
function trapFocus(dialogElement: HTMLElement) {
  const focusable = dialogElement.querySelectorAll<HTMLElement>(
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
  );
  const first = focusable[0];
  const last = focusable[focusable.length - 1];

  dialogElement.addEventListener("keydown", (e) => {
    if (e.key !== "Tab") return;

    if (e.shiftKey) {
      if (document.activeElement === first) {
        last.focus();
        e.preventDefault();
      }
    } else {
      if (document.activeElement === last) {
        first.focus();
        e.preventDefault();
      }
    }
  });

  first.focus();
}
```

### Tabs Pattern

```tsx
function Tabs({ tabs }: { tabs: TabItem[] }) {
  const [activeIndex, setActiveIndex] = useState(0);

  const handleKeyDown = (e: React.KeyboardEvent, index: number) => {
    let newIndex = index;
    switch (e.key) {
      case "ArrowRight":
        newIndex = (index + 1) % tabs.length;
        break;
      case "ArrowLeft":
        newIndex = (index - 1 + tabs.length) % tabs.length;
        break;
      case "Home":
        newIndex = 0;
        break;
      case "End":
        newIndex = tabs.length - 1;
        break;
      default:
        return;
    }
    e.preventDefault();
    setActiveIndex(newIndex);
  };

  return (
    <div>
      <div role="tablist" aria-label="Settings">
        {tabs.map((tab, i) => (
          <button
            key={tab.id}
            role="tab"
            aria-selected={i === activeIndex}
            aria-controls={`panel-${tab.id}`}
            id={`tab-${tab.id}`}
            tabIndex={i === activeIndex ? 0 : -1}
            onKeyDown={(e) => handleKeyDown(e, i)}
            onClick={() => setActiveIndex(i)}
          >
            {tab.label}
          </button>
        ))}
      </div>
      {tabs.map((tab, i) => (
        <div
          key={tab.id}
          role="tabpanel"
          id={`panel-${tab.id}`}
          aria-labelledby={`tab-${tab.id}`}
          hidden={i !== activeIndex}
          tabIndex={0}
        >
          {tab.content}
        </div>
      ))}
    </div>
  );
}
```

---

## Keyboard Navigation

### Required Keyboard Support

| Component | Keys |
|-----------|------|
| Button | Enter, Space |
| Link | Enter |
| Checkbox | Space |
| Radio group | Arrow keys |
| Select/Dropdown | Arrow keys, Enter, Escape |
| Tabs | Arrow keys, Home, End |
| Dialog | Tab (trap), Escape (close) |
| Menu | Arrow keys, Enter, Escape |
| Tree view | Arrow keys, Enter, Home, End |
| Slider | Arrow keys, Home, End, Page Up/Down |

### Skip Navigation

```html
<!-- First element in body -->
<a href="#main-content" class="skip-link">
  Skip to main content
</a>

<nav><!-- Long navigation --></nav>

<main id="main-content" tabindex="-1">
  <!-- Page content -->
</main>

<style>
  .skip-link {
    position: absolute;
    top: -40px;
    left: 0;
    background: #000;
    color: #fff;
    padding: 8px;
    z-index: 100;
    transition: top 0.2s;
  }
  .skip-link:focus {
    top: 0;
  }
</style>
```

### Focus Visibility

```css
/* Never remove focus outlines globally */
/* ❌ */ *:focus { outline: none; }

/* ✅ Use :focus-visible for keyboard-only focus */
:focus-visible {
  outline: 2px solid #4A90D9;
  outline-offset: 2px;
}

/* Remove focus ring for mouse users only */
:focus:not(:focus-visible) {
  outline: none;
}

/* Custom focus styles */
button:focus-visible {
  outline: 2px solid var(--focus-color);
  outline-offset: 2px;
  box-shadow: 0 0 0 4px rgba(74, 144, 217, 0.3);
}
```

---

## Forms & Validation

### Accessible Form Pattern

```tsx
function SignupForm() {
  const [errors, setErrors] = useState<Record<string, string>>({});

  return (
    <form
      aria-label="Sign up"
      noValidate
      onSubmit={handleSubmit}
    >
      {/* Error summary at top */}
      {Object.keys(errors).length > 0 && (
        <div role="alert" aria-label="Form errors">
          <h2>Please fix the following errors:</h2>
          <ul>
            {Object.entries(errors).map(([field, message]) => (
              <li key={field}>
                <a href={`#${field}`}>{message}</a>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Field with error */}
      <div>
        <label htmlFor="email">
          Email <span aria-label="required">*</span>
        </label>
        <input
          id="email"
          type="email"
          required
          aria-required="true"
          aria-invalid={!!errors.email}
          aria-describedby={errors.email ? "email-error" : "email-hint"}
        />
        <p id="email-hint" className="hint">
          We'll never share your email
        </p>
        {errors.email && (
          <p id="email-error" role="alert" className="error">
            {errors.email}
          </p>
        )}
      </div>

      {/* Password with requirements */}
      <div>
        <label htmlFor="password">Password *</label>
        <input
          id="password"
          type="password"
          aria-required="true"
          aria-describedby="password-requirements"
          aria-invalid={!!errors.password}
        />
        <div id="password-requirements">
          <p>Password must contain:</p>
          <ul>
            <li aria-label="At least 8 characters - met">✓ At least 8 characters</li>
            <li aria-label="One uppercase letter - not met">✗ One uppercase letter</li>
          </ul>
        </div>
      </div>

      <button type="submit">Create Account</button>
    </form>
  );
}
```

---

## Color & Contrast

### Minimum Contrast Ratios (WCAG 2.2 AA)

| Text Type | Minimum Ratio |
|-----------|--------------|
| Normal text (< 18px / 14px bold) | **4.5:1** |
| Large text (≥ 18px / 14px bold) | **3:1** |
| UI components & graphics | **3:1** |
| AAA level normal text | 7:1 |

### Don't Rely on Color Alone

```css
/* ❌ BAD: Only color indicates error */
.error { color: red; }

/* ✅ GOOD: Icon + color + text */
.error {
  color: #d32f2f;
  border-left: 3px solid #d32f2f;
  padding-left: 8px;
}
.error::before {
  content: "⚠ ";
}
```

```html
<!-- ❌ BAD: Color-only status -->
<span class="dot green"></span> Active

<!-- ✅ GOOD: Icon + text + color -->
<span class="status active">
  <svg aria-hidden="true"><!-- checkmark icon --></svg>
  Active
</span>
```

### Prefers Reduced Motion

```css
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

### Prefers Color Scheme

```css
:root {
  --text: #1a1a1a;
  --bg: #ffffff;
  --focus: #4A90D9;
}

@media (prefers-color-scheme: dark) {
  :root {
    --text: #f0f0f0;
    --bg: #1a1a1a;
    --focus: #6BB5FF;
  }
}
```

---

## Images & Media

### Image Alt Text Decision Tree

```
Is the image decorative?
  → Yes: alt="" (empty alt)
  → No: Does it contain text?
    → Yes: alt = the text in the image
    → No: Is it a link/button?
      → Yes: alt = the link destination/action
      → No: alt = concise description of content
```

```html
<!-- Decorative -->
<img src="divider.svg" alt="" />

<!-- Informative -->
<img src="chart.png" alt="Sales increased 23% in Q3 2024, reaching $4.2M" />

<!-- Linked -->
<a href="/home">
  <img src="logo.png" alt="Company Name - Home" />
</a>

<!-- Complex image -->
<figure>
  <img src="architecture.png" alt="System architecture diagram"
       aria-describedby="arch-desc" />
  <figcaption id="arch-desc">
    The system consists of three tiers: web frontend (React),
    API gateway (Kong), and microservices (Go) backed by
    PostgreSQL and Redis.
  </figcaption>
</figure>
```

### Video & Audio

```html
<!-- Video with captions -->
<video controls>
  <source src="demo.mp4" type="video/mp4" />
  <track kind="captions" src="demo-en.vtt" srclang="en" label="English" default />
  <track kind="captions" src="demo-es.vtt" srclang="es" label="Español" />
  <track kind="descriptions" src="demo-desc.vtt" srclang="en" label="Descriptions" />
  <p>Your browser doesn't support video.
     <a href="demo.mp4">Download the video</a>.
  </p>
</video>
```

---

## Dynamic Content

### Loading States

```tsx
function DataTable() {
  const { data, isLoading } = useQuery(["items"], fetchItems);

  if (isLoading) {
    return (
      <div role="status" aria-live="polite">
        <span className="sr-only">Loading data table...</span>
        <Spinner aria-hidden="true" />
      </div>
    );
  }

  return (
    <div aria-live="polite" aria-atomic="false">
      <table aria-label="Product inventory">
        <caption className="sr-only">
          {data.length} items found. Sorted by name ascending.
        </caption>
        <thead>
          <tr>
            <th scope="col" aria-sort="ascending">
              <button>Name ▲</button>
            </th>
            <th scope="col" aria-sort="none">
              <button>Price</button>
            </th>
          </tr>
        </thead>
        <tbody>
          {data.map((item) => (
            <tr key={item.id}>
              <td>{item.name}</td>
              <td>{item.price}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

### Toast Notifications

```tsx
function ToastContainer() {
  return (
    <div
      role="log"
      aria-live="polite"
      aria-label="Notifications"
      className="toast-container"
    >
      {toasts.map((toast) => (
        <div
          key={toast.id}
          role={toast.type === "error" ? "alert" : "status"}
          className={`toast toast-${toast.type}`}
        >
          <span>{toast.message}</span>
          <button
            aria-label={`Dismiss: ${toast.message}`}
            onClick={() => dismiss(toast.id)}
          >
            ×
          </button>
        </div>
      ))}
    </div>
  );
}
```

---

## Focus Management

### Route Changes (SPA)

```tsx
// hooks/useRouteAnnouncer.ts
function useRouteAnnouncer() {
  const pathname = usePathname();

  useEffect(() => {
    // Announce page change to screen readers
    const title = document.title;
    const announcer = document.getElementById("route-announcer");
    if (announcer) {
      announcer.textContent = `Navigated to ${title}`;
    }

    // Move focus to main content
    const main = document.querySelector("main");
    if (main) {
      main.setAttribute("tabindex", "-1");
      main.focus();
      // Remove tabindex after focus to prevent tab stop
      main.addEventListener("blur", () => main.removeAttribute("tabindex"), {
        once: true,
      });
    }
  }, [pathname]);

  return (
    <div
      id="route-announcer"
      role="status"
      aria-live="assertive"
      aria-atomic="true"
      className="sr-only"
    />
  );
}
```

### After Deletions

```tsx
function ItemList() {
  const deleteItem = (id: string) => {
    const index = items.findIndex((i) => i.id === id);
    setItems(items.filter((i) => i.id !== id));

    // Focus management after deletion
    requestAnimationFrame(() => {
      const remaining = listRef.current?.querySelectorAll("[data-item]");
      if (remaining && remaining.length > 0) {
        // Focus next item, or previous if last was deleted
        const focusIndex = Math.min(index, remaining.length - 1);
        (remaining[focusIndex] as HTMLElement).focus();
      } else {
        // All items deleted — focus empty state
        emptyStateRef.current?.focus();
      }
    });
  };
}
```

---

## Testing

### Automated Testing Tools

| Tool | Type | Use For |
|------|------|---------|
| axe-core | Library | CI/CD integration, component tests |
| eslint-plugin-jsx-a11y | Linter | Catch issues at dev time |
| Pa11y | CLI | Page-level audits |
| Lighthouse | Browser | Comprehensive audits |
| WAVE | Browser ext. | Visual inspection |
| NVDA / VoiceOver | Screen reader | Manual testing |

### Automated Tests (Vitest + Testing Library)

```typescript
import { render, screen } from "@testing-library/react";
import { axe, toHaveNoViolations } from "jest-axe";
import userEvent from "@testing-library/user-event";

expect.extend(toHaveNoViolations);

describe("LoginForm", () => {
  it("should have no accessibility violations", async () => {
    const { container } = render(<LoginForm />);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it("should associate labels with inputs", () => {
    render(<LoginForm />);
    const emailInput = screen.getByLabelText(/email/i);
    expect(emailInput).toHaveAttribute("type", "email");
  });

  it("should show errors accessibly", async () => {
    render(<LoginForm />);
    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: /submit/i }));
    expect(screen.getByRole("alert")).toHaveTextContent(/email is required/i);
  });

  it("should be keyboard navigable", async () => {
    render(<LoginForm />);
    const user = userEvent.setup();

    await user.tab();
    expect(screen.getByLabelText(/email/i)).toHaveFocus();

    await user.tab();
    expect(screen.getByLabelText(/password/i)).toHaveFocus();

    await user.tab();
    expect(screen.getByRole("button", { name: /submit/i })).toHaveFocus();
  });
});
```

### Screen Reader Only CSS

```css
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border-width: 0;
}
```

---

## React Component Patterns

### Accessible Icon Button

```tsx
interface IconButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  icon: React.ReactNode;
  label: string;
  tooltipPosition?: "top" | "bottom" | "left" | "right";
}

function IconButton({ icon, label, tooltipPosition = "top", ...props }: IconButtonProps) {
  return (
    <button
      aria-label={label}
      title={label}
      {...props}
    >
      <span aria-hidden="true">{icon}</span>
    </button>
  );
}
```

### Accessible Dropdown Menu

```tsx
function DropdownMenu({ trigger, items }: DropdownMenuProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);
  const menuRef = useRef<HTMLUListElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    switch (e.key) {
      case "ArrowDown":
        e.preventDefault();
        setActiveIndex((prev) => Math.min(prev + 1, items.length - 1));
        break;
      case "ArrowUp":
        e.preventDefault();
        setActiveIndex((prev) => Math.max(prev - 1, 0));
        break;
      case "Escape":
        setIsOpen(false);
        triggerRef.current?.focus();
        break;
      case "Enter":
      case " ":
        if (activeIndex >= 0) {
          items[activeIndex].action();
          setIsOpen(false);
          triggerRef.current?.focus();
        }
        break;
    }
  };

  return (
    <div className="dropdown">
      <button
        ref={triggerRef}
        aria-haspopup="true"
        aria-expanded={isOpen}
        aria-controls="dropdown-menu"
        onClick={() => setIsOpen(!isOpen)}
      >
        {trigger}
      </button>

      {isOpen && (
        <ul
          ref={menuRef}
          id="dropdown-menu"
          role="menu"
          aria-label="Actions"
          onKeyDown={handleKeyDown}
        >
          {items.map((item, i) => (
            <li
              key={item.id}
              role="menuitem"
              tabIndex={i === activeIndex ? 0 : -1}
              aria-disabled={item.disabled}
              onClick={() => !item.disabled && item.action()}
            >
              {item.label}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
```

---

## Common Mistakes

| Mistake | Impact | Fix |
|---------|--------|-----|
| Missing alt text | Screen readers say "image" | Add descriptive alt or `alt=""` |
| `outline: none` globally | Keyboard users can't see focus | Use `:focus-visible` |
| Click-only interactions | Keyboard/switch users locked out | Add keyboard handlers |
| Low contrast text | Unreadable for low vision | Minimum 4.5:1 ratio |
| Missing form labels | Screen readers can't identify fields | `<label for>` or `aria-label` |
| Auto-playing media | Disorienting, disruptive | Require user action to play |
| Inaccessible error messages | Users don't know what's wrong | `role="alert"` + `aria-invalid` |
| Missing skip link | Keyboard users Tab through entire nav | Add skip-to-content link |
| Non-semantic modals | Can't be identified, no focus trap | `role="dialog"` + focus trap |
| Disabled button without context | Users don't know why it's disabled | Add tooltip/description |

---

## Production Checklist

### Development Phase
- [ ] Semantic HTML used (headings, landmarks, lists, tables)
- [ ] All images have appropriate alt text
- [ ] Color contrast meets 4.5:1 (text) / 3:1 (UI components)
- [ ] All interactive elements keyboard accessible
- [ ] Focus indicators visible (`:focus-visible`)
- [ ] Skip navigation link present
- [ ] Form fields have associated labels
- [ ] Error messages announced to screen readers
- [ ] No content conveys meaning through color alone
- [ ] `prefers-reduced-motion` respected

### Testing Phase
- [ ] axe-core passes with 0 violations
- [ ] eslint-plugin-jsx-a11y rules pass
- [ ] Tab order is logical
- [ ] Screen reader testing (NVDA or VoiceOver)
- [ ] Keyboard-only navigation test
- [ ] 200% zoom test (no content loss)
- [ ] High contrast mode test
- [ ] Reduced motion test

### Deployment Phase
- [ ] Accessibility statement published
- [ ] User feedback mechanism for a11y issues
- [ ] Monitoring for a11y regressions (Lighthouse CI)
- [ ] Team training on accessibility best practices

---

## References

- [WCAG 2.2 Quick Reference](https://www.w3.org/WAI/WCAG22/quickref/)
- [WAI-ARIA Authoring Practices](https://www.w3.org/WAI/ARIA/apg/)
- [Inclusive Components](https://inclusive-components.design/)
- [A11y Project Checklist](https://www.a11yproject.com/checklist/)
- [Axe-core Rules](https://dequeuniversity.com/rules/axe/)


---

## 7. Common Pitfalls & Anti-Patterns

| Anti-Pattern | Root Cause | Production Consequence | Remediated Standard |
| :--- | :--- | :--- | :--- |
| **Clickable Divs Without ARIA** | `<div onClick={...}>` instead of `<button>` | Inaccessible via keyboard navigation (Tab/Enter) and invisible to screen readers | Always use semantic HTML `<button>` or add `role="button"` and `tabIndex={0}` |
| **Missing Form Input Labels** | Relying solely on `placeholder="..."` | Screen readers cannot announce field purpose when input contains text | Provide an explicit `<label htmlFor="id">` or `aria-label` |
| **Outline None Without Custom Focus Ring** | `outline: none` in CSS | Keyboard users lose all visual focus indicator while tabbing | Use Tailwind `focus-visible:ring-2 focus-visible:ring-primary` |
| **Color as Sole Information Channel** | Indicating error states only with red text | Inaccessible to colorblind users | Pair color with text labels, icons, and `aria-invalid="true"` |
