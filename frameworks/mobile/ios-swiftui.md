# 🍎 Native iOS App Engineering: Swift 6 & SwiftUI (`frameworks/mobile/ios-swiftui.md`)

> **Standard Identifier**: `FW-MOBILE-IOS-SWIFTUI-001`  
> **Framework**: Swift 6 (Strict Concurrency), SwiftUI (iOS 17/18+), `@Observable` Observation, Swift Testing  
> **Status**: Active / Production Standard  
> **Governing Rules**: **R-001**, **R-033**, **R-064**, **R-258**  
> **Last Updated**: 2026-11-19

---

## 1. Core Philosophy & Golden Rule

> **Golden Rule**: *Embrace Swift 6 strict concurrency (`Sendable`, `@MainActor`, structured `async/await`), drive SwiftUI state with the `@Observable` macro instead of legacy `ObservableObject`/`@Published`, isolate domain logic behind protocol boundaries, and store all secrets exclusively in the iOS Keychain.*

---

## 2. Production `@Observable` + `@MainActor` SwiftUI Pattern

```swift
import Foundation
import Observation
import SwiftUI

struct OrderItem: Identifiable, Hashable, Sendable {
    let id: String
    let reference: String
    let totalCents: Int
}

protocol OrderRepository: Sendable {
    func fetchOrders() async throws -> [OrderItem]
}

@MainActor
@Observable
final class OrdersStore {
    enum LoadState: Equatable {
        case idle, loading
        case loaded([OrderItem])
        case failed(String)
    }

    private(set) var state: LoadState = .idle
    private let repository: any OrderRepository

    init(repository: any OrderRepository) {
        self.repository = repository
    }

    func load() async {
        state = .loading
        do {
            let items = try await repository.fetchOrders()
            state = .loaded(items)
        } catch is CancellationError {
            return
        } catch {
            state = .failed(error.localizedDescription)
        }
    }
}

struct OrdersView: View {
    @State private var store: OrdersStore

    init(repository: any OrderRepository) {
        _store = State(initialValue: OrdersStore(repository: repository))
    }

    var body: some View {
        NavigationStack {
            Group {
                switch store.state {
                case .idle, .loading:
                    ProgressView("Loading orders...")
                case .failed(let message):
                    ContentUnavailableView {
                        Label("Unable to Load Orders", systemImage: "exclamationmark.triangle")
                    } description: {
                        Text(message)
                    } actions: {
                        Button("Retry") { Task { await store.load() } }
                    }
                case .loaded(let orders):
                    List(orders) { order in
                        NavigationLink(value: order) {
                            HStack {
                                Text(order.reference).font(.headline)
                                Spacer()
                                Text(Decimal(order.totalCents) / 100, format: .currency(code: "USD"))
                                    .monospacedDigit()
                            }
                        }
                    }
                    .refreshable { await store.load() }
                }
            }
            .navigationTitle("Orders")
            .navigationDestination(for: OrderItem.self) { order in
                OrderDetailView(order: order)
            }
            // `.task` automatically cancels in-flight async work when view disappears
            .task { await store.load() }
        }
    }
}
```

---

## 3. Concurrency, Persistence & Security Rules

- **Swift 6 Concurrency**: Enable `StrictConcurrency = complete`. Annotate UI stores with `@MainActor`, mark DTOs/repositories `Sendable`, and use `.task(id:)` in SwiftUI views so async work automatically cancels on disappear or parameter change.
- **Navigation**: Standardize on `NavigationStack` + typed `NavigationPath` + `.navigationDestination(for:)`; never use deprecated `NavigationView`.
- **Secrets & Storage**: Store tokens exclusively in Keychain (`kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly`) — NEVER in `UserDefaults` or `@AppStorage`. Use SwiftData / GRDB / SQLite for offline structured persistence.
- **Accessibility**: Support Dynamic Type (never hardcode fixed frame heights around text), add `.accessibilityLabel` / `.accessibilityHint` on icon-only controls, and verify VoiceOver navigation.

---

## 4. Testing with Swift Testing (`import Testing`)

```swift
import Testing
@testable import MyApp

@Suite("OrdersStore Tests")
struct OrdersStoreTests {
    @Test("transitions to loaded state on repository success")
    @MainActor
    func loadsOrdersSuccessfully() async {
        let stub = StubOrderRepository(result: .success([OrderItem(id: "1", reference: "ORD-1", totalCents: 2500)]))
        let store = OrdersStore(repository: stub)
        await store.load()
        #expect(store.state == .loaded([OrderItem(id: "1", reference: "ORD-1", totalCents: 2500)]))
    }
}
```

---

## 5. Verification Checklist

- [ ] Swift 6 language mode with zero concurrency data-race warnings.
- [ ] `@Observable` used for all new iOS 17+ state models; zero retain cycles or leaked `Task` handles.
- [ ] Zero tokens/PII stored in `UserDefaults` or `@AppStorage` (Keychain enforced).
- [ ] Dynamic Type, Dark Mode, and VoiceOver verified on physical device / Simulator.
- [ ] `xcodebuild test` (Swift Testing + XCUITest) passes with Exit Code `0`.
