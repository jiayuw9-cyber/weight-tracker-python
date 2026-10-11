# My Weight Journal

A simple weight-tracking web app I built with Python and Streamlit. I wanted a place to log daily progress, check off completed days, and see changes over time without using a spreadsheet.

**[Try the live app](https://weight-loss-tracker.streamlit.app/)**

The public page uses **fictional demo data**. Personal records are available after email sign-in once Supabase is configured for the deployed app.

## Features

- Daily check-ins with editable goals, actual weight, notes, and checkboxes
- Weight progress chart and check-in progress
- Automatic BMI calculation from weight (lb) and height (cm)
- WHO adult BMI categories: Underweight, Normal weight, Overweight, and Obesity
- Public demo view with sample data
- Email-code sign-in and separate personal records for each account
- CSV import and export for backups

## Built with

- **Python** — app logic and calculations
- **Streamlit** — web interface
- **Pandas** — data handling and charts
- **Supabase** — email authentication and PostgreSQL storage

## Run locally

1. Clone the repository and open the project folder:

   ```bash
   git clone https://github.com/YOUR_USERNAME/weight-tracker-python.git
   cd weight-tracker-python
   ```

   Replace `YOUR_USERNAME` with your GitHub username.

2. Install dependencies:

   ```bash
   python -m pip install -r requirements.txt
   ```

3. Run the app:

   ```bash
   python -m streamlit run app.py
   ```

4. Open the local URL shown in the terminal (usually `http://localhost:8501`). Without Supabase configuration, you can still explore the public demo.

## Set up email login

1. Create a Supabase project at [supabase.com](https://supabase.com/dashboard).
2. Run `schema.sql` in the Supabase **SQL Editor**. It creates the user-specific tables and Row Level Security (RLS) policies.
3. Enable **Email** in Supabase Authentication. For numeric email codes, update the relevant email template to contain `{{ .Token }}` instead of only a magic link.
4. Create `.streamlit/secrets.toml` using the example file `.streamlit/secrets.toml.example`:

   ```toml
   supabase_url = "https://YOUR_PROJECT.supabase.co"
   supabase_anon_key = "YOUR_PUBLISHABLE_OR_ANON_KEY"
   ```

5. Restart the app. For the deployed version, enter the same two settings under **Streamlit Community Cloud → App settings → Secrets** and restart the deployment.
6. Test two different email accounts to confirm that each account can only view and edit its own records.

**Never commit `secrets.toml`, private measurements, passwords, or a Supabase secret/service-role key.** The client uses a publishable/anon key with user-specific authentication and RLS. Before publishing, verify that `.gitignore` excludes local database and secrets files.

## Privacy notes

The demo does not read private records. After login, the app uses the account's authentication token and Supabase RLS to restrict access to the signed-in user's records. The website itself is publicly accessible; it is not a private or medically certified health service. Do not assume data isolation is verified until the two-account test succeeds.

BMI is a general screening tool, not a medical diagnosis. The sample tracking calendar currently covers October 10 – December 18, 2026.

## Project files

| File | Purpose |
| --- | --- |
| `app.py` | Main Streamlit app |
| `schema.sql` | Supabase database tables and RLS policies |
| `requirements.txt` | Python dependencies |
| `.streamlit/secrets.toml.example` | Configuration template (no actual credentials) |

## Next steps

I'd like to keep improving the UI, make the tracking dates more flexible, and add more progress summaries.