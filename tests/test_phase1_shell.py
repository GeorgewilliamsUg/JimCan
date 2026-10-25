"""
Automated validation tests for Phase 1: App Shell and Feedback Patterns.
Tests role-based navigation filtering, active prefix matching,
PrivateCacheControlMiddleware, access boundaries, HTMX triggers, and error pages.
"""

import json
from django.test import TestCase, Client
from django.urls import reverse
from dashboard.navigation import get_navigation_items, NAVIGATION_ITEMS

class NavigationRegistryTests(TestCase):
    """Validates centralized navigation rules per docs/design/roles-permissions.md."""

    def test_admin_sees_all_items(self):
        items = get_navigation_items(role='admin', current_path='/')
        item_ids = [i['id'] for i in items]
        self.assertEqual(len(items), 12)
        self.assertIn('overview', item_ids)
        self.assertIn('settings', item_ids)
        self.assertIn('audit', item_ids)

    def test_manager_navigation_restrictions(self):
        items = get_navigation_items(role='manager', current_path='/')
        item_ids = [i['id'] for i in items]
        self.assertEqual(len(items), 9)
        self.assertNotIn('settings', item_ids)
        self.assertNotIn('audit', item_ids)
        self.assertIn('leads', item_ids)
        self.assertIn('projects', item_ids)

    def test_site_engineer_navigation_restrictions(self):
        """Site Engineers must never see commercial, margin, or tax items."""
        items = get_navigation_items(role='engineer', current_path='/')
        item_ids = [i['id'] for i in items]
        self.assertEqual(len(items), 5)
        self.assertNotIn('overview', item_ids)
        self.assertNotIn('leads', item_ids)
        self.assertNotIn('boq', item_ids)
        self.assertNotIn('invoices', item_ids)
        self.assertNotIn('tax', item_ids)
        self.assertNotIn('settings', item_ids)
        self.assertNotIn('audit', item_ids)
        self.assertIn('projects', item_ids)
        self.assertIn('expenses', item_ids)
        self.assertIn('files', item_ids)

    def test_accountant_navigation_restrictions(self):
        """Accountants must have read access to financial records but no site uploads or admin."""
        items = get_navigation_items(role='accountant', current_path='/')
        item_ids = [i['id'] for i in items]
        self.assertEqual(len(items), 7)
        self.assertNotIn('files', item_ids)
        self.assertNotIn('settings', item_ids)
        self.assertNotIn('audit', item_ids)
        self.assertIn('projects', item_ids)
        self.assertIn('boq', item_ids)
        self.assertIn('invoices', item_ids)
        self.assertIn('expenses', item_ids)
        self.assertIn('tax', item_ids)

    def test_active_url_prefix_matching(self):
        """Validates that section items match child paths by prefix."""
        # Exact root match
        items_root = get_navigation_items('admin', '/')
        overview_root = next(i for i in items_root if i['id'] == 'overview')
        projects_root = next(i for i in items_root if i['id'] == 'projects')
        self.assertTrue(overview_root['is_active'])
        self.assertFalse(projects_root['is_active'])

        # Subpath prefix match
        items_sub = get_navigation_items('admin', '/projects/123/edit/')
        overview_sub = next(i for i in items_sub if i['id'] == 'overview')
        projects_sub = next(i for i in items_sub if i['id'] == 'projects')
        self.assertFalse(overview_sub['is_active'])
        self.assertTrue(projects_sub['is_active'])


class PrivateCacheMiddlewareTests(TestCase):
    """Validates Risk #5 mitigation: no stale sensitive data cached after sign-out."""

    def setUp(self):
        self.client = Client()

    def test_html_responses_have_private_no_store_headers(self):
        response = self.client.get(reverse('dashboard:shell_demo'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('no-store', response['Cache-Control'])
        self.assertIn('private', response['Cache-Control'])
        self.assertIn('must-revalidate', response['Cache-Control'])
        self.assertEqual(response['Pragma'], 'no-cache')
        self.assertEqual(response['Expires'], '0')


class AccessEnforcementTests(TestCase):
    """Validates access control for section endpoints per user role."""

    def setUp(self):
        self.client = Client()

    def test_admin_can_access_rates(self):
        response = self.client.get(reverse('dashboard:rates') + '?role=admin')
        self.assertEqual(response.status_code, 200)

    def test_site_engineer_restricted_from_rates(self):
        response = self.client.get(reverse('dashboard:rates') + '?role=engineer')
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, 'HTTP 403 · Permission Denied', status_code=403)

    def test_site_engineer_can_access_projects(self):
        response = self.client.get(reverse('dashboard:projects') + '?role=engineer')
        self.assertEqual(response.status_code, 200)

    def test_site_engineer_restricted_from_tax(self):
        response = self.client.get(reverse('dashboard:tax') + '?role=engineer')
        self.assertEqual(response.status_code, 403)


class ErrorBoundaryTests(TestCase):
    """Validates custom branded error boundary views."""

    def setUp(self):
        self.client = Client()

    def test_403_view(self):
        response = self.client.get(reverse('dashboard:test_403'))
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, 'Access Restricted', status_code=403)

    def test_404_view(self):
        response = self.client.get(reverse('dashboard:test_404'))
        self.assertEqual(response.status_code, 404)
        self.assertContains(response, 'Record or Page Not Found', status_code=404)

    def test_500_view(self):
        response = self.client.get(reverse('dashboard:test_500'))
        self.assertEqual(response.status_code, 500)
        self.assertContains(response, 'Something Went Wrong', status_code=500)

    def test_400_view(self):
        response = self.client.get(reverse('dashboard:test_400'))
        self.assertEqual(response.status_code, 400)
        self.assertContains(response, 'Session or Security Token Expired', status_code=400)


class ApiAndHtmxTriggerTests(TestCase):
    """Validates session heartbeat and HTMX trigger responses."""

    def setUp(self):
        self.client = Client()

    def test_heartbeat_api(self):
        response = self.client.get(reverse('dashboard:api_heartbeat'))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data.get('status'), 'alive')

    def test_htmx_test_toast_trigger_header(self):
        response = self.client.post(reverse('dashboard:test_toast'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('HX-Trigger', response.headers)
        trigger = json.loads(response['HX-Trigger'])
        self.assertIn('showToast', trigger)
        self.assertEqual(trigger['showToast']['type'], 'success')
