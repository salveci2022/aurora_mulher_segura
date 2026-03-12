# ============================================
# AURORA MULHER SEGURA - BACKEND FLASK
# VERSÃO 3.0 - FINAL COM SERVICE WORKER
# ============================================

from __future__ import annotations
from flask import Flask, render_template, request, jsonify, redirect, session, send_file
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from datetime import datetime
import os
import json
from pathlib import Path
from fpdf import FPDF
import tempfile
import pytz
import bcrypt

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = os.urandom(32).hex()
CORS(app)

# Flask-Limiter 3.x+ usa init_app()
limiter = Limiter(key_func=get_remote_address, default_limits=["100 per hour"])
limiter.init_app(app)

BR_TZ = pytz.timezone('America/Sao_Paulo')
BASE_DIR = Path(__file__).resolve().parent
USERS_FILE = BASE_DIR / "data" / "users.json"
ALERTS_FILE = BASE_DIR / "data" / "alerts.log"
STATE_FILE = BASE_DIR / "data" / "state.json"
TERMOS_FILE = BASE_DIR / "data" / "termos_aceitos.log"

# Garantir diretórios existem
os.makedirs('data', exist_ok=True)
os.makedirs('static/css', exist_ok=True)
os.makedirs('static/js', exist_ok=True)
os.makedirs('static/audio', exist_ok=True)
os.makedirs('static/img', exist_ok=True)

# ============================================
# CRIAR ARQUIVOS NECESSÁRIOS
# ============================================

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
        STATE_FILE.write_text(json.dumps({
            "last_id": 0,
            "total_alerts": 0,
            "last_update": datetime.now(BR_TZ).isoformat(),
            "version": "3.0",
            "stats": {
                "today": 0,
                "week": 0,
                "month": 0,
                "with_location": 0,
                "without_location": 0
            }
        }, indent=2, ensure_ascii=False), encoding="utf-8")

    if not TERMOS_FILE.exists():
        TERMOS_FILE.write_text("", encoding="utf-8")

# ============================================
# UTILIDADES
# ============================================

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

def atualizar_last_login(usuario):
    try:
        users = load_users()
        if usuario in users:
            users[usuario]['last_login'] = datetime.now(BR_TZ).isoformat()
            save_users(users)
    except Exception as e:
        print(f"Erro ao atualizar last_login: {e}")

def criar_hash_senha(senha):
    return bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def migrar_senhas_para_bcrypt():
    users = load_users()
    modificado = False
    for user, data in users.items():
        password = data.get('password', '')
        if password and not password.startswith('$2b$'):
            print(f"Migrando senha do usuário {user} para bcrypt...")
            data['password'] = criar_hash_senha(password)
            if 'created_at' not in data:
                data['created_at'] = datetime.now(BR_TZ).isoformat()
            if 'last_login' not in data:
                data['last_login'] = None
            modificado = True

    if modificado:
        save_users(users)
        print("✅ Senhas migradas para bcrypt com sucesso!")

def next_alert_id():
    ensure_files()
    try:
        state = json.loads(STATE_FILE.read_text())
    except:
        state = {"last_id": 0}

    state["last_id"] += 1
    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
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

def get_stats():
    alerts = get_all_alerts()
    hoje = datetime.now(BR_TZ).strftime("%d/%m/%Y")
    alerts_hoje = sum(1 for a in alerts if a.get("ts_br", "").startswith(hoje))
    
    with_location = sum(1 for a in alerts if a.get("lat"))
    without_location = sum(1 for a in alerts if not a.get("lat"))
    
    return {
        "total": len(alerts),
        "today": alerts_hoje,
        "with_location": with_location,
        "without_location": without_location
    }

# ============================================
# PÁGINAS PRINCIPAIS
# ============================================

@app.route("/")
@limiter.limit("30 per minute")
def index():
    return render_template("index.html")

@app.route("/termo")
def termo():
    return render_template("termo_responsabilidade.html")

@app.route("/aceitar-termo", methods=["POST"])
def aceitar_termo():
    session["termo_aceito"] = True
    with open(TERMOS_FILE, "a", encoding="utf-8") as f:
        f.write(datetime.now(BR_TZ).strftime("%d/%m/%Y %H:%M:%S") + "\n")
    return redirect("/panic")

@app.route("/panic")
@limiter.limit("20 per minute")
def panic():
    if not session.get("termo_aceito"):
        return redirect("/termo")
    
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

@app.route("/central")
def central():
    return render_template("central_aurora.html")

@app.route("/historico")
@limiter.limit("10 per minute")
def historico():
    alerts = get_all_alerts()
    return render_template("historico.html", alerts=alerts)

@app.route("/pagamentos")
def pagamentos():
    return render_template("pagamentos.html")

@app.route("/recibo")
def recibo():
    return render_template("recibo_entrega.html")

@app.route("/offline")
def offline():
    return render_template("offline.html")

@app.route("/legal")
def legal():
    return render_template("legal.html")

@app.route("/anual")
def anual():
    return render_template("anual_aurora.html")

# ============================================
# MANIFEST E SERVICE WORKER (PWA)
# ============================================

@app.route("/static/manifest.json")
def manifest():
    return send_file('static/manifest.json', mimetype='application/json')

@app.route("/manifest.json")
def manifest_root():
    return send_file('static/manifest.json', mimetype='application/json')

@app.route("/sw.js")
def service_worker():
    return send_file('static/js/sw.js', mimetype='application/javascript')

# ============================================
# API ALERTA
# ============================================

@app.route("/api/send_alert", methods=["POST"])
@limiter.limit("10 per minute")
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
        "lat": data.get("lat"),
        "lng": data.get("lng"),
        "accuracy": data.get("accuracy"),
        "user_agent": data.get("userAgent", "")
    }

    save_alert(alert)
    
    estado = get_stats()
    estado["last_update"] = now.isoformat()
    estado["version"] = "3.0"
    STATE_FILE.write_text(json.dumps(estado, indent=2, ensure_ascii=False), encoding="utf-8")

    return jsonify({"ok": True, "alert": alert})

@app.route("/api/last_alert")
@limiter.limit("20 per minute")
def api_last_alert():
    return jsonify({"ok": True, "last": get_last_alert()})

@app.route("/api/alerts")
@limiter.limit("20 per minute")
def get_alerts():
    if session.get("role") not in ["admin", "trusted"]:
        return jsonify({"ok": False, "message": "Não autorizado"}), 401
    
    alerts = get_all_alerts()
    return jsonify(alerts)

# ============================================
# ADMIN
# ============================================

@app.route("/panel/login", methods=["GET", "POST"])
@limiter.limit("5 per minute")
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
            atualizar_last_login(u)
            return redirect("/panel")

        error = True

    return render_template("login_admin.html", error=error)

@app.route("/panel")
@limiter.limit("10 per minute")
def admin_panel():
    if session.get("role") != "admin":
        return redirect("/panel/login")

    alerts = get_all_alerts()
    users = load_users()
    trusted = {k: v for k, v in users.items() if v.get("role") == "trusted"}
    stats = get_stats()
    stats["trusted"] = len(trusted)

    return render_template("panel_admin.html", alerts=alerts, trusted=trusted, stats=stats)

@app.route("/panel/add_trusted", methods=["POST"])
@limiter.limit("5 per minute")
def add_trusted():
    if session.get("role") != "admin":
        return redirect("/panel/login")
    
    name = request.form.get("trusted_name")
    username = request.form.get("trusted_user")
    password = request.form.get("trusted_password")

    users = load_users()

    if username in users:
        return redirect("/panel?err=Usuário+já+existe")

    if len(password) < 4:
        return redirect("/panel?err=Senha+deve+ter+no+mínimo+4+caracteres")

    trusted_count = sum(1 for u in users.values() if u.get("role") == "trusted")
    if trusted_count >= 3:
        return redirect("/panel?err=Máximo+de+3+pessoas+de+confiança+atingido")

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

@app.route("/panel/delete_trusted", methods=["POST"])
def delete_trusted():
    if session.get("role") != "admin":
        return jsonify({"ok": False, "message": "Não autorizado"}), 401
    
    username = request.form.get("username")
    users = load_users()

    if username in users and users[username].get("role") == "trusted":
        del users[username]
        save_users(users)
        return jsonify({"ok": True})

    return jsonify({"ok": False, "message": "Usuário não encontrado"}), 404

@app.route("/logout_admin")
def logout_admin():
    session.clear()
    return redirect("/panel/login")

# ============================================
# TRUSTED
# ============================================

@app.route("/trusted/login", methods=["GET", "POST"])
@limiter.limit("5 per minute")
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
            atualizar_last_login(u)
            return redirect("/trusted/panel")

        error = True

    return render_template("login_trusted.html", error=error)

@app.route("/trusted/panel")
@limiter.limit("10 per minute")
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
        confirm = request.form.get("confirm_password")
        users = load_users()
        username = session.get("trusted")

        if username in users:
            if verificar_senha(old, users[username]["password"]):
                if len(new) >= 4:
                    if new == confirm:
                        users[username]["password"] = criar_hash_senha(new)
                        save_users(users)
                        return render_template("trusted_change_password.html", msg="Senha alterada com sucesso!")
                    else:
                        return render_template("trusted_change_password.html", err="Senhas não coincidem")
                else:
                    return render_template("trusted_change_password.html", err="Senha deve ter no mínimo 4 caracteres")
            else:
                return render_template("trusted_change_password.html", err="Senha atual incorreta")

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
            return render_template("trusted_recover.html", msg="Senha redefinida com sucesso!")
        
        return render_template("trusted_recover.html", err="Usuário não encontrado ou senha muito curta")

    return render_template("trusted_recover.html")

@app.route("/logout_trusted")
def logout_trusted():
    session.clear()
    return redirect("/panic")

# ============================================
# RELATÓRIO PDF
# ============================================

@app.route("/relatorio/pdf")
@limiter.limit("5 per minute")
def relatorio_pdf():
    if session.get("role") != "admin":
        return redirect("/panel/login")
    
    alerts = get_all_alerts()
    stats = get_stats()

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "RELATORIO DE ALERTAS - AURORA MULHER SEGURA", ln=1, align="C")
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 8, f"Gerado em: {datetime.now(BR_TZ).strftime('%d/%m/%Y %H:%M:%S')}", ln=1)
    pdf.cell(0, 8, f"Total de Alertas: {stats['total']}", ln=1)
    pdf.cell(0, 8, f"Alertas Hoje: {stats['today']}", ln=1)
    pdf.cell(0, 8, f"Com Localização: {stats['with_location']}", ln=1)
    pdf.ln(5)
    
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "ULTIMOS ALERTAS:", ln=1)
    pdf.set_font("Arial", "", 9)

    for a in alerts[-20:]:
        linha = f"ID {a['id']} - {a['ts_br']} - {a['name']} - {a['situation']}"
        if a.get("lat"):
            linha += f" - GPS: {a['lat']}, {a['lng']}"
        pdf.cell(0, 6, linha, ln=1)

    temp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(temp.name)

    return send_file(temp.name, as_attachment=True, download_name="relatorio_aurora.pdf")

# ============================================
# HEALTH CHECK
# ============================================

@app.route("/health")
def health():
    return jsonify({
        "ok": True,
        "alerts": len(get_all_alerts()),
        "users_file": USERS_FILE.exists(),
        "alerts_file": ALERTS_FILE.exists(),
        "version": "3.0"
    })

# ============================================
# MIGRAÇÃO DE SENHAS
# ============================================

def migrar_senhas_inicial():
    try:
        migrar_senhas_para_bcrypt()
    except Exception as e:
        print(f"Erro na migração de senhas: {e}")

# ============================================
# START
# ============================================

if __name__ == "__main__":
    ensure_files()
    migrar_senhas_inicial()

    port = int(os.environ.get("PORT", 5000))

    print("=" * 60)
    print("🌸 AURORA MULHER SEGURA v3.0")
    print("=" * 60)
    print("🚀 Sistema iniciado com bcrypt")
    print("📍 Acesse: http://localhost:5000")
    print("🔐 Admin: admin / admin123")
    print("✅ Senhas protegidas com hash bcrypt")
    print("✅ Rota do manifest.json configurada")
    print("✅ Rota do sw.js configurada")
    print("✅ PWA pronto para instalar")
    print("=" * 60)

    app.run(host="0.0.0.0", port=port, debug=True)