from flask import Flask, render_template, request, redirect, session, jsonify
import json
import os
from datetime import datetime

app = Flask(__name__)

# chave de sessão
app.secret_key = "aurora_secret"


# ===============================
# ARQUIVOS
# ===============================

ALERT_FILE = "alerts.json"
USER_FILE = "users.json"


# ===============================
# FUNÇÕES AUXILIARES
# ===============================

def load_alerts():

    if not os.path.exists(ALERT_FILE):
        return []

    with open(ALERT_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_alerts(data):

    with open(ALERT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def load_users():

    if not os.path.exists(USER_FILE):
        return {}

    with open(USER_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_users(data):

    with open(USER_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


# ===============================
# PÁGINA INICIAL
# ===============================

@app.route("/")
def home():
    return redirect("/panic")


# ===============================
# BOTÃO DE PÂNICO
# ===============================

@app.route("/panic")
def panic():
    return render_template("panic_button.html")


# ===============================
# API ALERTA
# ===============================

@app.route("/api/alert", methods=["POST"])
def api_alert():

    data = request.json

    alerts = load_alerts()

    alert = {

        "nome": data.get("nome"),
        "situacao": data.get("situacao"),
        "mensagem": data.get("mensagem"),
        "localizacao": data.get("localizacao"),
        "hora": datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    }

    alerts.append(alert)

    save_alerts(alerts)

    return jsonify({"status": "ok"})


# ===============================
# LOGIN ADMIN
# ===============================

@app.route("/panel/login", methods=["GET","POST"])
def login_admin():

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        if username == "admin" and password == "123456":

            session["admin"] = True

            return redirect("/panel")

        return "Login inválido"

    return render_template("login_admin.html")


# ===============================
# PAINEL ADMIN
# ===============================

@app.route("/panel")
def panel_admin():

    if not session.get("admin"):
        return redirect("/panel/login")

    alerts = load_alerts()

    users = load_users()

    return render_template(
        "panel_admin.html",
        alerts=alerts,
        users=users
    )


# ===============================
# CADASTRAR PESSOA DE CONFIANÇA
# ===============================

@app.route("/trusted/register", methods=["GET","POST"])
def trusted_register():

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        users = load_users()

        if len(users) >= 3:
            return "Limite de 3 pessoas de confiança atingido"

        users[username] = {
            "password": password
        }

        save_users(users)

        return redirect("/trusted/login")

    return render_template("trusted_register.html")


# ===============================
# LOGIN PESSOA DE CONFIANÇA
# ===============================

@app.route("/trusted/login", methods=["GET","POST"])
def login_trusted():

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        users = load_users()

        if username in users and users[username]["password"] == password:

            session["trusted"] = username

            return redirect("/trusted/panel")

        return "Login inválido"

    return render_template("login_trusted.html")


# ===============================
# PAINEL PESSOA DE CONFIANÇA
# ===============================

@app.route("/trusted/panel")
def trusted_panel():

    if not session.get("trusted"):
        return redirect("/trusted/login")

    alerts = load_alerts()

    return render_template(
        "panel_trusted.html",
        alerts=alerts
    )


# ===============================
# LOGOUT
# ===============================

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/panic")


# ===============================
# INICIAR SERVIDOR
# ===============================

if __name__ == "__main__":

    app.run(host="0.0.0.0", port=5000)