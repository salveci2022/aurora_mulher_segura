from __future__ import annotations
from flask import Flask, render_template, request, redirect, session, url_for, jsonify
from pathlib import Path
import json
import time
import bcrypt
import os
import sys
import threading
import requests
from datetime import datetime
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

# ===== DEBUG =====
print("=" * 60)
print("🚀 INICIANDO AURORA MULHER SEGURA")
print("=" * 60)
print(f"🐍 Python version: {sys.version}")
print(f"📂 Diretório atual: {os.getcwd()}")
print(f"📋 Arquivos no diretório: {os.listdir()}")
print("=" * 60)

# Carrega variáveis do arquivo .env (apenas em desenvolvimento)
load_dotenv()

# ============================================
# REDUNDÂNCIA DE INFRAESTRUTURA
# ============================================
try:
    from multi_cloud import cloud_manager, get_active_backend, get_active_url
    print("✅ Módulo multi_cloud importado com sucesso")
except Exception as e:
    print(f"❌ Erro ao importar multi_cloud: {e}")
    # Versão fallback caso o módulo falhe
    class FallbackCloudManager:
        def __init__(self):
            self.backends = [{"name": "render", "url": "https://aurora-mulher-segura.onrender.com", "healthy": True, "failures": 0, "active": True}]
            self.current_backend = 0
            self.stats = {"total_switches": 0, "total_requests": 0, "failed_requests": 0}
        def get_active_backend(self): return self.backends[0]
        def get_active_url(self): return self.backends[0]["url"]
        def report_failure(self, *args): pass
        def get_status(self): return {"current": "render", "backends": [], "stats": self.stats}
    cloud_manager = FallbackCloudManager()
    get_active_backend = cloud_manager.get_active_backend
    get_active_url = cloud_manager.get_active_url
    print("⚠️ Usando fallback do cloud_manager")

# Windows pode não ter base de fusos (tzdata). Tentamos carregar e, se faltar,
# usamos horário local do sistema.
try:
    TZ = ZoneInfo("America/Sao_Paulo")
    print("✅ Fuso horário configurado: America/Sao_Paulo")
except Exception as e:
    TZ = None
    print(f"⚠️ Erro ao configurar fuso: {e}")

BASE_DIR = Path(__file__).resolve().parent
USERS_FILE = BASE_DIR / "users.json"
ALERTS_FILE = BASE_DIR / "alerts.log"
STATE_FILE = BASE_DIR / "state.json"

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "aurora_v21_ultra_estavel")

# Configurações de ambiente
ENCRYPTION_KEY = os.environ.get("ENCRYPTION_KEY")
STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY")
DATABASE_URL = os.environ.get("DATABASE_URL")
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")

# Rate limit simples (anti-spam)
_RATE = {"window_sec": 5, "last_by_ip": {}}

# Iniciar monitoramento em background
try:
    monitor_thread = threading.Thread(target=cloud_manager.monitor_loop, daemon=True)
    monitor_thread.start()
    print("✅ Thread de monitoramento iniciada")
except Exception as e:
    print(f"⚠️ Erro ao iniciar monitoramento: {e}")

def hash_password(raw: str) -> str:
    """Gera hash da senha usando bcrypt"""
    if not raw:
        return ""
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(raw.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(raw: str, hashed: str) -> bool:
    """Verifica se a senha corresponde ao hash"""
    try:
        if not raw or not hashed:
            return False
        return bcrypt.checkpw(raw.encode('utf-8'), hashed.encode('utf-8'))
    except Exception as e:
        print(f"Erro na verificação de senha: {e}")
        return False

def now_br_str() -> str:
    if TZ is None:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return datetime.now(TZ).strftime("%Y-%m-%d %H:%M:%S")

def ensure_files():
    """Garante que os arquivos necessários existam"""
    print("📁 Verificando arquivos necessários...")
    if not USERS_FILE.exists():
        admin_hash = hash_password("admin123")
        users_data = {
            "admin": {
                "password_hash": admin_hash,
                "role": "admin",
                "name": "Admin Aurora"
            }
        }
        USERS_FILE.write_text(
            json.dumps(users_data, indent=2, ensure_ascii=False), 
            encoding="utf-8"
        )
        print("✅ Arquivo users.json criado")
    
    if not ALERTS_FILE.exists():
        ALERTS_FILE.write_text("", encoding="utf-8")
        print("✅ Arquivo alerts.log criado")
    
    if not STATE_FILE.exists():
        STATE_FILE.write_text(
            json.dumps({"last_id": 0}, indent=2, ensure_ascii=False), 
            encoding="utf-8"
        )
        print("✅ Arquivo state.json criado")

def load_users() -> dict:
    """Carrega usuários do arquivo"""
    ensure_files()
    try:
        data = json.loads(USERS_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"Erro ao carregar users.json: {e}")
        data = {}
    
    # Verifica se o admin existe
    if "admin" not in data:
        data["admin"] = {
            "password_hash": hash_password("admin123"),
            "role": "admin",
            "name": "Admin Aurora"
        }
        save_users(data)
    
    return data

def save_users(data: dict) -> None:
    """Salva usuários no arquivo"""
    USERS_FILE.write_text(
        json.dumps(data, indent=2, ensure_ascii=False), 
        encoding="utf-8"
    )

def list_trusted_names() -> list[str]:
    users = load_users()
    arr = [info.get("name") or u for u, info in users.items() if info.get("role") == "trusted"]
    arr.sort(key=lambda s: s.lower())
    return arr

def next_alert_id() -> int:
    ensure_files()
    try:
        st = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        st = {"last_id": 0}
    st["last_id"] = int(st.get("last_id", 0)) + 1
    STATE_FILE.write_text(json.dumps(st, indent=2, ensure_ascii=False), encoding="utf-8")
    return st["last_id"]

def log_alert(payload: dict) -> None:
    ensure_files()
    with ALERTS_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    print(f"✅ Alerta #{payload['id']} salvo")

def read_last_alert():
    """Lê o último alerta do arquivo de logs"""
    ensure_files()
    txt = ALERTS_FILE.read_text(encoding="utf-8").strip()
    if not txt:
        return None
    lines = [ln for ln in txt.split("\n") if ln.strip()]
    try:
        last = json.loads(lines[-1])
        return last
    except Exception as e:
        print(f"Erro ao ler último alerta: {e}")
        return None

def replicate_alert(payload):
    """Replica alerta para backend secundário"""
    try:
        flyio_url = os.environ.get("FLYIO_URL", "https://aurora-backup.fly.dev")
        response = requests.post(
            f"{flyio_url}/api/replicate-alert",
            json=payload,
            timeout=2,
            headers={"X-Replication-Key": os.environ.get("REPLICATION_KEY", "aurora-secret")}
        )
        if response.status_code == 200:
            print("✅ Alerta replicado para Fly.io")
        else:
            print(f"⚠️ Falha na replicação: {response.status_code}")
    except Exception as e:
        print(f"⚠️ Erro na replicação: {e}")

# ===== ENDPOINTS =====

@app.get("/health")
def health():
    users = load_users()
    admin_ok = "admin" in users
    admin_login_ok = False
    if admin_ok:
        admin_hash = users["admin"].get("password_hash", "")
        admin_login_ok = verify_password("admin123", admin_hash)
    
    response = {
        "ok": True,
        "server_time_br": now_br_str(),
        "tz": "America/Sao_Paulo" if TZ is not None else "LOCAL_SYSTEM_TIME",
        "admin_exists": admin_ok,
        "admin_login_working": admin_login_ok,
        "css_ok": (BASE_DIR / "static" / "css" / "style.css").exists(),
        "js_ok": (BASE_DIR / "static" / "js" / "panic.js").exists(),
        "mp3_ok": (BASE_DIR / "static" / "audio" / "sirene.mp3").exists(),
        "template_panic_ok": (BASE_DIR / "templates" / "panic_button.html").exists(),
        "template_trusted_ok": (BASE_DIR / "templates" / "panel_trusted.html").exists(),
        "users_json_ok": USERS_FILE.exists(),
        "alerts_log_ok": ALERTS_FILE.exists(),
        "env_vars_configured": {
            "secret_key": bool(app.secret_key),
            "encryption_key": bool(ENCRYPTION_KEY),
            "stripe_key": bool(STRIPE_SECRET_KEY),
            "database_url": bool(DATABASE_URL),
            "admin_email": bool(ADMIN_EMAIL)
        },
        # Adiciona info de redundância
        "redundancy": {
            "active_backend": cloud_manager.get_active_backend()["name"],
            "backends": [
                {
                    "name": b["name"],
                    "healthy": b["healthy"],
                    "failures": b["failures"]
                }
                for b in cloud_manager.backends
            ],
            "total_switches": cloud_manager.stats["total_switches"]
        }
    }
    
    return jsonify(response)

@app.get("/legal")
def legal():
    return render_template("legal.html")

@app.get("/")
def index():
    return redirect(url_for("panic_button"))

@app.get("/panic")
def panic_button():
    trusted = list_trusted_names()
    return render_template("panic_button.html", trusted=trusted)

@app.post("/api/send_alert")
def send_alert():
    # Rate limit
    ip = request.headers.get("X-Forwarded-For", request.remote_addr) or "unknown"
    now = time.time()
    last = _RATE["last_by_ip"].get(ip, 0)
    if now - last < _RATE["window_sec"]:
        return jsonify({"ok": False, "error": "Aguarde alguns segundos."}), 429
    _RATE["last_by_ip"][ip] = now

    data = request.get_json(silent=True) or {}
    
    # Processar localização
    location_data = None
    if data.get("location"):
        loc = data.get("location")
        if isinstance(loc, dict):
            lat = loc.get("lat")
            lon = loc.get("lon")
            if lat is not None and lon is not None:
                location_data = {
                    "lat": float(lat),
                    "lon": float(lon),
                    "accuracy_m": loc.get("accuracy_m"),
                    "timestamp": now_br_str()
                }
    
    payload = {
        "id": next_alert_id(),
        "ts": now_br_str(),
        "name": (data.get("name") or "Não informado"),
        "situation": (data.get("situation") or "Não especificado"),
        "message": (data.get("message") or ""),
        "location": location_data,
        "consent_location": True if location_data else False,
        "processed_by": cloud_manager.get_active_backend()["name"]  # Qual backend processou
    }
    
    log_alert(payload)
    
    # Se estamos no Render, tenta replicar para o Fly.io (opcional)
    try:
        if cloud_manager.get_active_backend()["name"] == "render":
            # Envia cópia para o Fly.io em background
            threading.Thread(target=replicate_alert, args=(payload,)).start()
    except:
        pass
    
    return jsonify({"ok": True, "id": payload["id"]})

@app.get("/api/last_alert")
def last_alert():
    last = read_last_alert()
    return jsonify({"ok": True, "last": last})

@app.get("/api/alerts")
def get_alerts():
    ensure_files()
    txt = ALERTS_FILE.read_text(encoding="utf-8").strip()
    if not txt:
        return jsonify({"ok": True, "alerts": []})
    
    lines = [ln for ln in txt.split("\n") if ln.strip()]
    alerts = []
    for line in lines[-50:]:
        try:
            alerts.append(json.loads(line))
        except:
            pass
    return jsonify({"ok": True, "alerts": alerts})

# ===== ENDPOINTS DE REDUNDÂNCIA =====

@app.get("/api/redundancy-status")
def redundancy_status():
    """Mostra status dos backends e qual está ativo"""
    return jsonify(cloud_manager.get_status())

@app.post("/api/test-failover")
def test_failover():
    """Simula falha no backend atual para testar failover"""
    backend = cloud_manager.get_active_backend()
    cloud_manager.report_failure(backend["name"])
    
    # Forçar 3 falhas para causar troca
    for _ in range(3):
        cloud_manager.report_failure(backend["name"])
    
    return jsonify({
        "ok": True,
        "message": f"Failover testado. Novo backend: {cloud_manager.get_active_backend()['name']}",
        "status": cloud_manager.get_status()
    })

@app.post("/api/replicate-alert")
def replicate_alert_endpoint():
    """Recebe replicação de alerta do backend principal"""
    key = request.headers.get("X-Replication-Key")
    if key != os.environ.get("REPLICATION_KEY", "aurora-secret"):
        return jsonify({"ok": False}), 403
    
    data = request.get_json()
    if data:
        log_alert(data)
        return jsonify({"ok": True})
    return jsonify({"ok": False}), 400

# ===== ADMIN =====
@app.route("/panel/login", methods=["GET", "POST"])
def admin_login():
    users = load_users()
    error = False
    
    if request.method == "POST":
        u = (request.form.get("user") or "").strip()
        p = (request.form.get("password") or "")
        
        info = users.get(u)
        if info and info.get("role") == "admin" and verify_password(p, info.get("password_hash", "")):
            session.clear()
            session["role"] = "admin"
            session["user"] = u
            return redirect(url_for("admin_panel"))
        error = True
    
    return render_template("login_admin.html", error=error)

@app.get("/panel")
def admin_panel():
    if session.get("role") != "admin":
        return redirect(url_for("admin_login"))
    users = load_users()
    trusted = {u: info for u, info in users.items() if info.get("role") == "trusted"}
    msg = request.args.get("msg", "")
    err = request.args.get("err", "")
    return render_template("panel_admin.html", trusted=trusted, msg=msg, err=err)

@app.post("/panel/add_trusted")
def admin_add_trusted():
    if session.get("role") != "admin":
        return redirect(url_for("admin_login"))
    
    name = (request.form.get("trusted_name") or "").strip()
    username = (request.form.get("trusted_user") or "").strip().lower()
    password = (request.form.get("trusted_password") or "").strip()

    if not name or not username or not password:
        return redirect("/panel?err=Preencha+todos+os+campos")

    users = load_users()
    if username in users:
        return redirect("/panel?err=Usuario+ja+existe")

    trusted_users = [u for u, info in users.items() if info.get("role") == "trusted"]
    if len(trusted_users) >= 3:
        return redirect("/panel?err=Limite+de+3+pessoas+atingido")

    users[username] = {
        "password_hash": hash_password(password), 
        "role": "trusted", 
        "name": name
    }
    save_users(users)
    return redirect("/panel?msg=Pessoa+cadastrada+com+sucesso")

@app.post("/panel/delete_trusted")
def admin_delete_trusted():
    if session.get("role") != "admin":
        return redirect(url_for("admin_login"))
    username = (request.form.get("username") or "").strip()
    users = load_users()
    if username in users and users[username].get("role") == "trusted":
        users.pop(username)
        save_users(users)
        return redirect("/panel?msg=Pessoa+removida")
    return redirect("/panel?err=Nao+foi+possivel+remover")

@app.get("/logout_admin")
def logout_admin():
    session.clear()
    return redirect(url_for("admin_login"))

# ===== TRUSTED =====
@app.route("/trusted/login", methods=["GET", "POST"])
def trusted_login():
    users = load_users()
    error = False
    error_msg = ""
    
    if request.method == "POST":
        u = (request.form.get("user") or "").strip().lower()
        p = (request.form.get("password") or "")
        
        info = users.get(u)
        if info and info.get("role") == "trusted" and verify_password(p, info.get("password_hash", "")):
            session.clear()
            session["role"] = "trusted"
            session["trusted"] = u
            session["trusted_name"] = info.get("name", u)
            return redirect(url_for("trusted_panel"))
        error = True
        error_msg = "Usuário ou senha inválidos"
    
    return render_template("login_trusted.html", error=error, error_msg=error_msg)

@app.get("/trusted/panel")
def trusted_panel():
    if session.get("role") != "trusted":
        return redirect(url_for("trusted_login"))
    
    users = load_users()
    u = session.get("trusted")
    
    if not u:
        session.clear()
        return redirect(url_for("trusted_login"))
    
    info = users.get(u, {})
    display_name = info.get("name") or u
    
    return render_template("panel_trusted.html", display_name=display_name)

@app.get("/logout_trusted")
def logout_trusted():
    session.clear()
    return redirect(url_for("trusted_login"))

@app.route("/trusted/change_password", methods=["GET", "POST"])
def trusted_change_password():
    if session.get("role") != "trusted":
        return redirect(url_for("trusted_login"))
    
    msg, err = "", ""
    if request.method == "POST":
        old = request.form.get("old_password") or ""
        new = (request.form.get("new_password") or "").strip()
        users = load_users()
        u = session.get("trusted")
        info = users.get(u)
        
        if not info or (not verify_password(old, info.get("password_hash", ""))):
            err = "Senha atual incorreta."
        elif len(new) < 4:
            err = "Nova senha muito curta (mínimo 4)."
        else:
            users[u]["password_hash"] = hash_password(new)
            save_users(users)
            msg = "Senha alterada com sucesso."
    
    return render_template("trusted_change_password.html", msg=msg, err=err)

@app.route("/trusted/recover", methods=["GET", "POST"])
def trusted_recover():
    msg, err = "", ""
    if request.method == "POST":
        u = (request.form.get("user") or "").strip().lower()
        new = (request.form.get("new_password") or "").strip()
        users = load_users()
        info = users.get(u)
        
        if not info or info.get("role") != "trusted":
            err = "Usuário não encontrado."
        elif len(new) < 4:
            err = "Senha muito curta (mínimo 4)."
        else:
            users[u]["password_hash"] = hash_password(new)
            save_users(users)
            msg = "Senha redefinida. Faça login."
    
    return render_template("trusted_recover.html", msg=msg, err=err)

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Iniciando Aurora Mulher Segura")
    print("=" * 60)
    
    # Mostra status das variáveis de ambiente
    print("\n📋 Status das configurações:")
    print(f"   SECRET_KEY: {'✅' if app.secret_key else '❌'}")
    print(f"   ENCRYPTION_KEY: {'✅' if ENCRYPTION_KEY else '❌'}")
    print(f"   STRIPE_SECRET_KEY: {'✅' if STRIPE_SECRET_KEY else '❌'}")
    print(f"   DATABASE_URL: {'✅' if DATABASE_URL else '❌'}")
    print(f"   ADMIN_EMAIL: {'✅' if ADMIN_EMAIL else '❌'}")
    print("=" * 60)
    
    ensure_files()
    
    port = int(os.environ.get("PORT", 5000))
    print(f"\n🌐 Servidor rodando em: http://localhost:{port}")
    print("=" * 60)
    
    app.run(host="0.0.0.0", port=port, debug=False)