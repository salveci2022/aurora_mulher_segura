from __future__ import annotations
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session, send_file, make_response
from flask_cors import CORS
from datetime import datetime
import os
import json
from pathlib import Path
from fpdf import FPDF
import tempfile
import pytz

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = "aurora_v20_ultra_estavel_secure_2026"
CORS(app)

# Configuração do fuso horário do Brasil
BR_TZ = pytz.timezone('America/Sao_Paulo')

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"
USERS_FILE = BASE_DIR / "users.json"
ALERTS_FILE = BASE_DIR / "alerts.log"
STATE_FILE = BASE_DIR / "state.json"

# ===== EVITAR CACHE PARA ARQUIVOS ESTÁTICOS =====
@app.before_request
def before_request():
    # Para evitar cache
    if request.path.startswith('/static/'):
        response = make_response()
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

def _ensure_files():
    """Cria arquivos necessários se não existirem"""
    if not USERS_FILE.exists():
        USERS_FILE.write_text(json.dumps({
            "admin": {
                "password": "admin123",
                "role": "admin",
                "name": "Admin Aurora"
            }
        }, indent=2, ensure_ascii=False), encoding="utf-8")
    
    if not ALERTS_FILE.exists():
        ALERTS_FILE.write_text("", encoding="utf-8")
    
    if not STATE_FILE.exists():
        STATE_FILE.write_text(json.dumps({"last_id": 0}, indent=2), encoding="utf-8")

def load_users():
    """Carrega usuários do arquivo JSON"""
    _ensure_files()
    try:
        return json.loads(USERS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {
            "admin": {
                "password": "admin123",
                "role": "admin",
                "name": "Admin Aurora"
            }
        }

def save_users(data):
    """Salva usuários no arquivo JSON"""
    USERS_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

def _get_next_alert_id():
    """Gera próximo ID de alerta"""
    _ensure_files()
    try:
        st = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        st = {"last_id": 0}
    st["last_id"] = int(st.get("last_id", 0)) + 1
    STATE_FILE.write_text(json.dumps(st, indent=2, ensure_ascii=False), encoding="utf-8")
    return st["last_id"]

def log_alert(payload):
    """Registra alerta no arquivo de log"""
    _ensure_files()
    with ALERTS_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")

def read_last_alert():
    """Lê o último alerta do log"""
    _ensure_files()
    try:
        txt = ALERTS_FILE.read_text(encoding="utf-8").strip()
        if not txt:
            return None
        lines = [ln for ln in txt.split("\n") if ln.strip()]
        return json.loads(lines[-1])
    except Exception:
        return None

def get_all_alerts():
    """Retorna todos os alertas"""
    alerts = []
    try:
        if ALERTS_FILE.exists():
            with open(ALERTS_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        alerts.append(json.loads(line))
        return alerts
    except Exception:
        return []

# ===== ROTAS PRINCIPAIS =====
@app.route('/')
def index():
    return redirect(url_for('panic_button'))

@app.route('/panic')
def panic_button():
    users = load_users()
    trusted_names = [info.get("name") or username for username, info in users.items() if info.get("role") == "trusted"]
    return render_template('panic_button.html', trusted_names=trusted_names)

@app.route('/api/send_alert', methods=['POST'])
def api_send_alert():
    data = request.get_json(silent=True) or {}
    alert_id = _get_next_alert_id()
    
    # Captura localização GPS
    lat = data.get("lat")
    lng = data.get("lng")
    location = None
    if lat and lng:
        location = {"lat": float(lat), "lng": float(lng)}
    
    # Formata horário no fuso horário do Brasil
    now_br = datetime.now(BR_TZ)
    formatted_time = now_br.strftime("%Y-%m-%d %H:%M:%S")
    
    # Monta payload do alerta
    payload = {
        "id": alert_id,
        "ts": formatted_time,
        "name": (data.get("name") or "Usuária"),
        "situation": (data.get("situation") or "Emergência"),
        "message": (data.get("message") or ""),
        "location": location,
    }
    log_alert(payload)
    
    print(f"✅ Alerta #{alert_id} recebido - {payload['name']} - {payload['situation']}")
    if location:
        print(f"📍 Localização: {location['lat']}, {location['lng']}")
    
    return jsonify({
        "ok": True,
        "id": alert_id,
        "message": "Alerta recebido com sucesso!",
        "location": location
    })

@app.route('/api/last_alert')
def api_last_alert():
    last = read_last_alert()
    return jsonify({"ok": True, "last": last})

@app.route('/health')
def health():
    now_br = datetime.now(BR_TZ)
    return jsonify({
        "ok": True,
        "server_time": now_br.isoformat(),
        "users_json_ok": USERS_FILE.exists(),
        "alerts_log_ok": ALERTS_FILE.exists(),
        "state_file_ok": STATE_FILE.exists(),
    })

# ===== RELATÓRIOS EM PDF - CORRIGIDO =====
@app.route('/relatorio/pdf')
def relatorio_pdf():
    """Gera relatório PDF com todos os alertas - CORRIGIDO"""
    try:
        alerts = get_all_alerts()
        
        pdf = FPDF()
        pdf.add_page()
        
        # Cabeçalho
        pdf.set_font("Arial", "B", 16)
        pdf.cell(200, 10, txt="AURORA MULHER SEGURA", ln=1, align="C")
        pdf.set_font("Arial", "I", 12)
        pdf.cell(200, 10, txt="Relatorio de Alertas de Emergencia", ln=1, align="C")
        pdf.ln(10)
        
        # Data e hora no horário do Brasil
        now_br = datetime.now(BR_TZ)
        formatted_time = now_br.strftime("%d/%m/%Y %H:%M:%S")
        pdf.set_font("Arial", "", 10)
        pdf.cell(200, 8, txt=f"Data: {formatted_time}", ln=1)
        pdf.cell(200, 8, txt=f"Total de Alertas: {len(alerts)}", ln=1)
        pdf.ln(10)
        
        # Estatísticas
        with_location = sum(1 for a in alerts if a.get('location'))
        without_location = len(alerts) - with_location
        
        pdf.set_font("Arial", "B", 12)
        pdf.cell(200, 10, txt="ESTATISTICAS", ln=1)
        pdf.set_font("Arial", "", 10)
        pdf.cell(200, 8, txt=f"* Alertas com GPS: {with_location}", ln=1)
        pdf.cell(200, 8, txt=f"* Alertas sem GPS: {without_location}", ln=1)
        pdf.ln(10)
        
        # Tabela de alertas
        pdf.set_font("Arial", "B", 12)
        pdf.cell(200, 10, txt="HISTORICO DE ALERTAS", ln=1)
        pdf.ln(5)
        
        pdf.set_font("Arial", "B", 9)
        pdf.cell(25, 8, txt="ID", border=1)
        pdf.cell(40, 8, txt="DATA/HORA", border=1)
        pdf.cell(35, 8, txt="USUARIA", border=1)
        pdf.cell(45, 8, txt="SITUACAO", border=1)
        pdf.cell(45, 8, txt="LOCALIZACAO", border=1)
        pdf.ln()
        
        pdf.set_font("Arial", "", 8)
        for alert in alerts[-20:]:
            # Formata o horário corretamente
            ts = alert.get('ts', '')
            if ts:
                try:
                    dt = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
                    dt_br = dt.replace(tzinfo=pytz.utc).astimezone(BR_TZ)
                    formatted_ts = dt_br.strftime("%d/%m/%Y %H:%M:%S")
                except:
                    formatted_ts = ts
            else:
                formatted_ts = "N/A"
                
            pdf.cell(25, 6, txt=str(alert.get('id', 'N/A')), border=1)
            pdf.cell(40, 6, txt=formatted_ts, border=1)
            pdf.cell(35, 6, txt=alert.get('name', 'N/A'), border=1)
            pdf.cell(45, 6, txt=alert.get('situation', 'N/A'), border=1)
            
            loc = alert.get('location')
            if loc:
                loc_str = f"{loc.get('lat', 'N/A')}, {loc.get('lng', 'N/A')}"
            else:
                loc_str = "Nao disponivel"
            pdf.cell(45, 6, txt=loc_str[:40], border=1)
            pdf.ln()
        
        pdf.ln(10)
        
        # Rodapé
        pdf.set_font("Arial", "I", 8)
        pdf.cell(200, 8, txt="Documento gerado automaticamente pelo sistema Aurora Mulher Segura", ln=1, align="C")
        pdf.cell(200, 8, txt="Este relatorio contem informacoes confidenciais de seguranca", ln=1, align="C")
        
        # Salvar PDF temporário
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        pdf.output(temp_file.name)
        
        return send_file(
            temp_file.name,
            as_attachment=True,
            download_name=f"relatorio_aurora_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            mimetype='application/pdf'
        )
        
    except Exception as e:
        print(f"Erro ao gerar PDF: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# ===== ADMIN =====
@app.route('/panel/login', methods=['GET', 'POST'])
def admin_login():
    users = load_users()
    error = False
    if request.method == 'POST':
        u = (request.form.get("user") or "").strip()
        p = (request.form.get("password") or "")
        info = users.get(u)
        if info and info.get("role") == "admin" and info.get("password") == p:
            session.clear()
            session["role"] = "admin"
            session["user"] = u
            return redirect(url_for('admin_panel'))
        error = True
    return render_template('login_admin.html', error=error)

@app.route('/panel')
def admin_panel():
    if session.get("role") != "admin":
        return redirect(url_for('admin_login'))
    
    users = load_users()
    trusted = {u: info for u, info in users.items() if info.get("role") == "trusted"}
    
    alerts = get_all_alerts()
    today = datetime.now(BR_TZ).strftime('%Y-%m-%d')
    
    stats = {
        'total': len(alerts),
        'today': sum(1 for a in alerts if a.get('ts', '').startswith(today)),
        'with_location': sum(1 for a in alerts if a.get('location')),
        'without_location': sum(1 for a in alerts if not a.get('location'))
    }
    
    return render_template('panel_admin.html', trusted=trusted, alerts=alerts, stats=stats)

@app.route('/panel/add_trusted', methods=['POST'])
def admin_add_trusted():
    if session.get("role") != "admin":
        return redirect(url_for('admin_login'))
    
    name = (request.form.get("trusted_name") or "").strip()
    username = (request.form.get("trusted_user") or "").strip().lower()
    password = (request.form.get("trusted_password") or "").strip()
    
    if not name or not username or not password:
        return redirect("/panel?err=Preencha+nome,+usuario+e+senha")
    
    users = load_users()
    if username in users:
        return redirect("/panel?err=Este+usuario+ja+existe")
    
    trusted_users = [u for u, info in users.items() if info.get("role") == "trusted"]
    if len(trusted_users) >= 3:
        return redirect("/panel?err=Limite+de+3+pessoas+de+confianca+atingido")
    
    users[username] = {
        "password": password,
        "role": "trusted",
        "name": name
    }
    save_users(users)
    return redirect("/panel?msg=Pessoa+de+confianca+cadastrada")

@app.route('/panel/delete_trusted', methods=['POST'])
def admin_delete_trusted():
    if session.get("role") != "admin":
        return redirect(url_for('admin_login'))
    
    username = (request.form.get("username") or "").strip()
    users = load_users()
    
    if username in users and users[username].get("role") == "trusted":
        users.pop(username)
        save_users(users)
        return redirect("/panel?msg=Pessoa+removida")
    
    return redirect("/panel?err=Nao+foi+possivel+remover")

@app.route('/logout_admin')
def logout_admin():
    session.clear()
    return redirect(url_for('admin_login'))

# ===== TRUSTED =====
@app.route('/trusted/login', methods=['GET', 'POST'])
def trusted_login():
    users = load_users()
    error = False
    if request.method == 'POST':
        u = (request.form.get("user") or "").strip().lower()
        p = (request.form.get("password") or "")
        info = users.get(u)
        if info and info.get("role") == "trusted" and info.get("password") == p:
            session.clear()
            session["role"] = "trusted"
            session["trusted"] = u
            return redirect(url_for('trusted_panel'))
        error = True
    return render_template('login_trusted.html', error=error)

@app.route('/trusted/panel')
def trusted_panel():
    if session.get("role") != "trusted":
        return redirect(url_for('trusted_login'))
    
    users = load_users()
    u = session.get("trusted")
    name = users.get(u, {}).get("name") or u
    
    return render_template('panel_trusted.html', display_name=name)

@app.route('/logout_trusted')
def logout_trusted():
    session.clear()
    return redirect(url_for('panic_button'))

@app.route('/trusted/recover', methods=['GET', 'POST'])
def trusted_recover():
    msg, err = "", ""
    if request.method == 'POST':
        u = (request.form.get("user") or "").strip().lower()
        new = (request.form.get("new_password") or "").strip()
        users = load_users()
        info = users.get(u)
        if not info or info.get("role") != "trusted":
            err = "Usuario nao encontrado."
        elif len(new) < 4:
            err = "Senha muito curta (minimo 4)."
        else:
            users[u]["password"] = new
            save_users(users)
            msg = "Senha redefinida. Faca login."
    return render_template('trusted_recover.html', msg=msg, err=err)

@app.route('/trusted/change_password', methods=['GET', 'POST'])
def trusted_change_password():
    if session.get("role") != "trusted":
        return redirect(url_for('trusted_login'))
    
    msg, err = "", ""
    if request.method == 'POST':
        old = request.form.get("old_password") or ""
        new = (request.form.get("new_password") or "").strip()
        users = load_users()
        u = session.get("trusted")
        info = users.get(u)
        if not info or info.get("password") != old:
            err = "Senha atual incorreta."
        elif len(new) < 4:
            err = "Nova senha muito curta (minimo 4)."
        else:
            users[u]["password"] = new
            save_users(users)
            msg = "Senha alterada com sucesso."
    return render_template('trusted_change_password.html', msg=msg, err=err)

if __name__ == '__main__':
    _ensure_files()
    print("=" * 60)
    print("🚀 AURORA MULHER SEGURA - SISTEMA INICIADO!")
    print("=" * 60)
    print("📱 Acesse:")
    print("   - http://localhost:5000/panic          (Botão de Pânico)")
    print("   - http://localhost:5000/panel/login    (Admin)")
    print("   - http://localhost:5000/trusted/login  (Pessoa de Confiança)")
    print("   - http://localhost:5000/relatorio/pdf  (Relatório PDF)")
    print("   - http://localhost:5000/health         (Diagnóstico)")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5000, debug=True)