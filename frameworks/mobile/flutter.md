# 📱 Dart / Flutter 3.35+ Production Engineering Guide (`flutter.md`)

> **Framework**: Flutter 3.29 – 3.35+ / Dart 3.7 – 3.9+ / Impeller / Riverpod 3.x  
> **Classification**: Cross-Platform Mobile, Desktop & Web Architecture  
> **Applicability**: Production apps targeting iOS, Android (Kotlin DSL `build.gradle.kts`), Web, macOS, Windows, Linux  
> **Governing Rules**: **R-001**, **R-033**, **R-064**, **R-256**  
> **Last Updated**: 2026-11-19

---

## 1. Core Philosophy

**"Own every pixel, own every frame."** Flutter 3.29–3.35+ compiles ahead-of-time with **Impeller** as the default rendering engine on both iOS and Android (API 29+ Vulkan), eliminating Skia shader jank. Pair strict Dart 3.7–3.9+ pattern matching & records, **Riverpod 3.x** (`@riverpod` + `Ref.mounted` + `AsyncValue.guard`), **Material 3 Expressive**, and **Pigeon** type-safe native interop to ship 60/120fps apps with zero frame drops.

---

## 2. When to Use Flutter

| Use Flutter When | Do NOT Use Flutter When |
|---|---|
| You need pixel-perfect UI parity across iOS + Android | You need deep integration with a single platform's SDK (e.g., HealthKit-only app) |
| Your team knows Dart or can ramp up quickly | Your entire team is expert in Swift/Kotlin and the app is single-platform |
| You want custom rendering, animations, shaders | You are building a thin wrapper around a WebView |
| You need hot reload for rapid iteration | You need access to bleeding-edge platform APIs on day zero |
| You are building for mobile + web + desktop from one codebase | Your app is purely a background service with no UI |

---

## 3. Architecture & Project Structure

### 3.1 Recommended Feature-First Layout

```
lib/
├── main.dart                        # Entry point, ProviderScope / BlocProviders
├── app.dart                         # MaterialApp.router configuration
├── core/
│   ├── constants/
│   │   ├── app_colors.dart
│   │   └── api_endpoints.dart
│   ├── errors/
│   │   ├── failures.dart            # Domain failure classes
│   │   └── exceptions.dart          # Infrastructure exceptions
│   ├── network/
│   │   ├── dio_client.dart          # Configured Dio instance
│   │   ├── interceptors/
│   │   │   ├── auth_interceptor.dart
│   │   │   └── retry_interceptor.dart
│   │   └── api_result.dart          # sealed Result<T> type
│   ├── routing/
│   │   ├── app_router.dart          # GoRouter configuration
│   │   └── route_guards.dart
│   └── theme/
│       ├── app_theme.dart
│       └── typography.dart
├── features/
│   ├── auth/
│   │   ├── data/
│   │   │   ├── repositories/auth_repository_impl.dart
│   │   │   ├── datasources/auth_remote_datasource.dart
│   │   │   └── models/user_dto.dart
│   │   ├── domain/
│   │   │   ├── entities/user.dart
│   │   │   ├── repositories/auth_repository.dart
│   │   │   └── usecases/sign_in.dart
│   │   └── presentation/
│   │       ├── providers/auth_provider.dart     # Riverpod
│   │       ├── blocs/auth_bloc.dart             # or Bloc
│   │       ├── pages/login_page.dart
│   │       └── widgets/login_form.dart
│   └── orders/
│       ├── data/ ...
│       ├── domain/ ...
│       └── presentation/ ...
├── shared/
│   ├── widgets/
│   │   ├── app_button.dart
│   │   └── loading_overlay.dart
│   └── extensions/
│       ├── context_extensions.dart
│       └── string_extensions.dart
└── l10n/
    ├── app_en.arb
    └── app_es.arb
```

### 3.2 Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        UI Layer                              │
│  Page ──▶ Widget ──▶ reads Provider/Bloc ──▶ renders state  │
└──────────────────────────┬──────────────────────────────────┘
                           │ user action
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                   State Management Layer                     │
│  Riverpod Provider  /  Bloc + Events                        │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐              │
│  │AsyncValue│    │ BlocState │    │ Notifier │              │
│  └────┬─────┘    └─────┬────┘    └─────┬────┘              │
│       └────────────────┼───────────────┘                    │
│                        ▼                                    │
│                   Use Case                                  │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                     Domain Layer                             │
│  Entity ◀── Repository (abstract) ◀── UseCase               │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                  Data / Infrastructure Layer                  │
│  RepositoryImpl ──▶ RemoteDataSource (Dio)                  │
│                 ──▶ LocalDataSource  (Drift/Hive)           │
│                 ──▶ PlatformChannel  (MethodChannel)        │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. State Management — Riverpod 3.x (Recommended)

### 4.1 Why Riverpod 3.x Over Bloc

| Criterion | Riverpod 3.x (`@riverpod` + `riverpod_lint`) | Bloc 9.x |
|---|---|---|
| Boilerplate | Minimal with `@riverpod` codegen & plain `Ref` | Moderate (Event + State + Bloc classes) |
| Compile-time safety | Providers & `riverpod_lint` checked at compile time | Runtime `BlocProvider` lookups |
| Async lifecycle safety | Built-in `Ref.mounted`, `AsyncValue.guard`, `.copyWithPrevious()` | Manual cancellation / `isClosed` checks |
| Dependency injection | Built-in, declarative, scoped overrides | Requires manual wiring or `get_it` |
| Testing | Override any provider in `ProviderContainer` / `ProviderScope` | Requires `MockBloc` + `blocTest` |
| **Recommendation** | **Default for new production apps** | Use when team already standardizes on Bloc |

### 4.2 Riverpod 3.x — Production Patterns

```dart
// pubspec.yaml dependencies:
// flutter_riverpod: ^3.0.0
// riverpod_annotation: ^3.0.0
// riverpod_generator: ^3.0.0  (dev)
// riverpod_lint: ^3.0.0       (dev)
// build_runner: ^2.4.15       (dev)

// ── domain/repositories/order_repository.dart ──
abstract class OrderRepository {
  Future<List<Order>> getOrders({required int page, required int limit});
  Future<Order> getOrderById(String id);
  Future<void> cancelOrder(String id);
}

// ── data/repositories/order_repository_impl.dart ──
class OrderRepositoryImpl implements OrderRepository {
  final DioClient _client;
  final OrderLocalDataSource _local;

  OrderRepositoryImpl(this._client, this._local);

  @override
  Future<List<Order>> getOrders({required int page, required int limit}) async {
    try {
      final response = await _client.get(
        '/v1/orders',
        queryParameters: {'page': page, 'limit': limit},
      );
      final orders = (response.data['data'] as List)
          .map((json) => OrderDto.fromJson(json).toDomain())
          .toList();
      // Cache locally for offline support
      await _local.cacheOrders(orders, page: page);
      return orders;
    } on DioException catch (e) {
      if (e.type == DioExceptionType.connectionError) {
        // Fallback to cached data
        return _local.getCachedOrders(page: page, limit: limit);
      }
      throw ServerException.fromDioError(e);
    }
  }

  @override
  Future<Order> getOrderById(String id) async {
    final response = await _client.get('/v1/orders/$id');
    return OrderDto.fromJson(response.data['data']).toDomain();
  }

  @override
  Future<void> cancelOrder(String id) async {
    await _client.post('/v1/orders/$id/cancel');
  }
}

// ── presentation/providers/order_providers.dart ──
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

part 'order_providers.g.dart';

// Riverpod 3.x: Use unified `Ref` (custom `*Ref` typedefs were removed in 3.0)
@riverpod
OrderRepository orderRepository(Ref ref) {
  final client = ref.watch(dioClientProvider);
  final local = ref.watch(orderLocalDataSourceProvider);
  return OrderRepositoryImpl(client, local);
}

@riverpod
class OrderList extends _$OrderList {
  int _page = 1;
  static const _limit = 20;

  @override
  Future<List<Order>> build() => _fetch();

  Future<List<Order>> _fetch() {
    return ref.read(orderRepositoryProvider).getOrders(
      page: _page,
      limit: _limit,
    );
  }

  Future<void> loadNextPage() async {
    _page++;
    // Preserve previous items on screen while fetching next page (zero layout flash)
    state = const AsyncValue<List<Order>>.loading().copyWithPrevious(state);
    final next = await AsyncValue.guard(() => _fetch());
    if (!ref.mounted) return; // Riverpod 3.x lifecycle guard across async gaps
    state = next;
  }

  Future<void> refresh() async {
    _page = 1;
    ref.invalidateSelf();
  }
}

@riverpod
Future<Order> orderDetail(Ref ref, String orderId) {
  return ref.watch(orderRepositoryProvider).getOrderById(orderId);
}

// ── presentation/pages/orders_page.dart ──
class OrdersPage extends ConsumerWidget {
  const OrdersPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    // Keep providers pure: handle UI side effects (snackbars, navigation) via ref.listen
    ref.listen(orderListProvider, (previous, next) {
      if (next.hasError && !next.isLoading) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Refresh failed: ${next.error}')),
        );
      }
    });

    final ordersAsync = ref.watch(orderListProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Orders')),
      // Exhaustive Dart 3 pattern matching on AsyncValue
      body: switch (ordersAsync) {
        AsyncData(:final value) => RefreshIndicator(
            onRefresh: () => ref.read(orderListProvider.notifier).refresh(),
            child: ListView.builder(
              itemCount: value.length,
              itemBuilder: (context, index) => OrderTile(order: value[index]),
            ),
          ),
        AsyncError(:final error) => ErrorRetryWidget(
            message: error.toString(),
            onRetry: () => ref.invalidate(orderListProvider),
          ),
        _ => const Center(child: CircularProgressIndicator()),
      },
    );
  }
}
```

### 4.3 Bloc — Production Pattern (Alternative)

```dart
// pubspec.yaml: flutter_bloc: ^8.1.6

// ── Order Events ──
sealed class OrderEvent {}
final class OrdersLoadRequested extends OrderEvent {
  final int page;
  OrdersLoadRequested({this.page = 1});
}
final class OrderCancelRequested extends OrderEvent {
  final String orderId;
  OrderCancelRequested(this.orderId);
}

// ── Order State ──
sealed class OrderState {}
final class OrderInitial extends OrderState {}
final class OrderLoadInProgress extends OrderState {}
final class OrderLoadSuccess extends OrderState {
  final List<Order> orders;
  OrderLoadSuccess(this.orders);
}
final class OrderLoadFailure extends OrderState {
  final String message;
  OrderLoadFailure(this.message);
}

// ── Order Bloc ──
class OrderBloc extends Bloc<OrderEvent, OrderState> {
  final OrderRepository _repository;

  OrderBloc(this._repository) : super(OrderInitial()) {
    on<OrdersLoadRequested>(_onLoadRequested);
    on<OrderCancelRequested>(_onCancelRequested);
  }

  Future<void> _onLoadRequested(
    OrdersLoadRequested event,
    Emitter<OrderState> emit,
  ) async {
    emit(OrderLoadInProgress());
    try {
      final orders = await _repository.getOrders(
        page: event.page,
        limit: 20,
      );
      emit(OrderLoadSuccess(orders));
    } catch (e) {
      emit(OrderLoadFailure(e.toString()));
    }
  }

  Future<void> _onCancelRequested(
    OrderCancelRequested event,
    Emitter<OrderState> emit,
  ) async {
    await _repository.cancelOrder(event.orderId);
    add(OrdersLoadRequested()); // Reload after cancel
  }
}
```

---

## 5. Platform Channels — Native Interop

### 5.1 Architecture

```
┌─────────────────┐         ┌─────────────────┐
│   Dart (Flutter) │◀═══════▶│  Native (Swift/  │
│                  │  Binary  │  Kotlin/ObjC/   │
│  MethodChannel   │  Codec   │  Java)          │
│  EventChannel    │         │                  │
│  BasicMessage    │         │                  │
└─────────────────┘         └─────────────────┘

Channel Types & Modern Codegen:
  Pigeon (Recommended) → Generates compile-time type-safe Dart + Swift + Kotlin channels (eliminates stringly-typed Map casting)
  MethodChannel        → Request/Response (RPC-style, fallback for tiny 1-method bridges)
  EventChannel         → Stream of events from native → Dart
  dart:ffi / ffigen    → Direct zero-copy C/Rust/Objective-C/JNI interop for high-frequency compute
```

### 5.2 MethodChannel — Production Example (or Generate via `pigeon`)

```dart
// ── Dart side ──
class BiometricService {
  static const _channel = MethodChannel('com.myapp.biometric');

  /// Returns true if biometric authentication succeeded.
  Future<bool> authenticate({required String reason}) async {
    try {
      final result = await _channel.invokeMethod<bool>(
        'authenticate',
        {'reason': reason},
      );
      return result ?? false;
    } on PlatformException catch (e) {
      // ✅ Good: Map platform errors to domain errors
      switch (e.code) {
        case 'NOT_AVAILABLE':
          throw BiometricNotAvailableException();
        case 'NOT_ENROLLED':
          throw BiometricNotEnrolledException();
        case 'LOCKED_OUT':
          throw BiometricLockedOutException();
        default:
          throw BiometricUnknownException(e.message ?? 'Unknown error');
      }
    }
  }

  Future<bool> get isAvailable async {
    return await _channel.invokeMethod<bool>('isAvailable') ?? false;
  }
}
```

```kotlin
// ── Android (Kotlin) side ──
// android/app/src/main/kotlin/.../BiometricPlugin.kt

class BiometricPlugin(private val activity: FragmentActivity) :
    MethodChannel.MethodCallHandler {

    companion object {
        const val CHANNEL = "com.myapp.biometric"
    }

    fun register(messenger: BinaryMessenger) {
        MethodChannel(messenger, CHANNEL).setMethodCallHandler(this)
    }

    override fun onMethodCall(call: MethodCall, result: MethodChannel.Result) {
        when (call.method) {
            "authenticate" -> {
                val reason = call.argument<String>("reason") ?: "Authenticate"
                authenticateWithBiometric(reason, result)
            }
            "isAvailable" -> {
                val biometricManager = BiometricManager.from(activity)
                val canAuth = biometricManager.canAuthenticate(
                    BiometricManager.Authenticators.BIOMETRIC_STRONG
                )
                result.success(canAuth == BiometricManager.BIOMETRIC_SUCCESS)
            }
            else -> result.notImplemented()
        }
    }

    private fun authenticateWithBiometric(
        reason: String,
        result: MethodChannel.Result
    ) {
        val promptInfo = BiometricPrompt.PromptInfo.Builder()
            .setTitle("Authentication Required")
            .setSubtitle(reason)
            .setNegativeButtonText("Cancel")
            .setAllowedAuthenticators(
                BiometricManager.Authenticators.BIOMETRIC_STRONG
            )
            .build()

        val biometricPrompt = BiometricPrompt(
            activity,
            ContextCompat.getMainExecutor(activity),
            object : BiometricPrompt.AuthenticationCallback() {
                override fun onAuthenticationSucceeded(
                    authResult: BiometricPrompt.AuthenticationResult
                ) {
                    result.success(true)
                }
                override fun onAuthenticationError(
                    errorCode: Int, errString: CharSequence
                ) {
                    when (errorCode) {
                        BiometricPrompt.ERROR_LOCKOUT,
                        BiometricPrompt.ERROR_LOCKOUT_PERMANENT ->
                            result.error("LOCKED_OUT", errString.toString(), null)
                        BiometricPrompt.ERROR_NO_BIOMETRICS ->
                            result.error("NOT_ENROLLED", errString.toString(), null)
                        BiometricPrompt.ERROR_HW_NOT_PRESENT ->
                            result.error("NOT_AVAILABLE", errString.toString(), null)
                        else ->
                            result.error("AUTH_ERROR", errString.toString(), null)
                    }
                }
                override fun onAuthenticationFailed() {
                    // Don't call result here — prompt stays open for retry
                }
            }
        )
        biometricPrompt.authenticate(promptInfo)
    }
}
```

### 5.3 EventChannel — Streaming Native Data

```dart
// ── Dart: Listen to native sensor stream ──
class AccelerometerService {
  static const _eventChannel = EventChannel('com.myapp.accelerometer');

  Stream<AccelerometerData> get stream {
    return _eventChannel.receiveBroadcastStream().map((event) {
      final map = Map<String, double>.from(event as Map);
      return AccelerometerData(
        x: map['x']!,
        y: map['y']!,
        z: map['z']!,
        timestamp: DateTime.now(),
      );
    });
  }
}
```

---

## 6. Custom RenderObjects & Advanced Painting

### 6.1 When to Use Custom RenderObjects

Use `RenderObject` / `RenderBox` when:
- You need layout logic that no existing widget provides
- You need pixel-level control over hit testing
- Performance demands bypassing the widget rebuild cycle
- You are building a chart library, game canvas, or custom scrolling

**Do NOT use** for simple styling — use `CustomPainter` first, then `RenderBox` only if needed.

### 6.2 CustomPainter — Production Chart Example

```dart
class SparklineChart extends CustomPainter {
  final List<double> data;
  final Color lineColor;
  final Color gradientStart;
  final Color gradientEnd;

  SparklineChart({
    required this.data,
    this.lineColor = const Color(0xFF2196F3),
    this.gradientStart = const Color(0x402196F3),
    this.gradientEnd = const Color(0x002196F3),
  });

  @override
  void paint(Canvas canvas, Size size) {
    if (data.length < 2) return;

    final maxVal = data.reduce(max);
    final minVal = data.reduce(min);
    final range = maxVal - minVal;
    if (range == 0) return;

    final stepX = size.width / (data.length - 1);

    // Build path
    final path = Path();
    for (int i = 0; i < data.length; i++) {
      final x = i * stepX;
      final y = size.height - ((data[i] - minVal) / range * size.height);
      if (i == 0) {
        path.moveTo(x, y);
      } else {
        path.lineTo(x, y);
      }
    }

    // Draw line
    final linePaint = Paint()
      ..color = lineColor
      ..strokeWidth = 2.0
      ..style = PaintingStyle.stroke
      ..strokeCap = StrokeCap.round;
    canvas.drawPath(path, linePaint);

    // Draw gradient fill
    final gradientPath = Path.from(path)
      ..lineTo(size.width, size.height)
      ..lineTo(0, size.height)
      ..close();

    final gradientPaint = Paint()
      ..shader = LinearGradient(
        begin: Alignment.topCenter,
        end: Alignment.bottomCenter,
        colors: [gradientStart, gradientEnd],
      ).createShader(Rect.fromLTWH(0, 0, size.width, size.height));

    canvas.drawPath(gradientPath, gradientPaint);
  }

  @override
  bool shouldRepaint(SparklineChart oldDelegate) {
    return oldDelegate.data != data || oldDelegate.lineColor != lineColor;
  }
}

// Usage:
// CustomPaint(
//   painter: SparklineChart(data: priceHistory),
//   size: const Size(double.infinity, 100),
// )
```

---

## 7. Fragment Shaders & Impeller

### 7.1 Impeller Rendering Engine (Default on iOS & Android)

Flutter 3.29–3.35+ runs **Impeller** by default on both iOS (Metal) and Android (Vulkan on API 29+, OpenGL ES fallback). Do not disable Impeller in production or attempt legacy Skia manual shader warmup.

| Feature | Skia (Legacy) | Impeller (Default) |
|---|---|---|
| Shader compilation | Runtime (causes jank) | Ahead-of-time offline compilation (zero shader jank) |
| First-frame & blur performance | Slow warm-up | Fast (~50% lower blur rasterization cost) |
| iOS default | Legacy | Default since Flutter 3.16 (Metal) |
| Android default | Legacy | Default on API 29+ Vulkan (Flutter 3.27+) |
| Custom fragment shaders | `.glsl` | `.frag` compiled via `impellerc` |

### 7.2 Fragment Shader Example

```glsl
// shaders/ripple.frag
#version 460 core
#include <flutter/runtime_effect.glsl>

uniform vec2 uSize;         // Canvas size
uniform float uTime;        // Animation time
uniform vec2 uCenter;       // Ripple center
out vec4 fragColor;

void main() {
    vec2 uv = FlutterFragCoord().xy / uSize;
    vec2 center = uCenter / uSize;

    float dist = distance(uv, center);
    float ripple = sin(dist * 40.0 - uTime * 6.0) * 0.5 + 0.5;
    ripple *= smoothstep(0.5, 0.0, dist); // Fade at edges

    vec3 color = mix(
        vec3(0.1, 0.1, 0.2),
        vec3(0.2, 0.5, 1.0),
        ripple
    );

    fragColor = vec4(color, 1.0);
}
```

```dart
// ── Load and use the shader ──
class RippleShaderWidget extends StatefulWidget {
  const RippleShaderWidget({super.key});

  @override
  State<RippleShaderWidget> createState() => _RippleShaderWidgetState();
}

class _RippleShaderWidgetState extends State<RippleShaderWidget>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller;
  FragmentShader? _shader;
  Offset _center = Offset.zero;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 10),
    )..repeat();
    _loadShader();
  }

  Future<void> _loadShader() async {
    final program = await FragmentProgram.fromAsset('shaders/ripple.frag');
    setState(() => _shader = program.fragmentShader());
  }

  @override
  Widget build(BuildContext context) {
    if (_shader == null) return const SizedBox.shrink();

    return GestureDetector(
      onPanUpdate: (d) => setState(() => _center = d.localPosition),
      child: AnimatedBuilder(
        animation: _controller,
        builder: (context, _) {
          return CustomPaint(
            painter: ShaderPainter(
              shader: _shader!,
              time: _controller.value * 10,
              center: _center,
            ),
            size: Size.infinite,
          );
        },
      ),
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    _shader?.dispose();
    super.dispose();
  }
}

class ShaderPainter extends CustomPainter {
  final FragmentShader shader;
  final double time;
  final Offset center;

  ShaderPainter({
    required this.shader,
    required this.time,
    required this.center,
  });

  @override
  void paint(Canvas canvas, Size size) {
    shader
      ..setFloat(0, size.width)    // uSize.x
      ..setFloat(1, size.height)   // uSize.y
      ..setFloat(2, time)          // uTime
      ..setFloat(3, center.dx)     // uCenter.x
      ..setFloat(4, center.dy);    // uCenter.y

    canvas.drawRect(
      Rect.fromLTWH(0, 0, size.width, size.height),
      Paint()..shader = shader,
    );
  }

  @override
  bool shouldRepaint(ShaderPainter oldDelegate) => true;
}
```

---

## 8. Performance Profiling

### 8.1 Key Metrics & Budgets

| Metric | Target | Tool |
|---|---|---|
| Frame render time | < 16ms (60fps) / < 8ms (120fps) | DevTools Performance tab |
| Widget rebuild count | Minimize unnecessary rebuilds | `debugProfileBuildsEnabled` |
| Shader compilation jank | 0 frames on Impeller | DevTools Shader tab |
| App startup time | < 2s cold start | `flutter run --trace-startup` |
| Memory usage | < 150MB typical | DevTools Memory tab |
| Image cache size | < 100MB | `PaintingBinding.instance.imageCache` |

### 8.2 Profiling Commands

```bash
# Profile mode build (release optimizations + profiling hooks)
flutter run --profile

# Generate startup trace
flutter run --trace-startup --profile
# Outputs: build/start_up_info.json

# Build with size analysis
flutter build apk --analyze-size
flutter build ios --analyze-size
# Outputs tree map in DevTools

# Run with specific Impeller backend
flutter run --enable-impeller          # Force Impeller on Android
flutter run --no-enable-impeller       # Force Skia fallback
```

### 8.3 Common Performance Anti-Patterns

```dart
// ❌ BAD: Building expensive widgets inside build()
class BadList extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return ListView.builder(
      itemCount: 10000,
      itemBuilder: (context, index) {
        // Rebuilds every item on any parent rebuild
        return ExpensiveWidget(data: computeData(index));
      },
    );
  }
}

// ✅ GOOD: Use const constructors + extract widgets
class GoodList extends StatelessWidget {
  const GoodList({super.key});

  @override
  Widget build(BuildContext context) {
    return ListView.builder(
      itemCount: 10000,
      itemBuilder: (context, index) {
        return OrderItemTile(index: index); // Separate widget
      },
    );
  }
}

class OrderItemTile extends StatelessWidget {
  final int index;
  const OrderItemTile({super.key, required this.index});

  @override
  Widget build(BuildContext context) {
    // Only rebuilds when this widget's state changes
    return ListTile(title: Text('Order #$index'));
  }
}
```

```dart
// ❌ BAD: Watching entire object when you need one field
final allSettings = ref.watch(settingsProvider); // Rebuilds on ANY change

// ✅ GOOD: Select only what you need
final isDarkMode = ref.watch(
  settingsProvider.select((s) => s.isDarkMode),
); // Rebuilds only when isDarkMode changes
```

```dart
// ❌ BAD: Creating objects in build()
Widget build(BuildContext context) {
  final decoration = BoxDecoration(  // New object every build
    borderRadius: BorderRadius.circular(8),
    color: Colors.white,
  );
  return Container(decoration: decoration);
}

// ✅ GOOD: Use const or static
static const _decoration = BoxDecoration(
  borderRadius: BorderRadius.all(Radius.circular(8)),
  color: Colors.white,
);

Widget build(BuildContext context) {
  return Container(decoration: _decoration);
}
```

---

## 9. Testing

### 9.1 Test Pyramid

```
         ╱╲
        ╱  ╲         Integration Tests (10%)
       ╱ E2E╲        flutter_test + integration_test
      ╱──────╲
     ╱ Widget ╲      Widget Tests (30%)
    ╱  Tests   ╲     pump, find, tap, expect
   ╱────────────╲
  ╱  Unit Tests  ╲   Unit Tests (60%)
 ╱________________╲  Pure Dart, mocked deps
```

### 9.2 Golden Tests — Visual Regression (`alchemist` — replaces archived `golden_toolkit`)

```dart
// test/golden/order_card_test.dart
import 'package:alchemist/alchemist.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  goldenTest(
    'OrderCard renders all lifecycle states cleanly',
    fileName: 'order_card_states',
    builder: () => GoldenTestGroup(
      columns: 2,
      children: [
        GoldenTestScenario(
          name: 'processing',
          child: const OrderCard(
            order: Order(
              id: 'ORD-001',
              status: OrderStatus.processing,
              total: 99.99,
              itemCount: 3,
              createdAt: '2026-01-15',
            ),
          ),
        ),
        GoldenTestScenario(
          name: 'cancelled',
          child: const OrderCard(
            order: Order(
              id: 'ORD-002',
              status: OrderStatus.cancelled,
              total: 0,
              itemCount: 0,
              createdAt: '2026-01-10',
            ),
          ),
        ),
      ],
    ),
  );
}

// Run golden tests:
// flutter test --update-goldens              # Generate CI & platform reference images
// flutter test                                # Compare against references
```

### 9.3 Widget Test with Riverpod

```dart
// test/widget/orders_page_test.dart
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart'; // mocktail: ^1.0.4

class MockOrderRepository extends Mock implements OrderRepository {}

void main() {
  late MockOrderRepository mockRepo;

  setUp(() {
    mockRepo = MockOrderRepository();
  });

  testWidgets('OrdersPage shows orders on success', (tester) async {
    // Arrange
    when(() => mockRepo.getOrders(page: 1, limit: any(named: 'limit')))
        .thenAnswer((_) async => [
              Order(id: '1', status: OrderStatus.delivered, total: 42.0,
                    itemCount: 2, createdAt: '2026-01-15'),
            ]);

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          // ✅ Override the repository provider, not the UI provider
          orderRepositoryProvider.overrideWithValue(mockRepo),
        ],
        child: const MaterialApp(home: OrdersPage()),
      ),
    );

    // Act — wait for async provider to resolve
    await tester.pumpAndSettle();

    // Assert
    expect(find.text('Order #1'), findsOneWidget);
    expect(find.byType(CircularProgressIndicator), findsNothing);
  });

  testWidgets('OrdersPage shows error state', (tester) async {
    when(() => mockRepo.getOrders(page: any(named: 'page'), limit: any(named: 'limit')))
        .thenThrow(ServerException('Network error'));

    await tester.pumpWidget(
      ProviderScope(
        overrides: [orderRepositoryProvider.overrideWithValue(mockRepo)],
        child: const MaterialApp(home: OrdersPage()),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('Network error'), findsOneWidget);
    expect(find.byType(ErrorRetryWidget), findsOneWidget);
  });
}
```

---

## 10. Deep Linking & Navigation

### 10.1 GoRouter Configuration

```dart
// pubspec.yaml: go_router: ^14.3.0

// ── core/routing/app_router.dart ──
final routerProvider = Provider<GoRouter>((ref) {
  final authState = ref.watch(authStateProvider);

  return GoRouter(
    initialLocation: '/',
    debugLogDiagnostics: kDebugMode,
    refreshListenable: authState,  // Re-evaluate redirects on auth change
    redirect: (context, state) {
      final isLoggedIn = authState.isAuthenticated;
      final isLoggingIn = state.matchedLocation.startsWith('/auth');

      if (!isLoggedIn && !isLoggingIn) return '/auth/login';
      if (isLoggedIn && isLoggingIn) return '/';
      return null; // No redirect
    },
    routes: [
      ShellRoute(
        builder: (context, state, child) => AppShell(child: child),
        routes: [
          GoRoute(
            path: '/',
            name: 'home',
            builder: (context, state) => const HomePage(),
          ),
          GoRoute(
            path: '/orders',
            name: 'orders',
            builder: (context, state) => const OrdersPage(),
            routes: [
              GoRoute(
                path: ':orderId',
                name: 'order-detail',
                builder: (context, state) {
                  final orderId = state.pathParameters['orderId']!;
                  return OrderDetailPage(orderId: orderId);
                },
              ),
            ],
          ),
          GoRoute(
            path: '/profile',
            name: 'profile',
            builder: (context, state) => const ProfilePage(),
          ),
        ],
      ),
      GoRoute(
        path: '/auth/login',
        name: 'login',
        builder: (context, state) => const LoginPage(),
      ),
    ],
    errorBuilder: (context, state) => NotFoundPage(
      error: state.error,
    ),
  );
});
```

### 10.2 Platform Deep Link Configuration

```xml
<!-- android/app/src/main/AndroidManifest.xml -->
<activity ...>
  <!-- App Links (verified) -->
  <intent-filter android:autoVerify="true">
    <action android:name="android.intent.action.VIEW" />
    <category android:name="android.intent.category.DEFAULT" />
    <category android:name="android.intent.category.BROWSABLE" />
    <data android:scheme="https"
          android:host="myapp.com"
          android:pathPrefix="/orders" />
  </intent-filter>

  <!-- Custom scheme (non-verified, for dev/testing) -->
  <intent-filter>
    <action android:name="android.intent.action.VIEW" />
    <category android:name="android.intent.category.DEFAULT" />
    <category android:name="android.intent.category.BROWSABLE" />
    <data android:scheme="myapp"
          android:host="open" />
  </intent-filter>
</activity>
```

```xml
<!-- ios/Runner/Info.plist — Universal Links -->
<key>FlutterDeepLinkingEnabled</key>
<true/>

<!-- ios/Runner/Runner.entitlements -->
<key>com.apple.developer.associated-domains</key>
<array>
  <string>applinks:myapp.com</string>
</array>
```

---

## 11. Background Processing

### 11.1 Strategy Selection

| Scenario | Solution | Package |
|---|---|---|
| Periodic sync (every 15min+) | `workmanager` | `workmanager: ^0.5.2` |
| Long-running uploads | Foreground service + isolate | `flutter_foreground_task: ^8.0.0` |
| Push-triggered background work | Firebase Cloud Messaging | `firebase_messaging: ^15.0.0` |
| Heavy CPU computation | Dart Isolate | Built-in `Isolate.run()` |
| Local notifications scheduling | `flutter_local_notifications` | `^17.0.0` |

### 11.2 Dart Isolates for CPU-Intensive Work

```dart
// ✅ Dart 3.0+ — Use Isolate.run() for one-shot computation
Future<List<ProcessedImage>> processImages(List<Uint8List> rawImages) async {
  return await Isolate.run(() {
    // This runs on a separate isolate — no UI jank
    return rawImages.map((bytes) {
      final decoded = img.decodeImage(bytes)!;
      final resized = img.copyResize(decoded, width: 800);
      final compressed = img.encodeJpg(resized, quality: 85);
      return ProcessedImage(data: Uint8List.fromList(compressed));
    }).toList();
  });
}

// For long-lived background work with bidirectional communication:
class BackgroundSyncService {
  ReceivePort? _receivePort;
  Isolate? _isolate;

  Future<void> start() async {
    _receivePort = ReceivePort();
    _isolate = await Isolate.spawn(
      _syncWorker,
      _receivePort!.sendPort,
    );

    _receivePort!.listen((message) {
      if (message is SyncProgress) {
        // Update UI with progress
        debugPrint('Sync progress: ${message.percent}%');
      } else if (message is SyncComplete) {
        stop();
      }
    });
  }

  static void _syncWorker(SendPort sendPort) async {
    // Heavy work on background isolate
    for (int i = 0; i < 100; i++) {
      // ... sync chunk
      sendPort.send(SyncProgress(percent: i));
      await Future.delayed(const Duration(milliseconds: 100));
    }
    sendPort.send(SyncComplete());
  }

  void stop() {
    _isolate?.kill(priority: Isolate.immediate);
    _receivePort?.close();
  }
}
```

### 11.3 WorkManager for Periodic Background Tasks

```dart
// ── main.dart ──
void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  await Workmanager().initialize(
    callbackDispatcher,
    isInDebugMode: kDebugMode,
  );

  // Register periodic task (minimum 15 minutes on Android)
  await Workmanager().registerPeriodicTask(
    'sync-orders',
    'orderSync',
    frequency: const Duration(hours: 1),
    constraints: Constraints(
      networkType: NetworkType.connected,
      requiresBatteryNotLow: true,
    ),
    backoffPolicy: BackoffPolicy.exponential,
    initialDelay: const Duration(minutes: 5),
    existingWorkPolicy: ExistingWorkPolicy.keep,
  );

  runApp(const MyApp());
}

// Must be top-level function
@pragma('vm:entry-point')
void callbackDispatcher() {
  Workmanager().executeTask((taskName, inputData) async {
    switch (taskName) {
      case 'orderSync':
        try {
          // Initialize dependencies manually (no widget tree)
          final db = await openDatabase();
          final api = ApiClient(baseUrl: 'https://api.myapp.com');
          final pendingOrders = await db.getPendingOrders();

          for (final order in pendingOrders) {
            await api.syncOrder(order);
            await db.markSynced(order.id);
          }
          return true; // Success
        } catch (e) {
          return false; // Will retry with exponential backoff
        }
      default:
        return false;
    }
  });
}
```

---

## 12. Security Considerations

### 12.1 Secure Storage

```dart
// ✅ Use flutter_secure_storage for secrets (uses Keychain / KeyStore)
// pubspec.yaml: flutter_secure_storage: ^9.2.2

final secureStorage = const FlutterSecureStorage(
  aOptions: AndroidOptions(encryptedSharedPreferences: true),
  iOptions: IOSOptions(accessibility: KeychainAccessibility.first_unlock),
);

// Store
await secureStorage.write(key: 'refresh_token', value: token);

// Read
final token = await secureStorage.read(key: 'refresh_token');

// ❌ NEVER store tokens in SharedPreferences or Hive (unencrypted)
// ❌ NEVER log tokens or PII
// ❌ NEVER hardcode API keys in Dart source
```

### 12.2 Certificate Pinning

```dart
// ── Using Dio with certificate pinning ──
Dio createPinnedClient() {
  final dio = Dio();
  (dio.httpClientAdapter as IOHttpClientAdapter).createHttpClient = () {
    final client = HttpClient();
    client.badCertificateCallback = (cert, host, port) {
      // Compare certificate fingerprint
      final fingerprint = sha256.convert(cert.der).toString();
      return fingerprint == 'YOUR_EXPECTED_SHA256_FINGERPRINT';
    };
    return client;
  };
  return dio;
}
```

### 12.3 Code Obfuscation

```bash
# Always obfuscate release builds
flutter build apk --obfuscate --split-debug-info=build/debug-info/
flutter build ios --obfuscate --split-debug-info=build/debug-info/

# Save debug symbols for crash report symbolication
# Upload build/debug-info/ to Sentry/Crashlytics
```

---

## 13. Common Pitfalls & Anti-Patterns

| Anti-Pattern | Why It's Bad | Fix |
|---|---|---|
| Using `setState` everywhere | Doesn't scale, triggers full subtree rebuilds | Use Riverpod/Bloc for any shared state |
| Not using `const` constructors | Prevents Flutter from skipping rebuilds | Add `const` to every stateless constructor |
| `FutureBuilder` in `build()` | Creates new Future on every rebuild | Use `ref.watch` (Riverpod) or cache the Future |
| Blocking the UI isolate | Image processing, JSON parsing freezes UI | Use `Isolate.run()` or `compute()` |
| Storing secrets in `SharedPreferences` | Plaintext on disk, trivially readable | Use `flutter_secure_storage` |
| Not disposing controllers | Memory leaks, zombie listeners | Always `dispose()` in `State.dispose()` |
| Using `MediaQuery.of(context)` directly | Rebuilds on keyboard open/close | Use `MediaQuery.sizeOf(context)` (Flutter 3.10+) |
| Ignoring `RepaintBoundary` | Entire subtree repaints on animation | Wrap animated widgets in `RepaintBoundary` |
| Unbounded `ListView` in `Column` | Layout overflow error | Use `Expanded` or `SliverList` |
| Not testing on release mode | Debug mode hides jank, adds overhead | Always profile on physical device in profile mode |

---

## 14. Verification Checklist

Before shipping a Flutter production app, verify:

- [ ] **Build**: Release build succeeds with `--obfuscate` on both platforms
- [ ] **Performance**: No frame > 16ms in profile mode on lowest-tier target device
- [ ] **Startup**: Cold start < 2 seconds on mid-range device
- [ ] **Memory**: Peak memory < 200MB during normal usage
- [ ] **Tests**: Unit (>80%), Widget (>50%), Golden (all critical screens), Integration (happy paths)
- [ ] **Deep Links**: `https://` and custom scheme links open correct screens
- [ ] **Background**: WorkManager tasks execute after app kill (test on Android 12+)
- [ ] **Accessibility**: All interactive widgets have semantic labels; screen reader tested
- [ ] **Localization**: All user-facing strings use `AppLocalizations`, no hardcoded text
- [ ] **Security**: No secrets in source; certificate pinning enabled; secure storage for tokens
- [ ] **Error Handling**: Crashes reported to Sentry/Crashlytics with symbolicated stack traces
- [ ] **State Management**: No unnecessary rebuilds (verified with `debugProfileBuildsEnabled`)
- [ ] **Assets**: Images are resolution-aware (1x, 2x, 3x); fonts loaded with `FontManifest`
- [ ] **Platform Channels**: Error codes mapped to domain exceptions; null safety enforced
- [ ] **CI/CD**: `flutter analyze` clean; `flutter test` green; golden snapshots committed

---

## 15. Recommended Dependency Stack (2026)

| Category | Package | Version |
|---|---|---|
| State Management | `flutter_riverpod` + `riverpod_annotation` + `riverpod_lint` | `^3.0.0` |
| Routing | `go_router` | `^15.0.0` |
| HTTP Client | `dio` | `^5.8.0` |
| Local DB (SQLite) | `drift` | `^2.26.0` |
| Secure Storage | `flutter_secure_storage` | `^9.2.4` |
| Native Interop | `pigeon` (dev) | `^25.0.0` |
| Image Loading | `cached_network_image` | `^3.4.1` |
| Serialization | `freezed` + `json_serializable` | `^3.0.0` / `^6.9.0` |
| Testing (mocks) | `mocktail` | `^1.0.4` |
| Testing (golden) | `alchemist` (replaces archived `golden_toolkit`) | `^0.12.0` |
| Background Work | `workmanager` | `^0.7.0` |
| Analytics & Crash | `firebase_analytics` + `sentry_flutter` | `^11.4.0` / `^8.14.0` |
| Linting | `very_good_analysis` | `^7.0.0` |
