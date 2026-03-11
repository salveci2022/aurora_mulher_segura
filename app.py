from flask import Flask, render_template, request, redirect, session, jsonify
import json
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "aurora_secret")


# ================================
# ARQUIVOS
# ================================

USERS_FILE = "users.json"
ALERTS_FILE = "alerts.json"


# ================================
# ADMIN SEGURO
# ================================

ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASS = os.getenv("ADMIN_PASS", "admin123")


# ================================
# GARANTIR ARQUIVOS
# ================================

if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, "w") as f:
        json.dump({}, f)

if not os.path.exists(ALERTS_FILE):
    with open(ALERTS_FILE, "w") as f:
        json.dump([], f)


# ================================
# SISTEMA DE USUÁRIOS
# ================================

def load_users():
    with open(USERS_FILE, "r") as f:
        return json.load(f)


def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f)


# ================================
# ALERTAS
# ================================

def load_alerts():
    with open(ALERTS_FILE, "r") as f:
        return json.load(f)


def save_alerts(alerts):
    with open(ALERTS_FILE, "w") as f:
        json.dump(alerts, f)


# ================================
# PÁGINAS PRINCIPAIS
# ================================

@app.route("/")
def home():
    return redirect("/panic")


@app.route("/panic")
def panic():
    return render_template("panic_button.html")


@app.route("/termo")
def termo():
    return render_template("termo.html")


# ================================
# API ALERTA
# ================================

@app.route("/api/alert", methods=["POST"])
def api_alert():

    data = request.json
    alerts = load_alerts()

    alerta = {
        "nome": data.get("nome"),
        "situacao": data.get("situacao"),
        "mensagem": data.get("mensagem"),
        "lat": data.get("lat"),
        "lng": data.get("lng"),
        "foto": data.get("foto"),   # FOTO DA CAMERA
        "hora": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    }

    alerts.append(alerta)
    save_alerts(alerts)

    return jsonify({"status": "ok"})


@app.route("/api/alerts")
def api_alerts():
    return jsonify(load_alerts())


# ================================
# ULTIMO ALERTA
# ================================

@app.route("/api/last_alert")
def last_alert():

    alerts = load_alerts()

    if len(alerts) == 0:
        return jsonify({"alert": None})

    return jsonify({"alert": alerts[-1]})


# ================================
# LOGIN ADMIN
# ================================

@app.route("/panel/login", methods=["GET", "POST"])
def login_admin():

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if username == ADMIN_USER and password == ADMIN_PASS:

            session["admin"] = True
            return redirect("/panel")

        return render_template("login_admin.html", error="Usuário ou senha inválidos")

    return render_template("login_admin.html")


# ================================
# PAINEL ADMIN
# ================================

@app.route("/panel")
def panel_admin():

    if not session.get("admin"):
        return redirect("/panel/login")

    alerts = load_alerts()

    return render_template("panel_admin.html", alerts=alerts)


# ================================
# CADASTRO PESSOA DE CONFIANÇA
# ================================

@app.route("/trusted/register", methods=["GET", "POST"])
def trusted_register():

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        users = load_users()

        if len(users) >= 3:
            return "Limite de 3 pessoas de confiança atingido"

        users[username] = {
            "password": password
        }

        save_users(users)

        return redirect("/trusted/login")

    return render_template("trusted_register.html")


# ================================
# LOGIN PESSOA DE CONFIANÇA
# ================================

@app.route("/trusted/login", methods=["GET", "POST"])
def trusted_login():

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        users = load_users()

        if username in users and users[username]["password"] == password:

            session["trusted"] = username
            return redirect("/trusted/panel")

        return render_template("trusted_login.html", error="Login inválido")

    return render_template("trusted_login.html")


# ================================
# PAINEL PESSOA DE CONFIANÇA
# ================================

@app.route("/trusted/panel")
def trusted_panel():

    if not session.get("trusted"):
        return redirect("/trusted/login")

    alerts = load_alerts()

    return render_template("panel_trusted.html", alerts=alerts)


# ================================
# LOGOUT
# ================================

@app.route("/logout")
def logout():

    session.clear()
    return redirect("/")


# ================================
# HEALTH CHECK (Render)
# ================================

@app.route("/health")
def health():
    return {"status": "ok"}


# ================================
# EXECUÇÃO LOCAL
# ================================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)