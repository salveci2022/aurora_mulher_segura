from __future__ import annotations
from flask import Flask, render_template, request, jsonify, redirect, session, send_file
from flask_cors import CORS
from datetime import datetime
import os
import json
from pathlib import Path
from fpdf import FPDF
import tempfile
import pytz

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = "aurora_secure_2026"
CORS(app)

BR_TZ = pytz.timezone('America/Sao_Paulo')

BASE_DIR = Path(__file__).resolve().parent
USERS_FILE = BASE_DIR / "users.json"
ALERTS_FILE = BASE_DIR / "alerts.log"
STATE_FILE = BASE_DIR / "state.json"


# ===============================
# CRIAR ARQUIVOS
# ===============================
def ensure_files():

    if not USERS_FILE.exists():
        USERS_FILE.write_text(json.dumps({
            "admin": {
                "password": "admin123",
                "role": "admin",
                "name": "Administrador"
            }
        }, indent=2, ensure_ascii=False), encoding="utf-8")

    if not ALERTS_FILE.exists():
        ALERTS_FILE.write_text("", encoding="utf-8")

    if not STATE_FILE.exists():
        STATE_FILE.write_text(json.dumps({"last_id": 0}), encoding="utf-8")


# ===============================
# UTILIDADES
# ===============================
def load_users():
    ensure_files()
    return json.loads(USERS_FILE.read_text(encoding="utf-8"))


def save_users(data):
    USERS_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def next_alert_id():

    state = json.loads(STATE_FILE.read_text())

    state["last_id"] += 1

    STATE_FILE.write_text(json.dumps(state))

    return state["last_id"]


def save_alert(alert):

    with open(ALERTS_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(alert, ensure_ascii=False) + "\n")


def get_all_alerts():

    alerts = []

    if ALERTS_FILE.exists():

        with open(ALERTS_FILE, "r", encoding="utf-8") as f:

            for line in f:

                if line.strip():
                    alerts.append(json.loads(line))

    return alerts


def get_last_alert():

    alerts = get_all_alerts()

    if alerts:
        return alerts[-1]

    return None


# ===============================
# PAGINAS
# ===============================
@app.route("/")
def index():
    return render_template("termo_responsabilidade.html")


@app.route("/panic")
def panic():
    return render_template("panic_button.html")


@app.route("/ajuda")
def ajuda():
    return render_template("ajuda.html")


@app.route("/plano-seguranca")
def plano():
    return render_template("plano_seguranca.html")


@app.route("/saida-rapida")
def saida():
    return render_template("saida_rapida.html")


# ===============================
# API ALERTA
# ===============================
@app.route("/api/send_alert", methods=["POST"])
def send_alert():

    data = request.get_json()

    now = datetime.now(BR_TZ)

    alert = {
        "id": next_alert_id(),
        "ts": now.strftime("%Y-%m-%d %H:%M:%S"),
        "ts_br": now.strftime("%d/%m/%Y %H:%M:%S"),
        "name": data.get("name", "Usuária"),
        "situation": data.get("situation"),
        "message": data.get("message"),
        "location": data.get("location")
    }

    save_alert(alert)

    return jsonify({"ok": True})


@app.route("/api/last_alert")
def last_alert():

    alert = get_last_alert()

    return jsonify({"ok": True, "last": alert})


# ===============================
# ADMIN
# ===============================
@app.route("/panel/login", methods=["GET","POST"])
def admin_login():

    users = load_users()

    error = False

    if request.method == "POST":

        u = request.form.get("user")

        p = request.form.get("password")

        info = users.get(u)

        if info and info["password"] == p and info["role"] == "admin":

            session["role"] = "admin"

            return redirect("/panel")

        error = True

    return render_template("login_admin.html", error=error)


@app.route("/panel")
def admin_panel():

    if session.get("role") != "admin":
        return redirect("/panel/login")

    alerts = get_all_alerts()

    users = load_users()

    trusted = {k:v for k,v in users.items() if v.get("role")=="trusted"}

    return render_template("panel_admin.html",
                           alerts=alerts,
                           trusted=trusted)


# ===============================
# TRUSTED
# ===============================
@app.route("/trusted")
def trusted_panel():

    users = load_users()

    trusted = [v for v in users.values() if v.get("role")=="trusted"]

    if not trusted:
        return "Nenhuma pessoa de confiança cadastrada"

    name = trusted[0]["name"]

    return render_template("panel_trusted.html", display_name=name)


@app.route("/trusted/login")
def trusted_login():
    return redirect("/trusted")


# ===============================
# PDF
# ===============================
@app.route("/relatorio/pdf")
def relatorio():

    alerts = get_all_alerts()

    pdf = FPDF()

    pdf.add_page()

    pdf.set_font("Arial","B",16)

    pdf.cell(0,10,"RELATORIO DE ALERTAS",ln=1)

    pdf.set_font("Arial","",12)

    for a in alerts:

        pdf.cell(0,8,f"{a['ts_br']} - {a['name']} - {a['situation']}",ln=1)

    temp = tempfile.NamedTemporaryFile(delete=False,suffix=".pdf")

    pdf.output(temp.name)

    return send_file(temp.name,as_attachment=True)


# ===============================
# START
# ===============================
if __name__ == "__main__":

    ensure_files()

    port = int(os.environ.get("PORT",5000))

    print("🚀 Aurora iniciado")

    app.run(host="0.0.0.0",port=port,debug=True)