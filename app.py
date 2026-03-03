import os
import json
from flask import Flask, render_template, request, redirect, session, url_for, jsonify
from flask_cors import CORS
from pywebpush import webpush, WebPushException

app = Flask(__name__)
CORS(app)

# ==========================
# CONFIGURAÇÕES
# ==========================

app.secret_key = os.environ.get("SECRET_KEY", "dev_secret_key")

VAPID_PUBLIC_KEY = "BB7XEWW3AetNIC14i0HEpkgfelgS9drXIN5uRf9NOBkgQz_YTRst4GWiXn7fNZIQdprjYLUfTYmb4EtTF3F0ww8"
VAPID_PRIVATE_KEY = "MIGHAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBG0wawIBAQQg3cHwUAWs4FzFGJl9J2HdRJeuP9IjswY-Mib5tRv95H2hRANCAAQe1xFltwHrTSAteItBxKZIH3pYEvXa1yDebkX_TTgZIEM_2E0bLeBlol5-3zWSEHaa42C1H02Jm-BLUxdxdMMP"

SUBSCRIPTIONS_FILE = "subscriptions.json"


# ==========================
# FUNÇÕES AUXILIARES
# ==========================

def load_subscriptions():
    if not os.path.exists(SUBSCRIPTIONS_FILE):
        return []
    with open(SUBSCRIPTIONS_FILE, "r") as f:
        return json.load(f)


def save_subscriptions(subscriptions):
    with open(SUBSCRIPTIONS_FILE, "w") as f:
        json.dump(subscriptions, f)


# ==========================
# ROTAS PRINCIPAIS
# ==========================

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/panic")
def panic_page():
    return render_template("panic_button.html")


# ==========================
# LOGIN TRUSTED
# ==========================

@app.route("/trusted/login", methods=["GET", "POST"])
def trusted_login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username == "admin" and password == "123456":
            session["trusted_logged"] = True
            return redirect(url_for("trusted_panel"))
        else:
            return render_template("trusted_login.html", erro="Usuário ou senha inválidos")

    return render_template("trusted_login.html")


@app.route("/trusted/panel")
def trusted_panel():
    if not session.get("trusted_logged"):
        return redirect(url_for("trusted_login"))
    return render_template("panel_trusted.html")


@app.route("/trusted/logout")
def trusted_logout():
    session.clear()
    return redirect(url_for("trusted_login"))


# ==========================
# LOGIN ADMIN COMPATÍVEL
# ==========================

@app.route("/panel/login", methods=["GET", "POST"])
def panel_login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username == "admin" and password == "123456":
            session["trusted_logged"] = True
            return redirect(url_for("panel_dashboard"))
        else:
            return render_template("trusted_login.html", erro="Usuário ou senha inválidos")

    return render_template("trusted_login.html")


@app.route("/panel")
def panel_dashboard():
    if not session.get("trusted_logged"):
        return redirect(url_for("panel_login"))

    return render_template("panel_trusted.html")


# ==========================
# API PUSH
# ==========================

@app.route("/api/subscribe", methods=["POST"])
def subscribe():
    subscription = request.get_json()
    subscriptions = load_subscriptions()

    if subscription not in subscriptions:
        subscriptions.append(subscription)
        save_subscriptions(subscriptions)

    return jsonify({"status": "subscribed"}), 201


@app.route("/api/send_alert", methods=["POST"])
def send_alert():
    data = request.get_json()

    payload = {
        "title": "🚨 ALERTA AURORA",
        "body": data.get("message", "Alerta acionado!"),
        "url": "/panel"
    }

    subscriptions = load_subscriptions()

    for sub in subscriptions:
        try:
            webpush(
                subscription_info=sub,
                data=json.dumps(payload),
                vapid_private_key=VAPID_PRIVATE_KEY,
                vapid_claims={
                    "sub": "mailto:admin@aurora.com"
                }
            )
        except WebPushException as ex:
            print("Erro no envio:", ex)

    return jsonify({"status": "alert sent"}), 200


# ==========================
# BOTÃO DE PÂNICO (ENVIO)
# ==========================

@app.route("/panic/send", methods=["POST"])
def panic_send():
    return send_alert()


# ==========================
# START
# ==========================

if __name__ == "__main__":
    app.run(debug=True)