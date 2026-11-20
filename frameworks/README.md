# 🚀 Frameworks Directory (`frameworks/`)

This directory contains production-grade, 2026-current framework mastery guides across **Frontend**, **Backend**, **Mobile**, and **Enterprise ERP** platforms.

> For the universal, framework-agnostic frontend constitution (framework selection matrix, design tokens, modern CSS platform APIs, rendering spectrum, Core Web Vitals, accessibility, and security), start at [`../FRONTEND.md`](../FRONTEND.md) and [`../sections/frontend/design-systems-ui-craft.md`](../sections/frontend/design-systems-ui-craft.md).

## Directory Structure

### Frontend (`frameworks/frontend/`)
- [`react.md`](frontend/react.md): React 19.2+, React Compiler, `use()`, `useActionState`, `useOptimistic`, `<Activity>`, and component architecture.
- [`nextjs.md`](frontend/nextjs.md): Next.js 16 App Router, `"use cache"`, Turbopack, Server Components (RSC), Server Actions, and Auth.
- [`vue-nuxt.md`](frontend/vue-nuxt.md): Vue 3.5+ (Reactive Props Destructure, `defineModel`, Vapor Mode) & Nuxt 4 (`app/` layout, Nitro, Pinia).
- [`sveltekit.md`](frontend/sveltekit.md): Svelte 5 Runes (`$state`, `$derived`, `$effect`, `$props`, Snippets, `.svelte.ts`) & SvelteKit 2 Form Actions.
- [`angular.md`](frontend/angular.md): Angular 19/20+ Signals-First, Zoneless Change Detection, `linkedSignal`, `httpResource`, `@defer` incremental hydration, and NgRx SignalStore.
- [`astro.md`](frontend/astro.md): Astro 5+ Zero-JS Content Layer API, Server Islands (`server:defer`), Actions, `<ClientRouter />`, and multi-framework islands.
- [`solidjs.md`](frontend/solidjs.md): SolidJS & SolidStart fine-grained Signals without VDOM (`createSignal`, `createStore`, `splitProps`, `"use server"`).
- [`tailwindcss.md`](frontend/tailwindcss.md): Tailwind CSS v4 (Oxide Rust engine), CSS-first `@theme` OKLCH design tokens, `@utility`, native `@container` queries, and `cva` + `cn()`.

### Backend (`frameworks/backend/`)
- [`fastapi.md`](backend/fastapi.md): Python FastAPI, Pydantic v2, AsyncIO, Lifespan contextmanager, Async SQLAlchemy 2.0 / Asyncpg, OAuth2/JWT, and Uvicorn/Gunicorn tuning.
- [`nestjs.md`](backend/nestjs.md): TypeScript NestJS, Enterprise Hexagonal Architecture, Dynamic Modules, CQRS, Guards, Pipes, Interceptors, and Microservices.
- [`django.md`](backend/django.md): Django 5 + DRF, ORM Optimization (`select_related`, `prefetch_related`), Atomic Transactions, Celery Async Tasks, and Security Hardening.
- [`go-gin-axum.md`](backend/go-gin-axum.md): High-Throughput Microservices in Go (Gin/Chi) and Rust (Axum), Zero-Allocation Handlers, Connection Pooling, and Graceful Shutdown.
- [`dotnet-aspnet.md`](backend/dotnet-aspnet.md): C# .NET 8/9 Minimal APIs, EF Core DbContext Pooling, Polly v8 Resilience Pipelines, Rate Limiting, Kestrel Tuning, and Native AOT.
- [`express.md`](backend/express.md): TypeScript Express 5.x, Middleware Composition, Zod Validation, Error Boundaries, and Production Multi-Stage Docker.
- [`spring-boot.md`](backend/spring-boot.md): Spring Boot 3.3+, Java 21 LTS, Virtual Threads (Project Loom), Spring Security 6, and JPA/Hibernate.

### Mobile (`frameworks/mobile/`)
- [`flutter.md`](mobile/flutter.md): Flutter 3.29–3.35+ / Dart 3.7–3.9+, Impeller default, Riverpod 3.x (`Ref.mounted`, `AsyncValue.guard`), Pigeon interop, Drift SQLite, and Alchemist goldens.
- [`react-native-expo.md`](mobile/react-native-expo.md): React Native 0.79–0.81+ New Architecture (Fabric, TurboModules, JSI, Hermes), Expo SDK 53/54+, Expo Router, Reanimated, FlashList, hardware-keyed MMKV, and EAS Build/Update.
- [`android-kotlin-compose.md`](mobile/android-kotlin-compose.md): Native Android App Engineering with Kotlin 2.x, Jetpack Compose, Coroutines/StateFlow, Hilt, Room, and Baseline Profiles.
- [`ios-swiftui.md`](mobile/ios-swiftui.md): Native iOS App Engineering with Swift 6 strict concurrency, SwiftUI, `@Observable`, `NavigationStack`, Keychain, and Swift Testing.
- [`android-aosp.md`](mobile/android-aosp.md): Android Open Source Project (AOSP 14/15/16), Soong (`Android.bp`), Stable AIDL HALs, Binder IPC, SELinux, and GKI.

### Enterprise ERP (`frameworks/erp/`)
- [`odoo.md`](erp/odoo.md): Odoo 18 & 19 Enterprise Modules, `<list>`/`<chatter/>` views, `Command.*`, `_compute_display_name`, `@api.ondelete`, `res.users.apikeys`, OWL 2 components, and multi-company record rules.
- [`erpnext.md`](erp/erpnext.md): Frappe Framework & ERPNext v15/v16, DocType lifecycle, `frappe.qb` (PyPika) Query Builder, Doppio React/Vue SPAs, Frappe Recorder, and `patches.txt` migrations.
