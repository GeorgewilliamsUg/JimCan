"""
WSGI config for Jimcan Operations Dashboard on Phusion Passenger (cPanel).
This file bridges cPanel's CloudLinux Python selector / Passenger server with Django.
"""
import os
import sys
import traceback

# Ensure the application root is at the head of sys.path
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

# Point to project Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jimcan.settings')

try:
    # Expose WSGI application object for Passenger
    from jimcan.wsgi import application
except Exception as startup_err:
    # Record detailed traceback to passenger.log in project root
    err_tb = traceback.format_exc()
    try:
        log_file = os.path.join(PROJECT_DIR, 'passenger.log')
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"\n[{startup_err.__class__.__name__}] Startup Exception:\n{err_tb}\n")
    except Exception:
        pass

    # Fallback WSGI application to display the actionable startup diagnosis
    def application(environ, start_response):
        status = '500 Internal Server Error'
        error_type = startup_err.__class__.__name__
        error_msg = str(startup_err)

        html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Application Startup Error · Jimcan</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Inter", sans-serif; background: #0F172A; color: #F8FAFC; padding: 2rem; margin: 0; line-height: 1.5; }}
    .container {{ max-width: 840px; margin: 2rem auto; background: #1E293B; border: 1px solid #334155; border-radius: 12px; padding: 2rem; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.5); }}
    h1 {{ color: #F87171; font-size: 1.4rem; margin-top: 0; }}
    .badge {{ display: inline-block; padding: 0.2rem 0.6rem; border-radius: 4px; background: rgba(248,113,113,0.2); color: #FCA5A5; font-size: 0.8rem; font-weight: 600; font-family: monospace; }}
    .error-box {{ background: #0F172A; border-left: 4px solid #EF4444; border-radius: 4px; padding: 1rem; margin: 1.25rem 0; color: #E2E8F0; font-family: monospace; font-size: 0.9rem; word-break: break-all; }}
    pre {{ background: #0F172A; padding: 1rem; border-radius: 8px; font-size: 0.78rem; color: #94A3B8; overflow-x: auto; max-height: 320px; }}
    .checklist {{ margin-top: 1.5rem; font-size: 0.85rem; color: #CBD5E1; border-top: 1px solid #334155; padding-top: 1.25rem; }}
    .checklist ol {{ padding-left: 1.25rem; }}
    .checklist li {{ margin-bottom: 0.5rem; }}
    code {{ background: #334155; color: #38BDF8; padding: 0.15rem 0.4rem; border-radius: 4px; font-family: monospace; font-size: 0.85rem; }}
  </style>
</head>
<body>
  <div class="container">
    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 1rem;">
      <h1>Application Startup Failure</h1>
      <span class="badge">{error_type}</span>
    </div>
    <div class="error-box">
      <strong>{error_type}:</strong> {error_msg}
    </div>
    <pre>{err_tb}</pre>
    <div class="checklist">
      <strong>Configuration Resolution Checklist:</strong>
      <ol>
        <li><strong>Environment Variables:</strong> Verify <code>/home/&lt;user&gt;/jimcan/.env</code> exists and contains <code>SECRET_KEY</code>, <code>AUDIT_HMAC_KEY</code>, and <code>ALLOWED_HOSTS=jimcanconstruction.site,www.jimcanconstruction.site</code>.</li>
        <li><strong>Dependencies:</strong> Ensure all packages are installed in your cPanel virtual environment: <code>pip install -r requirements.txt</code>.</li>
        <li><strong>Database Migrations:</strong> Run <code>python manage.py migrate</code>.</li>
        <li><strong>Restart Passenger:</strong> In cPanel Python App manager, click <strong>Restart</strong>, or run <code>touch tmp/restart.txt</code>.</li>
      </ol>
    </div>
  </div>
</body>
</html>"""
        output = html.encode('utf-8')
        response_headers = [
            ('Content-Type', 'text/html; charset=utf-8'),
            ('Content-Length', str(len(output)))
        ]
        start_response(status, response_headers)
        return [output]
