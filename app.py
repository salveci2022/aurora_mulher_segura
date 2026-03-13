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
import bcrypt

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = "aurora_v20_ultra_estavel_secure_2026"
CORS(app)

BR_TZ = pytz.timezone('America/Sao_Paulo')
BASE_DIR = Path(__file__).resolve().parent
USERS_FILE = BASE_DIR / "users.json"
ALERTS_FILE = BASE_DIR / "alerts.log"
STATE_FILE = BASE_DIR / "data" / "state.json"
TERMOS_FILE = BASE_DIR / "data" / "termos_aceitos.log"

os.makedirs('data', exist_ok=True)

def ensure_files():
    if not USERS_FILE.exists():
        admin_hash = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        USERS_FILE.write_text(json.dumps({
            "admin": {
                "password": admin_hash,
                "role": "admin",
                "name": "Administrador",
                "created_at": datetime.now(BR_TZ).isoformat(),
                "last_login": None
            }
        }, indent=2, ensure_ascii=False), encoding="utf-8")

    if not ALERTS_FILE.exists():
        ALERTS_FILE.write_text("", encoding="utf-8")

    if not STATE_FILE.exists():
        STATE_FILE.write_text(json.dumps({"last_id": 0}), encoding="utf-8")

    if not TERMOS_FILE.exists():
        TERMOS_FILE.write_text("", encoding="utf-8")

def load_users():
    ensure_files()
    try:
        return json.loads(USERS_FILE.read_text(encoding="utf-8"))
    except:
        return {}

def save_users(users):
    USERS_FILE.write_text(json.dumps(users, indent=2, ensure_ascii=False), encoding="utf-8")

def verificar_senha(senha_digitada, hash_armazenado):
    try:
        if not hash_armazenado.startswith('$2b$'):
            return senha_digitada == hash_armazenado
        return bcrypt.checkpw(
            senha_digitada.encode('utf-8'),
            hash_armazenado.encode('utf-8')
        )
    except Exception as e:
        print(f"Erro ao verificar senha: {e}")
        return False

def criar_hash_senha(senha):
    return bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

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

@app.route("/")
def index():
    return render_template("termo_responsabilidade.html")

@app.route("/aceitar-termo", methods=["POST"])
def aceitar_termo():
    session["termo_aceito"] = True
    with open(TERMOS_FILE, "a", encoding="utf-8") as f:
        f.write(datetime.now(BR_TZ).strftime("%d/%m/%Y %H:%M:%S") + "\n")
    return redirect("/panic")

@app.route("/panic")
def panic():
    if not session.get("termo_aceito"):
        return redirect("/")
    users = load_users()
    trusted = [v.get("name") for k, v in users.items() if v.get("role") == "trusted"]
    return render_template("panic_button.html", trusted_names=trusted)

@app.route("/ajuda")
def ajuda():
    return render_template("ajuda.html")

@app.route("/plano-seguranca")
def plano():
    return render_template("plano_seguranca.html")

@app.route("/saida-rapida")
def saida():
    return render_template("saida_rapida.html")

@app.route("/central")
def central():
    return render_template("central_aurora.html")

@app.route("/api/send_alert", methods=["POST"])
def send_alert():
    data = request.get_json() or {}
    now = datetime.now(BR_TZ)

    alert = {
        "id": next_alert_id(),
        "ts": now.strftime("%Y-%m-%d %H:%M:%S"),
        "ts_br": now.strftime("%d/%m/%Y %H:%M:%S"),
        "timestamp": now.isoformat(),
        "name": data.get("name", "Usuária"),
        "situation": data.get("situation", "Emergência"),
        "message": data.get("message", ""),
        "lat": float(data.get("lat", 0)) if data.get("lat") else None,
        "lng": float(data.get("lng", 0)) if data.get("lng") else None,
        "accuracy": float(data.get("accuracy", 0)) if data.get("accuracy") else None,
        "gps_readings": int(data.get("gps_readings", 1))
    }

    save_alert(alert)
    return jsonify({"ok": True, "alert": alert})

@app.route("/api/last_alert")
def api_last_alert():
    return jsonify({"ok": True, "last": get_last_alert()})

@app.route("/api/alerts")
def get_alerts():
    alerts = get_all_alerts()
    return jsonify(alerts)

@app.route("/panel/login", methods=["GET", "POST"])
def admin_login():
    users = load_users()
    error = False

    if request.method == "POST":
        u = request.form.get("user")
        p = request.form.get("password")
        info = users.get(u)

        if info and info.get("role") == "admin" and verificar_senha(p, info.get("password", "")):
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

    hoje = datetime.now(BR_TZ).strftime("%d/%m/%Y")
    alerts_hoje = sum(1 for a in alerts if a.get("ts_br", "").startswith(hoje))

    stats = {
        "total": len(alerts),
        "today": alerts_hoje,
        "trusted": len(trusted),
        "with_location": sum(1 for a in alerts if a.get("lat")),
        "without_location": sum(1 for a in alerts if not a.get("lat"))
    }

    return render_template("panel_admin.html", alerts=alerts, trusted=trusted, stats=stats)

@app.route("/panel/add_trusted", methods=["POST"])
def add_trusted():
    if session.get("role") != "admin":
        return redirect("/panel/login")
    
    name = request.form.get("trusted_name")
    username = request.form.get("trusted_user")
    password = request.form.get("trusted_password")

    users = load_users()

    if username in users:
        return redirect("/panel?err=Usuário+já+existe")

    password_hash = criar_hash_senha(password)

    users[username] = {
        "password": password_hash,
        "role": "trusted",
        "name": name,
        "created_at": datetime.now(BR_TZ).isoformat(),
        "last_login": None
    }

    save_users(users)
    return redirect("/panel?msg=Pessoa+de+confiança+cadastrada")

@app.route("/logout_admin")
def logout_admin():
    session.clear()
    return redirect("/panel/login")

@app.route("/trusted/login", methods=["GET", "POST"])
def trusted_login():
    users = load_users()
    error = False

    if request.method == "POST":
        u = request.form.get("user")
        p = request.form.get("password")
        info = users.get(u)

        if info and info.get("role") == "trusted" and verificar_senha(p, info.get("password", "")):
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
    alerts = get_all_alerts()[-10:]

    return render_template("panel_trusted.html", display_name=name, alerts=alerts)

@app.route("/trusted/change_password", methods=["GET", "POST"])
def trusted_change_password():
    if session.get("role") != "trusted":
        return redirect("/trusted/login")
    
    if request.method == "POST":
        old = request.form.get("old_password")
        new = request.form.get("new_password")
        users = load_users()
        username = session.get("trusted")

        if username in users:
            if verificar_senha(old, users[username]["password"]):
                if len(new) >= 4:
                    users[username]["password"] = criar_hash_senha(new)
                    save_users(users)
                    return redirect("/trusted/panel?msg=Senha+alterada")

        return redirect("/trusted/panel?err=Senha+incorreta")

    return render_template("trusted_change_password.html")

@app.route("/trusted/recover", methods=["GET", "POST"])
def trusted_recover():
    if request.method == "POST":
        usuario = request.form.get("usuario")
        nova_senha = request.form.get("nova_senha")
        users = load_users()

        if usuario in users and len(nova_senha) >= 4:
            users[usuario]["password"] = criar_hash_senha(nova_senha)
            save_users(users)
            return render_template("trusted_recover.html", msg="Senha+redefinida")
        
        return render_template("trusted_recover.html", err="Usuário+não+encontrado")

    return render_template("trusted_recover.html")

@app.route("/logout_trusted")
def logout_trusted():
    session.clear()
    return redirect("/trusted/login")

@app.route("/historico")
def historico():
    alerts = get_all_alerts()
    return render_template("historico.html", alerts=alerts)

@app.route("/relatorio/pdf")
def relatorio_pdf():
    if session.get("role") != "admin":
        return redirect("/panel/login")
    
    alerts = get_all_alerts()
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 18)
    pdf.cell(0, 10, "RELATORIO DE ALERTAS - AURORA", ln=1)
    pdf.set_font("Arial", "", 12)
    for a in alerts:
        linha = f"ID {a['id']} - {a['ts_br']} - {a['name']} - {a['situation']}"
        if a.get('lat') and a.get('lng'):
            linha += f" - GPS: {a['lat']}, {a['lng']}"
        pdf.cell(0, 8, linha, ln=1)
    temp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(temp.name)
    return send_file(temp.name, as_attachment=True)

@app.route("/legal")
def legal():
    return render_template("legal.html")

@app.route("/offline")
def offline():
    return render_template("offline.html")

@app.route("/recibo")
def recibo():
    return render_template("recibo_entrega.html")

@app.route("/pagamentos")
def pagamentos():
    return render_template("pagamentos.html")

@app.route("/anual")
def anual():
    return render_template("anual_aurora.html")

@app.route("/health")
def health():
    return jsonify({
        "ok": True,
        "alerts": len(get_all_alerts()),
        "users_file": USERS_FILE.exists(),
        "alerts_file": ALERTS_FILE.exists()
    })

if __name__ == "__main__":
    ensure_files()
    port = int(os.environ.get("PORT", 5000))
    print("=" * 60)
    print("🌸 AURORA MULHER SEGURA v3.0")
    print("=" * 60)
    print("🚀 Sistema iniciado")
    print("📍 Fuso: America/Sao_Paulo")
    print("🔐 Admin: admin / admin123")
    print("🗺️ Mapa: Automático")
    print("🔔 Sirene: Automática")
    print("=" * 60)
    app.run(host="0.0.0.0", port=port, debug=True)