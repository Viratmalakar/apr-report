from flask import Flask, render_template, request, send_file
import pandas as pd
from datetime import datetime
import io

app = Flask(__name__)

# ================= TIME FUNCTIONS =================

def hms_to_seconds(time_str):
    if pd.isna(time_str):
        return 0
    time_str = str(time_str).strip()
    if time_str in ["-", "", "nan", "NaN", "None"]:
        return 0
    try:
        h, m, s = map(int, time_str.split(":"))
        return h*3600 + m*60 + s
    except:
        return 0


def seconds_to_hms(seconds):
    seconds = int(seconds)
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02}:{m:02}:{s:02}"


# ================= ROUTES =================

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

    agent_df.replace("-", "00:00:00", inplace=True)
    agent_df.fillna("00:00:00", inplace=True)
    cdr_df.fillna("", inplace=True)

    # ================= IVR HIT LOGIC =================
    total_ivr = len(
        cdr_df[
            cdr_df["Skill"].astype(str).str.strip().str.upper() == "INBOUND"
        ]
    )

    data = []
    total_mature = 0
    ib_total = 0

    for _, row in agent_df.iterrows():

        agent_id = str(row["Agent Name"]).strip()

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

        agent_calls = cdr_df[
            cdr_df["Username"].astype(str).str.strip() == agent_id
        ]

        mature_calls = agent_calls[
            agent_calls["Disposition"].astype(str).str.contains(
                "callmature|transfer", case=False, na=False
            )
        ]

        total_call = len(mature_calls)

        ib = len(
            mature_calls[
                mature_calls["Campaign"].astype(str).str.upper() == "CSRINBOUND"
            ]
        )

        ob = total_call - ib

        total_mature += total_call
        ib_total += ib

        talk_sec = hms_to_seconds(row.get("Total Talk Time", 0))
        aht = seconds_to_hms(talk_sec // total_call) if total_call > 0 else "00:00:00"

        data.append({
            "Agent Name": agent_id,
            "Agent Full Name": row.get("Agent Full Name", ""),
            "Total Login": seconds_to_hms(login_sec),
            "Net Login": seconds_to_hms(net_sec),
            "Total Break": seconds_to_hms(break_sec),
            "Total Meeting": seconds_to_hms(meeting_sec),
            "AHT": aht,
            "Total Call": total_call,
            "IB Mature": ib,
            "OB Mature": ob,
            "net_sec": net_sec,
            "break_sec": break_sec,
            "meeting_sec": meeting_sec
        })

    # Sort by total calls then net login
    data = sorted(data, key=lambda x: (x["Total Call"], x["net_sec"]), reverse=True)

    global last_export_data
    last_export_data = data

    ob_total = total_mature - ib_total

    overall_aht = "00:00:00"
    if len(data) > 0:
        overall_aht = seconds_to_hms(
            sum([hms_to_seconds(x["AHT"]) for x in data]) // len(data)
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


# ================= EXCEL EXPORT =================

@app.route("/export_excel")
def export_excel():

    df = pd.DataFrame(last_export_data)
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_export = df.drop(columns=["net_sec", "break_sec", "meeting_sec"])
        df_export.to_excel(writer, index=False, sheet_name="Report")

        workbook = writer.book
        sheet = writer.sheets["Report"]

        from openpyxl.styles import Font, Alignment, Border, Side
        from openpyxl.styles.fills import GradientFill

        header_fill = GradientFill(stop=("FFF3B0", "D4AF37"))
        green_fill = GradientFill(stop=("2ECC71", "145A32"))
        red_fill = GradientFill(stop=("E74C3C", "641E16"))

        thick = Side(border_style="medium", color="000000")
        border = Border(left=thick, right=thick, top=thick, bottom=thick)

        for cell in sheet[1]:
            cell.fill = header_fill
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = border

        for row in sheet.iter_rows(min_row=2):
            for cell in row:
                cell.alignment = Alignment(horizontal="center", vertical="center")
                cell.border = border

        for i, row in enumerate(last_export_data, start=2):

            if row["net_sec"] >= 28800:
                sheet[f"D{i}"].fill = green_fill

            if row["break_sec"] > 2100:
                sheet[f"E{i}"].fill = red_fill

            if row["meeting_sec"] > 2100:
                sheet[f"F{i}"].fill = red_fill

        for col in sheet.columns:
            max_length = 0
            col_letter = col[0].column_letter
            for cell in col:
                if cell.value:
                    max_length = max(max_length, len(str(cell.value)))
            sheet.column_dimensions[col_letter].width = max_length + 4

    output.seek(0)

    filename = f"Agent_Performance_Report_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.xlsx"

    return send_file(
        output,
        as_attachment=True,
        download_name=filename,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


if __name__ == "__main__":
    app.run(debug=True)
