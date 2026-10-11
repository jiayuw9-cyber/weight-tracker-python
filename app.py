"""A small daily weight tracker built with Streamlit."""

import csv
import io
import sqlite3
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import streamlit as st
#BMI status categories based on WHO standards
def get_bmi_status(bmi):
    if bmi < 18.5:
        return "Underweight"
    elif bmi < 25:
        return "Normal weight"
    elif bmi < 30:
        return "Overweight"
    else:
        return "Obesity"

# My starting plan. You can edit these values in the sidebar.
START_DATE = date(2026, 10, 10)
END_DATE = date(2026, 12, 18)
START_WEIGHT = 165.4
GOAL_WEIGHT = 144.0
HEIGHT_CM = 169.0
DB_PATH = Path(__file__).with_name("my_progress.db")

st.set_page_config(page_title="My Weight Journal", page_icon="🌷", layout="centered")
st.markdown("""
<style>
.stApp {background-color: #fffaf8;}
h1, h2, h3 {color: #694b53;}
[data-testid="stMetric"] {background: #fff0ef; border-radius: 12px; padding: 12px;}
</style>
""", unsafe_allow_html=True)


def connect():
    db = sqlite3.connect(DB_PATH)
    db.execute("""CREATE TABLE IF NOT EXISTS progress (
        day TEXT PRIMARY KEY,
        goal_lb REAL NOT NULL,
        actual_lb REAL,
        checked INTEGER NOT NULL DEFAULT 0,
        note TEXT NOT NULL DEFAULT ''
    )""")
    db.commit()
    return db


def bmi_from_lb(weight_lb, height_cm):
    return weight_lb * 0.45359237 / (height_cm / 100) ** 2


def make_dates(start, end):
    return [start + timedelta(days=i) for i in range((end - start).days + 1)]


def initial_goal(i, total, start_weight, end_weight):
    return round(start_weight + (end_weight - start_weight) * i / max(total - 1, 1), 1)


with st.sidebar:
    st.header("My settings ⚙️")
    height = st.number_input("Height (cm)", min_value=100.0, max_value=220.0, value=HEIGHT_CM, step=0.5)
    start_weight = st.number_input("Starting weight (lb)", min_value=50.0, max_value=500.0, value=START_WEIGHT, step=0.1)
    goal_weight = st.number_input("Goal weight (lb)", min_value=50.0, max_value=500.0, value=GOAL_WEIGHT, step=0.1)
    st.caption("Your height and starting goal settings apply to this session. Saved daily goals can be edited below.")

st.title("My Weight Journal")
st.write("A simple place to track my weight, one day at a time.")

conn = connect()
days = make_dates(START_DATE, END_DATE)
for i, d in enumerate(days):
    conn.execute(
        "INSERT OR IGNORE INTO progress (day, goal_lb) VALUES (?, ?)",
        (d.isoformat(), initial_goal(i, len(days), start_weight, goal_weight)),
    )
conn.commit()

records = pd.read_sql_query("SELECT * FROM progress ORDER BY day", conn)
records["day"] = pd.to_datetime(records["day"]).dt.date
actuals = records.dropna(subset=["actual_lb"])
current_weight = float(actuals.iloc[-1]["actual_lb"]) if not actuals.empty else start_weight
checked_count = int(records["checked"].sum())

m1, m2, m3 = st.columns(3)
m1.metric("Latest weight", f"{current_weight:.1f} lb")
m2.metric("BMI", f"{bmi_from_lb(current_weight, height):.1f}")
m3.metric("Checked days", f"{checked_count}/{len(records)}")
st.progress(checked_count / len(records))
st.caption("BMI is just a general screening number. It doesn't measure body composition or health on its own.")

# BMI health status
bmi = bmi_from_lb(current_weight, height)
status = get_bmi_status(bmi)

st.subheader("BMI Health Status")
st.write(f"Your BMI: {bmi:.1f}")
st.write(f"Category: {status}")

st.write("WHO Adult BMI Classification")

st.write("Underweight: Below 18.5")
st.write("Normal weight: 18.5 - 24.9")
st.write("Overweight: 25.0 - 29.9")
st.write("Obesity: 30.0 or higher")

st.subheader("Daily check-in")
week_count = (len(days) + 6) // 7
week = st.selectbox("Choose a week", range(week_count), format_func=lambda x: f"Week {x + 1} · {days[x * 7]:%m/%d} – {days[min(x * 7 + 6, len(days) - 1)]:%m/%d}")
week_days = days[week * 7: (week + 1) * 7]

for d in week_days:
    row = records.loc[records["day"] == d].iloc[0]
    with st.expander(f"{d:%a, %b %d}" + (" ✅" if row["checked"] else ""), expanded=(d == date.today())):
        with st.form(f"form_{d.isoformat()}"):
            checked = st.checkbox("Done for today", value=bool(row["checked"]))
            c1, c2 = st.columns(2)
            goal = c1.number_input("Goal (lb)", min_value=50.0, max_value=500.0, value=float(row["goal_lb"]), step=0.1, key=f"goal_{d}")
            old_actual = None if pd.isna(row["actual_lb"]) else float(row["actual_lb"])
            actual_text = c2.text_input("Actual weight (lb)", value="" if old_actual is None else str(old_actual), placeholder="e.g. 165.0", key=f"actual_{d}")
            note = st.text_input("Note (optional)", value=str(row["note"]), key=f"note_{d}")
            if st.form_submit_button("Save this day 💗"):
                try:
                    actual = None if not actual_text.strip() else float(actual_text)
                    if actual is not None and not (50 <= actual <= 500):
                        raise ValueError
                except ValueError:
                    st.error("Please enter a valid weight in pounds, or leave it blank.")
                else:
                    conn.execute(
                        "UPDATE progress SET goal_lb=?, actual_lb=?, checked=?, note=? WHERE day=?",
                        (goal, actual, int(checked), note, d.isoformat()),
                    )
                    conn.commit()
                    st.rerun()

st.subheader("My progress")
chart = records.set_index("day")[["goal_lb", "actual_lb"]].rename(columns={"goal_lb": "Goal", "actual_lb": "Actual"})
st.line_chart(chart)
if not actuals.empty:
    last7 = actuals.tail(7)["actual_lb"].mean()
    st.write(f"Average of my latest {min(7, len(actuals))} weigh-ins: **{last7:.1f} lb**")

st.subheader("Back up my data")
st.caption("The SQLite database saves records on the computer running this app. Cloud hosts may erase local files when restarting, so keep a CSV backup.")
backup = records.copy()
backup["day"] = backup["day"].astype(str)
st.download_button("Download CSV backup", backup.to_csv(index=False).encode("utf-8-sig"), "weight_journal_backup.csv", "text/csv")
upload = st.file_uploader("Restore a CSV backup", type="csv")
if upload is not None and st.button("Import backup"):
    try:
        imported = pd.read_csv(upload).fillna("")
        required = {"day", "goal_lb", "actual_lb", "checked", "note"}
        if not required.issubset(imported.columns):
            raise ValueError("Missing columns")
        valid_dates = {d.isoformat() for d in days}
        imported_rows = []
        for _, r in imported.iterrows():
            day = str(r["day"])
            if day not in valid_dates:
                continue
            goal = float(r["goal_lb"])
            actual = None if str(r["actual_lb"]).strip() == "" else float(r["actual_lb"])
            checked = int(r["checked"])
            if not (50 <= goal <= 500) or (actual is not None and not 50 <= actual <= 500) or checked not in (0, 1):
                raise ValueError("Invalid values")
            imported_rows.append((day, goal, actual, checked, str(r["note"])[:500]))
        if not imported_rows:
            raise ValueError("No matching dates")
        with conn:
            conn.executemany("INSERT OR REPLACE INTO progress(day, goal_lb, actual_lb, checked, note) VALUES (?, ?, ?, ?, ?)", imported_rows)
        st.success("Backup imported!")
        st.rerun()
    except (ValueError, KeyError, TypeError):
        st.error("This backup file isn't valid. Please use a CSV exported from this app.")

st.divider()
st.caption("Made with Python + Streamlit · Data is stored locally, not automatically in GitHub.")
conn.close()
