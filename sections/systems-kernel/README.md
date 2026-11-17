# 🐧 Linux Kernel, Systems Programming & Low-Level Drivers (`sections/systems-kernel/`)

> **Classification**: Low-Level Systems Architecture, Operating System Internals & Device Drivers  
> **Target Systems**: Linux Kernel 6.1 / 6.6 / 6.12 LTS, Embedded Linux, Android GKI, eBPF Subsystems  
> **Applicability Scope**: Device Drivers, Kernel Modules, Memory Subsystems, Real-Time Systems, Hardware Interfacing  

---

## 1. Directory Overview

Systems engineering at the kernel and device boundary demands mastery over hardware abstraction, hardware interrupt arbitration, memory-mapped I/O, and non-blocking synchronization.

```
sections/systems-kernel/
├── README.md                 # Directory overview and core low-level invariants
└── linux-kernel-driver.md     # Linux Kernel Modules, Character/Platform Drivers, Device Tree, eBPF & Locking
```

---

## 2. Universal Kernel-Space Invariants

1. **Ring 0 Memory Safety**:
   A single NULL-pointer dereference, buffer overflow, or use-after-free in kernel space crashes the entire host (`Kernel Panic` / OOPS). Defensive boundary checks and pointer validation are paramount.
2. **Never Sleep in Atomic Context**:
   Code executing within interrupt handlers, tasklets, timer callbacks, or while holding a spinlock (`spin_lock`) MUST NEVER sleep, block, or allocate memory with `GFP_KERNEL`. Always use `GFP_ATOMIC`.
3. **Hardware Synchronization & Memory Barriers**:
   Multi-core Symmetric Multiprocessing (SMP) and out-of-order execution necessitate explicit memory barriers (`smp_mb()`, `smp_rmb()`, `smp_wmb()`) or atomic primitives (`atomic_t`, RCU).
4. **User-Kernel Boundary Isolation**:
   Kernel code MUST NEVER directly dereference a user-space pointer. Memory transfers must use `copy_to_user()` and `copy_from_user()` to validate page permissions and prevent privilege escalation (Spectre/Meltdown mitigation).
