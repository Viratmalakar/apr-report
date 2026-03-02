
from flask import Flask, render_template, request
import pandas as pd
from datetime import timedelta

app = Flask(__name__)

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

    agent_df["Total Break"] = agent_df["LUNCHBREAK"] + agent_df["SHORTBREAK"] + agent_df["TEABREAK"]
    agent_df["Total Meeting"] = agent_df["MEETING"] + agent_df["SYSTEMDOWN"]
    agent_df["Total Net Login"] = agent_df["Total Login Time"] - agent_df["Total Break"]

    agent_df["Talk_sec"] = agent_df["Total Talk Time"].apply(time_to_seconds)

    cdr_df["Disposition"] = cdr_df["Disposition"].astype(str).str.lower()

    mature = cdr_df[
        cdr_df["Disposition"].str.contains("callmature") |
        cdr_df["Disposition"].str.contains("transfer")
    ]

    total_call = mature.groupby("Username").size().reset_index(name="Total Call")

    ib_mature = mature[mature["Campaign"] == "CSRINBOUND"]         .groupby("Username").size().reset_index(name="IB Mature")

    merged = agent_df.merge(total_call, left_on="Agent Name", right_on="Username", how="left")
    merged = merged.merge(ib_mature, left_on="Agent Name", right_on="Username", how="left")

    merged["Total Call"] = merged["Total Call"].fillna(0)
    merged["IB Mature"] = merged["IB Mature"].fillna(0)
    merged["OB Mature"] = merged["Total Call"] - merged["IB Mature"]

    merged["AHT_sec"] = merged.apply(
        lambda x: x["Talk_sec"] / x["Total Call"] if x["Total Call"] > 0 else 0,
        axis=1
    )

    merged["AHT"] = merged["AHT_sec"].apply(seconds_to_hms)

    summary = {
        "total_ivr": len(cdr_df),
        "total_mature": int(merged["Total Call"].sum()),
        "ib_mature": int(merged["IB Mature"].sum()),
        "ob_mature": int(merged["OB Mature"].sum()),
        "total_talk": seconds_to_hms(merged["Talk_sec"].sum()),
        "aht": seconds_to_hms(
            merged["Talk_sec"].sum() / merged["Total Call"].sum()
            if merged["Total Call"].sum() > 0 else 0
        ),
        "login_count": merged["Agent Name"].nunique()
    }

    display_cols = [
        "Agent Name", "Agent Full Name", "Total Login Time",
        "Total Net Login", "Total Break", "Total Meeting",
        "AHT", "Total Call", "IB Mature", "OB Mature"
    ]

    table = merged[display_cols].to_dict(orient="records")

    return render_template("dashboard.html", table=table, summary=summary)

if __name__ == '__main__':
    app.run(debug=True)
