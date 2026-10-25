#!/usr/bin/env bash
# ==============================================================================
# Jimcan Operations Dashboard - Quality & Verification Suite
# Conforms to docs/design/qa-checklist.md and pp.md Phase 0 & Phase 1.
# ==============================================================================

set -e

# Select Python binary (prefer active venv)
if [ -f "./venv/bin/python" ]; then
  PYTHON="./venv/bin/python"
else
  PYTHON="python3"
fi

echo "=== [1/6] Verifying Core Phase 0 & Phase 1 Files ==="
REQUIRED_FILES=(
  "manage.py"
  "requirements.txt"
  "tailwind.config.js"
  "static/css/app.css"
  "jimcan/settings.py"
  "jimcan/urls.py"
  "jimcan/middleware.py"
  "dashboard/navigation.py"
  "dashboard/context_processors.py"
  "dashboard/views.py"
  "dashboard/urls.py"
  "templates/base.html"
  "templates/styleguide/showroom.html"
  "templates/dashboard/shell_demo.html"
  "templates/dashboard/section_placeholder.html"
  "templates/components/_page_header.html"
  "templates/components/_user_menu.html"
  "templates/components/_confirm_dialog.html"
  "templates/components/_session_timeout.html"
  "templates/400.html"
  "templates/403.html"
  "templates/404.html"
  "templates/500.html"
  "fixtures/demo_data.json"
  "tests/test_phase1_shell.py"
  "templates/registration/login.html"
  "templates/registration/password_change_form.html"
  "templates/registration/password_change_done.html"
  "templates/registration/password_reset_form.html"
  "templates/registration/password_reset_done.html"
  "templates/registration/password_reset_confirm.html"
  "templates/registration/password_reset_complete.html"
  "templates/registration/logged_out.html"
  "templates/accounts/setup_checklist.html"
  "tests/test_phase2_auth.py"
)

for file in "${REQUIRED_FILES[@]}"; do
  if [ -f "$file" ]; then
    echo "  [OK] $file exists"
  else
    echo "  [FAIL] Missing required file: $file"
    exit 1
  fi
done

echo "=== [2/6] Validating JSON Demo Fixtures ==="
$PYTHON -c "import json; data=json.load(open('fixtures/demo_data.json')); assert data['currency'] == 'UGX'; print('  [OK] Fixtures parsed successfully with currency: ' + data['currency'])"

echo "=== [3/6] Verifying Design System Tokens in CSS ==="
for token in "charcoal" "safety" "brass" "bone" "line" "muted" "go" "danger"; do
  if grep -q "color-$token" static/css/app.css; then
    echo "  [OK] CSS contains token variable: --color-$token"
  else
    echo "  [FAIL] Missing CSS token: --color-$token"
    exit 1
  fi
done

echo "=== [4/6] Verifying WCAG AA & Semantic Accessibility Landmarks ==="
if grep -q 'class="skip-link"' templates/base.html; then
  echo "  [OK] Skip-to-content anchor present"
else
  echo "  [FAIL] Missing accessible skip link in templates/base.html"
  exit 1
fi

if grep -q 'role="main"' templates/base.html && grep -q 'role="navigation"' templates/base.html; then
  echo "  [OK] Semantic landmarks present (main, navigation)"
else
  echo "  [FAIL] Missing semantic landmarks in templates/base.html"
  exit 1
fi

if grep -q 'prefers-reduced-motion' static/css/app.css; then
  echo "  [OK] Reduced-motion media query active"
else
  echo "  [FAIL] Missing prefers-reduced-motion stylesheet block"
  exit 1
fi

echo "=== [5/6] Running Django System Configuration Checks ==="
$PYTHON manage.py check

echo "=== [6/6] Executing Automated Phase 1 Unit and Integration Test Suite ==="
$PYTHON manage.py test tests

echo ""
echo "=============================================================================="
echo " [SUCCESS] All Foundation & Phase 1 Verification Checks Passed (Exit code 0)!"
echo "=============================================================================="
