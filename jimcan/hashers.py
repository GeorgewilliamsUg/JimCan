"""
Custom Password Hashers for Jimcan Operations Dashboard.
Implements Phase 2 Task 1: Custom Argon2 subclass tailored for shared hosting environments.
"""

from django.contrib.auth.hashers import Argon2PasswordHasher


class JimcanArgon2PasswordHasher(Argon2PasswordHasher):
    """
    Argon2id password hasher with parameters optimized for shared hosting constraints:
    - memory_cost: 19456 (approx 19 MB, well within 1GB cPanel memory limits)
    - time_cost: 2 iterations
    - parallelism: 1 thread
    """
    memory_cost = 19456
    time_cost = 2
    parallelism = 1
