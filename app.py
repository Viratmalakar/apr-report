from flask import Flask, render_template, request
import pandas as pd
import os

app = Flask(__name__, static_url_path='/static', static_folder='static', template_folder='templates')

def seconds_to_hms(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h:02}:{m:02}:{s:02}"

def hms_to_seconds(time_str):
    h, m, s = map(int, time_str.split(":"))
    return h*3600 + m*60 + s

@app.route('/')
def home():
    return render_template("upload.html")

@app.route('/dashboard', methods=['POST'])
def dashboard():

    agent_file = request.files['agent_file']
    cdr_file = request.files['cdr_file']

    agent_df = pd.read_excel(agent_file, header=2)
    cdr_df = pd.read_excel(cdr_file, header=1)

    agent_df.columns = agent_df.columns.str.strip()
    cdr_df.columns = cdr_df.columns.str.strip()

    agent_df.fillna(0, inplace=True)
    cdr_df.fillna("", inplace=True)

    # Convert time columns
    for col in ["Total Login Time","Total Talk Time","LUNCHBREAK","SHORTBREAK","TEABREAK","MEETING","SYSTEMDOWN"]:
        agent_df[col] = agent_df[col].astype(str)

    data = []
    total_ivr = len(cdr_df)
    total_mature = 0
    ib_mature = 0

    for _, row in agent_df.iterrows():

        agent_id = str(row["Agent Name"]).strip()

        login_sec = hms_to_seconds(row["Total Login Time"])
        break_sec = hms_to_seconds(row["LUNCHBREAK"]) + \
                    hms_to_seconds(row["SHORTBREAK"]) + \
                    hms_to_seconds(row["TEABREAK"])

        meeting_sec = hms_to_seconds(row["MEETING"]) + \
                      hms_to_seconds(row["SYSTEMDOWN"])

        net_sec = login_sec - break_sec
        talk_sec = hms_to_seconds(row["Total Talk Time"])

        agent_calls = cdr_df[cdr_df["Username"].astype(str).str.strip() == agent_id]

        mature_calls = agent_calls[
            agent_calls["Disposition"].str.contains("callmature|transfer", case=False, na=False)
        ]

        total_call = len(mature_calls)
        ib = len(mature_calls[mature_calls["Campaign"] == "CSRINBOUND"])
        ob = total_call - ib

        total_mature += total_call
        ib_mature += ib

        aht = seconds_to_hms(talk_sec//total_call) if total_call > 0 else "00:00:00"

        data.append({
            "agent_name": agent_id,
            "full_name": row["Agent Full Name"],
            "total_login": seconds_to_hms(login_sec),
            "net_login": seconds_to_hms(net_sec),
            "total_break": seconds_to_hms(break_sec),
            "total_meeting": seconds_to_hms(meeting_sec),
            "aht": aht,
            "total_call": int(total_call),
            "ib": int(ib),
            "ob": int(ob),
            "net_class": "green-cell" if net_sec >= 28800 else "",
            "break_class": "red-cell" if break_sec > 2100 else "",
            "meeting_class": "red-cell" if meeting_sec > 2100 else ""
        })

    ob_mature = total_mature - ib_mature
    overall_aht = seconds_to_hms(
        sum([hms_to_seconds(x["aht"]) for x in data]) // len(data)
    ) if data else "00:00:00"

    return render_template(
        "dashboard.html",
        data=data,
        total_ivr=total_ivr,
        total_mature=total_mature,
        ib_mature=ib_mature,
        ob_mature=ob_mature,
        aht=overall_aht
    )

if __name__ == "__main__":
    app.run(debug=True)
