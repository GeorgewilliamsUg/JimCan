# Documented Middleware Pipeline & Architecture

This document defines the strict, verified order of middleware components for the Jimcan Operations Dashboard.
Any change to this pipeline must be deliberate, documented here, and validated against automated regression tests.

| Order | Middleware | Purpose & Rationale |
|---|---|---|
| 1 | `django.middleware.security.SecurityMiddleware` | First line of defense. Enforces HTTPS redirects, HSTS policies, and X-Content-Type sniffing protection before any request processing. |
| 2 | `whitenoise.middleware.WhiteNoiseMiddleware` | High-performance static asset serving. Sits immediately behind security middleware to serve assets without invoking session or database overhead. |
| 3 | `django.contrib.sessions.middleware.SessionMiddleware` | Initializes session storage (`request.session`). Must precede Common, Authentication, and CSRF middlewares. |
| 4 | `django.middleware.common.CommonMiddleware` | URL normalization, trailing slash enforcement, and Host header validation. |
| 5 | `django.middleware.csrf.CsrfViewMiddleware` | Validates CSRF tokens on POST/PUT/DELETE requests. Must precede authentication actions and view execution. |
| 6 | `django.contrib.auth.middleware.AuthenticationMiddleware` | Resolves user identity and attaches `request.user` based on active session. Required by all downstream access controls. |
| 7 | `django.contrib.messages.middleware.MessageMiddleware` | Flash notification storage. Must precede downstream middleware and views so flash notices can be queued on redirects. |
| 8 | `django.contrib.auth.middleware.LoginRequiredMiddleware` | Deny-by-default architecture. Automatically rejects unauthenticated requests across all routes unless explicitly exempted via `@login_not_required`. |
| 9 | `jimcan.middleware.SessionTimeoutMiddleware` | Enforces 30-minute idle inactivity timeout and 8-hour absolute session ceiling. Terminates expired sessions and queues user notification. |
| 10 | `audit.middleware.AuditContextMiddleware` | Ambient request context capture. Attaches authenticated user, client IP, user agent, and request UUID to thread/coroutine contextvars for tamper-evident audit logging. |
| 11 | `django.middleware.clickjacking.XFrameOptionsMiddleware` | Emits `X-Frame-Options: DENY` header to mitigate clickjacking and unauthorized iframe framing. |
| 12 | `django_htmx.middleware.HtmxMiddleware` | Parses incoming HTMX headers and attaches `request.htmx` helper attributes. |
| 13 | `jimcan.middleware.HtmxAuthRedirectMiddleware` | Guards against HTMX requests rendering HTML login forms inside partial widget containers; emits `HX-Redirect` for full-window navigation. |
| 14 | `jimcan.middleware.PrivateCacheControlMiddleware` | Injects `Cache-Control: no-store, no-cache, must-revalidate, private` on authenticated responses and credential pages to prevent browser history back-button exposure. |
| 15 | `axes.middleware.AxesMiddleware` | Brute-force lockout and attempt tracking. Per official django-axes documentation, AxesMiddleware must run last to accurately monitor completed responses and credentials. |
