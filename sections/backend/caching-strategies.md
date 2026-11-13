# ⚡ Caching Strategies & Redis Mastery (`caching-strategies.md`)

> **Classification**: High-Throughput Performance Architecture  
> **Core Tool**: Redis / Valkey  
> **Core Philosophy**: "Treat Cache as Ephemeral; Always Have a Deterministic Fallback to Source of Truth."

---

## 1. The Core Caching Patterns

```
1. CACHE-ASIDE (LAZY LOADING) - Default for read-heavy workloads
   App ──► Read Cache ──(Miss)──► Read DB ──► Populate Cache ──► Return

2. WRITE-THROUGH - Ensures cache is always fresh on write
   App ──► Write to Cache ──(Synchronous)──► Write to DB ──► Return

3. WRITE-BEHIND (WRITE-BACK) - High write throughput (IoT, analytics)
   App ──► Write to Cache ──► Return immediately ──(Async Queue)──► Batch write to DB
```

---

## 2. Preventing Cache Stampede (Dog-Piling)

When a hot cache key expires, thousands of concurrent requests can hammer the database simultaneously.

### Strategy: Probabilistic Early Expiration (XFetch Algorithm)
Recompute and re-cache the value *before* it officially expires based on read frequency and computation time:

```python
import math
import random
import time

def should_recompute(delta_time: float, beta: float, ttl_remaining: float) -> bool:
    """
    delta_time: time in seconds it takes to compute the value
    beta: aggressiveness factor (usually 1.0)
    ttl_remaining: remaining TTL in seconds
    """
    if ttl_remaining <= 0:
        return True
    return -(delta_time * beta * math.log(random.random())) >= ttl_remaining
```

---

## 3. Redis Key Namespacing & TTL Standards

All keys must adhere to strict hierarchical namespacing:
```
<service>:<environment>:<tenant_id>:<entity>:<entity_id>
Example: orders:prod:tenant_912:order:89472
```

### Mandatory Rules
1. **Never set a key without a TTL**: Unbounded keys cause out-of-memory crashes (`OOM`).
2. **Add Jitter to TTLs**: Avoid mass simultaneous expiration by randomizing expiration:
   ```python
   base_ttl = 3600  # 1 hour
   jitter = random.randint(-300, 300) # +/- 5 minutes
   redis.set(key, value, ex=base_ttl + jitter)
   ```
3. **Use Redis Hashes for Objects**: Avoid serializing large JSON blobs into single string keys when only specific fields are updated.
