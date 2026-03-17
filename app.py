from flask import Flask, render_template, request, jsonify
from datetime import datetime
import json
import os

app = Flask(__name__)

ALERT_FILE = "alerts.json"


# ================================
# CRIAR ARQUIVO DE ALERTAS
# ================================

if not os.path.exists(ALERT_FILE):
    with open(ALERT_FILE, "w") as f:
        json.dump([], f)


# ================================
# CARREGAR ALERTAS
# ================================

def load_alerts():

    try:
        with open(ALERT_FILE, "r") as f:
            return json.load(f)

    except:
        return []


# ================================
# SALVAR ALERTAS
# ================================

def save_alerts(alerts):

    with open(ALERT_FILE, "w") as f:
        json.dump(alerts, f, indent=4)


# ================================
# TELA INICIAL
# ================================

@app.route("/")
def home():

    return render_template("panic_button.html")


# ================================
# PAINEL DA MULHER
# ================================

@app.route("/panic")
def panic():

    return render_template("panic_button.html")


# ================================
# PAINEL PESSOA DE CONFIANÇA
# ================================

@app.route("/confidant")
def confidant():

    return render_template("panel_confidant.html")


# ================================
# HISTÓRICO
# ================================

@app.route("/historico")
def historico():

    alerts = load_alerts()

    return jsonify(alerts)


# ================================
# RECEBER ALERTA
# ================================

@app.route("/api/alert", methods=["POST"])
def receber_alerta():

    try:

        data = request.get_json(force=True)

    except:

        return jsonify({
            "status": "erro",
            "msg": "JSON inválido"
        }), 400


    alerts = load_alerts()


    # validar localização
    localizacao = data.get("localizacao")

    if isinstance(localizacao, dict):

        lat = localizacao.get("lat")
        lng = localizacao.get("lng")

        if lat is None or lng is None:
            localizacao = None

    else:

        localizacao = None


    alerta = {

        "nome": data.get("nome", "Usuária"),

        "situacao": data.get("situacao", "Emergência"),

        "mensagem": data.get("mensagem", ""),

        "hora": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),

        "localizacao": localizacao

    }


    alerts.append(alerta)

    save_alerts(alerts)


    return jsonify({
        "status": "ok"
    })


# ================================
# LISTAR ALERTAS
# ================================

@app.route("/api/alerts")
def listar_alertas():

    alerts = load_alerts()

    return jsonify(alerts)


# ================================
# HEALTH CHECK
# ================================

@app.route("/health")
def health():

    return jsonify({
        "status": "online"
    })


# ================================
# EXECUTAR SERVIDOR
# ================================

if __name__ == "__main__":

    app.run(debug=True)