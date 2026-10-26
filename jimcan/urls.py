from django.conf import settings
from django.contrib import admin
from django.core.exceptions import ImproperlyConfigured
from django.urls import path, include
from dashboard.views import WelcomeLoginView

from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_not_required
from django.urls import reverse_lazy
from accounts.views import JimcanLogoutView, JimcanPasswordChangeView

urlpatterns = [
    path('', WelcomeLoginView.as_view(), name='welcome'),
    path('login/', WelcomeLoginView.as_view(), name='login'),
    path('logout/', JimcanLogoutView.as_view(), name='logout'),
    path('password_change/', JimcanPasswordChangeView.as_view(), name='password_change'),
    path(
        'password_reset/',
        login_not_required(auth_views.PasswordResetView.as_view(
            template_name='registration/password_reset_form.html',
            email_template_name='registration/password_reset_email.html',
            subject_template_name='registration/password_reset_subject.txt',
            success_url=reverse_lazy('password_reset_done'),
        )),
        name='password_reset'
    ),
    path(
        'password_reset/done/',
        login_not_required(auth_views.PasswordResetDoneView.as_view(
            template_name='registration/password_reset_done.html'
        )),
        name='password_reset_done'
    ),
    path(
        'reset/<uidb64>/<token>/',
        login_not_required(auth_views.PasswordResetConfirmView.as_view(
            template_name='registration/password_reset_confirm.html',
            success_url=reverse_lazy('password_reset_complete'),
        )),
        name='password_reset_confirm'
    ),
    path(
        'reset/done/',
        login_not_required(auth_views.PasswordResetCompleteView.as_view(
            template_name='registration/password_reset_complete.html'
        )),
        name='password_reset_complete'
    ),
    path('accounts/', include('accounts.urls', namespace='accounts')),
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
