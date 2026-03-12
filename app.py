from __future__ import annotations
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, send_file
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


# ==================================================
# CRIAR ARQUIVOS NECESSÁRIOS
# ==================================================
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

    if not TERMOS_FILE.exists():
        TERMOS_FILE.write_text("", encoding="utf-8")


# ==================================================
# UTILIDADES
# ==================================================
def load_users():
    ensure_files()
    try:
        return json.loads(USERS_FILE.read_text(encoding="utf-8"))
    except:
        return {}

def save_users(data):
    USERS_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

def next_alert_id():
    ensure_files()
    try:
        state = json.loads(STATE_FILE.read_text())
    except:
        state = {"last_id": 0}

    state["last_id"] += 1
    STATE_FILE.write_text(json.dumps(state), encoding="utf-8")

    return state["last_id"]

def save_alert(alert):
    ensure_files()
    with open(ALERTS_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(alert, ensure_ascii=False) + "\n")

def get_all_alerts():
    alerts = []
    if ALERTS_FILE.exists():
        with open(ALERTS_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        alerts.append(json.loads(line))
                    except:
                        pass
    return alerts

def get_last_alert():
    alerts = get_all_alerts()
    if alerts:
        return alerts[-1]
    return None


# ==================================================
# PÁGINAS
# ==================================================
@app.route("/")
def index():
    return render_template("termo_responsabilidade.html")


@app.route("/panic")
def panic():
    users = load_users()
    trusted = [v.get("name") for k, v in users.items() if v.get("role") == "trusted"]
    return render_template("panic_button.html", trusted_names=trusted)


@app.route("/painel-da-mulher")
def painel_mulher():
    return redirect("/panic")


@app.route("/ajuda")
def ajuda():
    return render_template("ajuda.html")


@app.route("/plano-seguranca")
def plano():
    return render_template("plano_seguranca.html")


@app.route("/saida-rapida")
def saida():
    return render_template("saida_rapida.html")


# ==================================================
# API ALERTA
# ==================================================
@app.route("/api/send_alert", methods=["POST"])
def send_alert():

    data = request.get_json() or {}

    now = datetime.now(BR_TZ)

    alert = {
        "id": next_alert_id(),
        "ts": now.strftime("%Y-%m-%d %H:%M:%S"),
        "ts_br": now.strftime("%d/%m/%Y %H:%M:%S"),
        "name": data.get("name", "Usuária"),
        "situation": data.get("situation", "Emergência"),
        "message": data.get("message", ""),
        "location": data.get("location")
    }

    save_alert(alert)

    return jsonify({"ok": True, "alert": alert})


@app.route("/api/last_alert")
def api_last_alert():
    return jsonify({"ok": True, "last": get_last_alert()})


# ==================================================
# ADMIN
# ==================================================
@app.route("/panel/login", methods=["GET", "POST"])
def admin_login():

    users = load_users()
    error = False

    if request.method == "POST":

        u = request.form.get("user")
        p = request.form.get("password")

        info = users.get(u)

        if info and info.get("password") == p and info.get("role") == "admin":
            session["role"] = "admin"
            session["user"] = u
            return redirect("/panel")

        error = True

    return render_template("login_admin.html", error=error)


@app.route("/panel")
def admin_panel():

    if session.get("role") != "admin":
        return redirect("/panel/login")

    alerts = get_all_alerts()
    users = load_users()

    trusted = {k: v for k, v in users.items() if v.get("role") == "trusted"}
    
    # ==================================================
    # CORREÇÃO: ADICIONADO stats
    # ==================================================
    hoje = datetime.now(BR_TZ).strftime("%d/%m/%Y")
    
    alerts_hoje = 0
    for alert in alerts:
        if alert.get("ts_br", "").startswith(hoje):
            alerts_hoje += 1
    
    stats = {
        "total": len(alerts),
        "hoje": alerts_hoje,
        "trusted": len(trusted)
    }

    return render_template("panel_admin.html",
                           alerts=alerts,
                           trusted=trusted,
                           stats=stats)  # ← VARIÁVEL ADICIONADA


@app.route("/logout_admin")
def logout_admin():
    session.clear()
    return redirect("/panel/login")


# ==================================================
# TRUSTED
# ==================================================
@app.route("/trusted/login", methods=["GET", "POST"])
def trusted_login():

    users = load_users()
    error = False

    if request.method == "POST":

        u = request.form.get("user")
        p = request.form.get("password")

        info = users.get(u)

        if info and info.get("role") == "trusted" and info.get("password") == p:
            session["role"] = "trusted"
            session["trusted"] = u
            return redirect("/trusted/panel")

        error = True

    return render_template("login_trusted.html", error=error)


@app.route("/trusted/panel")
def trusted_panel():

    if session.get("role") != "trusted":
        return redirect("/trusted/login")

    users = load_users()
    u = session.get("trusted")

    name = users.get(u, {}).get("name", u)

    return render_template("panel_trusted.html", display_name=name)


@app.route("/logout_trusted")
def logout_trusted():
    session.clear()
    return redirect("/panic")


# ==================================================
# RELATÓRIO PDF
# ==================================================
@app.route("/relatorio/pdf")
def relatorio_pdf():

    alerts = get_all_alerts()

    pdf = FPDF()
    pdf.add_page()

    pdf.set_font("Arial", "B", 18)
    pdf.cell(0, 10, "RELATORIO DE ALERTAS - AURORA", ln=1)

    pdf.set_font("Arial", "", 12)

    for a in alerts:
        pdf.cell(0, 8, f"ID {a['id']} - {a['ts_br']} - {a['name']} - {a['situation']}", ln=1)

    temp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(temp.name)

    return send_file(temp.name, as_attachment=True)


# ==================================================
# HEALTH CHECK
# ==================================================
@app.route("/health")
def health():

    return jsonify({
        "ok": True,
        "alerts": len(get_all_alerts()),
        "users_file": USERS_FILE.exists(),
        "alerts_file": ALERTS_FILE.exists()
    })


# ==================================================
# START
# ==================================================
if __name__ == "__main__":

    ensure_files()

    port = int(os.environ.get("PORT", 5000))

    print("🚀 AURORA SISTEMA INICIADO")
    print("http://localhost:5000")

    app.run(host="0.0.0.0", port=port, debug=True)