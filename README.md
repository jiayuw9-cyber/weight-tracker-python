# My Weight Journal

A small daily weight tracker I made with Python and Streamlit.

## Features
- Daily checkboxes and editable goals
- Actual weight and optional notes
- Automatic BMI calculation (height starts at 169 cm, but it's editable)
- Weight progress chart
- SQLite saving + CSV export/import

## Run on my computer

1. Install Python 3.10 or newer.
2. Open this folder in VS Code.
3. Open the Terminal and run:

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Streamlit will open a local web page. My daily check-ins are saved in `my_progress.db` in this folder.

## Put it on GitHub

Create a new repository, then upload `app.py`, `requirements.txt`, `README.md`, and `.gitignore`.
**Do not upload `my_progress.db` or any real weight CSV backups.** They are excluded by `.gitignore`.

## Publish online (optional)

GitHub stores the code; GitHub Pages **cannot run Python apps**. You can deploy this repository using [Streamlit Community Cloud](https://share.streamlit.io/): select the repository and set the main file to `app.py`.

**Privacy warning:** this app has no login. Do not publish it as a public Streamlit site with real personal records. A private GitHub repository alone does not password-protect a deployed site. Streamlit Community Cloud's local SQLite file is also not permanent storage and may reset. For a genuinely private synced app, add authentication and persistent database storage first. For now, running it locally is the simplest privacy-first choice; export a CSV as a backup.

## About BMI

BMI = kilograms / meters². It's a screening statistic, not a complete picture of health.

## Notes

The initial schedule is October 10 – December 18, 2026, and the suggested goal line is only a reference. You can change each daily goal, and there is no need to chase a specific daily number.
