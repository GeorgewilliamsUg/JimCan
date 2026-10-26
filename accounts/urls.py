from django.urls import path
from accounts.views import (
    ReauthView,
    AccountSetupView,
    JimcanPasswordChangeView,
    JimcanLogoutView
)

app_name = 'accounts'

urlpatterns = [
    path('reauth/', ReauthView.as_view(), name='reauth'),
    path('setup/<uidb64>/<token>/', AccountSetupView.as_view(), name='set_password'),
    path('password_change/', JimcanPasswordChangeView.as_view(), name='password_change'),
    path('logout/', JimcanLogoutView.as_view(), name='logout'),
]
