# -*- coding: utf-8 -*-

import os
import json
import bcrypt
import tempfile
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, request, redirect, session, jsonify

# =========================
# CONFIG
# =========================

BASE_DIR = Path(tempfile.gettempdir())

USERS_FILE = BASE_DIR / "users.json"
ALERTS_FILE = BASE_DIR / "alerts.log"

app = Flask(__name__)
app.secret_key = "aurora_secret_key_2026"

# =========================
# HELPERS
# =========================

def ensure_files():
    if not USERS_FILE.exists():
        admin_hash = bcrypt.hashpw("admin123".encode(), bcrypt.gensalt()).decode()
        data = {
            "admin": {
                "password_hash": admin_hash,
                "role": "admin",
                "name": "Admin Aurora"
            }
        }
        USERS_FILE.write_text(json.dumps(data))

    if not ALERTS_FILE.exists():
        ALERTS_FILE.write_text("")

def load_users():
    return json.loads(USERS_FILE.read_text())

def save_users(data):
    USERS_FILE.write_text(json.dumps(data))

def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password, hashed):
    return bcrypt.checkpw(password.encode(), hashed.encode())

# =========================
# ROUTES
# =========================

@app.route("/")
def home():
    return redirect("/panic")

@app.route("/panic")
def panic():
    users = load_users()
    trusted = [
        info["name"]
        for u, info in users.items()
        if info.get("role") == "trusted"
    ]
    return render_template("panic_button.html", trusted=trusted)

@app.route("/api/send_alert", methods=["POST"])
def send_alert():
    data = request.json
    alert = {
        "timestamp": datetime.now().isoformat(),
        "data": data
    }
    with open(ALERTS_FILE, "a") as f:
        f.write(json.dumps(alert) + "\n")
    return jsonify({"status": "ok"})

@app.route("/api/last_alert")
def last_alert():
    if not ALERTS_FILE.exists():
        return jsonify({"last": None})

    lines = ALERTS_FILE.read_text().splitlines()
    if not lines:
        return jsonify({"last": None})

    return jsonify({"last": json.loads(lines[-1])})

# =========================
# ADMIN LOGIN
# =========================

@app.route("/panel/login", methods=["GET", "POST"])
def login_admin():
    error = False
    if request.method == "POST":
        user = request.form.get("user")
        password = request.form.get("password")

        users = load_users()
        info = users.get(user)

        if info and verify_password(password, info["password_hash"]) and info["role"] == "admin":
            session["admin"] = user
            return redirect("/panel")
        else:
            error = True

    return render_template("login_admin.html", error=error)

@app.route("/panel")
def panel_admin():
    if "admin" not in session:
        return redirect("/panel/login")

    users = load_users()
    trusted = {u:info for u,info in users.items() if info.get("role") == "trusted"}

    return render_template("panel_admin.html", trusted=trusted)

@app.route("/panel/add_trusted", methods=["POST"])
def add_trusted():
    if "admin" not in session:
        return redirect("/panel/login")

    users = load_users()

    name = request.form.get("trusted_name")
    username = request.form.get("trusted_user")
    password = request.form.get("trusted_password")

    if username in users:
        return redirect("/panel")

    users[username] = {
        "name": name,
        "password_hash": hash_password(password),
        "role": "trusted"
    }

    save_users(users)
    return redirect("/panel")

@app.route("/panel/delete_trusted", methods=["POST"])
def delete_trusted():
    if "admin" not in session:
        return redirect("/panel/login")

    users = load_users()
    username = request.form.get("username")

    if username in users:
        del users[username]
        save_users(users)

    return redirect("/panel")

@app.route("/logout_admin")
def logout_admin():
    session.clear()
    return redirect("/panel/login")

# =========================
# TRUSTED LOGIN
# =========================

@app.route("/trusted/login", methods=["GET", "POST"])
def login_trusted():
    error = False
    if request.method == "POST":
        user = request.form.get("user")
        password = request.form.get("password")

        users = load_users()
        info = users.get(user)

        if info and verify_password(password, info["password_hash"]) and info["role"] == "trusted":
            session["trusted"] = user
            return redirect("/trusted")
        else:
            error = True

    return render_template("login_trusted.html", error=error)

@app.route("/trusted")
def panel_trusted():
    if "trusted" not in session:
        return redirect("/trusted/login")

    user = session["trusted"]
    users = load_users()
    display_name = users[user]["name"]

    return render_template("panel_trusted.html", display_name=display_name)

@app.route("/logout_trusted")
def logout_trusted():
    session.clear()
    return redirect("/trusted/login")

# =========================
# START
# =========================

if __name__ == "__main__":
    ensure_files()
    app.run(host="0.0.0.0", port=5000)