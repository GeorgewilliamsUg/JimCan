from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    # Operational & Administrative Section Views
    path('', views.overview_view, name='overview'),
    path('leads/', views.leads_view, name='leads'),
    path('projects/', views.projects_view, name='projects'),
    path('rates/', views.rates_view, name='rates'),
    path('invoices/', views.invoices_view, name='invoices'),
    path('expenses/', views.expenses_view, name='expenses'),
    path('tax/', views.tax_view, name='tax'),
    path('files/', views.files_view, name='files'),
    path('styleguide/', views.styleguide_view, name='styleguide'),
    path('shell-demo/', views.shell_demo_view, name='shell_demo'),
    path('settings/', views.settings_view, name='settings'),
    path('setup/', views.setup_checklist_view, name='setup_checklist'),
    path('audit/', views.audit_view, name='audit'),

    # API Endpoints
    path('api/heartbeat/', views.api_heartbeat_view, name='api_heartbeat'),
    path('api/test-toast/', views.api_test_toast_view, name='test_toast'),
    path('api/test-htmx-401/', views.api_test_htmx_401, name='test_htmx_401'),
    path('api/test-htmx-403/', views.api_test_htmx_403, name='test_htmx_403'),

    # Error Boundary Preview Endpoints
    path('test-403/', views.test_403_view, name='test_403'),
    path('test-404/', views.test_404_view, name='test_404'),
    path('test-500/', views.test_500_view, name='test_500'),
    path('test-400/', views.test_400_view, name='test_400'),
]
