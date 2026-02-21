from __future__ import annotations
from flask import Flask, render_template, request, redirect, session, url_for, jsonify
from pathlib import Path
import json
import time
import bcrypt
import os
import threading
from datetime import datetime
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

load_dotenv()

# =============================
# FALLBACK CLOUD (SEM QUEBRAR)
# =============================

class FallbackCloudManager:
    def __init__(self):
        self.backends = [{
            "name": "render",
            "url": "https://aurora-mulher-segura.onrender.com",
            "healthy": True,
            "failures": 0,
            "active": True
        }]
        self.stats = {"total_switches": 0}

    def monitor_loop(self):
        while True:
            time.sleep(10)

    def get_active_backend(self):
        return self.backends[0]

    def get_status(self):
        return {
            "current": "render",
            "backends": self.backends,
            "stats": self.stats
        }

cloud_manager = FallbackCloudManager()

# =============================
# CONFIG
# =============================

try:
    TZ = ZoneInfo("America/Sao_Paulo")
except:
    TZ = None

BASE_DIR = Path(__file__).resolve().parent
USERS_FILE = BASE_DIR / "users.json"

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "aurora_ultra_estavel")

# =============================
# HELPERS
# =============================

def now_br():
    if TZ:
        return datetime.now(TZ).strftime("%Y-%m-%d %H:%M:%S")
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def hash_password(raw):
    return bcrypt.hashpw(raw.encode(), bcrypt.gensalt()).decode()

def verify_password(raw, hashed):
    try:
        return bcrypt.checkpw(raw.encode(), hashed.encode())
    except:
        return False

def ensure_users():
    if not USERS_FILE.exists():
        USERS_FILE.write_text(json.dumps({
            "admin": {
                "password_hash": hash_password("admin123"),
                "role": "admin",
                "name": "Admin Aurora"
            }
        }, indent=2))

def load_users():
    ensure_users()
    try:
        return json.loads(USERS_FILE.read_text())
    except:
        return {}

def save_users(data):
    USERS_FILE.write_text(json.dumps(data, indent=2))

# =============================
# ROTAS
# =============================

@app.route("/")
def home():
    return redirect("/panic")

@app.route("/panic")
def panic():
    return "<h2>Sistema Aurora Rodando</h2>"

# =============================
# ADMIN LOGIN
# =============================

@app.route("/panel/login", methods=["GET","POST"])
def admin_login():
    users = load_users()
    error = False

    if request.method == "POST":
        user = request.form.get("user","").strip()
        password = request.form.get("password","")

        info = users.get(user)
        if info and info.get("role") == "admin" and verify_password(password, info.get("password_hash")):
            session.clear()
            session["role"] = "admin"
            session["user"] = user
            return redirect("/panel")
        error = True

    return render_template("login_admin.html", error=error)

@app.route("/panel")
def admin_panel():
    if session.get("role") != "admin":
        return redirect("/panel/login")

    users = load_users()
    trusted = {u:v for u,v in users.items() if v.get("role")=="trusted"}
    return render_template("panel_admin.html", trusted=trusted)

@app.post("/panel/add_trusted")
def add_trusted():
    if session.get("role") != "admin":
        return redirect("/panel/login")

    name = request.form.get("name","").strip()
    username = request.form.get("username","").strip().lower()
    password = request.form.get("password","")

    if not name or not username or not password:
        return redirect("/panel")

    users = load_users()

    if username in users:
        return redirect("/panel")

    users[username] = {
        "password_hash": hash_password(password),
        "role": "trusted",
        "name": name
    }

    save_users(users)
    return redirect("/panel")

@app.route("/logout_admin")
def logout_admin():
    session.clear()
    return redirect("/panel/login")

# =============================
# TRUSTED LOGIN
# =============================

@app.route("/trusted/login", methods=["GET","POST"])
def trusted_login():
    users = load_users()
    error = False

    if request.method == "POST":
        user = request.form.get("user","").strip().lower()
        password = request.form.get("password","")

        info = users.get(user)
        if info and info.get("role")=="trusted" and verify_password(password, info.get("password_hash")):
            session.clear()
            session["role"]="trusted"
            session["user"]=user
            session["name"]=info.get("name")
            return redirect("/trusted/panel")
        error=True

    return render_template("login_trusted.html", error=error)

@app.route("/trusted/panel")
def trusted_panel():
    if session.get("role")!="trusted":
        return redirect("/trusted/login")

    return render_template("panel_trusted.html", name=session.get("name"))

@app.route("/logout_trusted")
def logout_trusted():
    session.clear()
    return redirect("/trusted/login")

# =============================
# START
# =============================

if __name__ == "__main__":
    ensure_users()
    port = int(os.environ.get("PORT",5000))
    app.run(host="0.0.0.0", port=port)