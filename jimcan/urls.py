from django.contrib import admin
from django.urls import path, include
from dashboard.views import WelcomeLoginView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', WelcomeLoginView.as_view(), name='welcome'),
    path('login/', WelcomeLoginView.as_view(), name='login'),
    path('', include('django.contrib.auth.urls')),
    path('', include('dashboard.urls', namespace='dashboard')),
]

# Custom Error Handlers (pp.md Phase 1 §10)
handler400 = 'dashboard.views.error_400_view'
handler403 = 'dashboard.views.error_403_view'
handler404 = 'dashboard.views.error_404_view'
handler500 = 'dashboard.views.error_500_view'
