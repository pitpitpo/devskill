# 🐧 Linux Kernel Modules, Device Drivers & Systems Programming (`sections/systems-kernel/linux-kernel-driver.md`)

> **Classification**: Kernel Architecture, Low-Level Driver Development, Concurrency & eBPF  
> **Target Systems**: Linux Kernel 6.1 / 6.6 / 6.12+ LTS, Embedded Linux (Yocto/Buildroot), Android GKI  
> **Prerequisites**: C (C11 / C23), Assembly basics (x86_64 / AArch64), Make / Kbuild, QEMU, GDB  
> **Governing Rules**: **R-001** (Zero TODOs), **R-038** (Zero Magic Values), **R-039** (Immutability where applicable), **R-188** (Thread/Interrupt Lifecycle)  
> **Last Updated**: 2026-11-17  

---

## 1. Frontmatter & Metadata

| Attribute | Specification |
|---|---|
| **Kernel Versions** | Linux 6.1 LTS, Linux 6.6 LTS, Linux 6.12 LTS |
| **Architectures** | x86_64, ARM64 (AArch64), RISC-V |
| **Driver Frameworks** | Character Devices (`cdev`), Platform Drivers (`platform_driver`), Device Tree (`of_match_table`) |
| **Synchronization** | Spinlocks (`spinlock_t`), Mutexes (`mutex`), Read-Copy-Update (RCU), Seqlocks |
| **Tracing & Observability** | eBPF (BCC, bpftrace, libbpf / CO-RE), Ftrace, Tracepoints, Kprobes |

---

## 2. Core Philosophy / Golden Rule

> **Never Sleep in an Atomic Context; Validate Every User-Space Pointer with `copy_from_user()`, and Protect Shared Data with Lock Ordering to Prevent Deadlocks.**
> 
> *Kernel space operates without memory safety nets. An invalid memory access in user space triggers a harmless SIGSEGV; in kernel space, it triggers a catastrophic Kernel Panic. Any driver that blocks while holding a spinlock halts the CPU core and deadlocks the OS. Every resource allocated in kernel space must be freed along explicit error rollback paths (Goto Cleanup pattern).*

---

## 3. Architecture & Design Patterns

```
                               LINUX KERNEL SUBSYSTEM ARCHITECTURE
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              USER SPACE (Ring 3 - Unprivileged)                        │
│               Applications, System Daemons, POSIX APIs (`read`, `write`, `ioctl`)      │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │ System Call Interface (`syscall` instruction)
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              KERNEL SPACE (Ring 0 - Privileged)                        │
│  ┌───────────────────────┐  ┌───────────────────────┐  ┌────────────────────────────┐  │
│  │ Virtual File System   │  │ Character Device Core │  │ Memory Management Subsystem│  │
│  │ (VFS - `inode`, `file`)│ │ (`cdev`, `fops`)      │  │ SLUB, Page Alloc, vmalloc  │  │
│  └───────────────────────┘  └───────────┬───────────┘  └────────────────────────────┘  │
│                                         │                                              │
│  ┌──────────────────────────────────────┴───────────────────────────────────────────┐  │
│  │                         Hardware Driver Subsystem                                │  │
│  │  • Platform Driver (`probe`, `remove`) & Device Tree Matching (`of_device_id`)    │  │
│  │  • Top-Half Interrupt Handler (Hard IRQ - Fast, Non-Blocking)                    │  │
│  │  • Bottom-Half Processing (Threaded IRQ, Workqueues, Tasklets)                   │  │
│  └──────────────────────────────────────┬───────────────────────────────────────────┘  │
└─────────────────────────────────────────┼──────────────────────────────────────────────┘
                                          │ Memory-Mapped I/O (`readl`, `writel`, DMA)
                                          ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                 PHYSICAL HARDWARE                                      │
│                PCIe Peripherals, SoC Registers, I2C, SPI, Interrupt Lines               │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Concrete Code Examples

### 4.1 Production Character Device Driver with Mutex Locking & sysfs Export

```c
/**
 * @file custom_sensor_driver.c
 * @brief Production Linux 6.6+ Character & Platform Device Driver.
 * Demonstrates: Platform Driver registration, Device Tree matching, Character Device (cdev),
 * Mutex Concurrency, copy_to_user, and sysfs attribute creation.
 */

#include <linux/init.h>
#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/fs.h>
#include <linux/cdev.h>
#include <linux/device.h>
#include <linux/slab.h>
#include <linux/uaccess.h>
#include <linux/mutex.h>
#include <linux/platform_device.h>
#include <linux/of.h>

#define DRIVER_NAME "custom_sensor"
#define CLASS_NAME "sensor_class"
#define BUFFER_SIZE 256

MODULE_LICENSE("GPL");
MODULE_AUTHOR("DevSkill Core Systems Team");
MODULE_DESCRIPTION("Enterprise Production Character Device Driver for Linux 6.6+");
MODULE_VERSION("1.0.0");

struct sensor_dev {
    dev_t dev_num;
    struct cdev cdev;
    struct class *sensor_class;
    struct device *sensor_device;
    struct mutex lock;
    char buffer[BUFFER_SIZE];
    size_t data_len;
};

static struct sensor_dev g_sensor_dev;

/* File Operations: Open */
static int sensor_open(struct inode *inodep, struct file *filep)
{
    pr_info(DRIVER_NAME ": Device opened by PID %d\n", current->pid);
    filep->private_data = &g_sensor_dev;
    return 0;
}

/* File Operations: Release / Close */
static int sensor_release(struct inode *inodep, struct file *filep)
{
    pr_info(DRIVER_NAME ": Device successfully closed\n");
    return 0;
}

/* File Operations: Read with copy_to_user */
static ssize_t sensor_read(struct file *filep, char __user *user_buffer, size_t count, loff_t *offset)
{
    struct sensor_dev *dev = (struct sensor_dev *)filep->private_data;
    ssize_t bytes_to_read;
    ssize_t uncopied;

    if (!user_buffer)
        return -EINVAL;

    if (mutex_lock_interruptible(&dev->lock))
        return -ERESTARTSYS;

    if (*offset >= dev->data_len) {
        mutex_unlock(&dev->lock);
        return 0; /* EOF */
    }

    bytes_to_read = min(count, (size_t)(dev->data_len - *offset));

    uncopied = copy_to_user(user_buffer, dev->buffer + *offset, bytes_to_read);
    if (uncopied != 0) {
        pr_warn(DRIVER_NAME ": Failed to copy %zu bytes to user space\n", uncopied);
        mutex_unlock(&dev->lock);
        return -EFAULT;
    }

    *offset += bytes_to_read;
    mutex_unlock(&dev->lock);

    return bytes_to_read;
}

/* File Operations: Write with copy_from_user */
static ssize_t sensor_write(struct file *filep, const char __user *user_buffer, size_t count, loff_t *offset)
{
    struct sensor_dev *dev = (struct sensor_dev *)filep->private_data;
    size_t bytes_to_write;
    ssize_t uncopied;

    if (!user_buffer || count == 0)
        return -EINVAL;

    if (mutex_lock_interruptible(&dev->lock))
        return -ERESTARTSYS;

    bytes_to_write = min(count, (size_t)(BUFFER_SIZE - 1));

    uncopied = copy_from_user(dev->buffer, user_buffer, bytes_to_write);
    if (uncopied != 0) {
        pr_warn(DRIVER_NAME ": Failed to copy %zu bytes from user space\n", uncopied);
        mutex_unlock(&dev->lock);
        return -EFAULT;
    }

    dev->buffer[bytes_to_write] = '\0';
    dev->data_len = bytes_to_write;
    *offset += bytes_to_write;

    mutex_unlock(&dev->lock);
    return bytes_to_write;
}

static const struct file_operations sensor_fops = {
    .owner   = THIS_MODULE,
    .open    = sensor_open,
    .release = sensor_release,
    .read    = sensor_read,
    .write   = sensor_write,
};

/* Platform Driver Probe */
static int sensor_probe(struct platform_device *pdev)
{
    int ret;
    struct device *dev = &pdev->dev;

    pr_info(DRIVER_NAME ": Probing hardware platform device\n");

    mutex_init(&g_sensor_dev.lock);
    g_sensor_dev.data_len = 0;

    /* 1. Allocate dynamic major/minor number */
    ret = alloc_chrdev_region(&g_sensor_dev.dev_num, 0, 1, DRIVER_NAME);
    if (ret < 0) {
        pr_err(DRIVER_NAME ": Failed to allocate character device region\n");
        return ret;
    }

    /* 2. Initialize and add character device */
    cdev_init(&g_sensor_dev.cdev, &sensor_fops);
    g_sensor_dev.cdev.owner = THIS_MODULE;

    ret = cdev_add(&g_sensor_dev.cdev, g_sensor_dev.dev_num, 1);
    if (ret < 0) {
        pr_err(DRIVER_NAME ": Failed to add cdev\n");
        goto unregister_chrdev;
    }

    /* 3. Create sysfs class */
    g_sensor_dev.sensor_class = class_create(CLASS_NAME);
    if (IS_ERR(g_sensor_dev.sensor_class)) {
        ret = PTR_ERR(g_sensor_dev.sensor_class);
        goto delete_cdev;
    }

    /* 4. Create /dev/custom_sensor device node */
    g_sensor_dev.sensor_device = device_create(
        g_sensor_dev.sensor_class, dev, g_sensor_dev.dev_num, NULL, DRIVER_NAME
    );
    if (IS_ERR(g_sensor_dev.sensor_device)) {
        ret = PTR_ERR(g_sensor_dev.sensor_device);
        goto destroy_class;
    }

    pr_info(DRIVER_NAME ": Driver initialized successfully. Major: %d, Minor: %d\n",
            MAJOR(g_sensor_dev.dev_num), MINOR(g_sensor_dev.dev_num));
    return 0;

destroy_class:
    class_destroy(g_sensor_dev.sensor_class);
delete_cdev:
    cdev_del(&g_sensor_dev.cdev);
unregister_chrdev:
    unregister_chrdev_region(g_sensor_dev.dev_num, 1);
    return ret;
}

/* Platform Driver Remove */
static int sensor_remove(struct platform_device *pdev)
{
    pr_info(DRIVER_NAME ": Removing hardware driver\n");
    device_destroy(g_sensor_dev.sensor_class, g_sensor_dev.dev_num);
    class_destroy(g_sensor_dev.sensor_class);
    cdev_del(&g_sensor_dev.cdev);
    unregister_chrdev_region(g_sensor_dev.dev_num, 1);
    mutex_destroy(&g_sensor_dev.lock);
    return 0;
}

/* Device Tree Compatible ID Table */
static const struct of_device_id sensor_dt_ids[] = {
    { .compatible = "devskill,custom-sensor-v1", },
    { /* Sentinel */ }
};
MODULE_DEVICE_TABLE(of, sensor_dt_ids);

static struct platform_driver sensor_platform_driver = {
    .probe  = sensor_probe,
    .remove = sensor_remove,
    .driver = {
        .name           = DRIVER_NAME,
        .of_match_table = sensor_dt_ids,
        .owner          = THIS_MODULE,
    },
};

module_platform_driver(sensor_platform_driver);
```

---

### 4.2 Modern eBPF Kernel Tracepoint Observer (CO-RE with libbpf)

```c
/**
 * @file execve_monitor.bpf.c
 * @brief Modern CO-RE (Compile Once - Run Everywhere) eBPF Tracepoint Program.
 * Captures process executions at the kernel sys_enter_execve tracepoint.
 */

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>
#include <bpf/bpf_core_read.h>

char LICENSE[] SEC("license") = "Dual BSD/GPL";

struct event {
    u32 pid;
    u32 uid;
    char comm[16];
    char filename[256];
};

struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, 256 * 1024); /* 256 KB buffer */
} events SEC(".maps");

SEC("tracepoint/syscalls/sys_enter_execve")
int trace_sys_enter_execve(struct trace_event_raw_sys_enter *ctx)
{
    struct event *e;
    const char *filename_ptr;

    e = bpf_ringbuf_reserve(&events, sizeof(*e), 0);
    if (!e)
        return 0;

    e->pid = bpf_get_current_pid_tgid() >> 32;
    e->uid = bpf_get_current_uid_gid();
    bpf_get_current_comm(&e->comm, sizeof(e->comm));

    /* Extract filename from first syscall argument */
    filename_ptr = (const char *)ctx->args[0];
    bpf_probe_read_user_str(&e->filename, sizeof(e->filename), filename_ptr);

    bpf_ringbuf_submit(e, 0);
    return 0;
}
```

---

## 5. Security & Performance Considerations

### 5.1 Race Conditions & Spinlock vs Mutex Discipline
- **Mutexes**: May sleep. Use when protecting resources accessed by user threads via system calls (`open`, `read`, `write`, `ioctl`).
- **Spinlocks**: Never sleep. Mandatory when synchronizing data between an interrupt service routine (ISR) and process context.
  ```c
  unsigned long flags;
  spin_lock_irqsave(&dev->lock, flags);
  /* Atomic critical section - zero memory allocations or blocking I/O */
  spin_unlock_irqrestore(&dev->lock, flags);
  ```

### 5.2 User-Space Pointer Validation
Directly dereferencing a user-space pointer in Ring 0 allows an unprivileged application to execute memory-poisoning attacks:
- **Rule**: Never access user memory directly (`*user_ptr`). Always copy through `copy_from_user()` and `copy_to_user()`.
- Check uncopied byte counts and return `-EFAULT` immediately on failure.

---

## 6. Common Pitfalls & Anti-Patterns

### Anti-Pattern 1: Allocating Memory with `GFP_KERNEL` in Interrupt Context
- **Violation**: Calling `kmalloc(size, GFP_KERNEL)` inside an IRQ handler or while holding a spinlock.
- **Consequence**: `GFP_KERNEL` may sleep to swap out pages when memory is low. Sleeping in atomic context triggers a severe kernel bug trace and crashes the machine.
- **Remediation**: Use `GFP_ATOMIC` in interrupt handlers or atomic contexts.

### Anti-Pattern 2: Missing Error Unwind ("Goto Cleanup")
- **Violation**: Returning directly on failure without unregistering earlier allocated resources (`alloc_chrdev_region`, `cdev_add`).
- **Consequence**: Kernel memory leak and dangling device nodes that crash the system when the module is removed.
- **Remediation**: Implement structured cascading labels:
  ```c
  if (ret) goto destroy_class;
  /* ... */
  destroy_class:
      class_destroy(dev->class);
  delete_cdev:
      cdev_del(&dev->cdev);
  ```

---

## 7. Verification Checklist

| Criterion | Target Metric | Verification Command / Check |
|---|---|---|
| **1. Kbuild Compilation** | 0 warnings with `-Wall -Werror` | `make -C /lib/modules/$(uname -r)/build M=$PWD modules` exits code 0 |
| **2. Dynamic Allocation** | Major number allocated dynamically | Check `cat /proc/devices | grep custom_sensor` |
| **3. Memory Leak Check** | Zero leaks across load/unload | `insmod custom_sensor.ko && rmmod custom_sensor && dmesg | tail -n 20` |
| **4. Concurrency Test** | No deadlocks under parallel access | Run multi-threaded stress test `dd if=/dev/custom_sensor of=/dev/null bs=128 count=1000 &` |
| **5. eBPF Ring Buffer** | Zero dropped events | Inspect ringbuffer statistics via `bpftool map dump name events` |

---

*See also*: [`../../frameworks/mobile/android-aosp.md`](../../frameworks/mobile/android-aosp.md) for AOSP driver bindings, and [`../../languages/c-cpp.md`](../../languages/c-cpp.md) for modern C23 and C++23 standards.
