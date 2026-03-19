from __future__ import annotations
from flask import Flask, render_template, request, jsonify, redirect, session, send_file
from pathlib import Path
from werkzeug.security import generate_password_hash, check_password_hash
import json
import os
import secrets
import tempfile
from datetime import datetime
from zoneinfo import ZoneInfo
from fpdf import FPDF

# ==========================================
# CONFIGURAÇÃO
# ==========================================

try:
    TZ = ZoneInfo("America/Sao_Paulo")
except Exception:
    TZ = None

BASE_DIR = Path(__file__).resolve().parent
USERS_FILE  = BASE_DIR / "users.json"
ALERTS_FILE = BASE_DIR / "alerts.log"
STATE_FILE  = BASE_DIR / "state.json"

app = Flask(__name__)
_default_key = "aurora-local-dev-key-2026-change-in-production"
app.secret_key = os.environ.get("SECRET_KEY") or _default_key

# ==========================================
# UTILITÁRIOS DE DATA
# ==========================================

def now_br_str():
    if TZ is None:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return datetime.now(TZ).strftime("%Y-%m-%d %H:%M:%S")

def today_str():
    if TZ is None:
        return datetime.now().strftime("%Y-%m-%d")
    return datetime.now(TZ).strftime("%Y-%m-%d")

# ==========================================
# GESTÃO DE ARQUIVOS
# ==========================================

def ensure_files():
    if not USERS_FILE.exists():
        hashed = generate_password_hash("admin123")
        USERS_FILE.write_text(json.dumps({
            "admin": {"password": hashed, "role": "admin", "name": "Admin Aurora", "client_id": None}
        }, indent=2, ensure_ascii=False), encoding="utf-8")
    if not ALERTS_FILE.exists():
        ALERTS_FILE.write_text("", encoding="utf-8")
    if not STATE_FILE.exists():
        STATE_FILE.write_text(json.dumps({"last_id": 0}, indent=2, ensure_ascii=False), encoding="utf-8")

def load_users():
    ensure_files()
    try:
        return json.loads(USERS_FILE.read_text(encoding="utf-8"))
    except Exception:
        hashed = generate_password_hash("admin123")
        return {"admin": {"password": hashed, "role": "admin", "name": "Admin Aurora", "client_id": None}}

def save_users(data):
    USERS_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

def next_alert_id():
    ensure_files()
    try:
        st = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
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
                except Exception:
                    pass
        return alerts
    except Exception:
        return []

def get_alerts_for_client(client_id):
    """Retorna apenas os alertas do cliente específico."""
    all_alerts = get_all_alerts()
    if client_id is None:
        return all_alerts  # admin vê tudo
    return [a for a in all_alerts if a.get("client_id") == client_id]

def require_role(role):
    if session.get("role") != role:
        if role == "admin":
            return redirect("/panel/login")
        return redirect("/trusted/login")
    return None

# ==========================================
# GESTÃO DE CLIENTES
# ==========================================

def get_all_clients():
    """Retorna clientes salvos no users.json (role=client)."""
    users = load_users()
    clients = {}

    # Primeiro coleta clientes registrados com role=client
    for username, info in users.items():
        if info.get("role") == "client":
            cid = info.get("client_id", username)
            clients[cid] = {
                "client_id": cid,
                "name":      info.get("name", cid),
                "users":     []
            }

    # Depois associa trusted aos seus clientes
    for username, info in users.items():
        if info.get("role") == "trusted":
            cid = info.get("client_id")
            if cid:
                if cid not in clients:
                    clients[cid] = {
                        "client_id": cid,
                        "name":      info.get("client_name", cid),
                        "users":     []
                    }
                clients[cid]["users"].append(username)

    return clients

def generate_client_id():
    """Gera um ID único para novo cliente."""
    return secrets.token_hex(8)

# ==========================================
# ROTAS PÚBLICAS
# ==========================================

@app.get("/health")
def health():
    return jsonify({"ok": True, "server_time_br": now_br_str()})

@app.get("/")
def index():
    if not session.get("termo_aceito"):
        return redirect("/termo")
    return render_template("index.html")

@app.get("/panic")
def panic():
    if not session.get("termo_aceito"):
        return redirect("/termo")
    return render_template("panic_button.html")

@app.get("/historico")
def historico():
    alerts = get_all_alerts()
    return render_template("historico.html", alerts=alerts)

@app.get("/ajuda")
def ajuda():
    return render_template("ajuda.html")

@app.get("/plano-seguranca")
@app.get("/plano_seguranca")
def plano_seguranca():
    return render_template("plano_seguranca.html")

@app.get("/saida-rapida")
@app.get("/saida_rapida")
def saida_rapida():
    return render_template("saida_rapida.html")

@app.get("/legal")
def legal():
    return render_template("legal.html")

@app.get("/offline")
def offline():
    return render_template("offline.html")

@app.get("/termo")
@app.get("/termo_responsabilidade")
def termo():
    return render_template("termo_responsabilidade.html")

@app.route("/aceitar-termo", methods=["POST"])
def aceitar_termo():
    session["termo_aceito"] = True
    return redirect("/")

# ==========================================
# API DE ALERTAS
# ==========================================

@app.post("/api/send_alert")
def send_alert():
    data = request.get_json(silent=True) or {}
    location = data.get("location")

    name      = str(data.get("name", "Não informado"))[:100].strip() or "Não informado"
    situation = str(data.get("situation", "Emergência"))[:100].strip() or "Emergência"
    message   = str(data.get("message", ""))[:500].strip()

    # Pega o client_id da sessão se a mulher estiver logada,
    # ou do parâmetro enviado pelo frontend
    client_id = session.get("client_id") or data.get("client_id")

    payload = {
        "id":        next_alert_id(),
        "ts":        now_br_str(),
        "name":      name,
        "situation": situation,
        "message":   message,
        "client_id": client_id,
        "location":  location,
        "lat":       location.get("lat")      if location and isinstance(location, dict) else None,
        "lng":       location.get("lng")      if location and isinstance(location, dict) else None,
        "accuracy":  location.get("accuracy") if location and isinstance(location, dict) else None,
        "ip":        request.remote_addr
    }

    log_alert(payload)
    print(f"✅ Alerta #{payload['id']} — {situation} — cliente: {client_id}")
    if location:
        print(f"📍 {payload.get('lat')}, {payload.get('lng')}")

    return jsonify({"ok": True, "id": payload["id"]})

@app.get("/api/alerts")
def api_alerts():
    """Admin vê tudo. Trusted vê só do seu cliente."""
    role = session.get("role")
    if role == "trusted":
        client_id = session.get("client_id")
        return jsonify(get_alerts_for_client(client_id))
    return jsonify(get_all_alerts())

@app.get("/api/last_alert")
def api_last_alert():
    role = session.get("role")
    if role == "trusted":
        client_id = session.get("client_id")
        alerts = get_alerts_for_client(client_id)
    else:
        alerts = get_all_alerts()

    if not alerts:
        return jsonify({"alerta": False})
    last = alerts[-1]
    return jsonify({
        "alerta":    True,
        "id":        last.get("id"),
        "nome":      last.get("name"),
        "situacao":  last.get("situation"),
        "mensagem":  last.get("message"),
        "hora":      last.get("ts"),
        "lat":       last.get("lat"),
        "lng":       last.get("lng"),
        "localizacao": last.get("location"),
        **last
    })

@app.post("/api/clear_alerts")
def api_clear_alerts():
    if session.get("role") != "admin":
        return jsonify({"ok": False, "error": "Não autorizado"}), 403
    try:
        ALERTS_FILE.write_text("", encoding="utf-8")
        STATE_FILE.write_text('{"last_id": 0}', encoding="utf-8")
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

# ==========================================
# RELATÓRIO PDF
# ==========================================

@app.get("/relatorio/pdf")
def relatorio_pdf():
    if session.get("role") not in ("admin", "trusted"):
        return redirect("/panel/login")

    if session.get("role") == "trusted":
        alerts = get_alerts_for_client(session.get("client_id"))
    else:
        alerts = get_all_alerts()

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 18)
    pdf.cell(0, 10, "RELATORIO DE ALERTAS - AURORA", ln=1)
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 8, f"Gerado em: {now_br_str()} | Total: {len(alerts)} alertas", ln=1)
    pdf.ln(4)
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 8, "-" * 80, ln=1)
    pdf.set_font("Arial", "", 10)

    for a in alerts:
        linha = f"ID {a.get('id','?')} | {a.get('ts','N/A')} | {a.get('name','N/A')} | {a.get('situation','N/A')}"
        pdf.cell(0, 7, linha, ln=1)
        if a.get("message"):
            pdf.cell(0, 6, f"   Mensagem: {a['message'][:80]}", ln=1)
        if a.get("lat") and a.get("lng"):
            pdf.cell(0, 6, f"   GPS: {a['lat']}, {a['lng']}", ln=1)
        pdf.ln(1)

    temp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(temp.name)
    temp.close()

    try:
        return send_file(temp.name, as_attachment=True, download_name="relatorio_aurora.pdf")
    finally:
        try:
            os.unlink(temp.name)
        except Exception:
            pass

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

        if info:
            stored = info.get("password", "")
            ok = False
            if stored.startswith("pbkdf2:") or stored.startswith("scrypt:"):
                ok = check_password_hash(stored, p)
            else:
                ok = (stored == p)
                if ok:
                    info["password"] = generate_password_hash(p)
                    save_users(users)

            if ok and info.get("role") == "admin":
                session.clear()
                session["role"]  = "admin"
                session["user"]  = u
                return redirect("/panel")

        return render_template("login_admin.html", error=True)

    return render_template("login_admin.html")

@app.get("/panel")
def admin_panel():
    redir = require_role("admin")
    if redir:
        return redir
    try:
        users   = load_users()
        trusted = {u: info for u, info in users.items() if info.get("role") == "trusted"}
        alerts  = get_all_alerts()
        clients = get_all_clients()

        stats = {
            "total":            len(alerts),
            "today":            sum(1 for a in alerts if a.get("ts", "").startswith(today_str())),
            "trusted":          len(trusted),
            "with_location":    sum(1 for a in alerts if a.get("lat")),
            "without_location": sum(1 for a in alerts if not a.get("lat")),
            "clients":          len(clients),
        }

        return render_template("panel_admin.html",
                               trusted=trusted,
                               alerts=alerts,
                               stats=stats,
                               clients=clients)
    except Exception as e:
        print(f"❌ admin_panel error: {e}")
        session.clear()
        return redirect("/panel/login")

@app.post("/panel/add_client")
def admin_add_client():
    """Cria um novo cliente — salvo dentro do users.json para persistir no Render."""
    redir = require_role("admin")
    if redir:
        return redir

    client_name = request.form.get("client_name", "").strip()
    if not client_name:
        return redirect("/panel?err=Preencha+o+nome+do+cliente")

    client_id = generate_client_id()

    # FIX: Salva cliente dentro do users.json com role="client"
    users = load_users()
    users[f"__client__{client_id}"] = {
        "role":       "client",
        "name":       client_name,
        "client_id":  client_id,
        "created_at": now_br_str(),
        "password":   ""
    }
    save_users(users)

    return redirect(f"/panel?msg=Cliente+criada:+{client_name}&client_id={client_id}")

@app.post("/panel/add_trusted")
def admin_add_trusted():
    redir = require_role("admin")
    if redir:
        return redir

    name      = request.form.get("trusted_name", "").strip()
    username  = request.form.get("trusted_user", "").strip().lower()
    password  = request.form.get("trusted_password", "")
    client_id = request.form.get("client_id", "").strip()

    if not name or not username or not password:
        return redirect("/panel?err=Preencha+todos+os+campos")
    if len(password) < 4:
        return redirect("/panel?err=Senha+muito+curta")

    users = load_users()
    if username in users:
        return redirect("/panel?err=Usuario+ja+existe")

    # Carrega nome do cliente direto do users.json
    client_name = client_id
    client_entry = users.get(f"__client__{client_id}", {})
    if client_entry:
        client_name = client_entry.get("name", client_id)

    users[username] = {
        "password":    generate_password_hash(password),
        "role":        "trusted",
        "name":        name,
        "client_id":   client_id or None,
        "client_name": client_name
    }
    save_users(users)
    return redirect(f"/panel?msg=Pessoa+cadastrada:+{name}")

@app.post("/panel/delete_trusted")
def admin_delete_trusted():
    redir = require_role("admin")
    if redir:
        return redir

    username = request.form.get("username", "").strip()
    users = load_users()

    if username in users and users[username].get("role") == "trusted":
        users.pop(username)
        save_users(users)
        return redirect("/panel?msg=Pessoa+removida")

    return redirect("/panel?err=Erro+ao+remover")

@app.post("/panel/delete_client")
def admin_delete_client():
    """Remove um cliente e todos os seus trusted."""
    redir = require_role("admin")
    if redir:
        return redir

    client_id = request.form.get("client_id", "").strip()
    if not client_id:
        return redirect("/panel?err=Cliente+não+encontrado")

    # Remove trusted do cliente
    users = load_users()
    to_remove = [u for u, info in users.items()
                 if info.get("client_id") == client_id and info.get("role") == "trusted"]
    for u in to_remove:
        users.pop(u)
    save_users(users)

    # Remove entrada __client__ do users.json
    client_key = f"__client__{client_id}"
    if client_key in users:
        users.pop(client_key)
    save_users(users)

    return redirect("/panel?msg=Cliente+removido")

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

        if info and info.get("role") == "trusted":
            stored = info.get("password", "")
            ok = False
            if stored.startswith("pbkdf2:") or stored.startswith("scrypt:"):
                ok = check_password_hash(stored, p)
            else:
                ok = (stored == p)
                if ok:
                    info["password"] = generate_password_hash(p)
                    save_users(users)

            if ok:
                session.clear()
                session["role"]        = "trusted"
                session["trusted"]     = u
                session["client_id"]   = info.get("client_id")
                session["client_name"] = info.get("client_name", "")
                return redirect("/trusted/panel")

        return render_template("login_trusted.html", error=True)

    return render_template("login_trusted.html")

@app.get("/trusted/panel")
def trusted_panel():
    redir = require_role("trusted")
    if redir:
        return redir
    try:
        users = load_users()
        u = session.get("trusted")
        if not u:
            session.clear()
            return redirect("/trusted/login")

        client_id    = session.get("client_id")
        display_name = users.get(u, {}).get("name") or u
        # Apenas alertas do cliente desta pessoa de confiança
        alerts = get_alerts_for_client(client_id)[-10:]

        return render_template("panel_trusted.html",
                               display_name=display_name,
                               alerts=alerts)
    except Exception as e:
        print(f"❌ trusted_panel error: {e}")
        session.clear()
        return redirect("/trusted/login")

@app.get("/logout_trusted")
def logout_trusted():
    session.clear()
    return redirect("/trusted/login")

@app.route("/trusted/change_password", methods=["GET", "POST"])
def trusted_change_password():
    redir = require_role("trusted")
    if redir:
        return redir

    if request.method == "POST":
        users  = load_users()
        u      = session.get("trusted")
        old_pw = request.form.get("old_password", "")
        new_pw = request.form.get("new_password", "")
        confirm= request.form.get("confirm_password", "")

        if new_pw != confirm:
            return render_template("trusted_change_password.html", err="As senhas não coincidem.")
        if len(new_pw) < 4:
            return render_template("trusted_change_password.html", err="Senha muito curta.")

        info   = users.get(u, {})
        stored = info.get("password", "")
        ok     = check_password_hash(stored, old_pw) if stored.startswith("pbkdf2:") or stored.startswith("scrypt:") else (stored == old_pw)

        if not ok:
            return render_template("trusted_change_password.html", err="Senha atual incorreta.")

        users[u]["password"] = generate_password_hash(new_pw)
        save_users(users)
        return render_template("trusted_change_password.html", msg="Senha alterada com sucesso!")

    return render_template("trusted_change_password.html")

@app.route("/trusted/recover", methods=["GET", "POST"])
def trusted_recover():
    if request.method == "POST":
        users = load_users()
        u     = request.form.get("usuario", "").strip().lower()
        nova  = request.form.get("nova_senha", "")

        if len(nova) < 4:
            return render_template("trusted_recover.html", err="Senha muito curta.")
        if u not in users or users[u].get("role") != "trusted":
            return render_template("trusted_recover.html", err="Usuário não encontrado.")

        users[u]["password"] = generate_password_hash(nova)
        save_users(users)
        return render_template("trusted_recover.html", msg="Senha redefinida! Faça login.")

    return render_template("trusted_recover.html")

# ==========================================
# AURORA IA — Proxy Anthropic
# ==========================================

@app.post("/api/aurora-ia")
def aurora_ia_chat():
    import urllib.request
    import json as _json

    data     = request.get_json(silent=True) or {}
    messages = data.get("messages", [])
    if not messages:
        return jsonify({"error": "No messages"}), 400

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return jsonify({"reply": "Aurora IA não configurada. Defina ANTHROPIC_API_KEY no servidor."}), 200

    SYSTEM = (
        "Você é a Aurora IA, assistente virtual especializada em apoio a mulheres "
        "vítimas de violência doméstica no Brasil. Ofereça acolhimento, empatia e "
        "informações sobre: Lei Maria da Penha, medidas protetivas, canais de ajuda "
        "(180, 190, DEAM, CRAM), como reconhecer abuso e sair com segurança. "
        "Seja gentil, sem julgamentos, nunca culpe a vítima. Em perigo imediato "
        "oriente sempre a ligar 190 ou 180. Respostas curtas em português do Brasil."
    )

    payload = _json.dumps({
        "model":      "claude-haiku-4-5-20251001",
        "max_tokens": 800,
        "system":     SYSTEM,
        "messages":   messages[-20:]
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "Content-Type":      "application/json",
            "x-api-key":         api_key,
            "anthropic-version": "2023-06-01"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = _json.loads(resp.read().decode("utf-8"))
            return jsonify({"reply": result["content"][0]["text"]})
    except Exception as e:
        print(f"❌ Aurora IA error: {e}")
        return jsonify({"reply": "Sem conexão no momento. Ligue 180 ou 190 se precisar de ajuda urgente. 💜"}), 200

# ==========================================
# ROTAS ADICIONAIS
# ==========================================

@app.get("/pagamentos")
def pagamentos():
    return render_template("pagamentos.html")

@app.get("/recibo")
@app.get("/recibo_entrega")
def recibo():
    return render_template("recibo_entrega.html")

@app.get("/central")
@app.get("/central_aurora")
def central():
    alerts = get_all_alerts()
    return render_template("central_aurora.html", alerts=alerts)

@app.get("/anual")
@app.get("/manual")
def anual():
    return render_template("anual_aurora.html")

@app.get("/confidant")
@app.get("/panel_confidant")
def panel_confidant():
    return render_template("panel_confidant.html")

@app.get("/aurora-ia")
@app.get("/ia")
def aurora_ia():
    return render_template("aurora_ia.html")

# /debug/users removido por segurança em produção

# ==========================================
# START
# ==========================================

if __name__ == "__main__":
    ensure_files()
    print("=" * 60)
    print("🌸 AURORA MULHER SEGURA v3.2 — MULTI-CLIENTE")
    print("=" * 60)
    print("🚀 http://localhost:5000")
    print("🔐 Admin: admin / admin123")
    print("=" * 60)
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
