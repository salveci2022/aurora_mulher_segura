from flask import Flask, render_template, request, redirect, session, url_for, jsonify
from pathlib import Path
import json
import bcrypt
import os
import time
from datetime import datetime

# ======================================
# CONFIG
# ======================================

BASE_DIR = Path(__file__).resolve().parent
USERS_FILE = BASE_DIR / "users.json"

app = Flask(__name__)
app.secret_key = "aurora_safe_2026"

# ======================================
# HELPERS
# ======================================

def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password, hashed):
    try:
        return bcrypt.checkpw(password.encode(), hashed.encode())
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

# ======================================
# ROTAS PUBLICAS
# ======================================

@app.route("/")
def home():
    return redirect("/panel/login")

# ======================================
# ADMIN
# ======================================

@app.route("/panel/login", methods=["GET","POST"])
def admin_login():
    users = load_users()
    error = False

    if request.method == "POST":
        user = request.form.get("user","")
        password = request.form.get("password","")

        if user in users:
            if users[user]["role"] == "admin" and verify_password(password, users[user]["password_hash"]):
                session["user"] = user
                session["role"] = "admin"
                return redirect("/panel")
        error = True

    return render_template("login_admin.html", error=error)

@app.route("/panel")
def panel_admin():
    if session.get("role") != "admin":
        return redirect("/panel/login")

    users = load_users()
    trusted = {u:v for u,v in users.items() if v["role"] == "trusted"}
    return render_template("panel_admin.html", trusted=trusted)

@app.post("/panel/add_trusted")
def add_trusted():
    if session.get("role") != "admin":
        return redirect("/panel/login")

    name = request.form.get("trusted_name","")
    username = request.form.get("trusted_user","").lower()
    password = request.form.get("trusted_password","")

    if not name or not username or not password:
        return redirect("/panel")

    users = load_users()

    users[username] = {
        "password_hash": hash_password(password),
        "role": "trusted",
        "name": name
    }

    save_users(users)
    return redirect("/panel")

@app.get("/logout_admin")
def logout_admin():
    session.clear()
    return redirect("/panel/login")

# ======================================
# TRUSTED
# ======================================

@app.route("/trusted/login", methods=["GET","POST"])
def trusted_login():
    users = load_users()
    error = False

    if request.method == "POST":
        user = request.form.get("user","")
        password = request.form.get("password","")

        if user in users:
            if users[user]["role"] == "trusted" and verify_password(password, users[user]["password_hash"]):
                session["user"] = user
                session["role"] = "trusted"
                session["name"] = users[user]["name"]
                return redirect("/trusted/panel")
        error = True

    return render_template("login_trusted.html", error=error)

@app.route("/trusted/panel")
def trusted_panel():
    if session.get("role") != "trusted":
        return redirect("/trusted/login")

    return render_template("panel_trusted.html", name=session.get("name"))

@app.get("/logout_trusted")
def logout_trusted():
    session.clear()
    return redirect("/trusted/login")

# ======================================
# START
# ======================================

if __name__ == "__main__":
    ensure_users()
    app.run(host="0.0.0.0", port=5000)