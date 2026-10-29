from django.urls import path
from accounts.views import (
    ReauthView,
    AccountSetupView,
    JimcanPasswordChangeView,
    JimcanLogoutView
)
from accounts.mfa_views import ResetUserMFAView
from accounts.user_views import (
    UserListView,
    UserCreateView,
    UserEditView,
    UserToggleActiveView,
    UserSendSetupLinkView,
    UserResetPasswordView,
    UserVaultCredentialView,
)

app_name = 'accounts'

urlpatterns = [
    path('reauth/', ReauthView.as_view(), name='reauth'),
    path('setup/<uidb64>/<token>/', AccountSetupView.as_view(), name='set_password'),
    path('password_change/', JimcanPasswordChangeView.as_view(), name='password_change'),
    path('logout/', JimcanLogoutView.as_view(), name='logout'),
    path('users/', UserListView.as_view(), name='user_list'),
    path('users/create/', UserCreateView.as_view(), name='user_create'),
    path('users/<int:user_id>/', UserEditView.as_view(), name='user_edit'),
    path('users/<int:user_id>/toggle-active/', UserToggleActiveView.as_view(), name='user_toggle_active'),
    path('users/<int:user_id>/send-setup-link/', UserSendSetupLinkView.as_view(), name='user_send_setup_link'),
    path('users/<int:user_id>/reset-password/', UserResetPasswordView.as_view(), name='user_reset_password'),
    path('users/<int:user_id>/reset-mfa/', ResetUserMFAView.as_view(), name='user_reset_mfa'),
    path('users/<int:user_id>/vault-credential/', UserVaultCredentialView.as_view(), name='user_vault_credential'),
    path('team/', UserListView.as_view(), name='team_list'),
    path('team/create/', UserCreateView.as_view(), name='team_create'),
    path('team/<int:user_id>/reset-password/', UserResetPasswordView.as_view(), name='team_reset_password'),
    path('team/<int:user_id>/vault-credential/', UserVaultCredentialView.as_view(), name='team_vault_credential'),
]
