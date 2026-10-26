import datetime
import os
import sys
from pathlib import Path
from django.core.exceptions import ImproperlyConfigured

# Load environment variables from .env file if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

BASE_DIR = Path(__file__).resolve().parent.parent

# Detect test execution mode
is_running_tests = 'test' in sys.argv

# ------------------------------------------------------------------------------
# 1. Core Cryptographic Secrets & Rotation
# ------------------------------------------------------------------------------
# SECRET_KEY has no default. If missing, raise ImproperlyConfigured so the app refuses to start.
SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    raise ImproperlyConfigured(
        "The SECRET_KEY environment variable is not set. "
        "The application refuses to start without a valid secret key."
    )

# Support SECRET_KEY_FALLBACKS from an environment variable for zero-downtime rotation.
secret_key_fallbacks_raw = os.environ.get('SECRET_KEY_FALLBACKS', '').strip()
if secret_key_fallbacks_raw:
    SECRET_KEY_FALLBACKS = [k.strip() for k in secret_key_fallbacks_raw.split(',') if k.strip()]
else:
    SECRET_KEY_FALLBACKS = []

# ------------------------------------------------------------------------------
# 2. Debug & Host Security
# ------------------------------------------------------------------------------
# DEBUG defaults to False. Only an explicit case-insensitive 'true', '1', or 'yes' enables it.
DEBUG = os.environ.get('DEBUG', 'False').strip().lower() in ('true', '1', 'yes')

# Keyed audit log HMAC secret (Phase 3). A different secret from SECRET_KEY.
AUDIT_HMAC_KEY = os.environ.get('AUDIT_HMAC_KEY', '').strip()
if not AUDIT_HMAC_KEY:
    if is_running_tests:
        AUDIT_HMAC_KEY = 'test-audit-hmac-key-only-never-use-in-production'
    elif DEBUG:
        AUDIT_HMAC_KEY = 'dev-audit-hmac-key-only-never-use-in-production'
    else:
        raise ImproperlyConfigured(
            "The AUDIT_HMAC_KEY environment variable is not set. "
            "The application refuses to start in production without an audit HMAC key."
        )

allowed_hosts_raw = os.environ.get('ALLOWED_HOSTS', '').strip()
if allowed_hosts_raw and allowed_hosts_raw != '*':
    ALLOWED_HOSTS = [h.strip() for h in allowed_hosts_raw.split(',') if h.strip()]
elif DEBUG:
    # Safe defaults for local development
    ALLOWED_HOSTS = ['localhost', '127.0.0.1', '[::1]']
else:
    raise ImproperlyConfigured(
        "ALLOWED_HOSTS must be set in the environment when DEBUG is False. "
        "Wildcard '*' is forbidden in production."
    )

is_running_runserver = 'runserver' in sys.argv

# When running tests, development server, or with DEBUG=True, ensure local host is allowed
if is_running_tests or DEBUG or is_running_runserver:
    for local_host in ['testserver', 'localhost', '127.0.0.1', '[::1]']:
        if local_host not in ALLOWED_HOSTS:
            ALLOWED_HOSTS.append(local_host)

csrf_trusted_raw = os.environ.get('CSRF_TRUSTED_ORIGINS', '').strip()
if csrf_trusted_raw:
    CSRF_TRUSTED_ORIGINS = [o.strip() for o in csrf_trusted_raw.split(',') if o.strip()]
else:
    CSRF_TRUSTED_ORIGINS = []

# ------------------------------------------------------------------------------
# 3. Application Definition
# ------------------------------------------------------------------------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third-party
    'django_htmx',
    'axes',
    # Two-Factor & OTP (TOTP and static backup tokens only; no SMS/calls)
    'django_otp',
    'django_otp.plugins.otp_totp',
    'django_otp.plugins.otp_static',
    'two_factor',
    # Local Apps
    'accounts.apps.AccountsConfig',
    'audit.apps.AuditConfig',
    'dashboard.apps.DashboardConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django_otp.middleware.OTPMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.contrib.auth.middleware.LoginRequiredMiddleware',
    'jimcan.middleware.SessionTimeoutMiddleware',
    'audit.middleware.AuditContextMiddleware',
    'jimcan.middleware.MFAEnforcementMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_htmx.middleware.HtmxMiddleware',
    'jimcan.middleware.HtmxAuthRedirectMiddleware',
    'jimcan.middleware.PrivateCacheControlMiddleware',
    'axes.middleware.AxesMiddleware',
]

ROOT_URLCONF = 'jimcan.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'dashboard.context_processors.navigation_context',
            ],
            'libraries': {
                'dashboard_tags': 'dashboard.templatetags.dashboard_tags',
            },
        },
    },
]

WSGI_APPLICATION = 'jimcan.wsgi.application'

# ------------------------------------------------------------------------------
# 4. Database Configuration (supports MySQL via cPanel or SQLite default)
# ------------------------------------------------------------------------------
DB_NAME = os.environ.get('DB_NAME')
DB_USER = os.environ.get('DB_USER')

if DB_NAME and DB_USER:
    try:
        import pymysql
        pymysql.install_as_MySQLdb()
    except ImportError:
        pass

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': DB_NAME,
            'USER': DB_USER,
            'PASSWORD': os.environ.get('DB_PASSWORD', ''),
            'HOST': os.environ.get('DB_HOST', 'localhost'),
            'PORT': os.environ.get('DB_PORT', '3306'),
            'OPTIONS': {
                'charset': 'utf8mb4',
            },
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# ------------------------------------------------------------------------------
# 5. Security & Browser Headers (Strict Production Guardrails)
# ------------------------------------------------------------------------------
if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    CSRF_COOKIE_SAMESITE = 'Lax'
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_REFERRER_POLICY = 'same-origin'
    X_FRAME_OPTIONS = 'DENY'
    SECURE_HSTS_SECONDS = 300  # Staged: raised later in the production runbook
    SECURE_HSTS_INCLUDE_SUBDOMAINS = False
    SECURE_HSTS_PRELOAD = False
else:
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    CSRF_COOKIE_SAMESITE = 'Lax'
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_REFERRER_POLICY = 'same-origin'
    X_FRAME_OPTIONS = 'DENY'
    SECURE_HSTS_SECONDS = 0
    SECURE_HSTS_INCLUDE_SUBDOMAINS = False
    SECURE_HSTS_PRELOAD = False

# SECURE_SSL_REDIRECT: defaults to True in production (DEBUG=False); overridable via environment variable
is_running_tests = 'test' in sys.argv
if is_running_tests:
    default_ssl_redirect = 'False'
elif not DEBUG:
    default_ssl_redirect = 'True'
else:
    default_ssl_redirect = 'False'

SECURE_SSL_REDIRECT = os.environ.get('SECURE_SSL_REDIRECT', default_ssl_redirect).strip().lower() in ('true', '1', 'yes')

# SECURE_PROXY_SSL_HEADER is deliberately NOT set:
# Phase 0 proved that reverse proxy headers on Namecheap are unverified.
# Setting it without a confirmed, sanitizing upstream proxy enables attackers to spoof HTTPS.

# ------------------------------------------------------------------------------
# 6. Admin Configuration Switch
# ------------------------------------------------------------------------------
# ENABLE_ADMIN environment switch, defaults to False.
ENABLE_ADMIN = os.environ.get('ENABLE_ADMIN', 'False').lower() in ('true', '1', 'yes')
DJANGO_ADMIN_PATH = os.environ.get('DJANGO_ADMIN_PATH', 'admin/').strip('/')

# ------------------------------------------------------------------------------
# 7. Authentication Backends, Password Hashers & Validation (Phase 2)
# ------------------------------------------------------------------------------
AUTHENTICATION_BACKENDS = [
    'accounts.backends.JimcanAxesBackend',
    'django.contrib.auth.backends.ModelBackend',
]

PASSWORD_HASHERS = [
    'jimcan.hashers.JimcanArgon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
]

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 12},
    },
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

PASSWORD_RESET_TIMEOUT = 3600

# Session Engine & Storage (Database-backed)
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 28800  # 8 hours absolute session ceiling

# ------------------------------------------------------------------------------
# 7b. Brute-Force Attack Protection (django-axes)
# ------------------------------------------------------------------------------
AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = datetime.timedelta(minutes=30)
AXES_RESET_ON_SUCCESS = True
AXES_LOCKOUT_PARAMETERS = [["username", "ip_address"]]
AXES_IPWARE_META_PRECEDENCE_ORDER = ("REMOTE_ADDR",)
AXES_LOCKOUT_CALLABLE = None
AXES_VERBOSE = True

# ------------------------------------------------------------------------------
# 8. Internationalization & Localization
# ------------------------------------------------------------------------------
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Kampala'
USE_I18N = True
USE_TZ = True

# ------------------------------------------------------------------------------
# 9. Static & Media Storage
# ------------------------------------------------------------------------------
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom CSRF Failure View
CSRF_FAILURE_VIEW = 'dashboard.views.error_400_view'

# Authentication & Session Guardrails
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard:overview'
LOGOUT_REDIRECT_URL = 'login'

# Two-Factor Authentication & Throttling (Phase 4)
OTP_TOTP_THROTTLE_FACTOR = 1
OTP_STATIC_THROTTLE_FACTOR = 1
TWO_FACTOR_PATCH_ADMIN = True
TWO_FACTOR_REMEMBER_COOKIE_AGE = None  # Strict: require second factor on every login session

# Staged MFA Rollout Switch: 'off', 'owners', 'all'. Default in production: 'all'
MFA_ENFORCEMENT = os.environ.get('MFA_ENFORCEMENT', 'all' if not DEBUG else 'off').lower().strip()

# ------------------------------------------------------------------------------
# 10. Logging Configuration (Outside Web-Served Directory with Rotation)
# ------------------------------------------------------------------------------
LOGS_DIR = BASE_DIR / 'logs'
LOGS_DIR.mkdir(parents=True, exist_ok=True)
SECURITY_LOG_PATH = os.environ.get('SECURITY_LOG_PATH', str(LOGS_DIR / 'security.log'))

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} [{name}] [PID:{process}] {message}',
            'style': '{',
        },
    },
    'handlers': {
        'security_file': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': SECURITY_LOG_PATH,
            'maxBytes': 5 * 1024 * 1024,  # 5 MB rotation
            'backupCount': 5,
            'formatter': 'verbose',
            'encoding': 'utf-8',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django.security': {
            'handlers': ['security_file', 'console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['security_file', 'console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'jimcan.security': {
            'handlers': ['security_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# ------------------------------------------------------------------------------
# 11. Email Backend Configuration
# ------------------------------------------------------------------------------
EMAIL_BACKEND = os.environ.get(
    'EMAIL_BACKEND',
    'django.core.mail.backends.console.EmailBackend' if DEBUG else 'django.core.mail.backends.smtp.EmailBackend'
)
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'localhost')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USE_SSL = os.environ.get('EMAIL_USE_SSL', 'False').lower() in ('true', '1', 'yes')
if EMAIL_USE_SSL:
    EMAIL_USE_TLS = False
else:
    EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True').lower() in ('true', '1', 'yes')
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@jimcanconstruction.site')
