# FRONTEND.md — Universal Multi-Surface Frontend Engineering & Client Craft Master Skill

> **Standard Identifier**: `DEVSKILL-FRONTEND-MASTER-001`  
> **Scope**: Framework-Agnostic Master Constitution for ALL Frontend Surfaces: Web, Mobile, Desktop, and Terminal (TUI)  
> **Governing Rules**: **R-001**, **R-034**, **R-074**, **R-075**, **R-085**, **R-125–R-139**, **R-251–R-260**, **R-273–R-274**  
> **Last Updated**: 2026-11-20  

> **Golden Rule**: *Frontend engineering encompasses every client surface where humans interact with software. Every pixel and ANSI glyph ships a contract: native platform primitives first, fine-grained reactivity without thread-blocking, semantic accessibility by default across screen readers and viewports, 60/120 FPS frame budgeting, zero visual or structural slop, and hardened client-boundary security.*

---

## 1. The Multi-Surface Frontend Selection Matrix (2026)

Frontend engineering is not limited to web browsers. It spans **Web**, **Mobile**, **Desktop**, and **Terminal (TUI)** clients. Choose the simplest execution model, rendering engine, and host runtime that fulfills the product's latency, distribution, hardware access, and UX requirements.

```
                                 THE FRONTEND CLIENT SPECTRUM
┌─────────────────────────┬─────────────────────────┬─────────────────────────┬─────────────────────────┐
│      WEB FRONTEND       │     MOBILE FRONTEND     │    DESKTOP FRONTEND     │   TERMINAL (TUI) UI     │
├─────────────────────────┼─────────────────────────┼─────────────────────────┼─────────────────────────┤
│ • Next.js 16 / React 19 │ • Native iOS (SwiftUI)  │ • Tauri v2 (Rust + Web) │ • Ratatui (Rust)        │
│ • Vue 3.5 / Nuxt 4      │ • Native Android        │ • Electron 33+          │ • Bubble Tea (Go)       │
│ • Svelte 5 / SvelteKit  │   (Kotlin / Compose)    │ • Native macOS / Win    │ • Textual (Python)      │
│ • Angular 19/20         │ • React Native / Expo   │ • Qt 6 / QML            │ • Ink (React / Node)    │
│ • Astro 5 / SolidJS     │ • Flutter 3.29–3.35+    │                         │                         │
└─────────────────────────┴─────────────────────────┴─────────────────────────┴─────────────────────────┘
```

### 1.1 Web Frontend Frameworks
| Framework | Core Paradigm | Killer Strengths (2025–2026) | Ideal Workload | Deep-Dive Skill |
|---|---|---|---|---|
| **Next.js 16 + React 19.2** | RSC + Streaming SSR + React Compiler | `"use cache"`, Turbopack, Server Actions, `use()`, `useActionState`, massive ecosystem | Full-stack SaaS, e-commerce, multi-team web apps | [`frameworks/frontend/nextjs.md`](frameworks/frontend/nextjs.md), [`frameworks/frontend/react.md`](frameworks/frontend/react.md) |
| **Vue 3.5 + Nuxt 4** | Proxy Reactivity + Hybrid Nitro SSR | Reactive props destructure, `defineModel`, Vapor Mode, Nuxt 4 `app/` structure | Full-stack apps, rapid team velocity, hybrid SSR/SPA | [`frameworks/frontend/vue-nuxt.md`](frameworks/frontend/vue-nuxt.md) |
| **Svelte 5 + SvelteKit 2** | Compile-Time Signals (Runes) | `$state`/`$derived`/`$effect` in `.svelte.ts`, Snippets, progressive Form Actions | Ultra-fast interactive apps, small bundles, edge SSR | [`frameworks/frontend/sveltekit.md`](frameworks/frontend/sveltekit.md) |
| **Angular 19 / 20** | Signals + Zoneless Architecture | Native Zoneless change detection, `linkedSignal`, `httpResource`, `@defer` incremental hydration | Large enterprise apps, strict DI, monorepos | [`frameworks/frontend/angular.md`](frameworks/frontend/angular.md) |
| **Astro 5** | Zero-JS Content + Server Islands | `server:defer` Server Islands, Content Layer API, Actions, multi-framework islands | Marketing, docs, blogs, e-commerce storefronts | [`frameworks/frontend/astro.md`](frameworks/frontend/astro.md) |
| **SolidJS / SolidStart** | Fine-Grained Signals (Zero VDOM) | Direct DOM updates, `"use server"` RPC, `createStore`, highest JS perf/byte | High-frequency dashboards, data-dense trading/telemetry UIs | [`frameworks/frontend/solidjs.md`](frameworks/frontend/solidjs.md) |
| **Tailwind CSS v4 (Oxide)** | Rust Utility Engine + CSS-First Tokens | `@import "tailwindcss"`, `@theme` OKLCH tokens, native `@container` queries | Universal styling layer across every web framework above | [`frameworks/frontend/tailwindcss.md`](frameworks/frontend/tailwindcss.md) |

### 1.2 Mobile Frontend Frameworks
| Framework / Platform | Core Paradigm | Killer Strengths (2025–2026) | Ideal Workload | Deep-Dive Skill |
|---|---|---|---|---|
| **iOS Native (SwiftUI + Swift 6)** | Declarative View Graph + Strict Actor Concurrency | `@Observable`, `@MainActor`, zero-copy Metal rendering, instant OS feature parity, Keychain | Mission-critical iOS apps, deep Apple platform integration | [`frameworks/mobile/ios-swiftui.md`](frameworks/mobile/ios-swiftui.md) |
| **Android Native (Compose + Kotlin 2)** | Declarative Node Graph + Coroutine Concurrency | `StateFlow`, `collectAsStateWithLifecycle`, Baseline Profiles, Material Design 3, Room | Mission-critical Android apps, automotive, hardware SDKs | [`frameworks/mobile/android-kotlin-compose.md`](frameworks/mobile/android-kotlin-compose.md), [`frameworks/mobile/android-aosp.md`](frameworks/mobile/android-aosp.md) |
| **React Native (Expo SDK 53/54)** | New Architecture (Fabric + TurboModules + Hermes) | Shared TypeScript codebase, Expo Router file-based navigation, Reanimated 60/120 FPS worklets, FlashList | Cross-platform commercial mobile apps with web-team velocity | [`frameworks/mobile/react-native-expo.md`](frameworks/mobile/react-native-expo.md) |
| **Flutter 3.29–3.35+** | Own-Rendered Canvas (Impeller Engine) | Pixel-perfect deterministic rendering across iOS/Android, Riverpod 3, Pigeon type-safe native interop | Design-heavy cross-platform apps, embedded screens, kiosk UIs | [`frameworks/mobile/flutter.md`](frameworks/mobile/flutter.md) |

### 1.3 Desktop Frontend Frameworks
| Framework / Platform | Core Paradigm | Killer Strengths (2025–2026) | Ideal Workload | Deep-Dive Skill |
|---|---|---|---|---|
| **Tauri v2** | Rust Core + Webview / Native Windows | < 15MB binary, < 40MB RAM, granular capability JSON security, multi-window, OS system tray | Resource-constrained, secure, high-performance desktop apps | [`frameworks/desktop/tauri.md`](frameworks/desktop/tauri.md) |
| **Electron 33+** | Chromium + Node.js Sandboxed Runtimes | 100% web API fidelity, massive desktop ecosystem, battle-tested `contextBridge` IPC | Complex desktop productivity suites (editors, collaborative tools) | [`frameworks/desktop/electron.md`](frameworks/desktop/electron.md) |
| **Native Desktop (SwiftUI / WinUI 3 / Qt 6)** | Native OS UI Toolkit (AppKit / WinUI / QML) | Direct GPU integration, OS accessibility hookup, zero-web-runtime overhead | High-throughput media editors, CAD, OS utilities, DAW apps | [`frameworks/desktop/tauri.md`](frameworks/desktop/tauri.md), [`languages/c-cpp.md`](languages/c-cpp.md) |

### 1.4 Terminal User Interface (TUI) Frontends
| Framework / Library | Language | Core Paradigm | Ideal Workload | Deep-Dive Skill |
|---|---|---|---|---|
| **Ratatui** | Rust | Immediate-mode terminal buffer rendering, zero-allocation diffing | Cloud-native dashboards, DevOps CLI tools, high-frequency monitors | [`frameworks/tui/terminal-ui.md`](frameworks/tui/terminal-ui.md) |
| **Bubble Tea** | Go | The Elm Architecture (Model-Update-View), functional event loop | Developer CLI tools, installer wizards, interactive terminal agents | [`frameworks/tui/terminal-ui.md`](frameworks/tui/terminal-ui.md) |
| **Textual** | Python | Asyncio-first CSS-driven terminal layout & widget tree | Data science terminals, quick sysadmin dashboards, Python tools | [`frameworks/tui/terminal-ui.md`](frameworks/tui/terminal-ui.md) |
| **Ink** | TypeScript | React component tree compiled to ANSI string streams | Node.js / Bun interactive CLI tools, scaffolding generators | [`frameworks/tui/terminal-ui.md`](frameworks/tui/terminal-ui.md) |

---

## 2. Universal Design Engineering & Anti-Slop Visual Craft (R-251)

Great frontend engineering fuses client architecture with visual and interaction craft. Low-craft, generic interfaces fail users across every platform, whether on a 4K OLED monitor, an iPhone screen, or an xterm-256color terminal.

### 2.1 Multi-Surface Design Token Hierarchy
Never hardcode raw hex codes (`#3b82f6`), magic pixels (`p-[13px]`), or arbitrary terminal escape codes inside feature components. Enforce three strict token layers across all client surfaces:

```
┌────────────────────────────────────────────────────────┐
│ 1. Primitive Palette (Raw OKLCH / Hex / ANSI codes)   │
├────────────────────────────────────────────────────────┤
│ 2. Semantic Tokens (Surface, Text, Accent, Danger)     │
├────────────────────────────────────────────────────────┤
│ 3. Component Tokens (ButtonBg, ModalRadius, NavHeight) │
└────────────────────────────────────────────────────────┘
```

#### Web (CSS / OKLCH Tokens)
```css
/* 1. Primitive Palette */
:root {
  --palette-neutral-50:  oklch(0.985 0.002 247);
  --palette-neutral-900: oklch(0.175 0.012 255);
  --palette-brand-600:   oklch(0.550 0.195 258);
  --palette-danger-600:  oklch(0.560 0.215 27);
}

/* 2. Semantic Tokens (Adapts to Dark / Light / High-Contrast) */
:root {
  --surface-canvas:  var(--palette-neutral-50);
  --text-primary:    var(--palette-neutral-900);
  --accent-primary:  var(--palette-brand-600);
  --status-danger:   var(--palette-danger-600);
  --radius-control:  0.5rem;
  --z-dropdown:      20;
  --z-modal:         40;
}
```

#### Mobile & Desktop (SwiftUI / Compose / Flutter)
- **SwiftUI**: Implement `Color.semanticSurface`, `Color.semanticAccent` backed by Asset Catalog dynamic colors or custom `@Observable` theme providers.
- **Compose**: Bind to `MaterialTheme.colorScheme.surface`, `primary`, and `errorContainer` via Material Design 3 tokens.
- **Flutter**: Bind to `Theme.of(context).colorScheme` with `ColorScheme.fromSeed()` and custom `ThemeExtension<AppCustomColors>`.

#### Terminal UI (TUI ANSI / TrueColor Tokens)
- Abstract color codes into semantic palette structs (`Theme::surface()`, `Theme::accent()`, `Theme::danger()`).
- Support automatic fallback: 24-bit RGB TrueColor $\to$ 256-color ANSI $\to$ 16-color ANSI $\to$ monochrome high-contrast.

### 2.2 Visual Craft Non-Negotiables
- **Typographic Hierarchy**: Pair at most two font families (sans/serif + monospace for code/numbers). Use `font-variant-numeric: tabular-nums` (or fixed-width monospace on TUI/mobile) for tables, prices, counters, and timers so numbers align vertically without jitter. Cap body text line length at `60ch–72ch`.
- **Spatial Rhythm & Density**: Adhere strictly to a 4px/8px spatial grid across Web, Mobile, and Desktop (or 1-character/row grid in TUI). Never mix haphazard spacing values.
- **Complete Interactive State Matrix**: Every interactive control MUST implement all 6 states explicitly: `default`, `hover` (or pointer-over), `focus-visible` (keyboard focus rings), `active` (pressed), `disabled`, and `loading`/`error`.
- **Intentional Motion & Reduced Motion**: Animate only GPU-composited transforms (`transform`, `opacity`). Honor `prefers-reduced-motion` on Web/Desktop, `UIAccessibility.isReduceMotionEnabled` on iOS, and `Settings.Global.TRANSITION_ANIMATION_SCALE` on Android.
- **Zero Layout Thrash & Skeleton Loading**: Render structural skeleton loaders matching exact final dimensions instead of layout-collapsing spinners.

→ Deep dive: [`sections/frontend/design-systems-ui-craft.md`](sections/frontend/design-systems-ui-craft.md)

---

## 3. Platform First — Native Host Capabilities Before Abstractions (R-252)

Before importing third-party libraries, inspect the native platform host capabilities. Native primitives provide superior performance, automated accessibility, zero bundle overhead, and guaranteed platform consistency.

### 3.1 Web Platform Primitives
| UI / Functional Need | Legacy Library Overhead | Modern Baseline Web Platform API |
|---|---|---|
| Modals & focus trapping | Custom portal + focus-trap | Native `<dialog>` + `.showModal()` + `::backdrop` + `inert` |
| Tooltips, popovers, menus | Heavy Popper.js / custom portal | **Popover API** (`popover="auto"`) + **CSS Anchor Positioning** |
| Container-aware components | `ResizeObserver` JS hacks | **CSS Container Queries** (`container-type: inline-size`, `@container`) |
| Parent-conditional styling | State-toggled class names | **CSS `:has()`** selector (e.g. `form:has(:invalid) button`) |
| Page & state transitions | Heavy JS animation libraries | **View Transitions API** (`document.startViewTransition()`) |
| Collapsible disclosures | Custom state + ARIA wiring | `<details name="group"><summary>...</summary></details>` |
| RTL & bidirectional layout | Duplicate `.rtl` stylesheets | **CSS Logical Properties** (`margin-inline`, `padding-block`, `inset-inline-start`) |

### 3.2 Mobile Platform Primitives
- **Biometrics & Security**: Use native OS biometrics (`LocalAuthentication` on iOS, `BiometricPrompt` on Android) and hardware-backed storage (`Keychain`, `AndroidKeyStore`) via platform-first plugins (`expo-secure-store`, `flutter_secure_storage`).
- **Haptics**: Trigger native haptic feedback engines (`UIImpactFeedbackGenerator` on iOS, `Vibrator` / `HapticFeedbackConstants` on Android) for tactile confirmation on toggles, pull-to-refresh, and confirmations.
- **Safe Area Insets**: Respect display cutouts, notches, dynamic islands, and system navigation bars via native safe area APIs (`SafeAreaView`, `WindowInsetsCompat`, `UIWindow.safeAreaInsets`).

### 3.3 Desktop Platform Primitives
- **System Integration**: Use native OS window chrome, system tray menus, dock badges, native file dialogs, and OS-registered global keyboard shortcuts rather than web-emulated approximations.
- **Capabilities & Permissions**: Declare strict, least-privilege capability manifests in Tauri v2 (`capabilities/*.json`) or hardened sandboxes in Electron 33+ (`contextIsolation`, `sandbox`).

### 3.4 Terminal Platform Primitives
- **Terminal Control**: Enter the alternate screen buffer (`EnterAlternateScreen`) and enable raw mode (`enable_raw_mode()`) to intercept keystrokes without stdout echoing.
- **Signal & Teardown Traps**: Always register panic hooks and OS signal handlers (`SIGINT`, `SIGTERM`, `SIGWINCH`) to restore cooked terminal mode, re-enable cursor visibility, and exit alternate screen buffers cleanly.

---

## 4. Universal Client Architecture & Rendering Spectrum

Client applications run on diverse rendering engines. Understanding the underlying execution pipeline prevents UI-thread jank and ensures 60/120 FPS responsiveness.

```
                              THE CLIENT RENDERING SPECTRUM
┌───────────────────┬───────────────────┬───────────────────┬───────────────────┐
│     DOM / CSS     │ CANVAS / IMPELLER │ NATIVE COMPOSITOR │  ANSI / TTY GRID  │
├───────────────────┼───────────────────┼───────────────────┼───────────────────┤
│ • Web Browsers    │ • Flutter         │ • SwiftUI (Metal) │ • Ratatui         │
│ • Tauri Webview   │ • Skia Canvas     │ • Jetpack Compose │ • Bubble Tea      │
│ • Electron App    │ • WebGL / WebGPU  │ • WinUI 3 / WPF   │ • Textual         │
└───────────────────┴───────────────────┴───────────────────┴───────────────────┘
```

### 4.1 UI-Thread Hygiene & Frame Budgeting (16.6ms / 8.3ms)
To achieve smooth 60 FPS (16.6ms budget) or 120 FPS ProMotion (8.3ms budget), the main/UI thread MUST NEVER perform CPU-intensive or blocking tasks:
1. **Web**: Offload intensive parsing, cryptographic operations, or syntax highlighting to **Web Workers**. Yield long tasks (>50ms) using `scheduler.yield()`.
2. **React Native**: Run gesture handling and animations on the UI thread via **Reanimated worklets**. Offload heavy JS work to Hermes bytecode compilation.
3. **Flutter**: Run computationally heavy tasks in background **Isolates** via `Isolate.run()`. Keep the UI isolate free for Impeller draw passes.
4. **Android Native**: Collect flows with `collectAsStateWithLifecycle()` and execute IO/CPU work on `Dispatchers.IO` or `Dispatchers.Default` inside `viewModelScope`.
5. **iOS Native**: Isolate UI updates to `@MainActor` and offload data crunching to detached `Task.detached(priority: .userInitiated)` background actors.
6. **Desktop (Tauri / Electron)**: Execute heavy workloads in Rust background threads / Tokio tasks (Tauri) or Node.js Worker Threads (Electron).
7. **Terminal (TUI)**: Run event polling and background command execution in async channels (`tokio::sync::mpsc` in Rust, Go channels in Bubble Tea, asyncio tasks in Textual) so terminal drawing diffs run at full refresh rate.

---

## 5. Universal State Taxonomy

Every piece of frontend client state belongs to exactly one of seven categories. Conflating these buckets causes cascading re-renders, race conditions, and stale state bugs:

| Category | Owner | Scope & Lifecycle | Universal Tooling Across Surfaces |
|---|---|---|---|
| **1. Navigation / Route State** | Host Shell / Router | Shareable, deep-linkable, back-stack history | Web: URL Search Params (`nuqs`), Next/Nuxt Router<br>Mobile: Expo Router, GoRouter, SwiftUI NavigationStack<br>TUI: Screen stack / Tab model |
| **2. Server Cache State** | Remote API / Backend | Async, stale-while-revalidate, optimistic rollback | TanStack Query (Web/React/Vue/Solid), Riverpod (Flutter), Android Room sync, Apollo GraphQL |
| **3. Form / Input State** | Active Form / Input Field | Dirty tracking, validation errors, submit locks | React Hook Form + Zod, Superforms, Compose TextFieldValue, SwiftUI Form binding |
| **4. Ephemeral Local UI State** | Component Node | Dropdown open, hover, scroll offset, cursor index | React `useState`, Vue `ref`, Svelte `$state`, Compose `remember`, SwiftUI `@State`, TUI widget state |
| **5. Shared Client UI State** | Session Memory | Dark mode, sidebar collapse, multi-step drafts | Zustand / Jotai, Pinia, NgRx SignalStore, Riverpod, SwiftUI `@Observable` environment |
| **6. Device & Environment State** | Host OS / Hardware | Window geometry, safe areas, battery, terminal cols | CSS Media Queries / Viewport, SwiftUI `GeometryReader`, Android WindowInsets, TUI `SIGWINCH` |
| **7. Offline Persistence State** | Client Storage Engine | Key-value records, local relational DB, secure vault | Web: IndexedDB / OPFS<br>Mobile: MMKV, SQLite, Keychain/Keystore<br>Desktop: SQLite, OS Keyring<br>TUI: Config file |

**Universal Law**: *Derive, never duplicate.* If a value can be computed from existing state (e.g. `filteredList`, `cartSubtotal`, `hasErrors`), derive it dynamically via a computed expression or memoized signal (`computed()`, `$derived`, `derivedStateOf`, SwiftUI computed property) rather than synchronizing it across mutable effects.

→ Deep dive: [`sections/frontend/state-management.md`](sections/frontend/state-management.md)

---

## 6. Performance Budgets & Frame Hygiene Across Surfaces

Establish strict performance criteria in continuous integration for every frontend client:

### 6.1 Web Frontend Budgets (Core Web Vitals)
- **LCP (Largest Contentful Paint)**: **≤ 2.5s** (SSR/CDN delivery, `fetchpriority="high"` on hero assets, AVIF/WebP image formats).
- **INP (Interaction to Next Paint)**: **≤ 200ms** (yield with `scheduler.yield()`, virtualize long lists, avoid long script evaluation).
- **CLS (Cumulative Layout Shift)**: **≤ 0.1** (explicit `width`/`height` or CSS `aspect-ratio`, reserved layout skeleton space).
- **Initial JS Bundle**: **≤ 150KB gzipped** (route-level dynamic imports, zero heavy legacy utility libraries).

### 6.2 Mobile & Desktop Client Budgets
- **Frame Rate**: Constant **60 FPS** (16.6ms) / **120 FPS** (8.3ms) with zero dropped frames during scrolling or gestures.
- **Cold App Launch (Time to Interactive)**: **≤ 1.5s** on mid-tier mobile hardware and desktop machines.
- **Memory Footprint (Resident Set Size)**: **≤ 150MB** for mobile clients, **≤ 80MB** for Tauri desktop clients under standard navigation.
- **Battery & Thermal Efficiency**: Zero continuous CPU busy-loops or unthrottled timers when the app is backgrounded or minimized.

### 6.3 Terminal (TUI) Budgets
- **Frame Draw Latency**: **≤ 16ms** per render pass.
- **Zero Terminal Flicker**: Double-buffered render diffing (only emit ANSI control sequences for changed character cells).
- **Idle CPU Utilization**: **< 1%** CPU usage when no user keypress or streaming event is occurring.
- **Terminal Resize Latency**: Re-layout within **< 30ms** upon `SIGWINCH` without buffer clipping or panic.

---

## 7. Accessibility Across All Surfaces

Accessibility (a11y) is a universal requirement for human-computer interaction across Web, Mobile, Desktop, and Terminal interfaces.

### 7.1 Web Accessibility (WCAG 2.2 Level AA Mandatory)
- **Semantic Structure**: Proper landmarks (`<main>`, `<nav>`, `<header>`), sequential heading hierarchy (`h1` $\to$ `h2`), and native `<button>`/`<a>` controls.
- **Keyboard Traversal**: Full operation via `Tab`, `Shift+Tab`, `Enter`, `Space`, `Escape`, and arrow keys with high-contrast visible focus rings (`:focus-visible`).
- **Screen Reader Associations**: Explicit `<label for="...">`, `aria-describedby` linking error text, and `role="alert"` / `aria-live="polite"` for dynamic asynchronous updates.

### 7.2 Mobile Accessibility
- **iOS VoiceOver**: Provide clear `accessibilityLabel`, `accessibilityHint`, and correct `accessibilityTraits` (e.g. `.isButton`, `.isHeader`). Support Dynamic Type font scaling up to 200% without clipped text.
- **Android TalkBack**: Set semantic `contentDescription` on non-text elements, group related information using `Modifier.semantics(mergeDescendants = true)`, and maintain minimum 48×48dp touch targets.

### 7.3 Desktop Accessibility
- Connect UI elements to native OS accessibility APIs (Apple Accessibility API on macOS, UI Automation on Windows, AT-SPI on Linux). Ensure native shortcut accelerators (`Cmd/Ctrl + S`) are documented and keyboard operable.

### 7.4 Terminal (TUI) Accessibility
- **Screen Reader Compatibility**: Provide a clean text output mode (`--plain` or `--no-tui`) for blind users utilizing terminal screen readers.
- **High-Contrast & Color Independence**: Support monochrome or 16-color ANSI palettes. Never convey status exclusively through color (always pair colors with icons or labels: `[✓] PASS`, `[✗] FAIL`).

→ Deep dive: [`sections/frontend/accessibility.md`](sections/frontend/accessibility.md)

---

## 8. Frontend Security Hardening (R-260, R-270, R-273)

Client software runs in untrusted, hostile user environments. Defense-in-depth is non-negotiable across every surface:

### 8.1 Web Security
- **Strict Content Security Policy (CSP)**: Nonce-based CSP (`script-src 'strict-dynamic'`), `object-src 'none'`, `frame-ancestors 'none'`.
- **Token Hygiene**: Store session tokens exclusively in `HttpOnly; Secure; SameSite=Lax` cookies. NEVER store session JWTs or secrets in `localStorage` or `sessionStorage` where XSS can extract them.
- **XSS & Injection Protection**: Sanitize all untrusted HTML via DOMPurify + Trusted Types. Validate all URLs against `javascript:` and `data:` schemes.

### 8.2 Mobile Security
- **Encrypted Local Storage**: Store cryptographic keys, biometric tokens, and auth secrets exclusively in the iOS Keychain or Android Keystore.
- **Network Security**: Implement TLS Certificate Pinning on financial and healthcare APIs. Prevent proxy MITM inspection.
- **Screen Privacy & Logging**: Mask sensitive payment/auth screens in the app switcher (`FLAG_SECURE` on Android, hiding window contents in `sceneWillResignActive` on iOS). Strip all sensitive tokens from production logs.

### 8.3 Desktop Security (Tauri v2 & Electron 33+)
- **Tauri v2 Capabilities**: Define granular permission capabilities in `src-tauri/capabilities/`. Prohibit wildcard permissions (`*`). Validate and sanitize every command argument passed to `#[tauri::command]`.
- **Electron Sandboxing**: Always enforce `contextIsolation: true`, `sandbox: true`, and `nodeIntegration: false`. Expose minimal, typed IPC via `contextBridge.exposeInMainWorld()`. Never pass `shell.openExternal()` unvalidated URLs.

### 8.4 Terminal (TUI) Security
- **ANSI Injection Defense**: Sanitize all external user inputs, server logs, or untrusted file paths before printing to the terminal buffer. Malicious ANSI escape sequences can manipulate terminal titles, alter clipboard contents, or inject keystrokes into the host shell.

---

## 9. Internationalization (i18n), RTL & Localization

1. **Externalized Localization**: Zero user-facing strings hardcoded in component templates. Use typed localization catalogs (`i18next`, `typesafe-i18n`, `flutter_localizations`, Apple `.xcstrings`).
2. **Native Platform Formatters**: Format numbers, dates, ranges, and currencies using platform-native formatters (`Intl.DateTimeFormat` / `Intl.NumberFormat` on Web, `Foundation.FormatStyle` in Swift, `java.text.NumberFormat` in Kotlin) respecting device locale.
3. **Right-to-Left (RTL) Layouts**:
   - Web: Use CSS Logical Properties (`margin-inline-start`, `padding-inline-end`, `inset-inline-start`, `text-start`).
   - Mobile & Desktop: Use directional layout primitives (`start`/`end` instead of `left`/`right`). Verify mirroring in Arabic and Hebrew locales.
   - TUI: Ensure terminal layout engines handle wide-character UTF-8 glyphs and bidirectional text without horizontal alignment corruption.

---

## 10. The Multi-Surface Frontend Testing Pyramid

```
                                  E2E & INTEGRATION
                              Web: Playwright / Cypress
                              Mobile: Maestro / Detox
                              Desktop: Playwright / WebDriver
                              TUI: Virtual PTY Test Harness
                         ──────────────────────────────────────────
                                 COMPONENT & VISUAL TESTS
                              Web: Testing Library + Storybook / Loki
                              Mobile: Alchemist / Roborazzi / Paparazzi
                              Desktop: Component Screenshot Goldens
                              TUI: Buffer Snapshot Comparison
                         ──────────────────────────────────────────
                                    UNIT & LOGIC TESTS
                              Vitest / Jest / Swift Testing /
                              Kotlin Test / Cargo Test / Go Test
                         ──────────────────────────────────────────
                                   STATIC TYPE & A11Y LINT
                              TypeScript strict / Biome / ESLint a11y /
                              Swift strict concurrency / Android Lint
```

| Layer | Surface | Primary Tooling | Verification Scope |
|---|---|---|---|
| **Static & Type** | All | TypeScript `strict`, Swift 6 compiler, Kotlin 2, `cargo clippy` | Zero `any`, zero thread-safety violations, strict nullability |
| **Unit** | All | Vitest, Swift Testing, JUnit, Cargo test, Go test | Domain models, reducers, pure formatters, validation schemas |
| **Component** | Web | Testing Library + MSW | Accessible queries (`getByRole`), state transitions, error boundaries |
| | Mobile | Compose UI Test, XCTest UI, Alchemist (Flutter) | Widget layout, gesture interactions, theme variants |
| | TUI | `ratatui::backend::TestBackend` | Character grid assertion, focus traversal, keybindings |
| **Accessibility** | Web/Mobile | `axe-core`, Accessibility Inspector, TalkBack automated test | Zero WCAG 2.2 AA violations, accessible names & traits verified |
| **End-to-End** | Web | Playwright | Full user journeys, auth flows, cross-browser regressions |
| | Mobile | Maestro / Detox | Native device flows, biometric prompts, push notification taps |
| | Desktop | Playwright (Electron/Tauri) | Native window management, file drag-and-drop, tray menus |
| | TUI | Headless PTY test driver (`teletypewriter`, `expect`) | Process launch, ANSI output parsing, exit code verification |

---

## 11. Universal Frontend Ship Gate Checklist

Every frontend client release—whether deployed as a web bundle, mobile app binary, desktop installer, or CLI binary—MUST satisfy this checklist before production release:

- [ ] **Semantic & Accessible**: Zero WCAG 2.2 AA violations on Web; VoiceOver and TalkBack accessibility traits and minimum touch targets verified on Mobile; full keyboard accessibility on Desktop; clean text fallback mode available for TUI.
- [ ] **Visual Craft & Tokens**: Colors, typography, spacing, and elevation derived exclusively from semantic tokens; all 6 interactive states (`default`, `hover`, `focus-visible`, `active`, `disabled`, `loading/error`) styled; `prefers-reduced-motion` honored; zero layout shifts.
- [ ] **Platform First**: Native host APIs used before third-party libraries (Web primitives on web, Keyring/Biometrics on mobile, native window chrome on desktop, raw mode and alternate screen buffers on TUI).
- [ ] **Frame & Performance Budgets**: 60/120 FPS frame budgeting enforced without UI-thread jank; Web LCP ≤ 2.5s, INP ≤ 200ms, CLS ≤ 0.1; Mobile/Desktop cold launch ≤ 1.5s; TUI idle CPU < 1%.
- [ ] **State & Cache Hygiene**: Zero remote server data duplicated into client stores; derived state computed on the fly; offline caching cleanly handled with rollback on failure.
- [ ] **Client Security Boundary**: Session tokens stored securely (`HttpOnly` cookies on web, Keychain/Keystore on mobile, capability-isolated IPC on desktop); zero unescaped ANSI injection on TUI; client form validation mirrored authoritatively on backend.
- [ ] **Internationalization & RTL**: Zero hardcoded strings; dates/numbers formatted via native locale engines; layouts mirror seamlessly in RTL languages without horizontal clipping.
- [ ] **Automated Test Gate**: Static typecheck, linter, unit/component tests, and E2E integration test journeys pass with Exit Code `0`.
