from flask import Flask, render_template, jsonify, request, redirect, session
import json
import os
from datetime import datetime

app = Flask(__name__)

app.secret_key = "aurora_secret"

ALERT_FILE = "alerts.log"
TRUSTED_FILE = "trusted.json"


# ==============================
# GARANTIR ARQUIVOS
# ==============================

if not os.path.exists(ALERT_FILE):
    with open(ALERT_FILE, "w") as f:
        json.dump([], f)

if not os.path.exists(TRUSTED_FILE):
    with open(TRUSTED_FILE, "w") as f:
        json.dump({}, f)


# ==============================
# FUNÇÕES
# ==============================

def load_alerts():

    try:
        with open(ALERT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []


def save_alerts(data):

    with open(ALERT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


# ==============================
# HOME
# ==============================

@app.route("/")
def home():
    return render_template("panic_button.html")


# ==============================
# LOGIN ADMIN
# ==============================

@app.route("/panel/login", methods=["GET", "POST"])
def panel_login():

    if request.method == "POST":

        user = request.form.get("username")
        password = request.form.get("password")

        if user == "admin" and password == "admin123":

            session["admin"] = True
            return redirect("/panel")

    return render_template("login_admin.html")


# ==============================
# PAINEL ADMIN
# ==============================

@app.route("/panel")
def panel_admin():

    if not session.get("admin"):
        return redirect("/panel/login")

    return render_template("panel_admin.html")


@app.route("/panel/logout")
def panel_logout():

    session.pop("admin", None)

    return redirect("/panel/login")


# ==============================
# LOGIN TRUSTED
# ==============================

@app.route("/trusted/login", methods=["GET", "POST"])
def trusted_login():

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        if username == "trusted" and password == "1234":

            session["trusted"] = True
            return redirect("/trusted")

    return render_template("login_trusted.html")


# ==============================
# PAINEL TRUSTED
# ==============================

@app.route("/trusted")
def trusted_panel():

    if not session.get("trusted"):
        return redirect("/trusted/login")

    return render_template("panel_trusted.html")


@app.route("/trusted/logout")
def trusted_logout():

    session.pop("trusted", None)

    return redirect("/trusted/login")


# ==============================
# SALVAR PESSOAS DE CONFIANÇA
# ==============================

@app.route("/api/trusted/save", methods=["POST"])
def save_trusted():

    data = request.json

    with open(TRUSTED_FILE, "w") as f:
        json.dump(data, f, indent=2)

    return {"status": "ok"}


# ==============================
# ENVIAR ALERTA
# ==============================

@app.route("/api/alert", methods=["POST"])
def receive_alert():

    data = request.json

    alerts = load_alerts()

    alerta = {
        "nome": data.get("nome"),
        "situacao": data.get("situacao"),
        "hora": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "localizacao": data.get("localizacao", "")
    }

    alerts.append(alerta)

    save_alerts(alerts)

    return {"status": "ok"}


# ==============================
# ÚLTIMO ALERTA
# ==============================

@app.route("/api/last_alert")
def api_last_alert():

    alerts = load_alerts()

    if not alerts:
        return jsonify({"last": None})

    return jsonify({"last": alerts[-1]})


# ==============================
# HISTÓRICO
# ==============================

@app.route("/api/alerts")
def api_alerts():

    alerts = load_alerts()

    return jsonify(alerts)


# ==============================
# LIMPAR ALERTAS
# ==============================

@app.route("/api/clear_alerts")
def clear_alerts():

    save_alerts([])

    return {"status": "ok"}


# ==============================
# REENVIAR ALERTA
# ==============================

@app.route("/api/resend_alert")
def resend_alert():

    alerts = load_alerts()

    if alerts:

        ultimo = alerts[-1]

        alerts.append(ultimo)

        save_alerts(alerts)

    return {"status": "resent"}


# ==============================
# RODAR SERVIDOR
# ==============================

if __name__ == "__main__":
    app.run(debug=True)