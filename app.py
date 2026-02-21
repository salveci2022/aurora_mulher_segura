# -*- coding: utf-8 -*-
import os
import json
from pathlib import Path
from datetime import datetime

import bcrypt
from flask import (
    Flask,
    render_template,
    render_template_string,
    request,
    redirect,
    session,
    jsonify,
)

# =========================
# CONFIG
# =========================
BASE_DIR = Path(__file__).resolve().parent
USERS_FILE = BASE_DIR / "users.json"
ALERTS_FILE = BASE_DIR / "alerts.log"

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = os.environ.get("SECRET_KEY", "aurora_secret_key_2026")


# =========================
# HELPERS
# =========================
def hash_password(raw: str) -> str:
    raw = (raw or "").encode("utf-8")
    return bcrypt.hashpw(raw, bcrypt.gensalt()).decode("utf-8")


def verify_password(raw: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw((raw or "").encode("utf-8"), (hashed or "").encode("utf-8"))
    except Exception:
        return False


def ensure_files():
    if not ALERTS_FILE.exists():
        ALERTS_FILE.write_text("", encoding="utf-8")

    if not USERS_FILE.exists():
        admin_hash = hash_password("admin123")
        data = {
            "admin": {"password_hash": admin_hash, "role": "admin", "name": "Admin Aurora"}
        }
        USERS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_users() -> dict:
    ensure_files()
    try:
        raw = USERS_FILE.read_text(encoding="utf-8")
        if not raw.strip():
            # arquivo vazio
            ensure_files()
            raw = USERS_FILE.read_text(encoding="utf-8")
        return json.loads(raw)
    except json.JSONDecodeError:
        # users.json corrompido -> recria admin padrão para não dar 500
        admin_hash = hash_password("admin123")
        data = {
            "admin": {"password_hash": admin_hash, "role": "admin", "name": "Admin Aurora"}
        }
        USERS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return data


def save_users(data: dict):
    USERS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def safe_render(template_name: str, **ctx):
    """
    Evita erro 500 caso o template esteja fora do lugar no deploy.
    1) tenta /templates/<template_name>
    2) tenta arquivo solto na raiz do projeto (BASE_DIR/<template_name>)
    3) fallback HTML mínimo (não muda seu layout se o template existir)
    """
    try:
        return render_template(template_name, **ctx)
    except Exception as e:
        # tenta fallback lendo arquivo da raiz (caso tenha sido commitado fora de /templates)
        fp = BASE_DIR / template_name
        if fp.exists():
            try:
                return render_template_string(fp.read_text(encoding="utf-8"), **ctx)
            except Exception:
                pass

        # fallback mínimo para não travar com 500
        html = f"""<!doctype html>
<html lang="pt-br">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Aurora · Painel</title>
  <link rel="stylesheet" href="/static/css/style.css">
</head>
<body style="font-family:Arial;padding:20px">
  <h2>⚠️ Template não encontrado: {template_name}</h2>
  <p>O backend está rodando, mas o HTML não está no lugar certo no deploy.</p>
  <p>Confirme se existe: <b>/templates/{template_name}</b></p>
  <pre style="white-space:pre-wrap;background:#111;color:#fff;padding:12px;border-radius:8px">{str(e)}</pre>
</body>
</html>"""
        return render_template_string(html), 200


# =========================
# ROTAS
# =========================
@app.route("/")
def home():
    return redirect("/panic")


@app.route("/panic")
def panic():
    users = load_users()
    trusted = [
        info.get("name", u)
        for u, info in users.items()
        if info.get("role") == "trusted"
    ]
    # usa safe_render para nunca dar 500 por template ausente
    return safe_render("panic_button.html", trusted=trusted)


# =========================
# API ALERTAS
# =========================
@app.route("/api/send_alert", methods=["POST"])
def send_alert():
    data = request.get_json(silent=True) or {}

    alert = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "name": (data.get("name") or "").strip(),
        "situation": (data.get("situation") or "").strip(),
        "message": (data.get("message") or "").strip(),
        "lat": data.get("lat"),
        "lng": data.get("lng"),
    }

    ensure_files()
    with open(ALERTS_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(alert, ensure_ascii=False) + "\n")

    return jsonify({"status": "ok"})


@app.route("/api/last_alert", methods=["GET"])
def last_alert():
    ensure_files()
    lines = ALERTS_FILE.read_text(encoding="utf-8").splitlines()
    if not lines:
        return jsonify({"last": None})

    # pega o último JSON válido
    for i in range(len(lines) - 1, -1, -1):
        try:
            return jsonify({"last": json.loads(lines[i])})
        except Exception:
            continue

    return jsonify({"last": None})


# =========================
# ADMIN
# =========================
@app.route("/panel/login", methods=["GET", "POST"])
def login_admin():
    err = ""
    if request.method == "POST":
        user = (request.form.get("user") or "").strip().lower()
        password = request.form.get("password") or ""

        users = load_users()
        info = users.get(user)
        if info and info.get("role") == "admin" and verify_password(password, info.get("password_hash", "")):
            session["admin"] = True
            return redirect("/panel")
        err = "Login inválido."

    return safe_render("login_admin.html", err=err)


@app.route("/panel")
def panel_admin():
    if not session.get("admin"):
        return redirect("/panel/login")

    users = load_users()
    trusted = {u: info for u, info in users.items() if info.get("role") == "trusted"}
    return safe_render("panel_admin.html", trusted=trusted)


@app.route("/panel/add_trusted", methods=["POST"])
def add_trusted():
    if not session.get("admin"):
        return redirect("/panel/login")

    name = (request.form.get("trusted_name") or "").strip()
    username = (request.form.get("trusted_user") or "").strip().lower()
    password = request.form.get("trusted_password") or ""

    users = load_users()
    trusted_count = sum(1 for _, info in users.items() if info.get("role") == "trusted")

    if trusted_count >= 3:
        return redirect("/panel?err=Limite+de+3+pessoas+atingido")
    if not name or not username or not password:
        return redirect("/panel?err=Preencha+todos+os+campos")
    if username in users:
        return redirect("/panel?err=Usuário+já+existe")

    users[username] = {
        "name": name,
        "role": "trusted",
        "password_hash": hash_password(password),
    }
    save_users(users)
    return redirect("/panel?msg=Cadastrado+com+sucesso")


@app.route("/panel/delete_trusted", methods=["POST"])
def delete_trusted():
    if not session.get("admin"):
        return redirect("/panel/login")

    username = (request.form.get("username") or "").strip().lower()
    users = load_users()

    if username in users and users[username].get("role") == "trusted":
        del users[username]
        save_users(users)

    return redirect("/panel?msg=Removido+com+sucesso")


@app.route("/logout_admin")
def logout_admin():
    session.pop("admin", None)
    return redirect("/panel/login")


# =========================
# TRUSTED (Pessoa de confiança)
# =========================
@app.route("/trusted/login", methods=["GET", "POST"])
def login_trusted():
    err = ""
    if request.method == "POST":
        user = (request.form.get("user") or "").strip().lower()
        password = request.form.get("password") or ""

        users = load_users()
        info = users.get(user)
        if info and info.get("role") == "trusted" and verify_password(password, info.get("password_hash", "")):
            session["trusted"] = user
            return redirect("/trusted/panel")
        err = "Login inválido."

    return safe_render("login_trusted.html", err=err)


@app.route("/trusted/panel")
def panel_trusted():
    if not session.get("trusted"):
        return redirect("/trusted/login")

    users = load_users()
    me = users.get(session["trusted"], {})
    display_name = me.get("name", "Pessoa de Confiança")
    return safe_render("panel_trusted.html", display_name=display_name)


@app.route("/logout_trusted")
def logout_trusted():
    session.pop("trusted", None)
    return redirect("/trusted/login")


if __name__ == "__main__":
    ensure_files()
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=False)