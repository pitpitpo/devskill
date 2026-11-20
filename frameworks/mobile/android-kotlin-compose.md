# 🤖 Native Android App Engineering: Kotlin 2.x & Jetpack Compose (`frameworks/mobile/android-kotlin-compose.md`)

> **Standard Identifier**: `FW-MOBILE-ANDROID-APP-001`  
> **Framework**: Kotlin 2.0/2.1+, Jetpack Compose (Material 3), Coroutines + StateFlow, Hilt, Room  
> **Status**: Active / Production Standard  
> **Governing Rules**: **R-001**, **R-033**, **R-064**, **R-258**  
> **Last Updated**: 2026-11-19

---

## 1. Core Philosophy & Golden Rule

> **Golden Rule**: *Model UI as an immutable `StateFlow<UiState>` emitted by a `ViewModel` and collected lifecycle-safely via `collectAsStateWithLifecycle()`. Keep Composables stateless and hoisted, run all I/O on `Dispatchers.IO` inside structured Coroutines, and enforce offline-first persistence with Room.*

*(For OS-level Android ROM, HAL, AIDL, and SELinux development, see [`frameworks/mobile/android-aosp.md`](android-aosp.md).)*

---

## 2. Unidirectional Data Flow (UDF) & Clean Architecture

```
Composable UI ──(User Intent / Callback)──► ViewModel (viewModelScope)
      ▲                                            │
      │ collectAsStateWithLifecycle()              ▼
  StateFlow<UiState> ◄──── Repository ◄── Room (SSOT) + Ktor/Retrofit API
```

---

## 3. Production ViewModel + Compose Pattern

```kotlin
// feature/orders/OrdersViewModel.kt
sealed interface OrdersUiState {
    data object Loading : OrdersUiState
    data class Success(val orders: ImmutableList<OrderItem>) : OrdersUiState
    data class Error(val message: String) : OrdersUiState
}

@HiltViewModel
class OrdersViewModel @Inject constructor(
    private val repository: OrderRepository,
) : ViewModel() {

    val uiState: StateFlow<OrdersUiState> = repository
        .observeOrders()
        .map<List<OrderItem>, OrdersUiState> { OrdersUiState.Success(it.toImmutableList()) }
        .catch { emit(OrdersUiState.Error(it.message ?: "Unable to load orders")) }
        .stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(stopTimeoutMillis = 5_000),
            initialValue = OrdersUiState.Loading,
        )

    fun refresh() {
        viewModelScope.launch {
            runCatching { repository.syncFromRemote() }
        }
    }
}
```

```kotlin
// feature/orders/OrdersScreen.kt
@Composable
fun OrdersRoute(
    onOrderClick: (String) -> Unit,
    viewModel: OrdersViewModel = hiltViewModel(),
) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()
    OrdersScreen(state = state, onRefresh = viewModel::refresh, onOrderClick = onOrderClick)
}

@Composable
fun OrdersScreen(
    state: OrdersUiState,
    onRefresh: () -> Unit,
    onOrderClick: (String) -> Unit,
    modifier: Modifier = Modifier,
) {
    when (state) {
        OrdersUiState.Loading -> Box(modifier.fillMaxSize(), Alignment.Center) { CircularProgressIndicator() }
        is OrdersUiState.Error -> ErrorRetryView(message = state.message, onRetry = onRefresh)
        is OrdersUiState.Success -> LazyColumn(modifier = modifier.fillMaxSize()) {
            // Always supply stable `key` and `contentType` for smooth 120fps recycling
            items(items = state.orders, key = { it.id }, contentType = { "order_row" }) { order ->
                OrderRow(order = order, onClick = { onOrderClick(order.id) })
            }
        }
    }
}
```

---

## 4. Security, Performance & Anti-Patterns

- **Strong Skipping Mode (Kotlin 2.0+)**: Enabled by default in the Compose Compiler plugin; still prefer immutable data models (`kotlinx.collections.immutable` / `@Immutable`) to avoid accidental recompositions.
- **Type-Safe Navigation**: Use Compose Navigation 2.8+ with `@Serializable` Kotlin route objects instead of fragile string interpolation routes.
- **Encrypted Credentials**: Store tokens in Android Keystore-backed encrypted DataStore (Tink AEAD) — never plaintext `SharedPreferences`.
- **Release Optimization**: Enable R8 full mode (`isMinifyEnabled = true`, `isShrinkResources = true`), generate **Baseline Profiles** for fast cold startup, and upload mapping files to Crashlytics/Sentry.
- **Anti-Patterns**: Never use `GlobalScope.launch`, never pass a `ViewModel` down into reusable leaf Composables, never call `collectAsState()` instead of `collectAsStateWithLifecycle()` on Android, and never trigger side effects directly inside a Composable body (use `LaunchedEffect` / `DisposableEffect`).

---

## 5. Verification Checklist

- [ ] Kotlin 2.x Gradle Kotlin DSL (`build.gradle.kts`) with Version Catalog (`libs.versions.toml`).
- [ ] All flows collected via `collectAsStateWithLifecycle()` with `WhileSubscribed(5_000)`.
- [ ] Every `LazyColumn`/`LazyRow` provides stable `key` and `contentType`.
- [ ] R8 minification + Baseline Profiles verified on release build; `./gradlew testDebugUnitTest connectedAndroidTest lint` exits `0`.
