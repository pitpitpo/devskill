# 🦀 Tauri v2 Production Desktop Architecture (`frameworks/desktop/tauri.md`)

> **Standard Identifier**: `FW-DESKTOP-TAURI-001`  
> **Framework**: Tauri v2 (Rust Core + System Webview / Multi-Window / Native Desktop)  
> **Status**: Active / Production Standard  
> **Governing Rules**: **R-001**, **R-034**, **R-060**, **R-064**, **R-251**, **R-273**  
> **Last Updated**: 2026-11-20  

---

## 1. Core Philosophy & Golden Rule

> **Golden Rule**: *Tauri applications enforce least privilege at the host-client boundary. Every capability, IPC command, and file system path MUST be explicitly declared in JSON capability manifests. Never grant wildcard permissions (`*`), never execute raw shell strings without strict argument validation, and never block the main thread with heavy Rust compute.*

---

## 2. Architecture & Security Model

Tauri v2 splits the desktop application into two distinct realms: a hardened, memory-safe **Rust Core** process with full OS capabilities, and an unprivileged **Webview Frontend** executing the user interface.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        TAURI V2 ARCHITECTURE                           │
├────────────────────────────────────────────────────────────────────────┤
│  UNPRIVILEGED WEBVIEW (React / Vue / Svelte / Solid / Vanilla)        │
│  • DOM Rendering & Event Handling                                      │
│  • `@tauri-apps/api` Client Layer                                      │
│  • Typed IPC invokes via `invoke("command_name", { payload })`         │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ IPC Bridge (Typed JSON-RPC)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│  CAPABILITY & ACCESS CONTROL MANAGER (JSON Capabilities)               │
│  • Validates command permissions against `src-tauri/capabilities/`    │
│  • Enforces path scoping for FS, HTTP, and Shell access                │
│  • Blocks unauthorized IPC requests at the kernel boundary             │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Authorized Commands
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│  HARDENED RUST CORE (Tauri Runtime)                                    │
│  • `#[tauri::command]` Handlers running on Tokio threadpool            │
│  • OS System Tray, Native Menus, Window Chrome, Global Shortcuts       │
│  • Hardware-encrypted local SQLite persistence & OS Keyring            │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Concrete Implementation & IPC Pipeline

### 3.1 Strict Capability Manifest (`src-tauri/capabilities/default.json`)
Every Tauri v2 application defines explicit permission scopes. Wildcards (`*`) are prohibited in production:

```json
{
  "$schema": "../gen/schemas/desktop-schema.json",
  "identifier": "default-capability",
  "description": "Least-privilege permissions for the main window",
  "windows": ["main"],
  "permissions": [
    "core:default",
    "core:window:allow-set-title",
    "core:window:allow-minimize",
    "core:window:allow-maximize",
    "core:window:allow-close",
    {
      "identifier": "fs:allow-read-text-file",
      "allow": [{ "path": "$APPDATA/documents/**" }]
    },
    {
      "identifier": "fs:allow-write-text-file",
      "allow": [{ "path": "$APPDATA/documents/**" }]
    }
  ]
}
```

### 3.2 Type-Safe Asynchronous Rust Command Handler (`src-tauri/src/lib.rs`)

```rust
use serde::{Deserialize, Serialize};
use std::sync::Arc;
use tauri::{command, State};
use tokio::sync::Mutex;

#[derive(Debug, Serialize, Deserialize)]
pub struct DocumentPayload {
    pub id: String,
    pub title: String,
    pub content: String,
}

#[derive(Default)]
pub struct AppState {
    pub active_document_count: Arc<Mutex<usize>>,
}

#[command]
pub async fn save_document(
    payload: DocumentPayload,
    state: State<'_, AppState>,
) -> Result<String, String> {
    // Validate input payload before processing
    if payload.title.trim().is_empty() {
        return Err("Document title cannot be empty".to_string());
    }

    if payload.content.len() > 10 * 1024 * 1024 {
        return Err("Document exceeds maximum allowed size of 10MB".to_string());
    }

    // Perform async processing on Tokio threadpool without blocking UI
    let mut count = state.active_document_count.lock().await;
    *count += 1;

    // Simulate safe persistence
    Ok(format!("Successfully saved document: {}", payload.id))
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .manage(AppState::default())
        .invoke_handler(tauri::generate_handler![save_document])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
```

### 3.3 Frontend Type-Safe IPC Invocation (TypeScript)

```typescript
import { invoke } from '@tauri-apps/api/core';

export interface DocumentPayload {
  id: string;
  title: string;
  content: string;
}

export async function persistDocument(doc: DocumentPayload): Promise<string> {
  try {
    const response = await invoke<string>('save_document', { payload: doc });
    return response;
  } catch (error) {
    // Tauri returns Err(String) as a rejected Promise
    throw new Error(`Failed to save document via Tauri IPC: ${error}`);
  }
}
```

---

## 4. Production Window & System Tray Management

In desktop applications, closing the main window should hide to the system tray rather than terminating if background sync is active:

```rust
use tauri::{
    menu::{Menu, MenuItem},
    tray::{TrayIconBuilder, TrayIconEvent},
    Manager, WindowEvent,
};

pub fn setup_tray(app: &mut tauri::App) -> Result<(), Box<dyn std::error::Error>> {
    let quit_i = MenuItem::with_id(app, "quit", "Quit App", true, None::<&str>)?;
    let show_i = MenuItem::with_id(app, "show", "Show Window", true, None::<&str>)?;
    let menu = Menu::with_items(app, &[&show_i, &quit_i])?;

    TrayIconBuilder::new()
        .icon(app.default_window_icon().unwrap().clone())
        .menu(&menu)
        .on_menu_event(|app, event| match event.id.as_ref() {
            "quit" => app.exit(0),
            "show" => {
                if let Some(window) = app.get_webview_window("main") {
                    let _ = window.show();
                    let _ = window.set_focus();
                }
            }
            _ => {}
        })
        .on_tray_icon_event(|tray, event| {
            if let TrayIconEvent::Click { .. } = event {
                let app = tray.app_handle();
                if let Some(window) = app.get_webview_window("main") {
                    let _ = window.show();
                    let _ = window.set_focus();
                }
            }
        })
        .build(app)?;

    Ok(())
}
```

---

## 5. Security & Performance Considerations

1. **CSP Enforcement in `tauri.conf.json`**:
   Always configure a strict Content Security Policy inside `tauri.conf.json`:
   ```json
   "security": {
     "csp": "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' asset: https://asset.localhost;"
   }
   ```
2. **Path Traversal & Scoping**:
   Never concatenate raw paths received from the frontend with the filesystem. Always validate canonical paths using `std::fs::canonicalize()` and verify they remain inside approved `$APPDATA` boundaries.
3. **Memory Footprint**:
   Tauri leverages the OS webview (WebKit on macOS/Linux, WebView2 on Windows), keeping RAM usage below 40–80MB. Avoid loading multi-megabyte bundle scripts on launch.
4. **Binary Stripping & Native Optimization**:
   Compile release binaries with LTO (Link-Time Optimization) and size stripping in `Cargo.toml`:
   ```toml
   [profile.release]
   codegen-units = 1
   lto = true
   opt-level = "z"
   panic = "abort"
   strip = true
   ```

---

## 6. Common Pitfalls & Anti-Patterns

- ❌ **Granting Wildcard Permissions**: Using `"permissions": ["*"]` or allowing unrestricted shell command execution exposes the user machine to remote code execution if any frontend dependency is compromised.
- ❌ **Blocking the Tokio / Main Thread**: Running blocking CPU operations or synchronous file reads inside `#[tauri::command]` freezes the entire webview window. Always use `tokio::task::spawn_blocking` for heavy compute.
- ❌ **Hardcoding OS-Specific Paths**: Hardcoding `/Users/...` or `C:\Users\...` breaks cross-platform execution. Always use Tauri's path resolver (`app.path().app_data_dir()`).
- ❌ **Silent Errors in IPC Handlers**: Returning untyped errors or swallowing panics leaves the frontend in an indefinite loading state. Always return `Result<T, AppError>` where `AppError: Serialize`.

---

## 7. Verification Checklist

- [ ] All permissions are explicitly scoped in `src-tauri/capabilities/` with zero wildcards (`*`).
- [ ] Strict Content Security Policy configured in `tauri.conf.json`.
- [ ] All `#[tauri::command]` handlers validate input parameters and return typed `Result<T, E>`.
- [ ] No synchronous blocking operations run on the main UI/Tokio event threads.
- [ ] System tray, window close, and window minimize behaviors handle backgrounding gracefully.
- [ ] Release binaries compile cleanly with `cargo clippy --all-targets -- -D warnings` and `npm run tauri build`.
