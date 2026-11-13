# 📱 React Native & Expo Production Guide (`react-native-expo.md`)

> **Framework**: React Native with Expo (SDK 50+)  
> **Classification**: Cross-Platform Mobile Architecture (iOS & Android)  
> **Core Philosophy**: "Native Performance via Hermès, Universal Routing via Expo Router, Secure Local Storage."

---

## 1. Expo Router & Navigation Structure

Organize navigation using directory-based routing:

```
app/
├── (auth)/
│   ├── login.tsx
│   └── register.tsx
├── (tabs)/
│   ├── _layout.tsx       # Bottom tabs navigator
│   ├── index.tsx         # Home tab
│   └── profile.tsx       # Profile tab
├── _layout.tsx           # Root stack, Theme provider, Auth guard
└── modal.tsx             # Universal modal presentation
```

---

## 2. Secure Storage vs Standard Storage

Never store sensitive tokens in standard `AsyncStorage`:

| Storage Solution | Data Type | Security Level |
|---|---|---|
| **Expo SecureStore** | JWT tokens, refresh tokens, biometric keys, user credentials | Hardware Keychain (iOS) / KeyStore (Android) |
| **AsyncStorage / MMKV** | Theme preferences, non-sensitive cached lists, UI state | Unencrypted plaintext on device storage |

```typescript
import * as SecureStore from 'expo-secure-store';

export async function saveAuthToken(token: string): Promise<void> {
  await SecureStore.setItemAsync('auth_token', token, {
    keychainAccessible: SecureStore.AFTER_FIRST_UNLOCK,
  });
}

export async function getAuthToken(): Promise<string | null> {
  return await SecureStore.getItemAsync('auth_token');
}
```

---

## 3. Hermès Engine & Performance Checklist

1. **Enable Hermès**: Ensure `"jsEngine": "hermes"` is active in `app.json` for fast bytecode compilation and low memory consumption.
2. **FlashList over FlatList**: Replace standard React Native `FlatList` with `@shopify/flash-list` for smooth 60fps scrolling on long lists.
3. **Safe Area Insets**: Always wrap screens with `react-native-safe-area-context` to avoid notch and navigation bar overlap.
