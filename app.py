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

# ===== WEB PUSH =====
from pywebpush import webpush, WebPushException

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = "aurora_v20_ultra_estavel_secure_2026"
CORS(app)

BR_TZ = pytz.timezone('America/Sao_Paulo')

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"
USERS_FILE = BASE_DIR / "users.json"
ALERTS_FILE = BASE_DIR / "alerts.log"
STATE_FILE = BASE_DIR / "state.json"
TERMOS_FILE = BASE_DIR / "termos_aceitos.log"

# ===== WEB PUSH CONFIG =====
VAPID_PUBLIC_KEY = "BB7XEWW3AetNIC14i0HEpkgfelgS9drXIN5uRf9NOBkgQz_YTRst4GWiXn7fNZIQdprjYLUfTYmb4EtTF3F0ww8"
VAPID_PRIVATE_KEY = "MIGHAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBG0wawIBAQQg3cHwUAWs4FzFGJl9J2HdRJeuP9IjswY-Mib5tRv95H2hRANCAAQe1xFltwHrTSAteItBxKZIH3pYEvXa1yDebkX_TTgZIEM_2E0bLeBlol5-3zWSEHaa42C1H02Jm-BLUxdxdMMP"

VAPID_CLAIMS = {
    "sub": "mailto:contato@auroramulhersegura.com"
}

SUBSCRIPTIONS_FILE = BASE_DIR / "subscriptions.json"

# ================= WEB PUSH =================

def save_subscription(subscription):
    if not SUBSCRIPTIONS_FILE.exists():
        SUBSCRIPTIONS_FILE.write_text("[]", encoding="utf-8")

    subs = json.loads(SUBSCRIPTIONS_FILE.read_text(encoding="utf-8"))
    subs.append(subscription)

    SUBSCRIPTIONS_FILE.write_text(
        json.dumps(subs, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

def send_push_notification(payload):
    if not SUBSCRIPTIONS_FILE.exists():
        return

    subs = json.loads(SUBSCRIPTIONS_FILE.read_text(encoding="utf-8"))

    for sub in subs:
        try:
            webpush(
                subscription_info=sub,
                data=json.dumps({
                    "title": "🚨 ALERTA AURORA",
                    "body": f"{payload['name']} acionou alerta!",
                    "url": "/trusted/panel"
                }),
                vapid_private_key=VAPID_PRIVATE_KEY,
                vapid_claims=VAPID_CLAIMS
            )
        except WebPushException as ex:
            print("Erro ao enviar push:", ex)

@app.route("/api/subscribe", methods=["POST"])
def subscribe():
    subscription = request.get_json()
    save_subscription(subscription)
    return jsonify({"ok": True})

# ================= SISTEMA ORIGINAL =================

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

def load_users():
    _ensure_files()
    try:
        return json.loads(USERS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}

def save_users(data):
    USERS_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

def _get_next_alert_id():
    _ensure_files()
    try:
        st = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        st = {"last_id": 0}
    st["last_id"] = int(st.get("last_id", 0)) + 1
    STATE_FILE.write_text(json.dumps(st, indent=2, ensure_ascii=False), encoding="utf-8")
    return st["last_id"]

def log_alert(payload):
    _ensure_files()
    with ALERTS_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")

def read_last_alert():
    _ensure_files()
    try:
        txt = ALERTS_FILE.read_text(encoding="utf-8").strip()
        if not txt:
            return None
        lines = [ln for ln in txt.split("\n") if ln.strip()]
        return json.loads(lines[-1])
    except Exception:
        return None

def get_all_alerts():
    alerts = []
    if ALERTS_FILE.exists():
        with open(ALERTS_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        alerts.append(json.loads(line))
                    except:
                        pass
    return alerts

# ================= ROTAS =================

@app.route('/')
def index():
    return render_template('termo_responsabilidade.html')

@app.route('/panic')
def panic_button():
    users = load_users()
    trusted_names = [info.get("name") or username for username, info in users.items() if info.get("role") == "trusted"]
    return render_template('panic_button.html', trusted_names=trusted_names)

@app.route('/api/send_alert', methods=['POST'])
def api_send_alert():
    data = request.get_json(silent=True) or {}
    alert_id = _get_next_alert_id()

    now_br = datetime.now(BR_TZ)
    formatted_time = now_br.strftime("%Y-%m-%d %H:%M:%S")
    formatted_time_br = now_br.strftime("%d/%m/%Y %H:%M:%S")

    payload = {
        "id": alert_id,
        "ts": formatted_time,
        "ts_br": formatted_time_br,
        "name": data.get("name", "Usuária"),
        "situation": data.get("situation", "Emergência"),
        "message": data.get("message", ""),
        "location": data.get("location")
    }

    log_alert(payload)

    # ===== ENVIA PUSH =====
    send_push_notification(payload)

    return jsonify({
        "ok": True,
        "id": alert_id,
        "message": "Alerta recebido com sucesso!"
    })

@app.route('/api/last_alert')
def api_last_alert():
    last = read_last_alert()
    return jsonify({"ok": True, "last": last})

@app.route('/trusted/login', methods=['GET', 'POST'])
def trusted_login():
    users = load_users()
    error = False
    if request.method == 'POST':
        u = (request.form.get("user") or "").strip().lower()
        p = (request.form.get("password") or "")
        info = users.get(u)
        if info and info.get("role") == "trusted" and info.get("password") == p:
            session.clear()
            session["role"] = "trusted"
            session["trusted"] = u
            return redirect(url_for('trusted_panel'))
        error = True
    return render_template('login_trusted.html', error=error)

@app.route('/trusted/panel')
def trusted_panel():
    if session.get("role") != "trusted":
        return redirect(url_for('trusted_login'))

    users = load_users()
    u = session.get("trusted")
    name = users.get(u, {}).get("name") or u
    return render_template('panel_trusted.html', display_name=name)

# ================= INIT =================

if __name__ == '__main__':
    _ensure_files()
    print("🚀 AURORA MULHER SEGURA INICIADO")
    app.run(host='0.0.0.0', port=5000, debug=True)