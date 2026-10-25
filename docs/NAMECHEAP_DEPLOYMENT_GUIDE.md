# Deploying Jimcan Operations Dashboard to Namecheap cPanel

This guide provides step-by-step instructions for deploying the **Jimcan Operations Dashboard** to **Namecheap Shared Hosting** (Stellar, Stellar Plus, or Stellar Business) using cPanel's **Setup Python App** (CloudLinux + Phusion Passenger).

---

## Architecture Overview

- **Server Engine**: Phusion Passenger WSGI managed via cPanel's CloudLinux Python selector.
- **Entry Point**: `passenger_wsgi.py` (pre-configured in the repository root).
- **Static Assets**: Automatically served by **WhiteNoise** with compression and caching enabled (no complex Apache/`.htaccess` rewrites needed).
- **Environment**: Managed through a secure `.env` file in the application root.
- **Database**: Supports either zero-configuration **SQLite** or production-grade **MySQL/MariaDB** via cPanel's MySQL wizard.

---

## Step 1: Push Your Local Changes to GitHub

Ensure your latest code (including `passenger_wsgi.py` and `requirements.txt`) is pushed to GitHub:

```bash
git push origin main
git push origin main:master
```

---

## Step 2: Clone or Upload the Code to Namecheap

You have two simple ways to place your code in your cPanel hosting account:

### Option A: Via cPanel Terminal or SSH (Recommended)
1. In cPanel, open **Terminal** (under the **Advanced** section).
2. Clone your repository into your home directory:
   ```bash
   cd ~
   git clone https://github.com/GeorgewilliamsUg/JimCan.git jimcan
   cd jimcan
   ```

### Option B: Via cPanel Git™ Version Control
1. In cPanel, click **Git™ Version Control** (under **Files**).
2. Click **Create**:
   - **Clone URL**: `https://github.com/GeorgewilliamsUg/JimCan.git`
   - **Repository Path**: `jimcan`
   - **Repository Name**: `jimcan`
3. Click **Create** to clone the repository.

---

## Step 3: Create the Python Application in cPanel

1. In cPanel, navigate to the **Software** section and click **Setup Python App**.
2. Click the **Create Application** button (top right).
3. Fill in the following fields:
   - **Python Version**: Select **3.11** or **3.12** (match your preferred modern Python 3 release).
   - **Application root**: `jimcan` *(this points to `/home/username/jimcan`)*.
   - **Application URL**: Select your domain or subdomain (e.g., `yourdomain.com` or `dashboard.yourdomain.com`).
   - **Application startup file**: `passenger_wsgi.py`
   - **Application Entry point**: `application`
   - **Passenger log file**: `passenger.log` *(recommended for debugging)*
4. Click **Create** (top right).
5. Once created, a notification banner appears at the top containing a command to activate the virtual environment. It looks like:
   ```bash
   source /home/<username>/virtualenv/jimcan/3.11/bin/activate && cd /home/<username>/jimcan
   ```
   *Copy this command.*

---

## Step 4: Install Dependencies

1. Open cPanel **Terminal** (or connect via SSH).
2. Paste the activation command copied in the previous step:
   ```bash
   source /home/<username>/virtualenv/jimcan/3.11/bin/activate && cd /home/<username>/jimcan
   ```
3. Upgrade pip and install all required packages:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

---

## Step 5: Configure Environment Variables (`.env`)

1. In your application root (`/home/<username>/jimcan`), create your `.env` file from the provided template:
   ```bash
   cp .env.example .env
   nano .env
   ```
2. Update the values with your production settings:
   ```ini
   # Security
   SECRET_KEY=generate-a-unique-random-secret-key-here
   DEBUG=False
   ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
   CSRF_TRUSTED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

   # Database (Leave blank for SQLite, or fill in cPanel MySQL credentials)
   DB_NAME=
   DB_USER=
   DB_PASSWORD=
   DB_HOST=localhost
   DB_PORT=3306

   # Email (optional: Namecheap private email / cPanel webmail SMTP)
   EMAIL_HOST=mail.yourdomain.com
   EMAIL_PORT=465
   EMAIL_USE_SSL=True
   EMAIL_HOST_USER=notifications@yourdomain.com
   EMAIL_HOST_PASSWORD=your_email_password
   DEFAULT_FROM_EMAIL=Jimcan Operations <notifications@yourdomain.com>
   ```
3. Save and close `nano` (`Ctrl+O`, `Enter`, then `Ctrl+X`).

---

## Step 6: Database Setup

### Option 1: SQLite (Simplest, Zero Configuration)
If you leave `DB_NAME` blank in `.env`, Django automatically uses SQLite.
Ensure file permissions allow write access:
```bash
chmod 664 db.sqlite3 2>/dev/null || true
chmod 775 /home/<username>/jimcan
```

### Option 2: MySQL / MariaDB (Recommended for Multi-user Production)
1. In cPanel, go to **Databases** -> **MySQL Databases**.
2. **Create New Database**: e.g., `cpaneluser_jimcan`.
3. **Add New User**: e.g., `cpaneluser_admin`, generate a strong password.
4. **Add User To Database**: Select the user and database, click **Add**, and check **ALL PRIVILEGES**.
5. Put those credentials in your `.env` file:
   ```ini
   DB_NAME=cpaneluser_jimcan
   DB_USER=cpaneluser_admin
   DB_PASSWORD=your_password
   DB_HOST=localhost
   DB_PORT=3306
   ```

---

## Step 7: Run Migrations and Collect Static Files

From your active virtual environment terminal in `/home/<username>/jimcan`:

```bash
# 1. Apply database migrations
python manage.py migrate

# 2. Collect static files for WhiteNoise
python manage.py collectstatic --noinput

# 3. Create your administrative account
python manage.py createsuperuser
```

---

## Step 8: Restart the Application & Verify

1. Go back to cPanel -> **Setup Python App**.
2. Locate your application in the list and click the **Restart** icon (circular arrow).
   *(Or from the terminal, simply run: `touch tmp/restart.txt`)*
3. Visit your website: `https://yourdomain.com` (or your subdomain).
4. Verify the login page loads with full Tailwind styling and assets.
5. Log in using the superuser credentials created in Step 7.

---

## Step 9: Enable SSL (HTTPS)

1. In cPanel, go to **Security** -> **SSL/TLS Status**.
2. Select your domain/subdomain and click **Run AutoSSL** to install Namecheap's free Sectigo SSL certificate.

---

## Troubleshooting & Maintenance

### 1. Application Error / 500 Internal Server Error
Check the logs:
- In the application directory: `cat passenger.log`
- In cPanel: Go to **Metrics** -> **Errors**.

### 2. Static Files Not Loading
Run `python manage.py collectstatic --noinput` again to ensure all static files were collected into `/home/<username>/jimcan/staticfiles/`. WhiteNoise automatically serves them with cache headers.

### 3. Deploying Future Updates
Whenever you push updates to GitHub, deploy them in 3 simple commands in cPanel terminal:
```bash
cd /home/<username>/jimcan
git pull origin main
python manage.py migrate
python manage.py collectstatic --noinput
touch tmp/restart.txt
```
