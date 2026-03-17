from __future__ import annotations
from flask import Flask, render_template, request, jsonify, redirect, session, url_for, send_file
from pathlib import Path
import json
import os
import secrets
from datetime import datetime
from zoneinfo import ZoneInfo
from fpdf import FPDF
import tempfile

# Configurações
try:
    TZ = ZoneInfo("America/Sao_Paulo")
except Exception:
    TZ = None

BASE_DIR = Path(__file__).resolve().parent
USERS_FILE = BASE_DIR / "users.json"
ALERTS_FILE = BASE_DIR / "alerts.log"
STATE_FILE = BASE_DIR / "state.json"

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY') or secrets.token_hex(32)

def now_br_str():
    if TZ is None:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return datetime.now(TZ).strftime("%Y-%m-%d %H:%M:%S")

def ensure_files():
    if not USERS_FILE.exists():
        USERS_FILE.write_text(json.dumps({
            "admin": {"password": "admin123", "role": "admin", "name": "Admin Aurora"}
        }, indent=2, ensure_ascii=False), encoding="utf-8")
    if not ALERTS_FILE.exists():
        ALERTS_FILE.write_text("", encoding="utf-8")
    if not STATE_FILE.exists():
        STATE_FILE.write_text(json.dumps({"last_id": 0}, indent=2, ensure_ascii=False), encoding="utf-8")

def load_users():
    ensure_files()
    try:
        return json.loads(USERS_FILE.read_text(encoding="utf-8"))
    except:
        return {"admin": {"password": "admin123", "role": "admin", "name": "Admin Aurora"}}

def save_users(data):
    USERS_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

def next_alert_id():
    ensure_files()
    try:
        st = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except:
        st = {"last_id": 0}
    st["last_id"] = int(st.get("last_id", 0)) + 1
    STATE_FILE.write_text(json.dumps(st, indent=2, ensure_ascii=False), encoding="utf-8")
    return st["last_id"]

def log_alert(payload):
    ensure_files()
    with ALERTS_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")

def get_all_alerts():
    ensure_files()
    try:
        txt = ALERTS_FILE.read_text(encoding="utf-8").strip()
        if not txt:
            return []
        alerts = []
        for line in txt.split("\n"):
            if line.strip():
                try:
                    alerts.append(json.loads(line))
                except:
                    pass
        return alerts
    except:
        return []

# ==========================================
# ROTAS
# ==========================================

@app.get("/health")
def health():
    return jsonify({"ok": True, "server_time_br": now_br_str()})

@app.get("/")
def index():
    return render_template("index.html")

@app.get("/termo")
@app.get("/termo_responsabilidade")
def termo():
    return render_template("termo_responsabilidade.html")

@app.route("/aceitar-termo", methods=["POST"])
def aceitar_termo():
    session["termo_aceito"] = True
    return redirect("/panic")

@app.get("/panic")
def panic():
    return render_template("panic_button.html")

@app.get("/historico")
def historico():
    alerts = get_all_alerts()
    return render_template("historico.html", alerts=alerts)

@app.get("/plano-seguranca")
def plano_seguranca():
    return render_template("plano_seguranca.html")

@app.get("/ajuda")
def ajuda():
    return render_template("ajuda.html")

@app.get("/saida-rapida")
def saida_rapida():
    return render_template("saida_rapida.html")

@app.get("/legal")
def legal():
    return render_template("legal.html")

@app.get("/offline")
def offline():
    return render_template("offline.html")

@app.get("/anual")
def anual():
    return render_template("anual_aurora.html")

@app.get("/central")
def central():
    return render_template("central_aurora.html")

@app.get("/pagamentos")
def pagamentos():
    return render_template("pagamentos.html")

@app.get("/recibo")
def recibo():
    return render_template("recibo_entrega.html")

@app.post("/api/send_alert")
def send_alert():
    data = request.get_json(silent=True) or {}
    payload = {
        "id": next_alert_id(),
        "ts": now_br_str(),
        "name": data.get("name", "Não informado"),
        "situation": data.get("situation", "Emergência"),
        "message": data.get("message", ""),
        "location": data.get("location"),
        "ip": request.remote_addr
    }
    log_alert(payload)
    return jsonify({"ok": True, "id": payload["id"]})

@app.get("/api/alerts")
def api_alerts():
    return jsonify(get_all_alerts())

@app.get("/relatorio/pdf")
def relatorio_pdf():
    alerts = get_all_alerts()
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 18)
    pdf.cell(0, 10, "RELATORIO DE ALERTAS - AURORA", ln=1)
    pdf.set_font("Arial", "", 12)
    for a in alerts:
        linha = f"ID {a['id']} - {a.get('ts', 'N/A')} - {a.get('name', 'N/A')} - {a.get('situation', 'N/A')}"
        pdf.cell(0, 8, linha, ln=1)
    temp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(temp.name)
    return send_file(temp.name, as_attachment=True, download_name="relatorio_aurora.pdf")

# ==========================================
# ADMIN
# ==========================================

@app.route("/panel/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        users = load_users()
        u = request.form.get("user", "").strip()
        p = request.form.get("password", "")
        info = users.get(u)
        
        if info and info.get("password") == p:
            session.clear()
            session["role"] = "admin"
            session["user"] = u
            return redirect("/panel")
        
        return render_template("login_admin.html", error=True)
    
    return render_template("login_admin.html")

@app.get("/panel")
def admin_panel():
    if session.get("role") != "admin":
        return redirect("/panel/login")
    
    users = load_users()
    trusted = {u: info for u, info in users.items() if info.get("role") == "trusted"}
    alerts = get_all_alerts()
    
    stats = {
        "total": len(alerts),
        "today": sum(1 for a in alerts if a.get("ts", "").startswith(datetime.now().strftime("%d/%m/%Y"))),
        "trusted": len(trusted),
        "with_location": sum(1 for a in alerts if a.get("location")),
        "without_location": sum(1 for a in alerts if not a.get("location"))
    }
    
    return render_template("panel_admin.html", trusted=trusted, alerts=alerts, stats=stats)

@app.post("/panel/add_trusted")
def admin_add_trusted():
    if session.get("role") != "admin":
        return redirect("/panel/login")
    
    name = request.form.get("trusted_name", "").strip()
    username = request.form.get("trusted_user", "").strip().lower()
    password = request.form.get("trusted_password", "")

    if not name or not username or not password:
        return redirect("/panel?err=Preencha todos os campos")

    if len(password) < 4:
        return redirect("/panel?err=Senha muito curta")

    users = load_users()

    if username in users:
        return redirect("/panel?err=Usuario ja existe")

    users[username] = {
        "password": password,
        "role": "trusted",
        "name": name
    }
    save_users(users)
    return redirect(f"/panel?msg=Pessoa cadastrada: {name}")

@app.post("/panel/delete_trusted")
def admin_delete_trusted():
    if session.get("role") != "admin":
        return redirect("/panel/login")
    
    username = request.form.get("username", "").strip()
    users = load_users()

    if username in users and users[username].get("role") == "trusted":
        users.pop(username)
        save_users(users)
        return redirect("/panel?msg=Pessoa removida")

    return redirect("/panel?err=Erro ao remover")

@app.get("/logout_admin")
def logout_admin():
    session.clear()
    return redirect("/panel/login")

# ==========================================
# TRUSTED (PESSOA DE CONFIANÇA)
# ==========================================

@app.route("/trusted/login", methods=["GET", "POST"])
def trusted_login():
    if request.method == "POST":
        users = load_users()
        u = request.form.get("user", "").strip().lower()
        p = request.form.get("password", "")
        info = users.get(u)

        if info and info.get("role") == "trusted" and info.get("password") == p:
            session.clear()
            session["role"] = "trusted"
            session["trusted"] = u
            return redirect("/trusted/panel")

        return render_template("login_trusted.html", error=True)
    
    return render_template("login_trusted.html")

@app.get("/trusted/panel")
def trusted_panel():
    if session.get("role") != "trusted":
        return redirect("/trusted/login")
    
    users = load_users()
    u = session.get("trusted")
    display_name = users.get(u, {}).get("name") or u
    alerts = get_all_alerts()[-10:]
    return render_template("panel_trusted.html", display_name=display_name, alerts=alerts)

@app.get("/logout_trusted")
def logout_trusted():
    session.clear()
    return redirect("/trusted/login")

# ==========================================
# START
# ==========================================

if __name__ == "__main__":
    ensure_files()
    print("=" * 60)
    print("🌸 AURORA MULHER SEGURA v3.0")
    print("=" * 60)
    print("🚀 http://localhost:5000")
    print("🔐 Admin: admin / admin123")
    print("=" * 60)
    app.run(host="0.0.0.0", port=5000, debug=True)