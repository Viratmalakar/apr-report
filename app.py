from flask import Flask, render_template, request
import pandas as pd
from datetime import timedelta

app = Flask(__name__)

# -----------------------
# Utility Functions
# -----------------------

def clean_columns(df):
    df.columns = df.columns.str.strip()
    return df

def time_to_seconds(t):
    if pd.isna(t):
        return 0
    if isinstance(t, str):
        try:
            h, m, s = map(int, t.split(":"))
            return h*3600 + m*60 + s
        except:
            return 0
    if hasattr(t, "total_seconds"):
        return int(t.total_seconds())
    return 0

def seconds_to_hms(seconds):
    return str(timedelta(seconds=int(seconds)))

# -----------------------
# Routes
# -----------------------

@app.route('/')
def upload():
    return render_template("upload.html")

@app.route('/dashboard', methods=['POST'])
def dashboard():

    agent_file = request.files['agent_file']
    cdr_file = request.files['cdr_file']

    # Header rows fixed
    agent_df = pd.read_excel(agent_file, header=2)
    cdr_df = pd.read_excel(cdr_file, header=1)

    agent_df = clean_columns(agent_df)
    cdr_df = clean_columns(cdr_df)

    # FIX: ID numeric/text issue
    agent_df["Agent Name"] = agent_df["Agent Name"].astype(str).str.strip()
    cdr_df["Username"] = cdr_df["Username"].astype(str).str.strip()

    agent_df["Agent Name"] = agent_df["Agent Name"].str.replace(".0","", regex=False)
    cdr_df["Username"] = cdr_df["Username"].str.replace(".0","", regex=False)

    # -----------------------
    # Time Conversion
    # -----------------------

    agent_df["Login_sec"] = agent_df["Total Login Time"].apply(time_to_seconds)
    agent_df["Lunch_sec"] = agent_df["LUNCHBREAK"].apply(time_to_seconds)
    agent_df["Short_sec"] = agent_df["SHORTBREAK"].apply(time_to_seconds)
    agent_df["Tea_sec"] = agent_df["TEABREAK"].apply(time_to_seconds)
    agent_df["Meeting_sec"] = agent_df["MEETING"].apply(time_to_seconds)
    agent_df["System_sec"] = agent_df["SYSTEMDOWN"].apply(time_to_seconds)
    agent_df["Talk_sec"] = agent_df["Total Talk Time"].apply(time_to_seconds)

    # Calculations
    agent_df["Total Break_sec"] = (
        agent_df["Lunch_sec"] +
        agent_df["Short_sec"] +
        agent_df["Tea_sec"]
    )

    agent_df["Total Meeting_sec"] = (
        agent_df["Meeting_sec"] +
        agent_df["System_sec"]
    )

    agent_df["Total Net Login_sec"] = (
        agent_df["Login_sec"] -
        agent_df["Total Break_sec"]
    )

    # Convert back to hh:mm:ss
    agent_df["Total Break"] = agent_df["Total Break_sec"].apply(seconds_to_hms)
    agent_df["Total Meeting"] = agent_df["Total Meeting_sec"].apply(seconds_to_hms)
    agent_df["Total Net Login"] = agent_df["Total Net Login_sec"].apply(seconds_to_hms)

    # -----------------------
    # CDR Processing
    # -----------------------

    cdr_df["Disposition"] = cdr_df["Disposition"].astype(str).str.lower()

    mature = cdr_df[
        cdr_df["Disposition"].str.contains("callmature", na=False) |
        cdr_df["Disposition"].str.contains("transfer", na=False)
    ]

    total_call = mature.groupby("Username").size().reset_index(name="Total Call")

    ib_mature = mature[
        mature["Campaign"].astype(str).str.upper() == "CSRINBOUND"
    ].groupby("Username").size().reset_index(name="IB Mature")

    merged = agent_df.merge(
        total_call,
        left_on="Agent Name",
        right_on="Username",
        how="left"
    )

    merged = merged.merge(
        ib_mature,
        left_on="Agent Name",
        right_on="Username",
        how="left"
    )

    merged["Total Call"] = merged["Total Call"].fillna(0)
    merged["IB Mature"] = merged["IB Mature"].fillna(0)
    merged["OB Mature"] = merged["Total Call"] - merged["IB Mature"]

    # AHT
    merged["AHT_sec"] = merged.apply(
        lambda x: x["Talk_sec"] / x["Total Call"]
        if x["Total Call"] > 0 else 0,
        axis=1
    )

    merged["AHT"] = merged["AHT_sec"].apply(seconds_to_hms)

    # Summary
    total_calls_sum = merged["Total Call"].sum()
    total_talk_sum = merged["Talk_sec"].sum()

    summary = {
        "total_ivr": len(cdr_df),
        "total_mature": int(total_calls_sum),
        "ib_mature": int(merged["IB Mature"].sum()),
        "ob_mature": int(merged["OB Mature"].sum()),
        "total_talk": seconds_to_hms(total_talk_sum),
        "aht": seconds_to_hms(
            total_talk_sum / total_calls_sum
            if total_calls_sum > 0 else 0
        ),
        "login_count": merged["Agent Name"].nunique()
    }

    display_cols = [
        "Agent Name",
        "Agent Full Name",
        "Total Login Time",
        "Total Net Login",
        "Total Break",
        "Total Meeting",
        "AHT",
        "Total Call",
        "IB Mature",
        "OB Mature"
    ]

    table = merged[display_cols].to_dict(orient="records")

    return render_template("dashboard.html", table=table, summary=summary)

if __name__ == '__main__':
    app.run(debug=True)
