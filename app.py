from __future__ import annotations
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session, send_file, make_response
from flask_cors import CORS
from datetime import datetime
import os
import json
from pathlib import Path
from fpdf import FPDF
import tempfile
import pytz

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = "aurora_v20_ultra_estavel_secure_2026"
CORS(app)

BR_TZ = pytz.timezone('America/Sao_Paulo')

BASE_DIR = Path(__file__).resolve().parent
USERS_FILE = BASE_DIR / "users.json"
ALERTS_FILE = BASE_DIR / "alerts.log"
STATE_FILE = BASE_DIR / "state.json"
TERMOS_FILE = BASE_DIR / "termos_aceitos.log"


# ==============================
# CRIA ARQUIVOS SE NÃO EXISTIREM
# ==============================
def _ensure_files():

    if not USERS_FILE.exists():
        USERS_FILE.write_text(json.dumps({
            "admin": {
                "password": "admin123",
                "role": "admin",
                "name": "Admin Aurora"
            }
        }, indent=2, ensure_ascii=False), encoding="utf-8")

    if not ALERTS_FILE.exists():
        ALERTS_FILE.write_text("", encoding="utf-8")

    if not STATE_FILE.exists():
        STATE_FILE.write_text(json.dumps({"last_id": 0}, indent=2), encoding="utf-8")

    if not TERMOS_FILE.exists():
        TERMOS_FILE.write_text("", encoding="utf-8")


# ==============================
# USUÁRIOS
# ==============================
def load_users():
    _ensure_files()
    try:
        return json.loads(USERS_FILE.read_text(encoding="utf-8"))
    except:
        return {}


def save_users(data):
    USERS_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


# ==============================
# ALERTAS
# ==============================
def _get_next_alert_id():

    st = json.loads(STATE_FILE.read_text())
    st["last_id"] += 1

    STATE_FILE.write_text(json.dumps(st, indent=2))

    return st["last_id"]


def log_alert(payload):

    with ALERTS_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")


def read_last_alert():

    if not ALERTS_FILE.exists():
        return None

    txt = ALERTS_FILE.read_text().strip()

    if not txt:
        return None

    lines = txt.split("\n")

    return json.loads(lines[-1])


def get_all_alerts():

    alerts = []

    if ALERTS_FILE.exists():

        with open(ALERTS_FILE, "r", encoding="utf-8") as f:

            for line in f:
                line = line.strip()

                if line:
                    alerts.append(json.loads(line))

    return alerts


# ==============================
# PÁGINA INICIAL
# ==============================
@app.route('/')
def index():
    return render_template('termo_responsabilidade.html')


# ==============================
# ACEITAR TERMO
# ==============================
@app.route('/api/aceitar-termo', methods=['POST'])
def api_aceitar_termo():

    data = request.get_json() or {}

    registro = {
        "nome": data.get("nome"),
        "data": datetime.now(BR_TZ).strftime("%d/%m/%Y %H:%M:%S"),
        "ip": request.remote_addr
    }

    with TERMOS_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(registro) + "\n")

    return jsonify({"ok": True})


# ==============================
# LOGIN ADMIN
# ==============================
@app.route('/admin/login', methods=['GET','POST'])
def admin_login():

    users = load_users()
    error = False

    if request.method == 'POST':

        u = request.form.get("username")
        p = request.form.get("password")

        info = users.get(u)

        if info and info.get("role") == "admin" and info.get("password") == p:

            session["admin"] = u
            session["role"] = "admin"

            return redirect("/admin")

        error = True

    return render_template("login_admin.html", error=error)


@app.route('/admin')
def admin_panel():

    if session.get("role") != "admin":
        return redirect("/admin/login")

    alerts = get_all_alerts()

    return render_template("panel_admin.html", alerts=alerts)


@app.route('/logout_admin')
def logout_admin():
    session.clear()
    return redirect("/admin/login")


# ==============================
# LOGIN PESSOA DE CONFIANÇA
# ==============================
@app.route('/trusted/login', methods=['GET','POST'])
def trusted_login():

    users = load_users()
    error = False

    if request.method == 'POST':

        u = (request.form.get("username") or "").strip().lower()
        p = (request.form.get("password") or "")

        info = users.get(u)

        if info and info.get("role") == "trusted" and info.get("password") == p:

            session["trusted"] = u
            session["role"] = "trusted"

            return redirect("/trusted/panel")

        error = True

    return render_template("login_trusted.html", error=error)


@app.route('/trusted/panel')
def trusted_panel():

    if session.get("role") != "trusted":
        return redirect("/trusted/login")

    users = load_users()
    u = session.get("trusted")

    name = users.get(u, {}).get("name") or u

    return render_template("panel_trusted.html", display_name=name)


@app.route('/logout_trusted')
def logout_trusted():
    session.clear()
    return redirect("/trusted/login")


# ==============================
# BOTÃO DE PÂNICO
# ==============================
@app.route('/panic')
def panic_page():
    return render_template("panic_button.html")


@app.route('/api/panic', methods=['POST'])
def api_panic():

    data = request.get_json() or {}

    alert = {
        "id": _get_next_alert_id(),
        "name": data.get("name"),
        "msg": data.get("msg"),
        "lat": data.get("lat"),
        "lon": data.get("lon"),
        "time": datetime.now(BR_TZ).strftime("%d/%m/%Y %H:%M:%S")
    }

    log_alert(alert)

    return jsonify({"ok": True})


@app.route('/api/last_alert')
def api_last_alert():
    return jsonify(read_last_alert())


@app.route('/api/alerts')
def api_alerts():
    return jsonify(get_all_alerts())


# ==============================
# PDF RELATÓRIO
# ==============================
@app.route('/report/<int:alert_id>')
def report(alert_id):

    alerts = get_all_alerts()

    alert = next((a for a in alerts if a["id"] == alert_id), None)

    if not alert:
        return "Alerta não encontrado"

    pdf = FPDF()
    pdf.add_page()

    pdf.set_font("Arial", size=14)

    pdf.cell(200,10,"Relatório Aurora Mulher Segura", ln=True)

    for k,v in alert.items():
        pdf.cell(200,10,f"{k}: {v}", ln=True)

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(tmp.name)

    return send_file(tmp.name, as_attachment=True)
    

# ==============================
# RUN
# ==============================
if __name__ == "__main__":
    app.run(debug=True)