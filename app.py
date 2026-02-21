from __future__ import annotations

import os
import json
import bcrypt
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

from flask import Flask, render_template, request, redirect, session, jsonify
from jinja2 import TemplateNotFound

# =========================
# CONFIG
# =========================
try:
    TZ = ZoneInfo("America/Sao_Paulo")
except Exception:
    TZ = None

BASE_DIR = Path(__file__).resolve().parent
USERS_FILE = BASE_DIR / "users.json"
ALERTS_FILE = BASE_DIR / "alerts.log"

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "aurora_v21_ultra_estavel")

# Anti-spam simples
_RATE = {"window_sec": 5, "last_by_ip": {}}


# =========================
# HELPERS
# =========================
def now_iso() -> str:
    dt = datetime.now(TZ) if TZ else datetime.now()
    return dt.isoformat(timespec="seconds")


def hash_password(raw: str) -> str:
    raw_b = (raw or "").encode("utf-8")
    return bcrypt.hashpw(raw_b, bcrypt.gensalt()).decode("utf-8")


def verify_password(raw: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw((raw or "").encode("utf-8"), (hashed or "").encode("utf-8"))
    except Exception:
        return False


def ensure_files() -> None:
    # users.json
    if not USERS_FILE.exists():
        admin_hash = hash_password("admin123")
        USERS_FILE.write_text(
            json.dumps(
                {
                    "admin": {
                        "password_hash": admin_hash,
                        "role": "admin",
                        "name": "Admin Aurora",
                    }
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    # alerts.log
    if not ALERTS_FILE.exists():
        ALERTS_FILE.write_text("", encoding="utf-8")


def load_users() -> dict:
    ensure_files()
    try:
        raw = USERS_FILE.read_text(encoding="utf-8").strip()
        if not raw:
            return {}
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except Exception:
        # Se corromper, recria admin padrão
        admin_hash = hash_password("admin123")
        data = {
            "admin": {
                "password_hash": admin_hash,
                "role": "admin",
                "name": "Admin Aurora",
            }
        }
        USERS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return data


def save_users(data: dict) -> None:
    USERS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def rate_limit_ok(ip: str) -> bool:
    win = _RATE["window_sec"]
    last = _RATE["last_by_ip"].get(ip)
    now_ts = datetime.now().timestamp()
    if last and (now_ts - last) < win:
        return False
    _RATE["last_by_ip"][ip] = now_ts
    return True


def render_panic_template(trusted_list: list[str]):
    """
    Não muda aparência.
    Só garante que não quebra se o template estiver com .htm ou .html.
    """
    try:
        return render_template("panic_button.html", trusted=trusted_list)
    except TemplateNotFound:
        return render_template("panic_button.htm", trusted=trusted_list)


# =========================
# ROUTES (Mulher / Panic)
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
        if isinstance(info, dict) and info.get("role") == "trusted"
    ]
    return render_panic_template(trusted)


@app.route("/api/send_alert", methods=["POST"])
def send_alert():
    # anti-spam
    ip = request.headers.get("X-Forwarded-For", request.remote_addr) or "unknown"
    ip = ip.split(",")[0].strip()
    if not rate_limit_ok(ip):
        return jsonify({"status": "rate_limited"}), 429

    data = request.get_json(silent=True) or {}
    payload = {"timestamp": now_iso(), "data": data}

    ensure_files()
    with open(ALERTS_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")

    return jsonify({"status": "ok"})


@app.route("/api/last_alert")
def last_alert():
    ensure_files()
    try:
        lines = ALERTS_FILE.read_text(encoding="utf-8").splitlines()
        if not lines:
            return jsonify({"last": None})
        last = json.loads(lines[-1])
        return jsonify({"last": last})
    except Exception:
        return jsonify({"last": None})


# =========================
# ADMIN
# =========================
@app.route("/panel/login", methods=["GET", "POST"])
def login_admin():
    error = False
    if request.method == "POST":
        user = (request.form.get("user") or "").strip().lower()
        password = request.form.get("password") or ""
        users = load_users()
        info = users.get(user) if isinstance(users, dict) else None

        if info and info.get("role") == "admin" and verify_password(password, info.get("password_hash", "")):
            session["admin"] = user
            return redirect("/panel")
        error = True

    return render_template("login_admin.html", error=error)


@app.route("/panel")
def panel_admin():
    if "admin" not in session:
        return redirect("/panel/login")

    users = load_users()
    trusted = [
        {"user": u, "name": info.get("name", u)}
        for u, info in users.items()
        if isinstance(info, dict) and info.get("role") == "trusted"
    ]
    return render_template("panel_admin.html", trusted=trusted)


@app.route("/panel/add_trusted", methods=["POST"])
def add_trusted():
    if "admin" not in session:
        return redirect("/panel/login")

    username = (request.form.get("trusted_user") or "").strip().lower()
    name = (request.form.get("trusted_name") or "").strip()
    password = request.form.get("trusted_password") or ""

    if not username or not name or not password:
        return redirect("/panel")

    users = load_users()

    # limite 3
    trusted_count = sum(1 for _, info in users.items() if isinstance(info, dict) and info.get("role") == "trusted")
    if trusted_count >= 3:
        return redirect("/panel?msg=Limite+de+3+pessoas+de+confianca")

    if username in users:
        return redirect("/panel?msg=Usuario+ja+existe")

    users[username] = {"name": name, "password_hash": hash_password(password), "role": "trusted"}
    save_users(users)
    return redirect("/panel?msg=Cadastrado+com+sucesso")


@app.route("/panel/delete_trusted", methods=["POST"])
def delete_trusted():
    if "admin" not in session:
        return redirect("/panel/login")

    username = (request.form.get("username") or "").strip().lower()
    users = load_users()

    if username in users and users[username].get("role") == "trusted":
        users.pop(username, None)
        save_users(users)

    return redirect("/panel?msg=Removido")


@app.route("/logout_admin")
def logout_admin():
    session.clear()
    return redirect("/panel/login")


# =========================
# TRUSTED
# =========================
@app.route("/trusted/login", methods=["GET", "POST"])
def login_trusted():
    error = False
    if request.method == "POST":
        user = (request.form.get("user") or "").strip().lower()
        password = request.form.get("password") or ""
        users = load_users()
        info = users.get(user)

        if info and info.get("role") == "trusted" and verify_password(password, info.get("password_hash", "")):
            session["trusted"] = user
            return redirect("/trusted")
        error = True

    return render_template("login_trusted.html", error=error)


@app.route("/trusted")
def panel_trusted():
    if "trusted" not in session:
        return redirect("/trusted/login")

    user = session["trusted"]
    users = load_users()
    display_name = users.get(user, {}).get("name", "Pessoa de Confiança")
    return render_template("panel_trusted.html", display_name=display_name)


@app.route("/logout_trusted")
def logout_trusted():
    session.clear()
    return redirect("/trusted/login")


# =========================
# LOCAL RUN
# =========================
if __name__ == "__main__":
    ensure_files()
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=False)