from flask import Flask, render_template, request, jsonify
from pathlib import Path
import json
from datetime import datetime

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

USERS_FILE = DATA_DIR / "users.json"
ALERTS_FILE = DATA_DIR / "alerts.json"

# ---------------------------
# SETUP
# ---------------------------

def ensure_files():
    DATA_DIR.mkdir(exist_ok=True)

    if not USERS_FILE.exists():
        USERS_FILE.write_text(json.dumps({}))

    if not ALERTS_FILE.exists():
        ALERTS_FILE.write_text(json.dumps([]))

ensure_files()

# ---------------------------
# HELPERS
# ---------------------------

def load_users():
    return json.loads(USERS_FILE.read_text())

def save_users(data):
    USERS_FILE.write_text(json.dumps(data, indent=4))

def load_alerts():
    return json.loads(ALERTS_FILE.read_text())

def save_alerts(data):
    ALERTS_FILE.write_text(json.dumps(data, indent=4))

# ---------------------------
# ROTAS
# ---------------------------

@app.route("/")
def home():
    return render_template("panic.html")

@app.route("/panic")
def panic():
    return render_template("panic.html")

@app.route("/trusted")
def trusted():
    return render_template("trusted.html")

@app.route("/api/panic", methods=["POST"])
def api_panic():
    data = request.json

    alerts = load_alerts()

    alerts.append({
        "name": data.get("name"),
        "lat": data.get("lat"),
        "lng": data.get("lng"),
        "time": datetime.now().strftime("%H:%M:%S")
    })

    save_alerts(alerts)

    return jsonify({"status": "ok"})

@app.route("/api/alerts")
def api_alerts():
    return jsonify(load_alerts())

# ---------------------------
# START
# ---------------------------

if __name__ == "__main__":
    app.run(debug=True)