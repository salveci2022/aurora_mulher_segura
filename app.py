"""
Aurora Mulher Segura — Sistema SOS de Proteção Feminina
Versão 3.3 SafeHer — SpyNet Tecnologia Forense
"""

from flask import (
    Flask, render_template, request, jsonify,
    redirect, url_for, session, send_file
)
from werkzeug.security import generate_password_hash, check_password_hash
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os, json, secrets
from pathlib import Path
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", secrets.token_hex(32))
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("FLASK_ENV") == "production",
    PERMANENT_SESSION_LIFETIME=timedelta(hours=12),
)

TZ = ZoneInfo("America/Sao_Paulo")
limiter = Limiter(get_remote_address, app=app,
    default_limits=["300 per minute"], storage_uri="memory://")
app.jinja_env.globals["csrf_token"] = lambda: csrf_get_token()

BASE_DIR    = Path(os.environ.get("RENDER_DATA_DIR", "."))
USERS_FILE  = BASE_DIR / "users.json"
ALERTS_FILE = BASE_DIR / "alerts.log"

ZAPI_INSTANCE = os.environ.get("ZAPI_INSTANCE", "").strip()
ZAPI_TOKEN    = os.environ.get("ZAPI_TOKEN", "").strip()
ZAPI_PHONE    = os.environ.get("ZAPI_PHONE", "").strip()


def now_br_str():
    return datetime.now(TZ).strftime("%d/%m/%Y %H:%M:%S")


def ensure_files():
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    if not USERS_FILE.exists():
        # Antes: senha padrão fixa "admin123" — previsível e igual em toda instalação.
        # Agora: gera uma senha aleatória forte na primeira execução e imprime
        # nos logs do servidor (Render -> Logs) para o operador copiar uma única vez.
        senha_inicial = secrets.token_urlsafe(12)
        USERS_FILE.write_text(json.dumps({
            "admin": {"password": generate_password_hash(senha_inicial),
                      "role": "admin", "name": "Admin Aurora"}
        }, indent=2, ensure_ascii=False), encoding="utf-8")
        print("=" * 60)
        print("PRIMEIRA EXECUÇÃO: conta admin criada.")
        print(f"  usuário: admin")
        print(f"  senha:   {senha_inicial}")
        print("Anote agora — essa senha não será mostrada de novo nos logs.")
        print("=" * 60)
    if not ALERTS_FILE.exists():
        ALERTS_FILE.write_text("", encoding="utf-8")


def load_users():
    try:
        return json.loads(USERS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_users(u):
    USERS_FILE.write_text(json.dumps(u, indent=2, ensure_ascii=False), encoding="utf-8")


def log_alert(p):
    with open(ALERTS_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(p, ensure_ascii=False) + "\n")


def get_all_alerts():
    alerts = []
    try:
        for line in ALERTS_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                try:
                    alerts.append(json.loads(line))
                except Exception:
                    pass
    except Exception:
        pass
    return list(reversed(alerts))


def next_alert_id():
    alerts = get_all_alerts()
    if not alerts:
        return 1
    ids = [a.get("id", 0) for a in alerts if isinstance(a.get("id"), int)]
    return (max(ids) + 1) if ids else 1


def get_all_clients():
    users = load_users()
    clients = {}
    for username, info in users.items():
        if info.get("role") == "client":
            cid = info.get("client_id", username)
            clients[cid] = {"client_id": cid, "name": info.get("name", cid), "users": []}
    for username, info in users.items():
        if info.get("role") == "trusted":
            cid = info.get("client_id")
            if cid:
                if cid not in clients:
                    clients[cid] = {"client_id": cid, "name": info.get("client_name", cid), "users": []}
                clients[cid]["users"].append(username)
    return clients


def csrf_get_token():
    if "_csrf_token" not in session:
        session["_csrf_token"] = secrets.token_hex(16)
    return session["_csrf_token"]


def csrf_valido():
    """Verifica o token CSRF enviado (header, JSON body ou form) contra o da sessão."""
    esperado = session.get("_csrf_token")
    enviado = (
        request.headers.get("X-CSRF-Token")
        or (request.get_json(silent=True) or {}).get("_csrf_token")
        or request.form.get("_csrf_token")
    )
    return bool(esperado) and bool(enviado) and secrets.compare_digest(esperado, enviado)


def generate_client_id():
    return secrets.token_hex(8)


def enviar_whatsapp(msg):
    if not all([ZAPI_INSTANCE, ZAPI_TOKEN, ZAPI_PHONE]):
        return
    try:
        import urllib.request as ur
        url = f"https://api.z-api.io/instances/{ZAPI_INSTANCE}/token/{ZAPI_TOKEN}/send-text"
        data = json.dumps({"phone": ZAPI_PHONE, "message": msg}).encode()
        req = ur.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
        ur.urlopen(req, timeout=5)
    except Exception as e:
        print(f"WhatsApp error: {e}")


@app.after_request
def security_headers(resp):
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["X-Frame-Options"] = "SAMEORIGIN"
    return resp


# ── Rotas públicas ────────────────────────────────────────────
@app.get("/health")
def health():
    return jsonify({"ok": True, "server_time_br": now_br_str(), "version": "3.3-SAFEHER"})

@app.get("/")
def index():
    return render_template("index.html")

@app.get("/panic")
def panic():
    return render_template("panic_button.html")

@app.get("/historico")
def historico():
    return render_template("historico.html", alerts=get_all_alerts())

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
    return render_template("legal.html")

@app.route("/aceitar-termo", methods=["POST"])
def aceitar_termo():
    session["termo_aceito"] = True
    return redirect("/")

@app.get("/bem-estar")
@app.get("/bem_estar")
def bem_estar():
    return render_template("bem_estar.html")

@app.get("/pagamentos")
def pagamentos():
    return render_template("pagamentos.html")

@app.get("/kit-entrega")
def kit_entrega():
    return render_template("kit_entrega.html")

@app.get("/aurora-ia")
def aurora_ia_page():
    return render_template("aurora_ia.html")


# ── API Alertas ───────────────────────────────────────────────
@app.post("/api/send_alert")
@limiter.limit("30 per minute")
def send_alert():
    data = request.get_json(silent=True) or {}
    location  = data.get("location")
    name      = str(data.get("name", "Não informado"))[:100].strip() or "Não informado"
    situation = str(data.get("situation", "Emergência"))[:100].strip() or "Emergência"
    message   = str(data.get("message", ""))[:500].strip()
    client_id = session.get("client_id") or data.get("client_id")

    payload = {
        "id": next_alert_id(), "ts": now_br_str(),
        "name": name, "situation": situation, "message": message,
        "client_id": client_id, "location": location,
        "lat": location.get("lat") if location and isinstance(location, dict) else None,
        "lng": location.get("lng") if location and isinstance(location, dict) else None,
        "accuracy": location.get("accuracy") if location and isinstance(location, dict) else None,
        "ip": request.remote_addr
    }
    log_alert(payload)

    lat = payload.get("lat"); lng = payload.get("lng")
    maps = f"https://www.google.com/maps?q={lat},{lng}" if lat and lng else "GPS indisponivel"
    enviar_whatsapp(f"SOS AURORA #{payload['id']}\n{name}\n{situation}\n{payload['ts']}\n{maps}")
    return jsonify({"ok": True, "id": payload["id"]})


@app.get("/api/alerts")
def api_alerts():
    if not (session.get("admin_auth") or session.get("trusted_auth")):
        return jsonify({"error": "Nao autorizado"}), 401
    client_id = request.args.get("client_id")
    alerts = get_all_alerts()
    if client_id:
        alerts = [a for a in alerts if a.get("client_id") == client_id]
    return jsonify(alerts)


# ── Aurora IA ─────────────────────────────────────────────────
@app.post("/api/aurora-ia")
@limiter.limit("30 per minute")
def aurora_ia_chat():
    import urllib.request as ur
    data = request.get_json(silent=True) or {}
    messages = data.get("messages", [])
    if not messages:
        return jsonify({"error": "No messages"}), 400
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return jsonify({"reply": "Aurora IA nao configurada."})

    SYSTEM = ("Voce e a Aurora IA, assistente para mulheres vitimas de violencia no Brasil. "
              "Ofereca acolhimento, empatia e informacoes sobre Lei Maria da Penha, "
              "canais de ajuda (180, 190, DEAM). Seja gentil, sem julgamentos. "
              "Em perigo imediato oriente a ligar 190 ou 180. Respostas curtas em portugues.")

    payload_ia = json.dumps({
        "model": "claude-haiku-4-5-20251001", "max_tokens": 800,
        "system": SYSTEM, "messages": messages[-20:]
    }).encode("utf-8")

    req = ur.Request("https://api.anthropic.com/v1/messages", data=payload_ia,
        headers={"Content-Type": "application/json", "x-api-key": api_key,
                 "anthropic-version": "2023-06-01"}, method="POST")
    try:
        with ur.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return jsonify({"reply": result["content"][0]["text"]})
    except Exception as e:
        print(f"Aurora IA error: {e}")
        return jsonify({"reply": "Ligue 180 ou 190 se precisar de ajuda urgente."})


# ── Login Admin ───────────────────────────────────────────────
@app.route("/login", methods=["GET", "POST"])
@app.route("/login_admin", methods=["GET", "POST"])
def login_admin():
    if request.method == "POST":
        u = (request.form.get("username") or "").strip()
        p = (request.form.get("password") or "").strip()
        users = load_users()
        user = users.get(u)
        if user and user.get("role") == "admin" and check_password_hash(user["password"], p):
            session.permanent = True
            session["admin_auth"] = True
            session["admin_user"] = u
            return redirect(url_for("panel_admin"))
        return render_template("login_admin.html", erro="Usuario ou senha incorretos.")
    return render_template("login_admin.html", erro=None)

@app.get("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.get("/admin")
@app.get("/panel_admin")
def panel_admin():
    if not session.get("admin_auth"):
        return redirect(url_for("login_admin"))
    clients = get_all_clients()
    alerts = get_all_alerts()
    users = load_users()
    trusted = {u: i for u, i in users.items() if i.get("role") in ("trusted", "confidant")}
    hoje = now_br_str()[:10]  # dd/mm/aaaa
    stats = {
        "total": len(alerts),
        "today": sum(1 for a in alerts if a.get("ts", "").startswith(hoje)),
        "with_location": sum(1 for a in alerts if a.get("lat") and a.get("lng")),
        "trusted": len(trusted),
        "clients": len(clients),
    }
    return render_template("panel_admin.html",
        clients=clients, trusted=trusted, alerts=alerts, stats=stats)


# ── Login Trusted ─────────────────────────────────────────────
@app.route("/login_trusted", methods=["GET", "POST"])
def login_trusted():
    if request.method == "POST":
        u = (request.form.get("username") or "").strip()
        p = (request.form.get("password") or "").strip()
        users = load_users()
        user = users.get(u)
        if user and user.get("role") in ("trusted", "confidant") and check_password_hash(user["password"], p):
            session.permanent = True
            session["trusted_auth"] = True
            session["trusted_user"] = u
            session["client_id"] = user.get("client_id")
            session["client_name"] = user.get("client_name", "")
            session["trusted_role"] = user.get("role")
            return redirect(url_for("panel_trusted"))
        return render_template("login_trusted.html", erro="Usuario ou senha incorretos.")
    return render_template("login_trusted.html", erro=None)

@app.get("/panel_trusted")
def panel_trusted():
    if not session.get("trusted_auth"):
        return redirect(url_for("login_trusted"))
    cid = session.get("client_id")
    alerts = [a for a in get_all_alerts() if a.get("client_id") == cid]
    return render_template("panel_trusted.html", alerts=alerts,
        client_name=session.get("client_name", ""))

@app.get("/panel_confidant")
def panel_confidant():
    if not session.get("trusted_auth"):
        return redirect(url_for("login_trusted"))
    cid = session.get("client_id")
    alerts = [a for a in get_all_alerts() if a.get("client_id") == cid]
    return render_template("panel_confidant.html", alerts=alerts,
        client_name=session.get("client_name", ""))

@app.get("/central_aurora")
def central_aurora():
    if not session.get("admin_auth"):
        return redirect(url_for("login_admin"))
    return render_template("central_aurora.html", alerts=get_all_alerts())

@app.route("/trusted_change_password", methods=["GET", "POST"])
def trusted_change_password():
    if not session.get("trusted_auth"):
        return redirect(url_for("login_trusted"))
    if request.method == "POST":
        atual = request.form.get("atual", "")
        nova  = request.form.get("nova", "")
        u = session.get("trusted_user")
        users = load_users()
        if u and u in users and check_password_hash(users[u]["password"], atual):
            users[u]["password"] = generate_password_hash(nova)
            save_users(users)
            return render_template("trusted_change_password.html", msg="Senha alterada!")
        return render_template("trusted_change_password.html", erro="Senha atual incorreta.")
    return render_template("trusted_change_password.html")

@app.route("/trusted_recover", methods=["GET", "POST"])
def trusted_recover():
    """
    Antes: qualquer pessoa podia redefinir a senha de um contato de confiança
    só digitando o username, sem nenhuma verificação — permitia sequestrar
    a conta de qualquer contato. Agora, a redefinição só pode ser feita pelo
    admin autenticado, em nome do usuário (fluxo em /api/admin/reset_trusted_password).
    """
    mensagem = (
        "Redefinição de senha não é mais feita por aqui. "
        "Peça ao administrador do sistema para redefinir sua senha no painel admin."
    )
    return mensagem, 200, {"Content-Type": "text/plain; charset=utf-8"}


# ── API Admin ─────────────────────────────────────────────────
@app.post("/api/admin/add_client")
def add_client():
    if not session.get("admin_auth"):
        return jsonify({"error": "Nao autorizado"}), 401
    if not csrf_valido():
        return jsonify({"error": "Token CSRF invalido"}), 403
    data = request.get_json(silent=True) or {}
    name = str(data.get("name", "")).strip()[:80]
    if not name:
        return jsonify({"error": "Nome obrigatorio"}), 400
    client_id = generate_client_id()
    users = load_users()
    users[f"__client__{client_id}"] = {"role": "client", "name": name, "client_id": client_id}
    save_users(users)
    return jsonify({"ok": True, "client_id": client_id, "name": name})

@app.post("/api/admin/delete_client")
def delete_client():
    if not session.get("admin_auth"):
        return jsonify({"error": "Nao autorizado"}), 401
    if not csrf_valido():
        return jsonify({"error": "Token CSRF invalido"}), 403
    data = request.get_json(silent=True) or {}
    client_id = data.get("client_id", "").strip()
    users = load_users()
    to_del = [u for u, i in users.items()
              if i.get("client_id") == client_id or u == f"__client__{client_id}"]
    for u in to_del:
        users.pop(u, None)
    save_users(users)
    return jsonify({"ok": True})

@app.post("/api/admin/add_trusted")
def add_trusted():
    if not session.get("admin_auth"):
        return jsonify({"error": "Nao autorizado"}), 401
    if not csrf_valido():
        return jsonify({"error": "Token CSRF invalido"}), 403
    data = request.get_json(silent=True) or {}
    username  = str(data.get("username", "")).strip()[:50]
    password  = str(data.get("password", "")).strip()
    client_id = str(data.get("client_id", "")).strip()
    role      = data.get("role", "trusted")
    name      = str(data.get("name", username)).strip()[:80]
    if not all([username, password, client_id]):
        return jsonify({"error": "Campos obrigatorios"}), 400
    users = load_users()
    if username in users:
        return jsonify({"error": "Usuario ja existe"}), 409
    client_name = users.get(f"__client__{client_id}", {}).get("name", client_id)
    users[username] = {
        "role": role, "password": generate_password_hash(password),
        "client_id": client_id, "client_name": client_name, "name": name
    }
    save_users(users)
    return jsonify({"ok": True})

@app.post("/api/admin/delete_trusted")
def delete_trusted():
    if not session.get("admin_auth"):
        return jsonify({"error": "Nao autorizado"}), 401
    if not csrf_valido():
        return jsonify({"error": "Token CSRF invalido"}), 403
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    users = load_users()
    users.pop(username, None)
    save_users(users)
    return jsonify({"ok": True})

@app.post("/api/admin/reset_trusted_password")
def reset_trusted_password():
    """Substitui o antigo /trusted_recover público. Só o admin autenticado
    pode redefinir a senha de um contato de confiança."""
    if not session.get("admin_auth"):
        return jsonify({"error": "Nao autorizado"}), 401
    if not csrf_valido():
        return jsonify({"error": "Token CSRF invalido"}), 403
    data = request.get_json(silent=True) or {}
    username = str(data.get("username", "")).strip()
    nova_senha = str(data.get("nova_senha", "")).strip()
    if not username or len(nova_senha) < 8:
        return jsonify({"error": "Usuario e nova senha (min. 8 caracteres) sao obrigatorios"}), 400
    users = load_users()
    if username not in users or users[username].get("role") not in ("trusted", "confidant"):
        return jsonify({"error": "Usuario nao encontrado"}), 404
    users[username]["password"] = generate_password_hash(nova_senha)
    save_users(users)
    return jsonify({"ok": True})

@app.post("/api/admin/clear_alerts")
def clear_alerts():
    if not session.get("admin_auth"):
        return jsonify({"error": "Nao autorizado"}), 401
    if not csrf_valido():
        return jsonify({"error": "Token CSRF invalido"}), 403
    client_id = (request.get_json(silent=True) or {}).get("client_id")
    if client_id:
        alerts = [a for a in get_all_alerts() if a.get("client_id") != client_id]
        with open(ALERTS_FILE, "w", encoding="utf-8") as f:
            for a in reversed(alerts):
                f.write(json.dumps(a, ensure_ascii=False) + "\n")
    else:
        ALERTS_FILE.write_text("", encoding="utf-8")
    return jsonify({"ok": True})




@app.get("/monitor/<client_id>")
def monitor_publico(client_id):
    # Antes: rota pública, sem login — qualquer pessoa com o client_id via
    # localização/nome/situação da vítima. Agora exige sessão autenticada
    # (admin, ou contato de confiança vinculado a ESSE client_id específico).
    autorizado = session.get("admin_auth") or (
        session.get("trusted_auth") and session.get("client_id") == client_id
    )
    if not autorizado:
        return redirect(url_for("login_trusted"))

    users = load_users()
    client = users.get(f"__client__{client_id}")
    if not client:
        return render_template("offline.html"), 404
    alerts = [a for a in get_all_alerts() if a.get("client_id") == client_id]
    return render_template("panel_trusted.html",
        alerts=alerts[:30],
        client_name=client.get("name", "")
    )

@app.errorhandler(404)
def e404(e):
    return render_template("nao_encontrado.html"), 404

@app.errorhandler(500)
def e500(e):
    return jsonify({"error": "Erro interno"}), 500


if __name__ == "__main__":
    ensure_files()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
else:
    ensure_files()


# ── API: Último alerta (para polling) ────────────────────────
@app.get("/api/ultimo_alerta/<client_id>")
def ultimo_alerta(client_id):
    # Antes: pública, sem login — permitia rastrear em tempo real a
    # localização da vítima só sabendo o client_id. Agora exige sessão
    # autenticada, igual à rota /monitor acima.
    autorizado = session.get("admin_auth") or (
        session.get("trusted_auth") and session.get("client_id") == client_id
    )
    if not autorizado:
        return jsonify({"error": "Nao autorizado"}), 401

    alerts = [a for a in get_all_alerts() if a.get("client_id") == client_id]
    if alerts:
        return jsonify({"ok": True, "alerta": alerts[0]})
    todos = get_all_alerts()
    if todos:
        return jsonify({"ok": True, "alerta": todos[0]})
    return jsonify({"ok": False})
