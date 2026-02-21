from flask import Flask, request, jsonify
from pathlib import Path
import json
from datetime import datetime
import traceback

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
TEMPL_DIR = BASE_DIR / "templates"

USERS_FILE = DATA_DIR / "users.json"
ALERTS_FILE = DATA_DIR / "alerts.json"

def ensure_files():
    DATA_DIR.mkdir(exist_ok=True)
    TEMPL_DIR.mkdir(exist_ok=True)

    if not USERS_FILE.exists():
        USERS_FILE.write_text(json.dumps({}, ensure_ascii=False), encoding="utf-8")

    if not ALERTS_FILE.exists():
        ALERTS_FILE.write_text(json.dumps([], ensure_ascii=False), encoding="utf-8")

def load_alerts():
    return json.loads(ALERTS_FILE.read_text(encoding="utf-8"))

def save_alerts(data):
    ALERTS_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

ensure_files()

@app.route("/health")
def health():
    return jsonify({"status": "ok", "time": datetime.now().isoformat()})

@app.route("/")
@app.route("/panic")
def panic():
    # Se o template não existir, NÃO quebra — mostra HTML mínimo
    panic_file = TEMPL_DIR / "panic.html"
    if not panic_file.exists():
        return """
        <h1>Aurora Mulher Segura</h1>
        <p>Template <b>templates/panic.html</b> não encontrado.</p>
        <p>Crie o arquivo e faça deploy novamente.</p>
        <p>Teste do servidor: <a href="/health">/health</a></p>
        """, 200

    # Renderizar manualmente (sem Jinja) pra evitar TemplateNotFound/Jinja errors
    return panic_file.read_text(encoding="utf-8"), 200

@app.route("/trusted")
def trusted():
    trusted_file = TEMPL_DIR / "trusted.html"
    if not trusted_file.exists():
        return """
        <h1>Pessoa de Confiança</h1>
        <p>Template <b>templates/trusted.html</b> não encontrado.</p>
        """, 200
    return trusted_file.read_text(encoding="utf-8"), 200

@app.route("/api/panic", methods=["POST"])
def api_panic():
    data = request.get_json(force=True, silent=True) or {}

    alerts = load_alerts()
    alerts.append({
        "name": data.get("name", "Sem nome"),
        "lat": data.get("lat"),
        "lng": data.get("lng"),
        "situation": data.get("situation", ""),
        "message": data.get("message", ""),
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    save_alerts(alerts)

    return jsonify({"status": "ok"})

@app.route("/api/alerts")
def api_alerts():
    return jsonify(load_alerts())

@app.errorhandler(Exception)
def handle_error(e):
    # Isso imprime o erro no LOG do Render (IMPORTANTÍSSIMO)
    print("=== ERRO 500 ===")
    traceback.print_exc()
    return "Erro interno (500). Veja os logs do servidor.", 500