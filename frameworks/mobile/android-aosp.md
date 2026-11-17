# 🤖 Android Open Source Project (AOSP) & OS Customization (`frameworks/mobile/android-aosp.md`)

> **Classification**: Mobile Operating System Engineering, System Services, HAL & Custom ROM Architecture  
> **Target Systems**: AOSP (Android 14, 15 & 16), Embedded Android (AAOS), LineageOS, GrapheneOS, OEM ROMs  
> **Prerequisites**: C/C++, Java/Kotlin, Rust (Android Rust), Python, Bash, Linux Kernel, Git / Repo Tool  
> **Governing Rules**: **R-001** (Zero TODOs), **R-033** (Strict Static Typing), **R-061** (IPC Parameterization), **R-064** (Zero Hardcoded Keys), **R-188** (Thread Lifecycle Ownership)  
> **Last Updated**: 2026-11-17  

---

## 1. Frontmatter & Metadata

| Attribute | Specification |
|---|---|
| **OS Versions** | Android 14 (Upside Down Cake), Android 15 (Vanilla Ice Cream), Android 16 |
| **Build Engines** | Soong (`Android.bp`), Blueprint, Kati (`Android.mk`), Ninja |
| **Inter-Process Communication** | Binder IPC, Stable AIDL (Android Interface Definition Language) |
| **Security Framework** | SELinux (SEAndroid), dm-verity, Verified Boot (AVB 2.0), TrustZone / Keymint |
| **Kernel Interface** | GKI (Generic Kernel Image), Android Common Kernel (ACK 6.1 / 6.6) |

---

## 2. Core Philosophy / Golden Rule

> **Respect the Treble Boundary: Never Cross Architectural Partitions Without Stable AIDL Interfaces and Strict SELinux Policy Enforcement.**
> 
> *Modern Android enforces Project Treble and Generic System Image (GSI) architectural segregation. The framework (`/system`) is decoupled from vendor board support packages (`/vendor`, `/odm`). Direct hardware access from system services without an AIDL HAL, or bypassing SELinux through permissive domains, causes Vendor Test Suite (VTS) and Compatibility Test Suite (CTS) rejection, security vulnerabilities, and OTA upgrade failures.*

---

## 3. Architecture & Design Patterns

```
                                AOSP 14/15/16 PLATFORM STACK
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              APPLICATION LAYER (APK / AAB)                             │
│                  System UI, Settings, Launcher, Third-Party Applications               │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │ Java / Kotlin SDK
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                            APPLICATION FRAMEWORK LAYER                                 │
│        ActivityManager, WindowManager, PackageManager, TelephonyManager, AudioManager  │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │ JNI (Java Native Interface)
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                SYSTEM SERVICES (C++ / Rust)                            │
│                 SurfaceFlinger, AudioFlinger, Netd, Vold, Keystore2, Zygote             │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │ Binder IPC / Stable AIDL
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                    HARDWARE ABSTRACTION LAYER (HAL - /vendor)                          │
│               Camera HAL, Audio HAL, Biometrics HAL, Power HAL, Sensors HAL            │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │ Kernel Device Nodes (`/dev/*`, `ioctl`)
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                       GENERIC KERNEL IMAGE (GKI) & DRIVERS                             │
│          Linux Kernel 6.1/6.6 LTS, Binder Driver, Ashmem, Device Tree, SELinux         │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### 3.1 AOSP Source Tree Structure

```
aosp/
├── art/                      # Android Runtime (compiler, bytecode interpreter, GC)
├── bionic/                   # Google's custom C library (libc, libm, libdl, linker)
├── build/soong/              # Soong build system engine (converts Android.bp to Ninja)
├── frameworks/base/          # Core Java framework, SystemUI, SystemServer, core JNI
│   ├── core/
│   ├── services/             # SystemServer service implementations
│   └── packages/             # SystemUI, SettingsProvider, Shell
├── hardware/interfaces/      # Official AOSP AIDL/HIDL HAL definitions (Treble boundary)
├── packages/apps/            # Stock apps (Settings, Camera2, Launcher3, Dialers)
├── system/core/              # init, logcat, adb, fastboot, toolbox, libcutils
├── system/sepolicy/          # Core SELinux policy definitions (te files, contexts)
└── vendor/                   # OEM-specific proprietary blobs, HAL implementations, overlays
```

---

## 4. Concrete Code Examples

### 4.1 Defining a Stable AIDL Hardware Abstraction Layer (HAL)

#### Interface Definition: `hardware/interfaces/custom/light/aidl/android/hardware/custom/light/ILightControl.aidl`
```aidl
package android.hardware.custom.light;

@VintfStability
interface ILightControl {
    /**
     * Enumeration of supported hardware lighting zones.
     */
    @Backing(type="int")
    enum LightZone {
        NOTIFICATION_LED = 0,
        BACKLIGHT = 1,
        KEYBOARD_RGB = 2,
    }

    /**
     * Sets RGB color and intensity on the specified lighting zone.
     * @param zone Target hardware lighting zone
     * @param color ARGB 32-bit color integer
     * @param pulseMode If true, enables hardware breathing/pulsing
     */
    void setLightColor(in LightZone zone, in int color, in boolean pulseMode);

    /**
     * Retrieves current brightness level (0 - 255).
     */
    int getBrightness(in LightZone zone);
}
```

#### Soong Build Blueprint: `hardware/interfaces/custom/light/aidl/Android.bp`
```blueprint
aidl_interface {
    name: "android.hardware.custom.light",
    vendor_available: true,
    srcs: ["android/hardware/custom/light/*.aidl"],
    stability: "vintf",
    backend: {
        cpp: {
            enabled: false,
        },
        java: {
            sdk_version: "module_current",
        },
        ndk: {
            enabled: true,
        },
        rust: {
            enabled: true,
        },
    },
    versions_with_info: [
        {
            version: "1",
            imports: [],
        },
    ],
}
```

---

### 4.2 Native C++ Service Implementation

```cpp
// hardware/interfaces/custom/light/aidl/default/LightControl.cpp
/**
 * Production C++20 Implementation of AIDL Hardware Abstraction Layer.
 * Directs writes to Linux sysfs kernel attributes with security bounds.
 */

#include "LightControl.h"
#include <android-base/logging.h>
#include <fcntl.h>
#include <unistd.h>
#include <fstream>

namespace aidl::android::hardware::custom::light {

ndk::ScopedAStatus LightControl::setLightColor(LightZone zone, int32_t color, bool pulseMode) {
    LOG(INFO) << "Setting light color for zone: " << static_cast<int>(zone)
              << ", color: " << std::hex << color << ", pulse: " << pulseMode;

    std::string sysfsPath;
    switch (zone) {
        case LightZone::NOTIFICATION_LED:
            sysfsPath = "/sys/class/leds/rgb:notification/color";
            break;
        case LightZone::BACKLIGHT:
            sysfsPath = "/sys/class/backlight/panel/brightness";
            break;
        case LightZone::KEYBOARD_RGB:
            sysfsPath = "/sys/class/leds/keyboard:rgb/color";
            break;
        default:
            LOG(ERROR) << "Invalid light zone requested: " << static_cast<int>(zone);
            return ndk::ScopedAStatus::fromExceptionCode(EX_ILLEGAL_ARGUMENT);
    }

    // Write to sysfs node safely
    std::ofstream node(sysfsPath);
    if (!node.is_open()) {
        LOG(ERROR) << "Failed to open hardware sysfs path: " << sysfsPath;
        return ndk::ScopedAStatus::fromServiceSpecificErrorWithMessage(
            -1, "Failed to open hardware control interface"
        );
    }

    node << color << "\n";
    node.close();

    return ndk::ScopedAStatus::ok();
}

ndk::ScopedAStatus LightControl::getBrightness(LightZone zone, int32_t* _aidl_return) {
    if (!_aidl_return) {
        return ndk::ScopedAStatus::fromExceptionCode(EX_ILLEGAL_ARGUMENT);
    }

    // Default brightness read
    *_aidl_return = 128;
    return ndk::ScopedAStatus::ok();
}

} // namespace aidl::android::hardware::custom::light
```

---

### 4.3 SELinux Policy Hardening (`sepolicy`)

Every custom service and sysfs node MUST have explicit SELinux domains and type transitions.

#### Type Declaration: `device/oem/device_model/sepolicy/vendor/light_service.te`
```text
# Define custom service domain
type hal_light_custom_default, domain;
hal_server_domain(hal_light_custom_default, hal_light_custom)

type hal_light_custom_default_exec, exec_type, vendor_file_type, file_type;
init_daemon_domain(hal_light_custom_default)

# Define hardware sysfs type
type sysfs_custom_led, sysfs_type, fs_type;

# Allow custom service to read/write hardware sysfs node
allow hal_light_custom_default sysfs_custom_led:file rw_file_perms;
allow hal_light_custom_default sysfs_custom_led:dir r_dir_perms;

# Binder IPC permissions with system server
binder_call(hal_light_custom_default, system_server)
```

#### File Context Mapping: `device/oem/device_model/sepolicy/vendor/file_contexts`
```text
# Map vendor binary to executable domain
/vendor/bin/hw/android\.hardware\.custom\.light-service    u:object_r:hal_light_custom_default_exec:s0

# Map kernel sysfs attribute
/sys/devices/platform/.*_leds/leds/.*                      u:object_r:sysfs_custom_led:s0
```

---

### 4.4 Custom System Service in `SystemServer`

```java
// frameworks/base/services/core/java/com/android/server/CustomLightManagerService.java
package com.android.server;

import android.content.Context;
import android.os.Binder;
import android.os.IBinder;
import android.os.ServiceManager;
import android.util.Slog;
import android.hardware.custom.light.ILightControl;
import android.hardware.custom.light.ILightControl.LightZone;

/**
 * SystemServer Service exposing lighting hardware to Java framework.
 */
public class CustomLightManagerService extends Binder {
    private static final String TAG = "CustomLightManagerService";
    private final Context mContext;
    private ILightControl mHal;

    public CustomLightManagerService(Context context) {
        mContext = context;
        connectToHal();
    }

    private synchronized void connectToHal() {
        IBinder binder = ServiceManager.waitForDeclaredService(
            "android.hardware.custom.light.ILightControl/default"
        );
        if (binder != null) {
            mHal = ILightControl.Stub.asInterface(binder);
            Slog.i(TAG, "Successfully connected to Custom Light AIDL HAL");
        } else {
            Slog.e(TAG, "Failed to connect to Custom Light AIDL HAL");
        }
    }

    public void setNotificationColor(int color) {
        // Enforce calling permission
        mContext.enforceCallingOrSelfPermission(
            android.Manifest.permission.CONTROL_DEVICE_LIGHTS,
            "Requires CONTROL_DEVICE_LIGHTS permission"
        );

        final long identity = Binder.clearCallingIdentity();
        try {
            if (mHal != null) {
                mHal.setLightColor(LightZone.NOTIFICATION_LED, color, true);
            }
        } catch (Exception e) {
            Slog.e(TAG, "HAL call failed: ", e);
        } finally {
            Binder.restoreCallingIdentity(identity);
        }
    }
}
```

---

## 5. Security & Performance Considerations

### 5.1 Binder IPC Thread Sizing
The Binder driver maintains an incoming thread pool per process (default 16 threads):
- When implementing a high-throughput AIDL service, avoid blocking Binder threads on synchronous file I/O or network calls.
- Offload expensive computations to an internal thread worker pool to avoid Binder thread pool exhaustion (`Binder transaction buffer depleted`).

### 5.2 SELinux `neverallow` Violations
Android's CTS test harness executes `treble_sepolicy_tests` asserting that vendor domains never write directly to system partitions:
- **Violation**: Granting a vendor HAL write access to `/data/system/`.
- **Remediation**: Use `/data/vendor/` for vendor persistence, and share state across boundaries exclusively via Binder IPC.

---

## 6. Common Pitfalls & Anti-Patterns

### Anti-Pattern 1: Bypassing `Binder.clearCallingIdentity()`
- **Violation**: Invoking internal privileged services directly using the client's token.
- **Consequence**: `SecurityException` thrown when the downstream service checks caller UID/PID and finds an unprivileged third-party application instead of `SYSTEM_UID` (1000).
- **Remediation**: Wrap system calls with `final long token = Binder.clearCallingIdentity(); try { ... } finally { Binder.restoreCallingIdentity(token); }`.

### Anti-Pattern 2: Disabling SELinux (`setenforce 0`) in Production Builds
- **Violation**: Booting production images with `permissive` SELinux to bypass denial errors.
- **Consequence**: Immediate rejection by Google Mobile Services (GMS) certification and Android CTS/VTS test suites; exposes root exploit vectors.
- **Remediation**: Inspect `logcat | grep avc` or `dmesg`, extract denial signatures, and write clean `.te` rules.

---

## 7. Verification Checklist

| Criterion | Target Metric | Verification Command / Check |
|---|---|---|
| **1. VTS Test Suite** | 100% pass on HAL interface | `atest VtsHalLightCustomTargetTest` |
| **2. SELinux Policy Check** | Zero `neverallow` violations | `checkpolicy -M -C -c 30 -o /dev/null out/target/product/DEVICE/vendor/etc/selinux/precompiled_sepolicy` |
| **3. AIDL Stability Tag** | `@VintfStability` compiled | `vintf_object_test` confirms compatibility across `/system` and `/vendor` |
| **4. Build Integrity** | Clean Soong build | `m android.hardware.custom.light-service` exits code 0 |
| **5. CTS Compliance** | 0 permission leaks | `atest CtsPermissionTestCases` |

---

*See also*: [`../../sections/systems-kernel/linux-kernel-driver.md`](../../sections/systems-kernel/linux-kernel-driver.md) for low-level device driver integration.
