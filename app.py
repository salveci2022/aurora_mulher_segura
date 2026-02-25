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
@app.after_request
def add_header(response):
    if 'Cache-Control' not in response.headers:
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '-1'
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

@app.route('/painel-da-mulher')
def painel_da_mulher():
    """Painel da mulher - versão melhorada"""
    return render_template('painel_da_mulher.html')

@app.route('/api/send_alert', methods=['POST'])
def api_send_alert():
    data = request.get_json(silent=True) or {}
    alert_id = _get_next_alert_id()
    
    # CORREÇÃO DA LOCALIZAÇÃO - ACEITA VÁRIOS FORMATOS
    location = None
    
    # Verificar vários formatos possíveis de localização
    if data.get("location"):
        # Se veio como objeto location
        location = data.get("location")
    elif data.get("lat") and data.get("lng"):
        # Se veio como lat/lng separados
        location = {
            "lat": float(data.get("lat")),
            "lng": float(data.get("lng")),
            "accuracy": data.get("accuracy")
        }
    elif data.get("latitude") and data.get("longitude"):
        # Se veio como latitude/longitude
        location = {
            "lat": float(data.get("latitude")),
            "lng": float(data.get("longitude")),
            "accuracy": data.get("accuracy")
        }
    
    # Garantir que tem lat/lng no objeto location
    if location:
        if 'lat' not in location and 'latitude' in location:
            location['lat'] = location['latitude']
        if 'lng' not in location and 'longitude' in location:
            location['lng'] = location['longitude']
        if 'lng' not in location and 'lon' in location:
            location['lng'] = location['lon']
    
    # Formata horário no fuso horário do Brasil
    now_br = datetime.now(BR_TZ)
    formatted_time = now_br.strftime("%Y-%m-%d %H:%M:%S")
    formatted_time_br = now_br.strftime("%d/%m/%Y %H:%M:%S")  # Formato brasileiro
    
    # Monta payload do alerta
    payload = {
        "id": alert_id,
        "ts": formatted_time,
        "ts_br": formatted_time_br,  # Formato brasileiro para exibição
        "name": (data.get("name") or "Usuária"),
        "situation": (data.get("situation") or "Emergência"),
        "message": (data.get("message") or ""),
        "location": location,
    }
    log_alert(payload)
    
    print(f"✅ Alerta #{alert_id} recebido - {payload['name']} - {payload['situation']}")
    if location:
        print(f"📍 Localização: {location.get('lat', 'N/A')}, {location.get('lng', 'N/A')}")
        if 'accuracy' in location:
            print(f"🎯 Precisão: ±{location['accuracy']}m")
    print(f"🕐 Horário: {formatted_time_br}")
    
    return jsonify({
        "ok": True,
        "id": alert_id,
        "message": "Alerta recebido com sucesso!",
        "location": location,
        "timestamp": formatted_time_br
    })

@app.route('/api/last_alert')
def api_last_alert():
    last = read_last_alert()
    return jsonify({"ok": True, "last": last})

@app.route('/health')
def health():
    now_br = datetime.now(BR_TZ)
    alerts = get_all_alerts()
    return jsonify({
        "ok": True,
        "server_time": now_br.isoformat(),
        "total_alertas": len(alerts),
        "users_json_ok": USERS_FILE.exists(),
        "alerts_log_ok": ALERTS_FILE.exists(),
        "state_file_ok": STATE_FILE.exists(),
    })

# ===== ROTA DE TESTE PDF =====
@app.route('/teste-pdf')
def teste_pdf():
    """Rota de teste para PDF"""
    try:
        from fpdf import FPDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt="TESTE PDF - AURORA MULHER SEGURA", ln=1, align="C")
        pdf.cell(200, 10, txt="Este é um teste de geração de PDF", ln=1, align="C")
        pdf.cell(200, 10, txt=f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", ln=1, align="C")
        
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        pdf.output(temp_file.name)
        
        return send_file(
            temp_file.name,
            as_attachment=True,
            download_name=f"teste_aurora_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            mimetype='application/pdf'
        )
    except Exception as e:
        print(f"Erro no teste PDF: {e}")
        import traceback
        traceback.print_exc()
        return f"Erro ao gerar PDF: {str(e)}"

# ===== RELATÓRIOS EM PDF CORRIGIDO (SEM ERRO DE CARACTERES) =====
@app.route('/relatorio/pdf')
def relatorio_pdf():
    """Gera relatório PDF com todos os alertas"""
    try:
        alerts = get_all_alerts()
        
        pdf = FPDF()
        pdf.add_page()
        
        # Configurar fonte para UTF-8 (usando Arial que suporta acentos)
        pdf.set_auto_page_break(auto=True, margin=15)
        
        # Título principal
        pdf.set_font("Arial", "B", 20)
        pdf.set_text_color(255, 79, 200)  # Rosa
        pdf.cell(190, 15, txt="AURORA MULHER SEGURA", ln=1, align="C")
        
        pdf.set_font("Arial", "B", 16)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(190, 10, txt="Relatorio de Alertas de Emergencia", ln=1, align="C")
        pdf.ln(10)
        
        # Data e hora
        now_br = datetime.now(BR_TZ)
        formatted_time = now_br.strftime("%d/%m/%Y as %H:%M:%S")
        pdf.set_font("Arial", "", 12)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(190, 8, txt=f"Gerado em: {formatted_time}", ln=1)
        pdf.cell(190, 8, txt=f"Total de Alertas: {len(alerts)}", ln=1)
        pdf.ln(10)
        
        # Estatísticas (sem caracteres especiais)
        with_location = sum(1 for a in alerts if a.get('location'))
        without_location = len(alerts) - with_location
        
        pdf.set_font("Arial", "B", 14)
        pdf.set_text_color(255, 79, 200)
        pdf.cell(190, 10, txt="ESTATISTICAS", ln=1)
        pdf.set_font("Arial", "", 12)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(190, 8, txt=f"* Alertas com localizacao: {with_location}", ln=1)
        pdf.cell(190, 8, txt=f"* Alertas sem localizacao: {without_location}", ln=1)
        pdf.ln(10)
        
        # Lista de alertas
        if alerts:
            pdf.set_font("Arial", "B", 14)
            pdf.set_text_color(255, 79, 200)
            pdf.cell(190, 10, txt="HISTORICO DE ALERTAS", ln=1)
            pdf.ln(5)
            
            # Ordenar do mais recente para o mais antigo
            alerts_ordenados = sorted(alerts, key=lambda x: x.get('id', 0), reverse=True)
            
            for alert in alerts_ordenados[:50]:  # Mostrar últimos 50
                pdf.set_font("Arial", "B", 11)
                pdf.set_text_color(0, 0, 0)
                
                # Usar formato brasileiro se disponível
                ts_display = alert.get('ts_br', alert.get('ts', 'N/A'))
                pdf.cell(190, 8, txt=f"ID {alert.get('id', 'N/A')} - {ts_display}", ln=1)
                
                pdf.set_font("Arial", "", 11)
                
                # Nome (truncar se muito longo)
                nome = alert.get('name', 'Nao informado')
                if len(nome) > 30:
                    nome = nome[:30] + "..."
                pdf.cell(190, 6, txt=f"   Nome: {nome}", ln=1)
                
                # Situação
                situacao = alert.get('situation', 'Emergencia')
                if len(situacao) > 40:
                    situacao = situacao[:40] + "..."
                pdf.cell(190, 6, txt=f"   Situacao: {situacao}", ln=1)
                
                # Mensagem (se existir)
                if alert.get('message'):
                    msg = alert.get('message', '')
                    if len(msg) > 50:
                        msg = msg[:50] + "..."
                    pdf.cell(190, 6, txt=f"   Mensagem: {msg}", ln=1)
                
                # Localização
                if alert.get('location'):
                    loc = alert.get('location')
                    lat = loc.get('lat', 'N/A')
                    lng = loc.get('lng', 'N/A')
                    acc = loc.get('accuracy', 'N/A')
                    
                    if isinstance(lat, float):
                        lat = f"{lat:.6f}"
                    if isinstance(lng, float):
                        lng = f"{lng:.6f}"
                    if acc != 'N/A' and isinstance(acc, (int, float)):
                        acc = f"{acc:.1f}m"
                    
                    pdf.cell(190, 6, txt=f"   Localizacao: {lat}, {lng} (+-{acc})", ln=1)
                else:
                    pdf.cell(190, 6, txt="   Localizacao: Nao compartilhada", ln=1)
                
                pdf.cell(190, 2, txt="", ln=1)  # Espaço
                pdf.ln(2)
        else:
            pdf.set_font("Arial", "I", 12)
            pdf.set_text_color(150, 150, 150)
            pdf.cell(190, 10, txt="Nenhum alerta registrado ate o momento.", ln=1, align="C")
        
        pdf.ln(10)
        
        # Rodapé
        pdf.set_y(-30)
        pdf.set_font("Arial", "I", 8)
        pdf.set_text_color(150, 150, 150)
        pdf.cell(190, 5, txt="Documento gerado automaticamente pelo sistema Aurora Mulher Segura", ln=1, align="C")
        pdf.cell(190, 5, txt="Este relatorio contem informacoes confidenciais de seguranca", ln=1, align="C")
        
        # Salvar arquivo
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

# ===== HISTÓRICO =====
@app.route('/historico')
def historico():
    """Página de histórico de alertas"""
    alerts = get_all_alerts()
    return render_template('historico.html', alerts=alerts)

# ===== TERMOS =====
@app.route('/termos')
def termos():
    return render_template('legal.html')

@app.route('/privacidade')
def privacidade():
    return render_template('legal.html')

@app.route('/lgpd')
def lgpd():
    return render_template('legal.html')

# ===== FAVICON =====
@app.route('/favicon.ico')
def favicon():
    return redirect(url_for('static', filename='favicon.ico'))

if __name__ == '__main__':
    _ensure_files()
    print("=" * 60)
    print("🚀 AURORA MULHER SEGURA - SISTEMA INICIADO!")
    print("=" * 60)
    print("📱 Acesse:")
    print("   - http://localhost:5000/                (Página inicial)")
    print("   - http://localhost:5000/panic           (Botão de Pânico)")
    print("   - http://localhost:5000/painel-da-mulher (Painel da Mulher)")
    print("   - http://localhost:5000/panel/login     (Admin)")
    print("   - http://localhost:5000/trusted/login   (Pessoa de Confiança)")
    print("   - http://localhost:5000/historico       (Histórico)")
    print("   - http://localhost:5000/relatorio/pdf   (Relatório PDF)")
    print("   - http://localhost:5000/teste-pdf       (Teste PDF)")
    print("   - http://localhost:5000/health          (Diagnóstico)")
    print("=" * 60)
    print(f"📁 Alertas salvos em: {ALERTS_FILE}")
    print(f"👥 Usuários salvos em: {USERS_FILE}")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5000, debug=True)