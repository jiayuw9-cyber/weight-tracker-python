# My Weight Journal

A small Python + Streamlit project. Visitors can try a **public demo with fictional numbers**. Anyone can sign in with **their own email code** and save only their own records. Supabase stores progress in the cloud. Database Row Level Security (RLS) isolates users' rows.

## Before changing your existing deployed app

**Back up any real entries from the old app first.** Open the old app, download its CSV, and save it privately. After switching to the new code, those old SQLite entries are NOT automatically migrated. Delete any existing real measurements from source files, Git history and any unintended public database exposures as appropriate. A public repository's old history may still contain old constants even after edits.

## Setup — once

1. Create a free project at https://supabase.com/dashboard .
2. Open **SQL Editor** and run the entire `schema.sql` file. It creates `journal_settings` and `journal_progress` with per-user RLS. Do not omit this step.
3. In Supabase **Authentication → Providers → Email**, enable email sign-in. If you want one-time numeric codes, in **Authentication → Email Templates → Magic Link** replace the link with `{{ .Token }}` so the email contains a code. (Dashboard labels can change.) Default Supabase Auth mail limits are small; for wider public use, configure a real SMTP provider.
4. In **Project Settings → API** (or **Connect → API keys**) copy your Project URL and **publishable / anon key**. Never use the `service_role` or secret key in this app.
5. For local development, copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and fill in the values. The real secrets file is ignored by Git.
6. Install and run:

   ```powershell
   python -m pip install -r requirements.txt
   python -m streamlit run app.py
   ```

7. Commit the updated `app.py`, `requirements.txt`, `schema.sql`, `README.md`, and `.gitignore` to your existing GitHub repository. Add these values in **Streamlit Community Cloud → app → Settings → Secrets** instead of committing them:

   ```toml
   supabase_url = "https://YOUR_PROJECT.supabase.co"
   supabase_anon_key = "YOUR_PUBLISHABLE_OR_ANON_KEY"
   ```

8. Reboot/redeploy the app, then send a login code to your own email and sign in. Sign in separately from any other email to test isolation. You can import your old CSV under **Export and restore** after logging in.

## How privacy works

- Logged-out visitors only see hardcoded **fictional demo data**. No private table is queried.
- Each account is tied to a Supabase Auth user ID, never just a user-typed email string.
- Every database request carries that signed-in user's access token. Postgres RLS checks `auth.uid() = user_id` on all reads/writes. No service-role key is used.
- Login session is kept in Streamlit's session state. You may need to log in again after closing the browser/restarting the app.
- Each user can save personal height, starting weight, goal and daily data. Those values are not published to GitHub.
- The site is **publicly reachable**, but the personal data is protected by email sign-in plus RLS. It's not a medical record system; the app operator/Supabase administrators may have database access.
- Anyone with an email can register unless you disable registrations in Supabase Auth. You can restrict signups later if desired.

## Files

- `app.py`: the web app, login and data views
- `schema.sql`: protected database tables and policies
- `.streamlit/secrets.toml.example`: safe settings template
- `requirements.txt`: Python packages

BMI uses standard WHO adult categories and is a screening measure, not a diagnosis. Plan dates currently run from 2026-10-10 through 2026-12-18.