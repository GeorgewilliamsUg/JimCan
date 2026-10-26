from django.conf import settings
from django.contrib import admin
from django.core.exceptions import ImproperlyConfigured
from django.urls import path, include
from dashboard.views import WelcomeLoginView

urlpatterns = [
    path('', WelcomeLoginView.as_view(), name='welcome'),
    path('login/', WelcomeLoginView.as_view(), name='login'),
    path('', include('django.contrib.auth.urls')),
    path('', include('dashboard.urls', namespace='dashboard')),
]

# Admin URLs registered only when ENABLE_ADMIN is True
if getattr(settings, 'ENABLE_ADMIN', False):
    admin_path = getattr(settings, 'DJANGO_ADMIN_PATH', 'admin').strip('/')
    if not settings.DEBUG and admin_path == 'admin':
        raise ImproperlyConfigured(
            'DJANGO_ADMIN_PATH cannot be the default "admin/" in production (DEBUG=False). '
            'Configure a secure, non-default path or set ENABLE_ADMIN=False.'
        )
    urlpatterns.insert(0, path(f'{admin_path}/', admin.site.urls))

# Custom Error Handlers
handler400 = 'dashboard.views.error_400_view'
handler403 = 'dashboard.views.error_403_view'
handler404 = 'dashboard.views.error_404_view'
handler500 = 'dashboard.views.error_500_view'
