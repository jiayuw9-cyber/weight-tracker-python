"""A simple weight journal with a public demo and private accounts."""

from datetime import date, timedelta
import io

import pandas as pd
import requests
import streamlit as st

START_DATE = date(2026, 10, 10)
END_DATE = date(2026, 12, 18)
# These are SAMPLE values. Never put personal measurements in public code.
DEMO_HEIGHT = 165.0
DEMO_START = 160.0
DEMO_GOAL = 150.0

st.set_page_config(page_title="My Weight Journal", page_icon="🌷", layout="centered")
st.markdown("""<style>
.stApp {background-color: #fffaf8;}
h1, h2, h3 {color: #694b53;}
[data-testid="stMetric"] {background: #fff0ef; border-radius: 12px; padding: 12px;}
</style>""", unsafe_allow_html=True)


def days_in_plan():
    return [START_DATE + timedelta(days=i) for i in range((END_DATE - START_DATE).days + 1)]


def daily_goal(i, count, starting, target):
    return round(starting + (target - starting) * i / max(1, count - 1), 1)


def bmi_from_lb(weight, height_cm):
    return weight * 0.45359237 / (height_cm / 100) ** 2


def bmi_status(bmi):
    if bmi < 18.5:
        return "Underweight"
    if bmi < 25:
        return "Normal weight"
    if bmi < 30:
        return "Overweight"
    return "Obesity"


def config():
    try:
        return st.secrets["supabase_url"].rstrip("/"), st.secrets["supabase_anon_key"]
    except (KeyError, FileNotFoundError):
        return None, None


def api_request(method, endpoint, payload=None, params=None, token=None, extra_headers=None):
    """Supabase REST API. Only the signed-in person's JWT is used for private rows."""
    url, anon_key = config()
    if not url or not anon_key:
        raise RuntimeError("Supabase is not configured yet. Follow README.md first.")
    headers = {
        "apikey": anon_key,
        "Authorization": f"Bearer {token or anon_key}",
        "Content-Type": "application/json",
    }
    if extra_headers:
        headers.update(extra_headers)
    try:
        response = requests.request(method, url + endpoint, json=payload, params=params,
                                    headers=headers, timeout=15)
    except requests.RequestException as exc:
        raise RuntimeError("Unable to connect to the server. Try again.") from exc
    if not response.ok:
        # Do not show raw server details or account tokens in the UI.
        if response.status_code in (401, 403):
            raise RuntimeError("Session expired or permission denied. Please sign in again.")
        if response.status_code == 429:
            raise RuntimeError("Too many requests. Please wait and try again.")
        raise RuntimeError(f"Request failed (HTTP {response.status_code}). Check the setup and try again.")
    if not response.content:
        return None
    return response.json()


def send_code(email):
    # Email template must use {{ .Token }} in Supabase, not a magic-link button.
    api_request("POST", "/auth/v1/otp", {"email": email, "create_user": True})


def verify_code(email, code):
    session = api_request("POST", "/auth/v1/verify", {
        "email": email, "token": code, "type": "email"
    })
    if not session or not session.get("access_token") or not session.get("user", {}).get("id"):
        raise RuntimeError("Sign-in did not return a valid session.")
    return session


def session_token():
    session = st.session_state.get("session")
    if not session:
        return None
    # Refresh on rerun only when the previous access token is rejected.
    return session["access_token"]


def refresh_session():
    session = st.session_state.get("session") or {}
    if not session.get("refresh_token"):
        return False
    try:
        new_session = api_request("POST", "/auth/v1/token?grant_type=refresh_token", {
            "refresh_token": session["refresh_token"]
        })
        if new_session and new_session.get("access_token"):
            st.session_state["session"] = new_session
            return True
    except RuntimeError:
        pass
    st.session_state.pop("session", None)
    return False

def handle_magic_link():
    params = st.query_params
    code = params.get("code")

    if not code:
        return

    try:
        session = api_request(
            "POST",
            "/auth/v1/token?grant_type=pkce",
            {"auth_code": code}
        )

        if not session or not session.get("access_token"):
            raise RuntimeError("Login failed.")

        st.session_state["session"] = session
        st.session_state.pop("login_email", None)
        st.query_params.clear()
        st.rerun()

    except RuntimeError:
        st.query_params.clear()
        st.error("Sign-in link could not be verified.")


def private_request(method, table, *, params=None, payload=None, extra_headers=None):
    endpoint = f"/rest/v1/{table}"
    try:
        return api_request(method, endpoint, payload, params, session_token(), extra_headers)
    except RuntimeError as exc:
        if "Session expired" in str(exc) and refresh_session():
            return api_request(method, endpoint, payload, params, session_token(), extra_headers)
        raise


def get_private_settings(user_id):
    rows = private_request("GET", "journal_settings", params={
        "select": "height_cm,start_weight,goal_weight", "user_id": f"eq.{user_id}"
    })
    if rows:
        return rows[0]
    return {"height_cm": DEMO_HEIGHT, "start_weight": DEMO_START, "goal_weight": DEMO_GOAL}


def save_private_settings(user_id, height, starting, target):
    private_request("POST", "journal_settings", payload={
        "user_id": user_id, "height_cm": height,
        "start_weight": starting, "goal_weight": target
    }, extra_headers={"Prefer": "resolution=merge-duplicates,return=minimal"})


def load_private_records(user_id):
    return private_request("GET", "journal_progress", params={
        "select": "day,goal_lb,actual_lb,checked,note", "user_id": f"eq.{user_id}", "order": "day.asc"
    }) or []


def save_private_day(user_id, record):
    private_request("POST", "journal_progress", payload={"user_id": user_id, **record},
                    extra_headers={"Prefer": "resolution=merge-duplicates,return=minimal"})


def make_table(height, starting, target, stored_rows):
    all_days = days_in_plan()
    stored = {r["day"]: r for r in stored_rows}
    rows = []
    for i, d in enumerate(all_days):
        day = d.isoformat()
        record = stored.get(day, {})
        rows.append({
            "day": day, "goal_lb": float(record.get("goal_lb", daily_goal(i, len(all_days), starting, target))),
            "actual_lb": record.get("actual_lb"), "checked": bool(record.get("checked", False)),
            "note": record.get("note", "")
        })
    frame = pd.DataFrame(rows)
    frame["day"] = pd.to_datetime(frame["day"]).dt.date
    return frame


def demo_rows():
    # Clearly fictional examples; no database query is made for logged-out visitors.
    return [
        {"day": "2026-10-10", "goal_lb": 160.0, "actual_lb": 160.0, "checked": True, "note": "Demo entry"},
        {"day": "2026-10-11", "goal_lb": 159.9, "actual_lb": 159.8, "checked": True, "note": "Demo entry"},
        {"day": "2026-10-12", "goal_lb": 159.7, "actual_lb": 159.9, "checked": False, "note": "Demo entry"},
    ]

handle_magic_link()
st.title("🌷 My Weight Journal")
st.write("A simple place to track weight, one day at a time.")

url, anon_key = config()
with st.sidebar:
    st.header("Account 🔐")
    if st.session_state.get("session"):
        user = st.session_state["session"].get("user", {})
        st.success(f"Signed in: {user.get('email', 'My account')}")
        if st.button("Log out"):
            st.session_state.pop("session", None)
            st.rerun()
    elif not url or not anon_key:
        st.warning("Demo mode. Add Supabase settings to enable email login.")
    else:
        with st.form("send_login_code"):
            email = st.text_input("Email address", placeholder="name@example.com")
            send = st.form_submit_button("Email me a login code")
        if send:
            if "@" not in email or len(email.strip()) > 254:
                st.error("Enter a valid email address.")
            else:
                try:
                    send_code(email.strip().lower())
                    st.session_state["login_email"] = email.strip().lower()
                    st.success("If the address can receive mail, check your inbox for a login code.")
                except RuntimeError as exc:
                    st.error(str(exc))
        if st.session_state.get("login_email"):
            with st.form("verify_login_code"):
                code = st.text_input("Code from email", placeholder="6-digit code")
                verify = st.form_submit_button("Sign in")
            if verify:
                try:
                    if not code.strip().isdigit():
                        raise RuntimeError("Enter the numeric code from your email.")
                    st.session_state["session"] = verify_code(st.session_state["login_email"], code.strip())
                    st.session_state.pop("login_email", None)
                    st.rerun()
                except RuntimeError as exc:
                    st.error(str(exc))

logged_in = bool(st.session_state.get("session"))
user_id = st.session_state["session"]["user"]["id"] if logged_in else None
if logged_in:
    try:
        settings = get_private_settings(user_id)
        stored_rows = load_private_records(user_id)
    except RuntimeError as exc:
        st.error(str(exc))
        st.stop()
    with st.sidebar:
        st.divider()
        st.header("My settings ⚙️")
        with st.form("personal_settings"):
            height = st.number_input("Height (cm)", min_value=100.0, max_value=220.0,
                                     value=float(settings["height_cm"]), step=0.5)
            starting = st.number_input("Starting weight (lb)", min_value=50.0, max_value=500.0,
                                       value=float(settings["start_weight"]), step=0.1)
            target = st.number_input("Goal weight (lb)", min_value=50.0, max_value=500.0,
                                     value=float(settings["goal_weight"]), step=0.1)
            save_settings = st.form_submit_button("Save settings")
        if save_settings:
            try:
                save_private_settings(user_id, height, starting, target)
                st.success("Settings saved!")
                st.rerun()
            except RuntimeError as exc:
                st.error(str(exc))
    st.success("Private journal · Only your signed-in account can read these entries.")
else:
    height, starting, target = DEMO_HEIGHT, DEMO_START, DEMO_GOAL
    stored_rows = demo_rows()
    st.info("Public demo with fictional sample numbers. Sign in with your email to see and edit your own private journal.")

records = make_table(height, starting, target, stored_rows)
actuals = records.dropna(subset=["actual_lb"])
current_weight = float(actuals.iloc[-1]["actual_lb"]) if not actuals.empty else starting
bmi = bmi_from_lb(current_weight, height)
checked_count = int(records["checked"].sum())

m1, m2, m3 = st.columns(3)
m1.metric("Latest weight", f"{current_weight:.1f} lb")
m2.metric("BMI", f"{bmi:.1f}")
m3.metric("Checked days", f"{checked_count}/{len(records)}")
st.progress(checked_count / len(records))
st.subheader("BMI Health Status")
st.write(f"**Category: {bmi_status(bmi)}**")
st.markdown("""**WHO Adult BMI Classification**

| BMI | Category |
|---|---|
| Below 18.5 | Underweight |
| 18.5–24.9 | Normal weight |
| 25.0–29.9 | Overweight |
| 30.0 or higher | Obesity |
""")
st.caption("BMI is a screening measure, not a medical diagnosis or a complete measure of health.")

st.subheader("📅 Daily check-in")
days = days_in_plan()
week_count = (len(days) + 6) // 7
week = st.selectbox("Choose a week", range(week_count), format_func=lambda i:
                    f"Week {i + 1} · {days[i * 7]:%m/%d} – {days[min(i * 7 + 6, len(days)-1)]:%m/%d}")

for day in days[week * 7:(week + 1) * 7]:
    row = records.loc[records["day"] == day].iloc[0]
    with st.expander(f"{day:%a, %b %d}" + (" ✅" if row["checked"] else ""), expanded=(day == date.today())):
        if not logged_in:
            st.write(f"Example goal: {row['goal_lb']:.1f} lb")
            st.caption("Sign in to check off a day, update goals or add notes.")
            continue
        with st.form(f"day_{day.isoformat()}"):
            checked = st.checkbox("Done for today", value=bool(row["checked"]))
            a, b = st.columns(2)
            goal = a.number_input("Goal (lb)", min_value=50.0, max_value=500.0,
                                  value=float(row["goal_lb"]), step=0.1)
            actual = row["actual_lb"]
            actual_text = b.text_input("Actual weight (lb)",
                                       value="" if pd.isna(actual) else str(float(actual)),
                                       placeholder="e.g. 160.0")
            note = st.text_input("Note (optional)", value=row["note"] or "")
            save = st.form_submit_button("Save this day 💗")
        if save:
            try:
                weight = None if not actual_text.strip() else float(actual_text)
                if weight is not None and not 50 <= weight <= 500:
                    raise ValueError
                save_private_day(user_id, {
                    "day": day.isoformat(), "goal_lb": goal, "actual_lb": weight,
                    "checked": checked, "note": note[:500]
                })
                st.rerun()
            except (ValueError, OverflowError):
                st.error("Enter a valid weight in pounds, or leave it blank.")
            except RuntimeError as exc:
                st.error(str(exc))

st.subheader("📈 Progress")
chart = records.set_index("day")[["goal_lb", "actual_lb"]].rename(
    columns={"goal_lb": "Goal", "actual_lb": "Actual"})
st.line_chart(chart)
if not actuals.empty:
    avg = actuals.tail(7)["actual_lb"].mean()
    st.write(f"Latest {min(7, len(actuals))} weigh-ins average: **{avg:.1f} lb**")

if logged_in:
    st.subheader("💾 Export and restore")
    st.caption("Your data is stored in your own protected Supabase rows, not in GitHub.")
    backup = records.copy()
    backup["day"] = backup["day"].astype(str)
    st.download_button("Download CSV backup", backup.to_csv(index=False).encode("utf-8-sig"),
                       "weight_journal_backup.csv", "text/csv")
    upload = st.file_uploader("Import a previous CSV backup", type="csv")
    if upload and st.button("Import CSV into my account"):
        try:
            imported = pd.read_csv(io.BytesIO(upload.getvalue())).fillna("")
            required = {"day", "goal_lb", "actual_lb", "checked", "note"}
            if not required.issubset(imported.columns):
                raise ValueError("Missing CSV columns")
            valid_days = {d.isoformat() for d in days}
            payload = []
            for _, r in imported.iterrows():
                day = str(r["day"])
                if day not in valid_days:
                    continue
                goal = float(r["goal_lb"])
                actual = None if str(r["actual_lb"]).strip() == "" else float(r["actual_lb"])
                checked = int(r["checked"])
                if not 50 <= goal <= 500 or actual is not None and not 50 <= actual <= 500 or checked not in (0, 1):
                    raise ValueError("Invalid CSV numbers")
                payload.append({"user_id": user_id, "day": day, "goal_lb": goal,
                                "actual_lb": actual, "checked": bool(checked), "note": str(r["note"])[:500]})
            if not payload:
                raise ValueError("No valid dates")
            private_request("POST", "journal_progress", payload=payload,
                            extra_headers={"Prefer": "resolution=merge-duplicates,return=minimal"})
            st.success("Backup imported!")
            st.rerun()
        except (ValueError, TypeError, OverflowError):
            st.error("Invalid CSV file. Use a backup downloaded from this app.")
        except RuntimeError as exc:
            st.error(str(exc))

st.divider()
st.caption("Made with Python + Streamlit · Public demo / private email accounts")
