from flask import Flask, render_template, request
import pandas as pd

app = Flask(__name__)

def hms_to_seconds(t):
    try:
        h, m, s = map(int, str(t).split(":"))
        return h*3600 + m*60 + s
    except:
        return 0

def seconds_to_hms(sec):
    h = sec // 3600
    m = (sec % 3600) // 60
    s = sec % 60
    return f"{h:02}:{m:02}:{s:02}"

@app.route("/")
def home():
    return render_template("upload.html")

@app.route("/dashboard", methods=["POST"])
def dashboard():

    agent_file = request.files["agent_file"]
    cdr_file = request.files["cdr_file"]

    agent_df = pd.read_excel(agent_file, header=2)
    cdr_df = pd.read_excel(cdr_file, header=1)

    agent_df.columns = agent_df.columns.str.strip()
    cdr_df.columns = cdr_df.columns.str.strip()

    agent_df.fillna("00:00:00", inplace=True)
    cdr_df.fillna("", inplace=True)

    data = []
    total_ivr = len(cdr_df)
    total_mature = 0
    ib_total = 0

    for _, row in agent_df.iterrows():

        agent_id = str(row["Agent Name"]).strip()

        login_sec = hms_to_seconds(row["Total Login Time"])
        break_sec = (
            hms_to_seconds(row["LUNCHBREAK"]) +
            hms_to_seconds(row["SHORTBREAK"]) +
            hms_to_seconds(row["TEABREAK"])
        )
        meeting_sec = (
            hms_to_seconds(row["MEETING"]) +
            hms_to_seconds(row["SYSTEMDOWN"])
        )

        net_sec = login_sec - break_sec

        agent_calls = cdr_df[cdr_df["Username"].astype(str).str.strip() == agent_id]

        mature_calls = agent_calls[
            agent_calls["Disposition"].str.contains("callmature|transfer", case=False, na=False)
        ]

        total_call = int(len(mature_calls))
        ib = int(len(mature_calls[mature_calls["Campaign"] == "CSRINBOUND"]))
        ob = total_call - ib

        total_mature += total_call
        ib_total += ib

        talk_sec = hms_to_seconds(row["Total Talk Time"])
        aht = seconds_to_hms(talk_sec // total_call) if total_call > 0 else "00:00:00"

        data.append({
            "agent_name": agent_id,
            "full_name": row["Agent Full Name"],
            "total_login": seconds_to_hms(login_sec),
            "net_login": seconds_to_hms(net_sec),
            "total_break": seconds_to_hms(break_sec),
            "total_meeting": seconds_to_hms(meeting_sec),
            "aht": aht,
            "total_call": total_call,
            "ib": ib,
            "ob": ob,
            "net_class": "green-cell" if net_sec >= 28800 else "",
            "break_class": "red-cell" if break_sec > 2100 else "",
            "meeting_class": "red-cell" if meeting_sec > 2100 else ""
        })

    ob_total = total_mature - ib_total

    overall_aht = "00:00:00"
    if len(data) > 0:
        overall_aht = seconds_to_hms(
            sum([hms_to_seconds(x["aht"]) for x in data]) // len(data)
        )

    return render_template(
        "dashboard.html",
        data=data,
        total_ivr=total_ivr,
        total_mature=total_mature,
        ib_mature=ib_total,
        ob_mature=ob_total,
        aht=overall_aht
    )

if __name__ == "__main__":
    app.run(debug=True)
