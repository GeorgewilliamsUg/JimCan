# Local Development Security Setup
**Jimcan Operations Dashboard**

This guide describes how to configure environment variables for local development without hardcoding secrets in repository files.

---

## 1. Environment Variables Configuration

All configuration is loaded via environment variables (or a local uncommitted `.env` file). Never commit real secrets, API keys, or credentials to git.

To run locally in development mode:

```bash
# Core Application Settings
export DEBUG="True"
export SECRET_KEY="local-dev-dummy-secret-key-change-in-production-min-50-chars"
export ALLOWED_HOSTS="localhost,127.0.0.1,[::1]"
export CSRF_TRUSTED_ORIGINS="http://localhost:8000,http://127.0.0.1:8000"

# Secret Key Rotation Support (Optional)
# export SECRET_KEY_FALLBACKS="previous-secret-key-1,previous-secret-key-2"

# Security & Request Logging Path
export SECURITY_LOG_PATH="./logs/security.log"

# Django Admin Access (Default: Disabled)
export ENABLE_ADMIN="True"
export DJANGO_ADMIN_PATH="management-portal-dev/"

# SSL & Reverse Proxy (False for local HTTP development)
export SECURE_SSL_REDIRECT="False"

# Database Configuration (Leave blank for local SQLite)
export DB_NAME=""
export DB_USER=""
export DB_PASSWORD=""
export DB_HOST="localhost"
export DB_PORT="3306"

# Email Settings (Console backend in development)
export EMAIL_BACKEND="django.core.mail.backends.console.EmailBackend"
export DEFAULT_FROM_EMAIL="Jimcan Operations <noreply@jimcanconstruction.site>"
```

---

## 2. Production Environment Variables (Reference Template)

In production or staging, configure via cPanel Python App environment variables or a secure, uncommitted server `.env` file (chmod 600):

```bash
# Mandatory Production Settings
export DEBUG="False"
export SECRET_KEY="<generate-random-50-character-high-entropy-string>"
export ALLOWED_HOSTS="jimcanconstruction.site,www.jimcanconstruction.site"
export CSRF_TRUSTED_ORIGINS="https://jimcanconstruction.site,https://www.jimcanconstruction.site"

# Admin: Disabled by default in production; if enabled, use secret non-default path
export ENABLE_ADMIN="False"
export DJANGO_ADMIN_PATH="<non-default-secret-admin-token-path>"

# SSL Enforcement (Default: True in production)
export SECURE_SSL_REDIRECT="True"

# Security Logging (Outside web-served directory)
export SECURITY_LOG_PATH="/home/username/jimcan_logs/security.log"

# Email Settings (Port 465 SSL or 587 TLS)
export EMAIL_BACKEND="django.core.mail.backends.smtp.EmailBackend"
export EMAIL_HOST="mail.jimcanconstruction.site"
export EMAIL_PORT="465"
export EMAIL_USE_SSL="True"
export EMAIL_HOST_USER="notifications@jimcanconstruction.site"
export EMAIL_HOST_PASSWORD="<strong-email-password>"
export DEFAULT_FROM_EMAIL="Jimcan Operations <notifications@jimcanconstruction.site>"
```

---

## 3. Secret Key Rotation Protocol

Django supports `SECRET_KEY_FALLBACKS` (introduced in Django 4.1). When rotating `SECRET_KEY`:
1. Move the existing `SECRET_KEY` value into `SECRET_KEY_FALLBACKS`.
2. Generate a new high-entropy string for `SECRET_KEY`.
3. Existing active sessions, signed cookies, and password reset tokens continue to validate using the fallback key while all new tokens and cookies are signed using the new key.
4. After session duration (e.g., 24 hours), remove the old key from `SECRET_KEY_FALLBACKS`.
