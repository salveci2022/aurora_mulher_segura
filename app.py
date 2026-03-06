from flask import Flask, render_template, request, jsonify, redirect
from flask_cors import CORS
from datetime import datetime
import json
import requests
from pathlib import Path
import pytz

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# TELEGRAM
BOT_TOKEN = "8535764483:AAGtUMUefjQbhO2zjzND9Ziu1qjQkPtznzE"
CHAT_ID = "5672315001"

BR_TZ = pytz.timezone('America/Sao_Paulo')

BASE_DIR = Path(__file__).resolve().parent
ALERTS_FILE = BASE_DIR / "alerts.log"
STATE_FILE = BASE_DIR / "state.json"


# ===============================
# ENVIAR ALERTA PARA TELEGRAM
# ===============================
def enviar_alerta_telegram(payload):

    try:

        if payload.get("location"):
            lat = payload["location"]["lat"]
            lng = payload["location"]["lng"]
            mapa = f"https://maps.google.com/?q={lat},{lng}"
        else:
            mapa = "Localização não enviada"

        mensagem = f"""
🚨 ALERTA AURORA 🚨

Nome: {payload.get("name")}
Situação: {payload.get("situation")}
Mensagem: {payload.get("message")}

📍 Localização:
{mapa}

⏰ {payload.get("ts_br")}
"""

        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

        requests.post(url, data={
            "chat_id": CHAT_ID,
            "text": mensagem
        })

        print("ALERTA ENVIADO TELEGRAM")

    except Exception as e:
        print("Erro Telegram:", e)


# ===============================
# SALVAR ALERTA
# ===============================
def salvar_alerta(payload):

    with open(ALERTS_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")


# ===============================
# LER ÚLTIMO ALERTA
# ===============================
def ler_ultimo_alerta():

    try:

        linhas = open(ALERTS_FILE, encoding="utf-8").read().strip().split("\n")

        if not linhas:
            return None

        return json.loads(linhas[-1])

    except:
        return None


# ===============================
# PÁGINAS
# ===============================
@app.route("/")
def home():
    return redirect("/panic")


@app.route("/panic")
def panic():
    return render_template("panic_button.html")


@app.route("/trusted")
def trusted():
    return render_template("panel_trusted.html")


# ===============================
# ENVIAR ALERTA
# ===============================
@app.route("/api/send_alert", methods=["POST"])
def enviar_alerta():

    data = request.get_json()

    location = None

    if data.get("lat") and data.get("lng"):

        location = {
            "lat": float(data.get("lat")),
            "lng": float(data.get("lng")),
            "accuracy": data.get("accuracy")
        }

    now = datetime.now(BR_TZ).strftime("%d/%m/%Y %H:%M:%S")

    payload = {
        "id": int(datetime.now().timestamp()),
        "ts_br": now,
        "name": data.get("name"),
        "situation": data.get("situation"),
        "message": data.get("message"),
        "location": location
    }

    salvar_alerta(payload)

    enviar_alerta_telegram(payload)

    return jsonify({"ok": True})


# ===============================
# RASTREAMENTO CONTÍNUO
# ===============================
@app.route("/api/send_location", methods=["POST"])
def send_location():

    data = request.get_json()

    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f)

    return jsonify({"ok": True})


# ===============================
# LER ÚLTIMO ALERTA
# ===============================
@app.route("/api/last_alert")
def ultimo():

    alerta = ler_ultimo_alerta()

    return jsonify({
        "ok": True,
        "last": alerta
    })


# ===============================
# INICIAR SERVIDOR
# ===============================
if __name__ == "__main__":

    if not ALERTS_FILE.exists():
        ALERTS_FILE.write_text("")

    if not STATE_FILE.exists():
        STATE_FILE.write_text("{}")

    app.run(host="0.0.0.0", port=5000, debug=True)