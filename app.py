from __future__ import annotations
from flask import Flask, render_template, request, jsonify, redirect, session
from pathlib import Path
import json
import os
import secrets
from datetime import datetime
from zoneinfo import ZoneInfo

try:
    TZ = ZoneInfo("America/Sao_Paulo")
except:
    TZ = None

BASE_DIR = Path(__file__).resolve().parent
USERS_FILE = BASE_DIR / "users.json"
ALERTS_FILE = BASE_DIR / "alerts.log"
STATE_FILE = BASE_DIR / "state.json"
TERMOS_FILE = BASE_DIR / "termos_aceitos.log"

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY') or secrets.token_hex(32)

def now_br_str():
    if TZ is None:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return datetime.now(TZ).strftime("%Y-%m-%d %H:%M:%S")

def ensure_files():
    if not USERS_FILE.exists():
        USERS_FILE.write_text(json.dumps({
            "admin": {"password": "admin123", "role": "admin", "name": "Admin"}
        }, indent=2, ensure_ascii=False), encoding="utf-8")
    if not ALERTS_FILE.exists():
        ALERTS_FILE.write_text("", encoding="utf-8")
    if not STATE_FILE.exists():
        STATE_FILE.write_text(json.dumps({"last_id": 0}, indent=2, ensure_ascii=False), encoding="utf-8")
    if not TERMOS_FILE.exists():
        TERMOS_FILE.write_text("", encoding="utf-8")

def load_users():
    ensure_files()
    try:
        return json.loads(USERS_FILE.read_text(encoding="utf-8"))
    except:
        return {"admin": {"password": "admin123", "role": "admin", "name": "Admin"}}

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

def log_termo_aceito():
    """Registra que o termo foi aceito"""
    ensure_files()
    with TERMOS_FILE.open("a", encoding="utf-8") as f:
        f.write(f"{now_br_str()}\n")

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

def get_all_termos():
    """Retorna lista de termos aceitos"""
    ensure_files()
    try:
        txt = TERMOS_FILE.read_text(encoding="utf-8").strip()
        return [t.strip() for t in txt.split("\n") if t.strip()]
    except:
        return []

@app.get("/health")
def health():
    return jsonify({"ok": True})

@app.get("/")
def index():
    return render_template("index.html")

@app.get("/panic")
def panic():
    return render_template("panic_button.html")

@app.get("/historico")
def historico():
    alerts = get_all_alerts()
    return render_template("historico.html", alerts=alerts)

@app.get("/ajuda")
def ajuda():
    return render_template("ajuda.html")

@app.get("/saida-rapida")
def saida_rapida():
    return render_template("saida_rapida.html")

@app.post("/aceitar-termo")
def aceitar_termo():
    """Rota para aceitar o termo de responsabilidade"""
    session["termo_aceito"] = True
    session["termo_aceito_em"] = now_br_str()
    log_termo_aceito()
    return redirect("/panic")

@app.post("/api/send_alert")
def send_alert():
    data = request.get_json(silent=True) or {}
    
    location = data.get("location")
    
    # 🔥 VERIFICA SE O TERMO FOI ACEITO
    termo_aceito = session.get("termo_aceito", False)
    termo_aceito_em = session.get("termo_aceito_em", None)
    
    payload = {
        "id": next_alert_id(),
        "ts": now_br_str(),
        "name": data.get("name", "Não informado"),
        "situation": data.get("situation", "Emergência"),
        "message": data.get("message", ""),
        "location": location,
        "lat": location.get("lat") if location and isinstance(location, dict) else None,
        "lng": location.get("lng") if location and isinstance(location, dict) else None,
        "accuracy": location.get("accuracy") if location and isinstance(location, dict) else None,
        "ip": request.remote_addr,
        # 🔥 NOVOS CAMPOS: LEGALIZAÇÃO
        "termo_aceito": termo_aceito,
        "termo_aceito_em": termo_aceito_em,
        "user_agent": request.headers.get("User-Agent", "")
    }
    
    log_alert(payload)
    print(f"✅ Alerta #{payload['id']} - {payload['situation']}")
    print(f"📜 Termo aceito: {termo_aceito} em {termo_aceito_em}")
    if location:
        print(f"📍 {location.get('lat')}, {location.get('lng')}")
    
    return jsonify({"ok": True, "id": payload["id"]})

@app.get("/api/alerts")
def api_alerts():
    return jsonify(get_all_alerts())

@app.get("/api/termos")
def api_termos():
    """Retorna lista de termos aceitos"""
    return jsonify(get_all_termos())

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
    termos = get_all_termos()
    
    stats = {
        "total": len(alerts),
        "today": sum(1 for a in alerts if a.get("ts", "").startswith(datetime.now().strftime("%Y-%m-%d"))),
        "trusted": len(trusted),
        "with_location": sum(1 for a in alerts if a.get("location")),
        "without_location": sum(1 for a in alerts if not a.get("location")),
        "termos_aceitos": len(termos)  # 🔥 NOVA ESTATÍSTICA
    }
    
    return render_template("panel_admin.html", trusted=trusted, alerts=alerts, stats=stats)

@app.get("/logout_admin")
def logout_admin():
    session.clear()
    return redirect("/panel/login")

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

if __name__ == "__main__":
    ensure_files()
    print("=" * 60)
    print("🌸 AURORA v3.0 - COM LEGALIZAÇÃO")
    print("=" * 60)
    print("📜 Termo de responsabilidade integrado")
    print("📍 Localização com consentimento")
    print("🚨 Alertas com status legal")
    print("=" * 60)
    app.run(host="0.0.0.0", port=5000, debug=True)