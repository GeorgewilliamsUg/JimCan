APPROVED

### 1. Are invoices submitted to URA EFRIS?
No direct EFRIS API integration for MVP; issued invoices are locked and corrected via Credit Notes.

### 2. Should Finance see Leads?
Yes (View only).

### 3. Is there any concept of staff being assigned to projects?
Yes, Site Staff should only see projects where they are assigned as members.

### 4. How many Owner accounts will exist?
Two Owner accounts.

### 5. Is there a terminal on the server (SSH or cPanel Terminal)?
Yes, cPanel Terminal is available.

### 6. Can the hosting send email, and from which domain?
Yes, via Namecheap cPanel Webmail SMTP (notifications@jimcanconstruction.site).

### 7. Can a staging copy be set up (subdomain, separate database)?
Yes (staging.jimcanconstruction.site with a separate staging database).

### 8. Is the Django admin used for daily work?
No, daily work is done via the custom dashboard. Admin is disabled by default in production.

### 9. How long must financial records be kept, according to the accountant?
7 years (per Uganda Tax Procedures Code Act).

### 10. Who is the Owner, who is Finance, and who is Site staff?
Owner: Managing Director / Partners; Finance: Accountant; Site Staff: Site Engineers.

### 11. Technical Decisions
- 11. Compile Tailwind CSS to static assets and remove the runtime Play CDN: Yes.
- 12. Untrack `.env` from git and add to `.gitignore`: Yes.
- 13. Fix port 465 SSL vs TLS settings in settings.py: Yes.
- 14. Server-side data scoping for dashboard overview tabs: Yes.
