from flask import Flask, render_template, request
import pandas as pd
from datetime import timedelta
import os

app = Flask(__name__)

# ------------------ Helpers ------------------

def clean_columns(df):
    df.columns = df.columns.str.strip()
    return df

def time_to_seconds(val):
    if pd.isna(val):
        return 0
    try:
        if isinstance(val, str):
            h, m, s = map(int, val.split(":"))
            return h * 3600 + m * 60 + s
        return int(val.total_seconds())
    except:
        return 0

def seconds_to_hms(sec):
    return str(timedelta(seconds=int(sec)))

# ------------------ Routes ------------------

@app.route("/")
def upload():
    return render_template("upload.html")

@app.route("/dashboard", methods=["POST"])
def dashboard():

    agent_file = request.files.get("agent_file")
    cdr_file = request.files.get("cdr_file")

    agent_df = pd.read_excel(agent_file, header=2)
    cdr_df = pd.read_excel(cdr_file, header=1)

    agent_df = clean_columns(agent_df)
    cdr_df = clean_columns(cdr_df)

    # Fix ID format
    agent_df["Agent Name"] = agent_df["Agent Name"].astype(str).str.replace(".0","", regex=False)
    cdr_df["Username"] = cdr_df["Username"].astype(str).str.replace(".0","", regex=False)

    # Convert times
    agent_df["Login_sec"] = agent_df["Total Login Time"].apply(time_to_seconds)

    agent_df["Break_sec"] = (
        agent_df["LUNCHBREAK"].apply(time_to_seconds) +
        agent_df["SHORTBREAK"].apply(time_to_seconds) +
        agent_df["TEABREAK"].apply(time_to_seconds)
    )

    agent_df["Meeting_sec"] = (
        agent_df["MEETING"].apply(time_to_seconds) +
        agent_df["SYSTEMDOWN"].apply(time_to_seconds)
    )

    agent_df["Talk_sec"] = agent_df["Total Talk Time"].apply(time_to_seconds)

    agent_df["NetLogin_sec"] = agent_df["Login_sec"] - agent_df["Break_sec"]

    agent_df["Total Break"] = agent_df["Break_sec"].apply(seconds_to_hms)
    agent_df["Total Meeting"] = agent_df["Meeting_sec"].apply(seconds_to_hms)
    agent_df["Total Net Login"] = agent_df["NetLogin_sec"].apply(seconds_to_hms)

    # Mature calls
    cdr_df["Disposition"] = cdr_df["Disposition"].astype(str).str.lower()

    mature_df = cdr_df[
        cdr_df["Disposition"].str.contains("callmature", na=False) |
        cdr_df["Disposition"].str.contains("transfer", na=False)
    ]

    total_call = mature_df.groupby("Username").size().reset_index(name="Total Call")

    ib_call = mature_df[
        mature_df["Campaign"].astype(str).str.upper() == "CSRINBOUND"
    ].groupby("Username").size().reset_index(name="IB Mature")

    merged = agent_df.merge(total_call, left_on="Agent Name", right_on="Username", how="left")
    merged = merged.merge(ib_call, left_on="Agent Name", right_on="Username", how="left")

    merged.drop(columns=["Username_x","Username_y"], errors="ignore", inplace=True)

    merged["Total Call"] = merged["Total Call"].fillna(0).astype(int)
    merged["IB Mature"] = merged["IB Mature"].fillna(0).astype(int)
    merged["OB Mature"] = (merged["Total Call"] - merged["IB Mature"]).astype(int)

    merged["AHT_sec"] = merged.apply(
        lambda x: x["Talk_sec"]/x["Total Call"] if x["Total Call"]>0 else 0,
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
        "aht": seconds_to_hms(total_talk_sum/total_calls_sum if total_calls_sum>0 else 0),
        "login_count": merged["Agent Name"].nunique()
    }

    # Visible columns only
    table = merged[[
        "Agent Name",
        "Agent Full Name",
        "Total Login Time",
        "Total Net Login",
        "Total Break",
        "Total Meeting",
        "AHT",
        "Total Call",
        "IB Mature",
        "OB Mature",
        "NetLogin_sec",
        "Break_sec",
        "Meeting_sec"
    ]]

    return render_template("dashboard.html",
                           table=table.to_dict(orient="records"),
                           summary=summary)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
