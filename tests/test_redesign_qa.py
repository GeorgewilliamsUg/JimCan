from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from decimal import Decimal

User = get_user_model()

class RedesignQATest(TestCase):
    def setUp(self):
        self.client = Client(SERVER_NAME='localhost')
        self.user = User.objects.create_superuser(
            username='admin_test',
            email='admin@jimcan.example.com',
            password='testpassword123',
            first_name='Admin'
        )
        self.client.force_login(self.user)

    def test_overview_admin_renders_200_and_components(self):
        response = self.client.get('/overview/?role=admin')
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        
        # Verify money flow panel
        self.assertIn('Money flow', content)
        self.assertIn('Contract value', content)
        self.assertIn('Invoiced', content)
        self.assertIn('Collected', content)
        self.assertIn('Still owed', content)
        
        # Verify tabs
        self.assertIn('Active projects', content)
        self.assertIn('Milestone invoices', content)
        self.assertIn('Leads', content)
        self.assertIn('BOQ rates', content)
        
        # Verify sidebar and shell
        self.assertIn('id="app-sidebar"', content)
        self.assertIn('id="sidebar-toggle"', content)
        self.assertIn('Good ', content) # greeting

    def test_projects_and_invoices_render_inside_new_shell(self):
        # Projects page
        resp_proj = self.client.get('/projects/?role=admin')
        self.assertEqual(resp_proj.status_code, 200)
        proj_content = resp_proj.content.decode('utf-8')
        self.assertIn('id="app-sidebar"', proj_content)
        self.assertIn('tokens.css', proj_content)

        # Invoices page
        resp_inv = self.client.get('/invoices/?role=admin')
        self.assertEqual(resp_inv.status_code, 200)
        inv_content = resp_inv.content.decode('utf-8')
        self.assertIn('id="app-sidebar"', inv_content)
        self.assertIn('tokens.css', inv_content)

    def test_empty_data_renders_safely_no_division_by_zero(self):
        """Test with empty data: 0 contract value, 0 invoiced, empty lists."""
        empty_context = {
            'projects': [],
            'invoices': [],
            'leads': [],
            'rates': [],
            'total_contract_value': Decimal('0'),
            'total_invoiced_gross': Decimal('0'),
            'total_collected_gross': Decimal('0'),
            'total_receivable': Decimal('0'),
            'committed_cost': Decimal('0'),
            'request': type('MockRequest', (), {
                'user': self.user,
                'path': '/overview/',
                'resolver_match': None,
                'GET': {},
            })(),
            'user': self.user,
        }
        # Render the template directly with empty context
        rendered = render_to_string('dashboard/overview.html', empty_context)
        self.assertIn('Money flow', rendered)
        self.assertIn('Contract value', rendered)
        # Should not raise ZeroDivisionError and should render safely
