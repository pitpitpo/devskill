# 📱 Enterprise React Native & Expo Production Engineering Standards

> **Standard Identifier**: `FW-MOBILE-EXPO-001`  
> **Status**: Active / Production Standard  
> **Target Audience**: Mobile Engineers, Cross-Platform Architects  
> **Classification**: Level 4 Framework Mastery Guide  

---

## 1. Executive Summary & Core Philosophy

> **Golden Rule**: *React Native with Expo is not a web view; it is a compiled native runtime executing JavaScript on the Hermès engine via the JSI (JavaScript Interface). Prioritize 60/120 FPS UI-thread animations with Reanimated, enforce offline-first architecture with MMKV, and automate binary generation via EAS Build.*

Modern cross-platform mobile delivery has converged on Expo with the New Architecture (Fabric renderer + TurboModules). By moving away from legacy asynchronous JSON bridges to direct C++ memory pointers via JSI, Expo delivers near-zero latency native performance while maintaining rapid iteration.

---

## 2. React Native New Architecture (Fabric & TurboModules)

```
                 ┌────────────────────────────────────────────────────────┐
                 │           REACT NATIVE APP (TYPESCRIPT)                │
                 └──────────────────────────┬─────────────────────────────┘
                                            │
                                            ▼
                 ┌────────────────────────────────────────────────────────┐
                 │                  HERMÈS JS ENGINE                      │
                 │          Ahead-Of-Time (AOT) Bytecode                  │
                 └──────────────────────────┬─────────────────────────────┘
                                            │ Direct Memory Binding (C++ JSI)
                                            ▼
                 ┌────────────────────────────────────────────────────────┐
                 │               JAVASCRIPT INTERFACE (JSI)               │
                 └──────────┬───────────────────────────────────┬─────────┘
                            │                                   │
                            ▼                                   ▼
                 ┌────────────────────┐               ┌────────────────────┐
                 │  FABRIC RENDERER   │               │   TURBOMODULES     │
                 │  Synchronous UI    │               │  Direct Native C++ │
                 │  Thread Mounts     │               │  Device Modules    │
                 └──────────┬─────────┘               └─────────┬──────────┘
                            │                                   │
                            ▼                                   ▼
                 ┌────────────────────┐               ┌────────────────────┐
                 │ iOS / Android UI   │               │ Native OS APIs     │
                 │ (UIKit / AndroidX) │               │ (Camera, Storage)  │
                 └────────────────────┘               └────────────────────┘
```

---

## 3. High-Performance Offline-First State & Storage: MMKV + TanStack Query

Standard `AsyncStorage` is slow and serialized over async storage queues. Production mobile apps mandate **react-native-mmkv** (Tencent's C++ memory-mapped key-value store, up to $30\times$ faster):

```typescript
// lib/storage.ts
import { MMKV } from "react-native-mmkv";

export const storage = new MMKV({
  id: "secure-app-storage",
  encryptionKey: "secure-hardware-backed-key", // Store key in Expo SecureStore
});

// Adapter for TanStack Query Persistence
export const clientPersister = {
  setItem: (key: string, value: string) => storage.set(key, value),
  getItem: (key: string) => storage.getString(key) ?? null,
  removeItem: (key: string) => storage.delete(key),
};
```

---

## 4. 60/120 FPS Declarative Gesture & Animation Engineering

Animations that calculate frames on the JavaScript thread drop frames whenever network queries or state updates occur. Standardize on **React Native Reanimated 3** and **Gesture Handler**:

```tsx
// components/SwipeableCard.tsx
import React from "react";
import { StyleSheet, Dimensions } from "react-native";
import { Gesture, GestureDetector } from "react-native-gesture-handler";
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withSpring,
  runOnJS,
} from "react-native-reanimated";

const { width: SCREEN_WIDTH } = Dimensions.get("window");
const SWIPE_THRESHOLD = SCREEN_WIDTH * 0.3;

interface SwipeableCardProps {
  onDismiss: () => void;
  children: React.ReactNode;
}

export function SwipeableCard({ onDismiss, children }: SwipeableCardProps) {
  const translateX = useSharedValue(0);

  const panGesture = Gesture.Pan()
    .onChange((event) => {
      "worklet"; // Executes directly on the native UI thread
      translateX.value = event.translationX;
    })
    .onEnd(() => {
      "worklet";
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
      <Animated.View style={[styles.card, animatedStyle]}>
        {children}
      </Animated.View>
    </GestureDetector>
  );
}

const styles = StyleSheet.create({
  card: {
    width: "100%",
    borderRadius: 16,
    backgroundColor: "#ffffff",
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 3,
  },
});
```

---

## 5. High-Throughput List Performance: FlashList vs FlatList

Legacy `FlatList` drops frames and produces blank spaces when scrolling thousands of items because of un-recycled native views. Use Shopify's **`@shopify/flash-list`**:

```tsx
import { FlashList } from "@shopify/flash-list";

export function OrderHistoryList({ orders }: { orders: Order[] }) {
  return (
    <FlashList
      data={orders}
      renderItem={({ item }) => <OrderItemRow order={item} />}
      estimatedItemSize={88} // Mandatory for instant recycling
      keyExtractor={(item) => item.id}
      getItemType={(item) => item.type} // Multi-layout recycling support
    />
  );
}
```

---

## 6. Enterprise EAS Build & OTA Update Strategy

```
                      ┌──────────────────────────────────────────────┐
                      │              CODE CHANGE MERGED              │
                      └──────────────────────┬───────────────────────┘
                                             │
                       Is Native Code Changed? (Pods / Gradle)
                                             │
                        ┌────────────────────┴────────────────────┐
                        ▼ YES                                     ▼ NO
             ┌───────────────────────┐                 ┌───────────────────────┐
             │       EAS BUILD       │                 │       EAS UPDATE      │
             │ Full native binary    │                 │ Over-The-Air (OTA)    │
             │ compiled in cloud     │                 │ JS bundle download    │
             │ -> App Store & Google │                 │ -> Instant user update│
             └───────────────────────┘                 └───────────────────────┘
```

### Production `eas.json` Configuration
```json
{
  "cli": {
    "version": ">= 12.0.0"
  },
  "build": {
    "production": {
      "channel": "production",
      "autoIncrement": true,
      "env": {
        "APP_ENV": "production"
      },
      "android": {
        "buildType": "app-bundle"
      },
      "ios": {
        "simulator": false
      }
    }
  }
}
```

---

## 7. Verification Checklist & Production Audit

- [ ] New Architecture (Fabric + TurboModules) and Hermès engine are enabled in `app.json`.
- [ ] Large lists standardize on `@shopify/flash-list` with calibrated `estimatedItemSize`.
- [ ] Animations run exclusively on the UI thread via `react-native-reanimated` worklets.
- [ ] Offline key-value data is stored in encrypted MMKV rather than legacy `AsyncStorage`.
- [ ] OTA updates via `eas-cli` are tied to strict semantic runtime versions (`runtimeVersion: { policy: "appVersion" }`).
- [ ] Secure hardware credentials use `expo-secure-store` backed by Keychain (iOS) and KeyStore (Android).
