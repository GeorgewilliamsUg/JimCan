# Jimcan Construction: System Architecture & Implementation Specification

## 1. Executive Summary
This document outlines the architecture, design system, and feature specifications for the Jimcan Construction internal CRM and Project Management dashboard. The system manages inbound leads from `jimcanconstruction.site`, tracks active builds, and manages portfolio assets. The architecture prioritizes zero-maintenance serverless infrastructure, strict data security, and enterprise-grade operational logging.

## 2. Technology Stack & Infrastructure
*   **Frontend Framework:** Next.js (App Router, Server Components).
*   **Form State & Validation:** React Hook Form bound with Zod schemas.
*   **UI & Styling:** Tailwind CSS + shadcn/ui (Accessible, headless components).
*   **Backend & Database:** PostgreSQL hosted on Supabase.
*   **Authentication & RBAC:** Supabase Auth (JWT-based session management).
*   **Storage:** Supabase Storage (for CAD files, PDFs, site photos).
*   **Transactional Email:** Resend (Triggered via API routes/webhooks).
*   **End-to-End (E2E) Testing:** Playwright.
*   **Hosting & CI/CD:** Vercel.

## 3. Security & Authentication Architecture

### 3.1 Role-Based Access Control (RBAC)
Authentication is handled via Supabase Auth. Access to data is strictly enforced at the PostgreSQL level using Row Level Security (RLS) policies based on the user's role.
*   **Admin:** Full read/write access to all system data, including user management and hard deletions.
*   **Project Manager:** Read/write access to assigned projects and leads. Cannot permanently delete records.
*   **Site Engineer:** Read access to assigned projects. Write access limited to uploading `project_assets` (e.g., site progress photos) and updating `current_phase`.

### 3.2 System Auditing & Soft Deletes
*   **Soft Deletes:** Records are never dropped from the database by standard users. An `is_deleted = true` boolean flags removed records to prevent data loss.
*   **Audit Trails:** Every mutation (INSERT, UPDATE, DELETE) on critical tables (`leads`, `projects`) triggers a database function that logs the action, the timestamp, the exact payload changes, and the `user_id` to the `audit_logs` table.

## 4. Database Schema (PostgreSQL)

**Table: `users` (Linked to Supabase Auth)**
*   `id` (uuid, primary key)
*   `role` (enum: admin, manager, engineer)
*   `full_name` (varchar)

**Table: `leads` (CRM)**
*   `id` (uuid, primary key)
*   `created_at` (timestamp)
*   `name`, `email`, `phone`, `project_type` (varchar)
*   `details` (text)
*   `status` (enum: new, contacted, site_visit, quoted, closed)
*   `assigned_to` (uuid, foreign key -> users.id)
*   `is_deleted` (boolean, default: false)

**Table: `projects` (Active Builds)**
*   `id` (uuid, primary key)
*   `lead_id` (uuid, foreign key)
*   `title`, `location` (varchar)
*   `budget` (numeric)
*   `current_phase` (enum: brief, design, foundation, superstructure, finishes, handover)
*   `start_date`, `target_completion` (date)
*   `is_deleted` (boolean, default: false)

**Table: `project_assets` (Media & Documents)**
*   `id` (uuid, primary key)
*   `project_id` (uuid, foreign key)
*   `uploaded_by` (uuid, foreign key -> users.id)
*   `file_url` (varchar)
*   `asset_type` (enum: photo, document, cad)

**Table: `audit_logs` (System Tracking)**
*   `id` (uuid, primary key)
*   `table_name` (varchar)
*   `record_id` (uuid)
*   `action` (enum: insert, update, delete)
*   `changed_by` (uuid, foreign key -> users.id)
*   `changes` (jsonb - stores before/after state)
*   `created_at` (timestamp)

## 5. Core Application Workflows

### 5.1 Inbound Lead Pipeline (Web to CRM)
1. User submits contact form on `jimcanconstruction.site`.
2. Form posts to a Next.js API Route protected by an IP rate limiter.
3. API validates payload using a Zod schema.
4. Data is inserted into the `leads` table.
5. **Notification:** A Supabase Database Webhook fires on the INSERT, calling the Resend API to email the Admin and Project Managers: *"New Lead: [Project Type] in [Location]"*.

### 5.2 Project Execution & Portfolio Sync
1. A lead is marked "Closed/Won" and converted into a `project`.
2. Site Engineers upload weekly progress photos to `project_assets` via the dashboard.
3. Once a project phase is changed to `handover`, an automated webhook triggers a Vercel deployment of the static `jimcanconstruction.site` to instantly update the public portfolio without manual webmaster intervention.

## 6. Deployment & CI/CD Pipeline

### 6.1 Testing Standards
*   **Unit/Integration:** Jest for testing utility functions and Zod validation schemas.
*   **E2E (Playwright):** Critical path testing runs on GitHub Actions before any merge to `main`. Tests must pass for:
    *   Logging in as a Manager.
    *   Creating and converting a Lead.
    *   Uploading a mock asset to a Project.

### 6.2 CI/CD Flow
1. **Pull Requests:** Vercel generates a secure Preview Deployment connected to a staging database.
2. **Merge to Main:** Triggers Playwright test suite. Upon success, Vercel builds and deploys to production.
3. **Database Migrations:** Supabase CLI runs `supabase db push` as part of the GitHub Action to ensure schema changes are applied before the Next.js production build completes.

### 6.3 Disaster Recovery
*   **Database:** Supabase Point-in-Time Recovery (PITR) is enabled, allowing restoration of the database to any exact minute within the last 7 days.
*   **Storage:** Automated weekly cron jobs back up all CAD files and site photos from Supabase Storage to an isolated cold-storage AWS S3 bucket.