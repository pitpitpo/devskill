# 📱 React Native 0.79–0.81+ (New Architecture) & Expo SDK 53/54+ Guide (`frameworks/mobile/react-native-expo.md`)

> **Standard Identifier**: `FW-MOBILE-EXPO-001`  
> **Framework**: React Native 0.79–0.81+ (Fabric, TurboModules, JSI, Bridgeless, Hermes) & Expo SDK 53/54+  
> **Status**: Active / Production Standard  
> **Governing Rules**: **R-001**, **R-034**, **R-064**, **R-257**  
> **Last Updated**: 2026-11-19

---

## 1. Executive Summary & Core Philosophy

> **Golden Rule**: *React Native with Expo is a compiled native runtime running on Hermes over C++ JSI (Fabric + TurboModules + Bridgeless Mode). Treat the New Architecture as non-negotiable, keep animations on the UI thread with Reanimated worklets, persist offline data in hardware-keyed MMKV or `expo-sqlite` + Drizzle, and validate native health with `npx expo-doctor` in CI.*

---

## 2. New Architecture Stack (Fabric + TurboModules + Hermes)

```
┌─────────────────────────────────────────────────────────────────────────┐
│             REACT NATIVE 0.79–0.81+ / EXPO SDK 53–54+ (TS)              │
└──────────────────────────────────┬──────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                  HERMES AOT BYTECODE JS ENGINE                          │
└──────────────────────────────────┬──────────────────────────────────────┘
                                   │ Direct C++ JSI (Zero JSON Bridge)
                 ┌─────────────────┴─────────────────┐
                 ▼                                   ▼
┌─────────────────────────────────┐ ┌─────────────────────────────────────┐
│        FABRIC RENDERER          │ │   TURBOMODULES / EXPO MODULES API   │
│ Synchronous Native Layout Tree  │ │ Typed Codegen + Swift/Kotlin Native │
└────────────────┬────────────────┘ └──────────────────┬──────────────────┘
                 ▼                                     ▼
       UIKit (iOS) / AndroidX              Keychain / KeyStore / Camera / SQLite
```

### Mandatory New Architecture Rules
- **No Legacy Bridge**: Keep `newArchEnabled: true` everywhere; audit third-party native packages with `npx expo-doctor@latest` before adding them.
- **Continuous Native Generation (CNG)**: Treat `ios/` and `android/` as ephemeral generated artifacts via `expo prebuild` + Expo Config Plugins rather than hand-editing Xcode/Gradle files.
- **Custom Native Code**: Write native bridges with the **Expo Modules API** (idiomatic Swift + Kotlin) instead of raw Objective-C/Java bridge boilerplate — it automatically compiles cleanly for Fabric & TurboModules.

---

## 3. Typed Navigation with Expo Router (v4 / v5)

```tsx
// app/(tabs)/orders/[id].tsx
import { Stack, useLocalSearchParams } from 'expo-router';
import { Text, View } from 'react-native';

export default function OrderDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();

  return (
    <View className="flex-1 p-4">
      <Stack.Screen options={{ title: `Order #${id}` }} />
      <Text>Viewing order {id}</Text>
    </View>
  );
}
```
- Enable `experiments: { typedRoutes: true }` in `app.json` for compile-time route path checking and automatic Universal Links / Android App Links deep linking.

---

## 4. Secure Hardware-Keyed Offline Storage (MMKV + `expo-secure-store` & `expo-sqlite`)

Never hardcode encryption keys in TypeScript source (violates **R-064**). Generate a random 256-bit key once, store it in hardware-backed **`expo-secure-store`** (iOS Keychain / Android KeyStore), and pass it to **MMKV** (30x faster C++ JSI storage than `AsyncStorage`):

```typescript
// src/lib/storage.ts
import * as Crypto from 'expo-crypto';
import * as SecureStore from 'expo-secure-store';
import { MMKV } from 'react-native-mmkv';

const KEY_ALIAS = 'mmkv.storage.master.key';

async function getOrCreateEncryptionKey(): Promise<string> {
  const existing = await SecureStore.getItemAsync(KEY_ALIAS, {
    keychainAccessible: SecureStore.AFTER_FIRST_UNLOCK_THIS_DEVICE_ONLY,
  });
  if (existing) return existing;

  const bytes = await Crypto.getRandomBytesAsync(32);
  const generated = Array.from(bytes, (b) => b.toString(16).padStart(2, '0')).join('');
  await SecureStore.setItemAsync(KEY_ALIAS, generated, {
    keychainAccessible: SecureStore.AFTER_FIRST_UNLOCK_THIS_DEVICE_ONLY,
  });
  return generated;
}

export async function createEncryptedStorage(): Promise<MMKV> {
  const encryptionKey = await getOrCreateEncryptionKey();
  return new MMKV({ id: 'app-encrypted-cache', encryptionKey });
}
```
- For structured relational offline-first data (sync queues, orders, catalogs), use **`expo-sqlite`** paired with **Drizzle ORM** instead of stuffing large JSON blobs into key-value storage.

---

## 5. 60/120 FPS UI-Thread Gestures & High-Throughput Lists

### 5.1 Reanimated Worklets + Gesture Handler
```tsx
// src/components/SwipeableCard.tsx
import type { ReactNode } from 'react';
import { Dimensions, StyleSheet } from 'react-native';
import { Gesture, GestureDetector } from 'react-native-gesture-handler';
import Animated, { runOnJS, useAnimatedStyle, useSharedValue, withSpring } from 'react-native-reanimated';

const SCREEN_WIDTH = Dimensions.get('window').width;
const SWIPE_THRESHOLD = SCREEN_WIDTH * 0.3;

export function SwipeableCard({ onDismiss, children }: { onDismiss: () => void; children: ReactNode }) {
  const translateX = useSharedValue(0);

  const panGesture = Gesture.Pan()
    .onChange((event) => {
      'worklet';
      translateX.value = event.translationX;
    })
    .onEnd(() => {
      'worklet';
      if (Math.abs(translateX.value) > SWIPE_THRESHOLD) {
        translateX.value = withSpring(Math.sign(translateX.value) * SCREEN_WIDTH, {}, () => {
          runOnJS(onDismiss)();
        });
      } else {
        translateX.value = withSpring(0);
      }
    });

  const animatedStyle = useAnimatedStyle(() => ({
    transform: [{ translateX: translateX.value }],
  }));

  return (
    <GestureDetector gesture={panGesture}>
      <Animated.View style={[styles.card, animatedStyle]}>{children}</Animated.View>
    </GestureDetector>
  );
}

const styles = StyleSheet.create({
  card: { width: '100%', borderRadius: 16, backgroundColor: '#ffffff', elevation: 3 },
});
```

### 5.2 Virtualized Lists (`@shopify/flash-list`)
Use **`@shopify/flash-list`** (or `LegendList`) instead of `ScrollView` / `FlatList` for large dynamic feeds, providing `keyExtractor`, `getItemType`, and calibrated `estimatedItemSize` (in FlashList v1) so native views recycle with zero blank frames.

---

## 6. EAS Build, Submit & Safe OTA Updates (`eas.json`)

- **Native changes (new SDK, Expo Module, permissions)** → **EAS Build** (`eas build --platform all --profile production`).
- **Pure JS/TS/Asset fixes** → **EAS Update** (`eas update --branch production`) guarded by strict `runtimeVersion: { policy: "appVersion" }` in `app.json` so JS bundles never load onto incompatible native binaries.

---

## 7. Testing & CI Diagnostics

- **Dependency & Architecture Gate**: `npx expo-doctor@latest` (must exit 0 in CI).
- **Unit & Component**: Jest (`jest-expo`) + `@testing-library/react-native`.
- **Native E2E**: **Maestro** (`maestro test .maestro/flows/`) for fast, deterministic YAML user-journey flows on iOS Simulator & Android Emulator without flaky Appium/Detox setup.

---

## 8. Common Pitfalls & Anti-Patterns

| Anti-Pattern | Root Cause | Remediated Standard |
|---|---|---|
| **Animating with React `useState`** | Drives layout recalculations on the JS thread | Use `react-native-reanimated` `useSharedValue` + worklets on UI thread |
| **Hardcoded MMKV encryption key or `AsyncStorage` tokens** | Plaintext key in bundle or unencrypted disk file (R-064) | Store secrets and encryption keys exclusively in `expo-secure-store` |
| **Unbounded `ScrollView` for 500+ items** | Mounts every native view simultaneously (OOM crash) | Use `@shopify/flash-list` with `keyExtractor` and `getItemType` |
| **OTA bundle/native mismatch** | Shipping JS requiring a newly installed native module via OTA | Pin `runtimeVersion: { policy: "appVersion" }` and cut an EAS Build for native changes |

---

## 9. Verification Checklist

- [ ] New Architecture (Fabric + TurboModules + Hermes) active and `npx expo-doctor@latest` passes with 0 errors.
- [ ] Zero secrets or hardcoded encryption keys in source; credentials stored in `expo-secure-store`.
- [ ] Large lists virtualized via `@shopify/flash-list`; gestures/animations execute on UI thread via Reanimated.
- [ ] Expo Router typed routes and Universal/App Links configured and tested on physical devices.
- [ ] `tsc --noEmit`, Jest/RNTL tests, and Maestro E2E flows pass cleanly in CI.
