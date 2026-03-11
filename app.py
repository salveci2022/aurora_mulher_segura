from flask import Flask, render_template, request, redirect, session, jsonify
import json
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = "aurora_segura_2026"

ALERT_FILE = "alerts.log"

if not os.path.exists(ALERT_FILE):
    with open(ALERT_FILE,"w") as f:
        json.dump([],f)


def load_alerts():

    try:
        with open(ALERT_FILE,"r") as f:
            return json.load(f)
    except:
        return []


def save_alerts(data):

    with open(ALERT_FILE,"w") as f:
        json.dump(data,f,indent=2)


# =========================
# PAGINA INICIAL
# =========================

@app.route("/")
def home():

    if not session.get("termo_aceito"):
        return redirect("/termo")

    return redirect("/panic")


# =========================
# TERMO DE RESPONSABILIDADE
# =========================

@app.route("/termo", methods=["GET","POST"])
def termo():

    if request.method == "POST":

        session["termo_aceito"] = True
        session["data_aceite"] = datetime.now().strftime("%d/%m/%Y %H:%M")

        return redirect("/panic")

    return render_template("termo_responsabilidade.html")


# =========================
# PAINEL DA MULHER (SOS)
# =========================

@app.route("/panic")
def panic():

    if not session.get("termo_aceito"):
        return redirect("/termo")

    return render_template("panic_button.html")


# =========================
# RECEBER ALERTA
# =========================

@app.route("/api/alert", methods=["POST"])
def receive_alert():

    data = request.json

    alerts = load_alerts()

    alerta = {

        "id": len(alerts)+1,
        "nome": data.get("nome"),
        "situacao": data.get("situacao"),
        "mensagem": data.get("mensagem"),
        "hora": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "localizacao": data.get("localizacao")

    }

    alerts.append(alerta)

    save_alerts(alerts)

    return jsonify({"status":"ok"})


# =========================
# ULTIMO ALERTA
# =========================

@app.route("/api/last_alert")
def last_alert():

    alerts = load_alerts()

    if not alerts:
        return {"alert":None}

    return {"alert":alerts[-1]}


# =========================
# HISTORICO
# =========================

@app.route("/api/alerts")
def alerts():

    return jsonify(load_alerts())


if __name__ == "__main__":
    app.run(debug=True)