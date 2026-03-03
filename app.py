from flask import Flask, render_template, request
import pandas as pd

app = Flask(__name__)


# ✅ SAFE TIME CONVERSION FUNCTION (NO CRASH VERSION)
def hms_to_seconds(time_str):

    if pd.isna(time_str):
        return 0

    time_str = str(time_str).strip()

    # Handle dash / blank / nan
    if time_str in ["-", "", "nan", "NaN", "None"]:
        return 0

    # If already numeric
    if isinstance(time_str, (int, float)):
        return int(time_str)

    try:
        parts = time_str.split(":")
        if len(parts) != 3:
            return 0

        h, m, s = map(int, parts)
        return h * 3600 + m * 60 + s
    except:
        return 0


def seconds_to_hms(seconds):
    seconds = int(seconds)
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02}:{m:02}:{s:02}"


@app.route("/")
def home():
    return render_template("upload.html")


@app.route("/dashboard", methods=["POST"])
def dashboard():

    agent_file = request.files["agent_file"]
    cdr_file = request.files["cdr_file"]

    # Read files
    agent_df = pd.read_excel(agent_file, header=2)
    cdr_df = pd.read_excel(cdr_file, header=1)

    # Clean column names
    agent_df.columns = agent_df.columns.str.strip()
    cdr_df.columns = cdr_df.columns.str.strip()

    # Replace "-" with 0 for safety
    agent_df.replace("-", "00:00:00", inplace=True)

    agent_df.fillna("00:00:00", inplace=True)
    cdr_df.fillna("", inplace=True)

    data = []

    total_ivr = len(cdr_df)
    total_mature = 0
    ib_total = 0

    # Convert Username to string once
    cdr_df["Username"] = cdr_df["Username"].astype(str).str.strip()

    for _, row in agent_df.iterrows():

        agent_id = str(row["Agent Name"]).strip()

        # ---- TIME CALCULATIONS ----
        login_sec = hms_to_seconds(row["Total Login Time"])

        break_sec = (
            hms_to_seconds(row.get("LUNCHBREAK", 0)) +
            hms_to_seconds(row.get("SHORTBREAK", 0)) +
            hms_to_seconds(row.get("TEABREAK", 0))
        )

        meeting_sec = (
            hms_to_seconds(row.get("MEETING", 0)) +
            hms_to_seconds(row.get("SYSTEMDOWN", 0))
        )

        net_sec = login_sec - break_sec

        # ---- CDR MATCHING (FIX FOR NUMERIC + TEXT ID ISSUE) ----
        agent_calls = cdr_df[cdr_df["Username"] == agent_id]

        mature_calls = agent_calls[
            agent_calls["Disposition"].astype(str).str.contains(
                "callmature|transfer", case=False, na=False
            )
        ]

        total_call = int(len(mature_calls))

        ib = int(
            len(
                mature_calls[
                    mature_calls["Campaign"].astype(str)
                    .str.strip()
                    .str.upper() == "CSRINBOUND"
                ]
            )
        )

        ob = total_call - ib

        total_mature += total_call
        ib_total += ib

        # ---- AHT CALCULATION ----
        talk_sec = hms_to_seconds(row.get("Total Talk Time", 0))

        if total_call > 0:
            aht = seconds_to_hms(talk_sec // total_call)
        else:
            aht = "00:00:00"

        data.append({
            "agent_name": agent_id,
            "full_name": row.get("Agent Full Name", ""),
            "total_login": seconds_to_hms(login_sec),
            "net_login": seconds_to_hms(net_sec),
            "total_break": seconds_to_hms(break_sec),
            "total_meeting": seconds_to_hms(meeting_sec),
            "aht": aht,
            "total_call": total_call,
            "ib": ib,
            "ob": ob,

            # ✅ CONDITIONAL FORMATTING RULES
            "net_class": "green-cell" if net_sec >= 28800 else "",  # 8 hours
            "break_class": "red-cell" if break_sec > 2100 else "",  # 35 min
            "meeting_class": "red-cell" if meeting_sec > 2100 else ""
        })

    ob_total = total_mature - ib_total

    # ---- OVERALL AHT ----
    overall_aht = "00:00:00"

    if len(data) > 0:
        total_aht_sec = sum([hms_to_seconds(x["aht"]) for x in data])
        overall_aht = seconds_to_hms(total_aht_sec // len(data))

    return render_template(
        "dashboard.html",
        data=data,
        total_ivr=int(total_ivr),
        total_mature=int(total_mature),
        ib_mature=int(ib_total),
        ob_mature=int(ob_total),
        aht=overall_aht
    )


if __name__ == "__main__":
    app.run(debug=True)
