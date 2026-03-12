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
import bcrypt  # ADICIONADO: bcrypt para hash de senhas

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
        # ADICIONADO: Cria usuário admin com hash bcrypt
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


# ==================================================
# UTILIDADES
# ==================================================
def load_users():
    ensure_files()
    try:
        return json.loads(USERS_FILE.read_text(encoding="utf-8"))
    except:
        return {}

def save_users(users):
    """ADICIONADO: Função para salvar usuários"""
    USERS_FILE.write_text(json.dumps(users, indent=2, ensure_ascii=False), encoding="utf-8")

def verificar_senha(senha_digitada, hash_armazenado):
    """ADICIONADO: Verifica senha com bcrypt"""
    try:
        # Se o hash não estiver no formato bcrypt (senha antiga em texto puro)
        if not hash_armazenado.startswith('$2b$'):
            # Comparação direta para migração
            return senha_digitada == hash_armazenado
        return bcrypt.checkpw(
            senha_digitada.encode('utf-8'), 
            hash_armazenado.encode('utf-8')
        )
    except Exception as e:
        print(f"Erro ao verificar senha: {e}")
        return False

def atualizar_last_login(usuario):
    """ADICIONADO: Atualiza timestamp do último login"""
    try:
        users = load_users()
        if usuario in users:
            users[usuario]['last_login'] = datetime.now(BR_TZ).isoformat()
            save_users(users)
    except Exception as e:
        print(f"Erro ao atualizar last_login: {e}")

def criar_hash_senha(senha):
    """ADICIONADO: Cria hash bcrypt para uma senha"""
    return bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def migrar_senhas_para_bcrypt():
    """ADICIONADO: Migra senhas antigas para bcrypt (uma vez)"""
    users = load_users()
    modificado = False
    
    for user, data in users.items():
        password = data.get('password', '')
        # Se a senha não é hash bcrypt (não começa com $2b$)
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
# CENTRAL AURORA (NOVO)
# ==================================================
@app.route("/central")
def central():
    return render_template("central_aurora.html")

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
        "lat": data.get("lat"),
        "lng": data.get("lng"),
        "accuracy": data.get("accuracy")
    }

    save_alert(alert)

    return jsonify({"ok": True, "alert": alert})


@app.route("/api/last_alert")
def api_last_alert():

    return jsonify({
        "ok": True,
        "last": get_last_alert()
    })


@app.route("/api/alerts")
def get_alerts():

    alerts = get_all_alerts()

    return jsonify(alerts)


# ==================================================
# ADMIN - MODIFICADO PARA USAR BCRYPT
# ==================================================
@app.route("/panel/login", methods=["GET", "POST"])
def admin_login():

    users = load_users()

    error = False

    if request.method == "POST":

        u = request.form.get("user")
        p = request.form.get("password")

        info = users.get(u)

        # MODIFICADO: Usa verificar_senha() com bcrypt
        if info and info.get("role") == "admin" and verificar_senha(p, info.get("password", "")):

            session["role"] = "admin"
            session["user"] = u
            
            # ADICIONADO: Atualiza último login
            atualizar_last_login(u)

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

    alerts_hoje = 0

    for alert in alerts:

        if alert.get("ts_br", "").startswith(hoje):
            alerts_hoje += 1

    stats = {
        "total": len(alerts),
        "today": alerts_hoje,  # MODIFICADO: de "hoje" para "today" (padronização)
        "trusted": len(trusted)
    }

    return render_template(
        "panel_admin.html",
        alerts=alerts,
        trusted=trusted,
        stats=stats
    )


@app.route("/panel/add_trusted", methods=["POST"])
def add_trusted():
    """ADICIONADO: Rota para adicionar pessoa de confiança"""
    if session.get("role") != "admin":
        return redirect("/panel/login")
    
    name = request.form.get("trusted_name")
    username = request.form.get("trusted_user")
    password = request.form.get("trusted_password")
    
    users = load_users()
    
    if username in users:
        return redirect("/panel?err=Usuário já existe")
    
    # Cria hash da senha
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
    """ADICIONADO: Rota para deletar pessoa de confiança"""
    if session.get("role") != "admin":
        return redirect("/panel/login")
    
    username = request.form.get("username")
    
    users = load_users()
    
    if username in users and users[username].get("role") == "trusted":
        del users[username]
        save_users(users)
        return "", 200
    
    return "Usuário não encontrado", 404


@app.route("/logout_admin")
def logout_admin():
    session.clear()
    return redirect("/panel/login")


# ==================================================
# TRUSTED - MODIFICADO PARA USAR BCRYPT
# ==================================================
@app.route("/trusted/login", methods=["GET", "POST"])
def trusted_login():

    users = load_users()

    error = False

    if request.method == "POST":

        u = request.form.get("user")
        p = request.form.get("password")

        info = users.get(u)

        # MODIFICADO: Usa verificar_senha() com bcrypt
        if info and info.get("role") == "trusted" and verificar_senha(p, info.get("password", "")):

            session["role"] = "trusted"
            session["trusted"] = u
            
            # ADICIONADO: Atualiza último login
            atualizar_last_login(u)

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


@app.route("/trusted/change_password", methods=["POST"])
def trusted_change_password():
    """ADICIONADO: Rota para alterar senha"""
    if session.get("role") != "trusted":
        return redirect("/trusted/login")
    
    old = request.form.get("old_password")
    new = request.form.get("new_password")
    
    users = load_users()
    username = session.get("trusted")
    
    if username in users:
        # Verifica senha atual
        if verificar_senha(old, users[username]["password"]):
            # Atualiza para nova senha
            users[username]["password"] = criar_hash_senha(new)
            save_users(users)
            return redirect("/trusted/panel?msg=Senha+alterada")
    
    return redirect("/trusted/panel?err=Senha+atual+incorreta")


@app.route("/trusted/recover", methods=["POST"])
def trusted_recover():
    """ADICIONADO: Rota para recuperar senha (admin only)"""
    # Esta rota deveria ser apenas para admin
    # Implementação básica - em produção, use email
    return redirect("/trusted/login?err=Função+desabilitada")


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

        pdf.cell(
            0,
            8,
            f"ID {a['id']} - {a['ts_br']} - {a['name']} - {a['situation']}",
            ln=1
        )

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
# MIGRAÇÃO DE SENHAS (executa uma vez na inicialização)
# ==================================================
def migrar_senhas_inicial():
    """ADICIONADO: Migra senhas antigas para bcrypt na inicialização"""
    try:
        migrar_senhas_para_bcrypt()
    except Exception as e:
        print(f"Erro na migração de senhas: {e}")


# ==================================================
# START
# ==================================================
if __name__ == "__main__":

    ensure_files()
    
    # ADICIONADO: Migra senhas antigas para bcrypt
    migrar_senhas_inicial()

    port = int(os.environ.get("PORT", 5000))

    print("🚀 AURORA SISTEMA INICIADO COM BCRYPT")
    print("http://localhost:5000")
    print("✅ Senhas protegidas com hash bcrypt")

    app.run(host="0.0.0.0", port=port, debug=True)