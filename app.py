from __future__ import annotations
from flask import Flask, render_template, request, jsonify, redirect, session, url_for, send_file
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
USERS_FILE = BASE_DIR / "users.json"
ALERTS_FILE = BASE_DIR / "alerts.log"
STATE_FILE = BASE_DIR / "state.json"

app = Flask(__name__)
# FIX: Fixed fallback key so session survives server restarts during local testing
# In production, always set SECRET_KEY as an environment variable on Render.com
_default_key = "aurora-local-dev-key-2026-change-in-production"
app.secret_key = os.environ.get("SECRET_KEY") or _default_key

# ==========================================
# UTILITÁRIOS
# ==========================================

def now_br_str():
    if TZ is None:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return datetime.now(TZ).strftime("%Y-%m-%d %H:%M:%S")

def today_str():
    if TZ is None:
        return datetime.now().strftime("%Y-%m-%d")
    return datetime.now(TZ).strftime("%Y-%m-%d")

def ensure_files():
    if not USERS_FILE.exists():
        # FIX: Default admin password is hashed, not plaintext
        hashed = generate_password_hash("admin123")
        USERS_FILE.write_text(json.dumps({
            "admin": {"password": hashed, "role": "admin", "name": "Admin Aurora"}
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
        return {"admin": {"password": hashed, "role": "admin", "name": "Admin Aurora"}}

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

def require_role(role):
    """Check session role, redirect if not authorized."""
    if session.get("role") != role:
        if role == "admin":
            return redirect("/panel/login")
        return redirect("/trusted/login")
    return None

# ==========================================
# ROTAS PÚBLICAS
# ==========================================

@app.get("/health")
def health():
    return jsonify({"ok": True, "server_time_br": now_br_str()})

@app.get("/")
def index():
    # Se ainda não aceitou o termo, redireciona para assinar primeiro
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

# FIX: Both hyphen and underscore accepted for safety
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

    # Sanitize string inputs
    name = str(data.get("name", "Não informado"))[:100].strip() or "Não informado"
    situation = str(data.get("situation", "Emergência"))[:100].strip() or "Emergência"
    message = str(data.get("message", ""))[:500].strip()

    payload = {
        "id": next_alert_id(),
        "ts": now_br_str(),
        "name": name,
        "situation": situation,
        "message": message,
        "location": location,
        # FIX: Flatten lat/lng to top level for easy access by trusted panel
        "lat": location.get("lat") if location and isinstance(location, dict) else None,
        "lng": location.get("lng") if location and isinstance(location, dict) else None,
        "accuracy": location.get("accuracy") if location and isinstance(location, dict) else None,
        "ip": request.remote_addr
    }

    log_alert(payload)
    print(f"✅ Alerta #{payload['id']} — {situation}")
    if location:
        print(f"📍 {payload.get('lat')}, {payload.get('lng')}")

    return jsonify({"ok": True, "id": payload["id"]})

@app.get("/api/alerts")
def api_alerts():
    return jsonify(get_all_alerts())

@app.get("/api/last_alert")
def api_last_alert():
    """FIX: Added missing endpoint that trusted.js depends on."""
    alerts = get_all_alerts()
    if not alerts:
        return jsonify({"alerta": False})
    last = alerts[-1]
    return jsonify({
        "alerta": True,
        "id": last.get("id"),
        "nome": last.get("name"),
        "situacao": last.get("situation"),
        "mensagem": last.get("message"),
        "hora": last.get("ts"),
        "lat": last.get("lat"),
        "lng": last.get("lng"),
        "localizacao": last.get("location"),
        **last
    })

# ==========================================
# RELATÓRIO PDF
# ==========================================

@app.get("/relatorio/pdf")
def relatorio_pdf():
    if session.get("role") not in ("admin", "trusted"):
        return redirect("/panel/login")

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

    # FIX: Delete temp file after sending to avoid disk leak
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

        # FIX: Support both hashed passwords (new) and plaintext (legacy migration)
        if info:
            stored = info.get("password", "")
            ok = False
            if stored.startswith("pbkdf2:") or stored.startswith("scrypt:"):
                ok = check_password_hash(stored, p)
            else:
                # Legacy plaintext — verify then upgrade
                ok = (stored == p)
                if ok:
                    info["password"] = generate_password_hash(p)
                    save_users(users)

            if ok and info.get("role") == "admin":
                session.clear()
                session["role"] = "admin"
                session["user"] = u
                return redirect("/panel")

        return render_template("login_admin.html", error=True)

    return render_template("login_admin.html")

@app.get("/panel")
def admin_panel():
    redir = require_role("admin")
    if redir:
        return redir
    try:
        users = load_users()
        trusted = {u: info for u, info in users.items() if info.get("role") == "trusted"}
        alerts = get_all_alerts()
        stats = {
            "total": len(alerts),
            "today": sum(1 for a in alerts if a.get("ts", "").startswith(today_str())),
            "trusted": len(trusted),
            "with_location": sum(1 for a in alerts if a.get("lat")),
            "without_location": sum(1 for a in alerts if not a.get("lat")),
        }
        return render_template("panel_admin.html", trusted=trusted, alerts=alerts, stats=stats)
    except Exception as e:
        print(f"❌ admin_panel error: {e}")
        session.clear()
        return redirect("/panel/login")

@app.post("/panel/add_trusted")
def admin_add_trusted():
    redir = require_role("admin")
    if redir:
        return redir

    name = request.form.get("trusted_name", "").strip()
    username = request.form.get("trusted_user", "").strip().lower()
    password = request.form.get("trusted_password", "")

    if not name or not username or not password:
        return redirect("/panel?err=Preencha+todos+os+campos")
    if len(password) < 4:
        return redirect("/panel?err=Senha+muito+curta")

    users = load_users()
    if username in users:
        return redirect("/panel?err=Usuario+ja+existe")

    users[username] = {
        "password": generate_password_hash(password),
        "role": "trusted",
        "name": name
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
                session["role"] = "trusted"
                session["trusted"] = u
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
        display_name = users.get(u, {}).get("name") or u
        alerts = get_all_alerts()[-10:]
        return render_template("panel_trusted.html", display_name=display_name, alerts=alerts)
    except Exception as e:
        print(f"❌ trusted_panel error: {e}")
        session.clear()
        return redirect("/trusted/login")

@app.get("/logout_trusted")
def logout_trusted():
    session.clear()
    return redirect("/trusted/login")

# ==========================================
# START
# ==========================================


# ==========================================
# DEBUG — TEMPORARY (remove after fixing login)
# ==========================================

@app.get("/debug/users")
def debug_users():
    """Shows registered users WITHOUT passwords — for troubleshooting only."""
    users = load_users()
    safe = {}
    for u, info in users.items():
        safe[u] = {
            "name": info.get("name"),
            "role": info.get("role"),
            "password_type": "hashed" if str(info.get("password","")).startswith("pbkdf2:") or str(info.get("password","")).startswith("scrypt:") else "plaintext"
        }
    return jsonify(safe)


# ==========================================
# AURORA IA — Proxy para API Anthropic
# ==========================================

@app.post("/api/aurora-ia")
def aurora_ia_chat():
    """Proxy the AI request server-side to avoid CORS issues in browser."""
    import urllib.request
    import json as _json

    data = request.get_json(silent=True) or {}
    messages = data.get("messages", [])
    if not messages:
        return jsonify({"error": "No messages"}), 400

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return jsonify({"reply": "Aurora IA não configurada. Defina a variável ANTHROPIC_API_KEY no servidor."}), 200

    SYSTEM = (
        "Você é a Aurora IA, assistente virtual especializada em apoio a mulheres "
        "vítimas de violência doméstica no Brasil. Ofereça acolhimento, empatia e "
        "informações sobre: Lei Maria da Penha, medidas protetivas, canais de ajuda "
        "(180, 190, DEAM, CRAM), como reconhecer abuso e sair com segurança. "
        "Seja gentil, sem julgamentos, nunca culpe a vítima. Em perigo imediato "
        "oriente sempre a ligar 190 ou 180. Respostas curtas em português do Brasil."
    )

    payload = _json.dumps({
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 800,
        "system": SYSTEM,
        "messages": messages[-20:]
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = _json.loads(resp.read().decode("utf-8"))
            reply = result["content"][0]["text"]
            return jsonify({"reply": reply})
    except Exception as e:
        print(f"❌ Aurora IA error: {e}")
        return jsonify({"reply": "Sem conexão no momento. Ligue 180 ou 190 se precisar de ajuda urgente. 💜"}), 200



# ==========================================
# TRUSTED — CHANGE PASSWORD & RECOVER
# ==========================================

@app.route("/trusted/change_password", methods=["GET", "POST"])
def trusted_change_password():
    redir = require_role("trusted")
    if redir:
        return redir

    if request.method == "POST":
        users = load_users()
        u = session.get("trusted")
        old_pw = request.form.get("old_password", "")
        new_pw = request.form.get("new_password", "")
        confirm = request.form.get("confirm_password", "")

        if new_pw != confirm:
            return render_template("trusted_change_password.html", err="As senhas não coincidem.")

        if len(new_pw) < 4:
            return render_template("trusted_change_password.html", err="Senha muito curta (mínimo 4 caracteres).")

        info = users.get(u, {})
        stored = info.get("password", "")
        ok = False
        if stored.startswith("pbkdf2:") or stored.startswith("scrypt:"):
            ok = check_password_hash(stored, old_pw)
        else:
            ok = (stored == old_pw)

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
        u = request.form.get("usuario", "").strip().lower()
        nova = request.form.get("nova_senha", "")

        if len(nova) < 4:
            return render_template("trusted_recover.html", err="Senha muito curta.")

        if u not in users or users[u].get("role") != "trusted":
            return render_template("trusted_recover.html", err="Usuário não encontrado.")

        users[u]["password"] = generate_password_hash(nova)
        save_users(users)
        return render_template("trusted_recover.html", msg="Senha redefinida! Faça login.")

    return render_template("trusted_recover.html")


# ==========================================
# API — CLEAR ALERTS (admin only)
# ==========================================

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
# ROTAS ADICIONAIS (pagamentos, central, anual, recibo, confidant)
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

# ==========================================
# AURORA IA — Assistente de apoio
# ==========================================

@app.get("/aurora-ia")
@app.get("/ia")
def aurora_ia():
    return render_template("aurora_ia.html")

if __name__ == "__main__":
    ensure_files()
    print("=" * 60)
    print("🌸 AURORA MULHER SEGURA v3.1 — CORRIGIDA")
    print("=" * 60)
    print("🚀 http://localhost:5000")
    print("🔐 Admin: admin / admin123 (senha será atualizada ao logar)")
    print("=" * 60)
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
