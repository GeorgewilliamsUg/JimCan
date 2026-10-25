"""
WSGI config for Jimcan Operations Dashboard on Phusion Passenger (cPanel).
This file bridges cPanel's CloudLinux Python selector / Passenger server with Django.
"""
import os
import sys

# Ensure the application root is at the head of sys.path
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

# Point to project Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jimcan.settings')

# Expose WSGI application object for Passenger
from jimcan.wsgi import application
