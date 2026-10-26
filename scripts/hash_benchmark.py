#!/usr/bin/env python3
"""
Password Hasher Benchmark Script (Phase 2, Task 1)
Measures execution time (ms) and peak memory (KB / MB) for:
1. Django Default PBKDF2 (PBKDF2PasswordHasher)
2. Django Default Argon2 (Argon2PasswordHasher)
3. Custom Tuned Argon2 (JimcanArgon2PasswordHasher: memory_cost=19456, time_cost=2, parallelism=1)
"""

import os
import sys
import time
import tracemalloc
from pathlib import Path

# Setup Django environment
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jimcan.settings')

import django
django.setup()

from django.contrib.auth.hashers import PBKDF2PasswordHasher, Argon2PasswordHasher

class JimcanArgon2PasswordHasher(Argon2PasswordHasher):
    """
    Tuned Argon2 hasher designed for shared hosting environments.
    Standard Django Argon2 uses 100MB+ which risks shared host OOM limits.
    Tuned parameters: memory_cost=19456 (19 MB), time_cost=2, parallelism=1.
    """
    memory_cost = 19456
    time_cost = 2
    parallelism = 1

def benchmark_hasher(hasher_cls, sample_password="StandardTestPassword123!Safe"):
    hasher = hasher_cls()
    salt = hasher.salt()
    
    # Warmup
    hasher.encode(sample_password, salt)
    
    # Measure
    tracemalloc.start()
    tracemalloc.reset_peak()
    
    start_time = time.perf_counter()
    encoded = hasher.encode(sample_password, salt)
    elapsed_ms = (time.perf_counter() - start_time) * 1000.0
    
    current_mem, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    return {
        "name": hasher_cls.__name__,
        "time_ms": elapsed_ms,
        "peak_kb": peak_mem / 1024.0,
        "peak_mb": peak_mem / (1024.0 * 1024.0),
        "encoded_sample": encoded[:35] + "..."
    }

def run_benchmarks():
    print("=" * 70)
    print(" Jimcan Password Hasher Benchmark")
    print("=" * 70)
    
    candidates = [
        PBKDF2PasswordHasher,
        Argon2PasswordHasher,
        JimcanArgon2PasswordHasher
    ]
    
    results = []
    for cand in candidates:
        res = benchmark_hasher(cand)
        results.append(res)
        print(f"[*] {res['name']:<28} | Time: {res['time_ms']:>8.2f} ms | Peak Mem: {res['peak_kb']:>8.2f} KB ({res['peak_mb']:>5.2f} MB)")
    
    print("-" * 70)
    tuned = next(r for r in results if r["name"] == "JimcanArgon2PasswordHasher")
    if 150 <= tuned["time_ms"] <= 600:
        print(f"[RECOMMENDATION] JimcanArgon2PasswordHasher meets the 150-600ms target ({tuned['time_ms']:.1f} ms) with {tuned['peak_mb']:.2f} MB memory.")
    else:
        print(f"[INFO] JimcanArgon2PasswordHasher measured {tuned['time_ms']:.1f} ms on this machine.")
    print("=" * 70)
    return results

if __name__ == "__main__":
    run_benchmarks()
