from flask import Flask, render_template, request
import pandas as pd
from datetime import timedelta

app = Flask(__name__)

def clean_columns(df):
    df.columns = df.columns.str.strip()
    df.columns = df.columns.str.replace(" ", "")
    return df

def time_to_seconds(t):
    if pd.isna(t):
        return 0
    if isinstance(t, str):
        h, m, s = map(int, t.split(":"))
        return h*3600 + m*60 + s
    return int(t.total_seconds())

def seconds_to_hms(seconds):
    return str(timedelta(seconds=int(seconds)))

@app.route('/')
def upload():
    return render_template("upload.html")

@app.route('/dashboard', methods=['POST'])
def dashboard():

    agent_file = request.files['agent_file']
    cdr_file = request.files['cdr_file']

    agent_df = pd.read_excel(agent_file)
    cdr_df = pd.read_excel(cdr_file)

    agent_df = clean_columns(agent_df)
    cdr_df = clean_columns(cdr_df)

    # ---- Agent Calculations ----
    agent_df["TotalBreak"] = (
        agent_df.get("LUNCHBREAK",0) +
        agent_df.get("SHORTBREAK",0) +
        agent_df.get("TEABREAK",0)
    )

    agent_df["TotalMeeting"] = (
        agent_df.get("MEETING",0) +
        agent_df.get("SYSTEMDOWN",0)
    )

    agent_df["TotalNetLogin"] = agent_df["TotalLoginTime"] - agent_df["TotalBreak"]

    agent_df["Talk_sec"] = agent_df["TotalTalkTime"].apply(time_to_seconds)

    # ---- CDR Calculations ----
    cdr_df["Disposition"] = cdr_df["Disposition"].astype(str).str.lower()

    mature = cdr_df[
        cdr_df["Disposition"].str.contains("callmature", na=False) |
        cdr_df["Disposition"].str.contains("transfer", na=False)
    ]

    total_call = mature.groupby("Username").size().reset_index(name="TotalCall")

    ib_mature = mature[
        mature["Campaign"].str.upper() == "CSRINBOUND"
    ].groupby("Username").size().reset_index(name="IBMature")

    merged = agent_df.merge(total_call, left_on="AgentName", right_on="Username", how="left")
    merged = merged.merge(ib_mature, left_on="AgentName", right_on="Username", how="left")

    merged["TotalCall"] = merged["TotalCall"].fillna(0)
    merged["IBMature"] = merged["IBMature"].fillna(0)
    merged["OBMature"] = merged["TotalCall"] - merged["IBMature"]

    merged["AHT_sec"] = merged.apply(
        lambda x: x["Talk_sec"]/x["TotalCall"] if x["TotalCall"]>0 else 0,
        axis=1
    )

    merged["AHT"] = merged["AHT_sec"].apply(seconds_to_hms)

    summary = {
        "total_ivr": len(cdr_df),
        "total_mature": int(merged["TotalCall"].sum()),
        "ib_mature": int(merged["IBMature"].sum()),
        "ob_mature": int(merged["OBMature"].sum()),
        "total_talk": seconds_to_hms(merged["Talk_sec"].sum()),
        "aht": seconds_to_hms(
            merged["Talk_sec"].sum()/merged["TotalCall"].sum()
            if merged["TotalCall"].sum()>0 else 0
        ),
        "login_count": merged["AgentName"].nunique()
    }

    display_cols = [
        "AgentName","AgentFullName","TotalLoginTime",
        "TotalNetLogin","TotalBreak","TotalMeeting",
        "AHT","TotalCall","IBMature","OBMature"
    ]

    table = merged[display_cols].to_dict(orient="records")

    return render_template("dashboard.html", table=table, summary=summary)

if __name__ == '__main__':
    app.run(debug=True)
