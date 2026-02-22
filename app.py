from flask import Flask, render_template, request, jsonify, send_file, make_response, redirect, url_for
from flask_cors import CORS
import logging
from datetime import datetime
import os
import json
from fpdf import FPDF
import tempfile

app = Flask(__name__, 
            static_folder='static',
            template_folder='templates')
CORS(app)

logging.basicConfig(level=logging.DEBUG)

# ========== DADOS SIMULADOS ==========
alertas_db = []
usuarios_db = []
contatos_confianca_db = []

# ========== PÁGINAS PRINCIPAIS ==========
@app.route('/')
def index():
    """Página inicial - Botão de Pânico"""
    return render_template('panic_button.html')

@app.route('/panic')
def panic():
    """Redireciona para página inicial"""
    return redirect(url_for('index'))

# ========== PESSOA DE CONFIANÇA ==========
@app.route('/trusted/login')
def trusted_login():
    """Página de login para pessoas de confiança"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Aurora - Pessoa de Confiança</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {
                font-family: Arial, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
            }
            .card {
                background: white;
                padding: 40px;
                border-radius: 20px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                width: 350px;
                text-align: center;
            }
            h1 { color: #333; margin-bottom: 30px; }
            input {
                width: 100%;
                padding: 12px;
                margin: 10px 0;
                border: 2px solid #e0e0e0;
                border-radius: 10px;
                font-size: 16px;
                box-sizing: border-box;
            }
            button {
                background: #667eea;
                color: white;
                border: none;
                padding: 12px 30px;
                border-radius: 10px;
                font-size: 16px;
                cursor: pointer;
                width: 100%;
                margin-top: 20px;
            }
            button:hover { background: #764ba2; }
            .link { color: #666; text-decoration: none; margin-top: 15px; display: block; }
            .link:hover { color: #667eea; }
        </style>
    </head>
    <body>
        <div class="card">
            <h1>👥 Pessoa de Confiança</h1>
            <p>Área para contatos de emergência</p>
            <input type="text" placeholder="Email" value="maria@email.com" disabled>
            <input type="password" placeholder="Senha" value="********" disabled>
            <button onclick="alert('Sistema em desenvolvimento. Em breve você poderá acessar.')">
                Entrar (Demo)
            </button>
            <a href="/" class="link">← Voltar ao início</a>
        </div>
    </body>
    </html>
    """

@app.route('/trusted/register')
def trusted_register():
    """Cadastro de pessoa de confiança"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Aurora - Cadastro</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {
                font-family: Arial, sans-serif;
                background: linear-gradient(135deg, #43cea2 0%, #185a9d 100%);
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                margin: 0;
                padding: 20px;
            }
            .card {
                background: white;
                padding: 40px;
                border-radius: 20px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                width: 400px;
            }
            h1 { color: #333; text-align: center; }
            input {
                width: 100%;
                padding: 12px;
                margin: 8px 0;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                box-sizing: border-box;
            }
            button {
                background: #43cea2;
                color: white;
                border: none;
                padding: 12px;
                border-radius: 8px;
                width: 100%;
                font-size: 16px;
                cursor: pointer;
                margin-top: 20px;
            }
            button:hover { background: #185a9d; }
        </style>
    </head>
    <body>
        <div class="card">
            <h1>📝 Cadastro</h1>
            <p>Cadastre-se como pessoa de confiança</p>
            <input placeholder="Nome completo" value="Maria Oliveira" disabled>
            <input placeholder="Email" value="maria@email.com" disabled>
            <input placeholder="Telefone" value="(11) 99999-9999" disabled>
            <input placeholder="Parentesco" value="Mãe" disabled>
            <button onclick="alert('Cadastro em desenvolvimento')">Cadastrar (Demo)</button>
            <p style="text-align:center; margin-top:15px"><a href="/trusted/login">Já tem cadastro?</a></p>
        </div>
    </body>
    </html>
    """

@app.route('/trusted/dashboard')
def trusted_dashboard():
    """Dashboard da pessoa de confiança"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Dashboard - Pessoa de Confiança</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {
                font-family: Arial, sans-serif;
                background: #f5f5f5;
                margin: 0;
                padding: 20px;
            }
            .container {
                max-width: 1000px;
                margin: 0 auto;
            }
            .header {
                background: white;
                padding: 20px;
                border-radius: 10px;
                margin-bottom: 20px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            .stats {
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 20px;
                margin-bottom: 20px;
            }
            .stat-card {
                background: white;
                padding: 20px;
                border-radius: 10px;
                text-align: center;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            .stat-value {
                font-size: 36px;
                font-weight: bold;
                color: #667eea;
            }
            .alert-card {
                background: white;
                padding: 20px;
                border-radius: 10px;
                margin-bottom: 10px;
                border-left: 4px solid #f44336;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>👥 Dashboard - Pessoa de Confiança</h1>
                <p>Bem-vinda, Maria!</p>
            </div>
            
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-value">3</div>
                    <div>Alertas recebidos</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">2</div>
                    <div>Pessoas vinculadas</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">98%</div>
                    <div>Tempo de resposta</div>
                </div>
            </div>
            
            <h2>Últimos alertas</h2>
            <div class="alert-card">
                <strong>⚠️ Alerta em 22/02/2026 16:30</strong><br>
                Maria Silva - Localização: Rua A, 123
            </div>
            <div class="alert-card">
                <strong>⚠️ Alerta em 22/02/2026 15:20</strong><br>
                Ana Costa - Localização: Av. B, 456
            </div>
            
            <p style="text-align:center; margin-top:20px">
                <a href="/">← Voltar</a>
            </p>
        </div>
    </body>
    </html>
    """

@app.route('/trusted/alerts')
def trusted_alerts():
    """Histórico de alertas para pessoa de confiança"""
    return redirect(url_for('trusted_dashboard'))

# ========== ADMINISTRAÇÃO ==========
@app.route('/panel/login')
def admin_login():
    """Login do administrador"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Admin - Aurora</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {
                font-family: Arial, sans-serif;
                background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
            }
            .card {
                background: white;
                padding: 40px;
                border-radius: 20px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                width: 350px;
            }
            h1 { color: #333; text-align: center; }
            input {
                width: 100%;
                padding: 12px;
                margin: 10px 0;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                box-sizing: border-box;
            }
            button {
                background: #f5576c;
                color: white;
                border: none;
                padding: 12px;
                border-radius: 8px;
                width: 100%;
                font-size: 16px;
                cursor: pointer;
            }
            button:hover { background: #f093fb; }
        </style>
    </head>
    <body>
        <div class="card">
            <h1>⚙️ Admin</h1>
            <p>Painel administrativo</p>
            <input type="text" placeholder="Usuário" value="admin" disabled>
            <input type="password" placeholder="Senha" value="********" disabled>
            <button onclick="window.location.href='/panel/dashboard'">Acessar Demo</button>
        </div>
    </body>
    </html>
    """

@app.route('/panel/dashboard')
def admin_dashboard():
    """Dashboard do administrador"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Dashboard Admin</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {
                font-family: Arial, sans-serif;
                background: #f5f5f5;
                margin: 0;
                padding: 20px;
            }
            .container { max-width: 1200px; margin: 0 auto; }
            .header {
                background: white;
                padding: 20px;
                border-radius: 10px;
                margin-bottom: 20px;
            }
            .grid {
                display: grid;
                grid-template-columns: repeat(4, 1fr);
                gap: 20px;
                margin-bottom: 20px;
            }
            .card {
                background: white;
                padding: 20px;
                border-radius: 10px;
                text-align: center;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            .number {
                font-size: 32px;
                font-weight: bold;
                color: #f5576c;
            }
            table {
                width: 100%;
                background: white;
                border-radius: 10px;
                padding: 20px;
            }
            th { text-align: left; padding: 10px; background: #f5f5f5; }
            td { padding: 10px; border-bottom: 1px solid #eee; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📊 Dashboard Administrativo</h1>
                <p>Bem-vindo, Administrador</p>
            </div>
            
            <div class="grid">
                <div class="card"><div class="number">127</div>Total Alertas</div>
                <div class="card"><div class="number">45</div>Usuários Ativos</div>
                <div class="card"><div class="number">89</div>Contatos</div>
                <div class="card"><div class="number">99.9%</div>Uptime</div>
            </div>
            
            <h2>Últimos Alertas</h2>
            <table>
                <tr><th>Data</th><th>Usuário</th><th>Situação</th><th>Status</th></tr>
                <tr><td>22/02 16:30</td><td>Maria S.</td><td>Violência física</td><td>✅ Atendido</td></tr>
                <tr><td>22/02 15:20</td><td>Ana C.</td><td>Ameaça</td><td>⏳ Em andamento</td></tr>
            </table>
            
            <p style="text-align:center; margin-top:20px"><a href="/">← Voltar</a></p>
        </div>
    </body>
    </html>
    """

@app.route('/panel/users')
def admin_users():
    """Gerenciamento de usuários"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Usuários - Admin</title>
        <style>
            body { font-family: Arial; padding: 20px; }
            table { width: 100%; border-collapse: collapse; }
            th, td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
        </style>
    </head>
    <body>
        <h1>👥 Usuários Cadastrados</h1>
        <table>
            <tr><th>ID</th><th>Nome</th><th>Email</th><th>Status</th></tr>
            <tr><td>1</td><td>Maria Silva</td><td>maria@email.com</td><td>Ativo</td></tr>
            <tr><td>2</td><td>Ana Costa</td><td>ana@email.com</td><td>Ativo</td></tr>
        </table>
        <p><a href="/panel/dashboard">← Voltar</a></p>
    </body>
    </html>
    """

@app.route('/panel/settings')
def admin_settings():
    """Configurações do sistema"""
    return "<h1>⚙️ Configurações</h1><p>Sistema em desenvolvimento</p><a href='/panel/dashboard'>Voltar</a>"

# ========== DIAGNÓSTICO ==========
@app.route('/health')
def health():
    """Status do sistema"""
    return jsonify({
        "status": "online",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "database": "conectado",
        "api": "funcionando",
        "uptime": "2d 4h 30m"
    })

@app.route('/metrics')
def metrics():
    """Métricas do sistema"""
    return jsonify({
        "alertas_hoje": 5,
        "alertas_mes": 127,
        "usuarios_ativos": 45,
        "tempo_medio_resposta": "2.5s",
        "memoria_uso": "45%",
        "cpu_uso": "23%"
    })

@app.route('/logs')
def logs():
    """Logs do sistema"""
    return jsonify({
        "logs": [
            {"timestamp": "2026-02-22 16:30", "level": "INFO", "message": "Alerta recebido"},
            {"timestamp": "2026-02-22 15:20", "level": "INFO", "message": "Usuário logado"},
            {"timestamp": "2026-02-22 14:10", "level": "WARNING", "message": "Tentativa de acesso"}
        ]
    })

# ========== HISTÓRICO ==========
@app.route('/historico')
def historico():
    """Página de histórico"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Histórico de Alertas</title>
        <meta charset="utf-8">
        <style>
            body {
                font-family: Arial, sans-serif;
                background: #f5f5f5;
                padding: 20px;
            }
            .container {
                max-width: 800px;
                margin: 0 auto;
                background: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            h1 { color: #333; }
            .alert-item {
                padding: 15px;
                border-left: 4px solid #f44336;
                background: #f9f9f9;
                margin-bottom: 10px;
                border-radius: 0 5px 5px 0;
            }
            .date { color: #666; font-size: 14px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📋 Histórico de Alertas</h1>
            
            <div class="alert-item">
                <strong>22/02/2026 16:30</strong> - Violência física<br>
                Maria Silva - Rua A, 123
            </div>
            <div class="alert-item">
                <strong>22/02/2026 15:20</strong> - Ameaça<br>
                Ana Costa - Av. B, 456
            </div>
            <div class="alert-item">
                <strong>22/02/2026 14:10</strong> - Perseguição<br>
                Carla Souza - Rua C, 789
            </div>
            
            <p style="text-align:center; margin-top:20px">
                <a href="/">← Voltar</a> | 
                <a href="/relatorio/pdf/geral">📄 Gerar PDF</a>
            </p>
        </div>
    </body>
    </html>
    """

@app.route('/historico/hoje')
def historico_hoje():
    """Alertas de hoje"""
    return jsonify({
        "data": "22/02/2026",
        "total": 5,
        "alertas": [
            {"hora": "16:30", "usuario": "Maria", "situacao": "Violência física"},
            {"hora": "15:20", "usuario": "Ana", "situacao": "Ameaça"}
        ]
    })

@app.route('/historico/estatisticas')
def historico_estatisticas():
    """Estatísticas do histórico"""
    return jsonify({
        "total_alertas": 127,
        "por_tipo": {
            "Violência física": 45,
            "Ameaça": 38,
            "Perseguição": 44
        },
        "media_diaria": 4.2
    })

# ========== RELATÓRIOS PDF ==========
@app.route('/relatorio/pdf/geral')
def relatorio_pdf_geral():
    """Gera relatório PDF geral"""
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        
        # Título
        pdf.cell(200, 10, txt="Relatório Geral - Aurora Mulher Segura", ln=1, align="C")
        pdf.cell(200, 10, txt=f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=1, align="C")
        pdf.ln(10)
        
        # Conteúdo
        pdf.cell(200, 10, txt="Total de Alertas: 127", ln=1)
        pdf.cell(200, 10, txt="Usuários Ativos: 45", ln=1)
        pdf.cell(200, 10, txt="Contatos de Confiança: 89", ln=1)
        
        # Salva arquivo temporário
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        pdf.output(temp_file.name)
        
        return send_file(
            temp_file.name,
            as_attachment=True,
            download_name=f"relatorio_geral_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
            mimetype='application/pdf'
        )
    except Exception as e:
        return jsonify({"erro": str(e)})

@app.route('/relatorio/pdf/mes')
def relatorio_pdf_mes():
    """Relatório mensal"""
    return jsonify({"message": "Relatório mensal sendo gerado..."})

@app.route('/relatorio/exportar')
def relatorio_exportar():
    """Exporta dados"""
    return jsonify({
        "dados": alertas_db,
        "formato": "json",
        "timestamp": datetime.now().isoformat()
    })

# ========== PÁGINAS LEGAIS ==========
@app.route('/termos')
def termos():
    return "<h1>📜 Termos de Uso</h1><p>Versão 1.0 - 2026</p><a href='/'>Voltar</a>"

@app.route('/privacidade')
def privacidade():
    return "<h1>🔒 Política de Privacidade</h1><p>Seus dados estão seguros</p><a href='/'>Voltar</a>"

@app.route('/lgpd')
def lgpd():
    return "<h1>📋 LGPD</h1><p>Conformidade com a Lei Geral de Proteção de Dados</p><a href='/'>Voltar</a>"

@app.route('/ajuda')
def ajuda():
    return "<h1>❓ Central de Ajuda</h1><p>Como usar o sistema</p><a href='/'>Voltar</a>"

@app.route('/faq')
def faq():
    return "<h1>❓ Perguntas Frequentes</h1><p>1. Como enviar alerta?<br>2. Quem recebe?</p><a href='/'>Voltar</a>"

@app.route('/contato')
def contato():
    return "<h1>📧 Contato</h1><p>Email: suporte@aurora.com</p><p>Tel: 180</p><a href='/'>Voltar</a>"

# ========== EMERGÊNCIA ==========
@app.route('/sos')
def sos_direto():
    """Página SOS direta"""
    return redirect(url_for('index'))

@app.route('/telefones-uteis')
def telefones_uteis():
    return """
    <h1>📞 Telefones Úteis</h1>
    <ul>
        <li>Polícia Militar: 190</li>
        <li>Central da Mulher: 180</li>
        <li>Samu: 192</li>
    </ul>
    <a href='/'>Voltar</a>
    """

# ========== API ==========
@app.route('/api/send_alert', methods=['POST'])
def api_send_alert():
    """Recebe alertas do botão SOS"""
    try:
        data = request.json
        alertas_db.append({
            "id": len(alertas_db) + 1,
            "data": data,
            "timestamp": datetime.now().isoformat()
        })
        return jsonify({"ok": True, "message": "Alerta recebido com sucesso!"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route('/api/status')
def api_status():
    """Status da API"""
    return jsonify({"status": "online", "timestamp": datetime.now().isoformat()})

@app.route('/api/historico')
def api_historico():
    """Retorna histórico de alertas"""
    return jsonify({"alertas": alertas_db})

@app.route('/api/usuarios')
def api_usuarios():
    """Retorna lista de usuários"""
    return jsonify({"usuarios": usuarios_db})

# ========== TRATAMENTO DE ERROS ==========
@app.errorhandler(404)
def not_found(error):
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Página não encontrada</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                text-align: center;
                padding: 50px;
                height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
            }
            .container {
                background: rgba(255,255,255,0.1);
                padding: 40px;
                border-radius: 20px;
                backdrop-filter: blur(10px);
            }
            h1 { font-size: 48px; margin-bottom: 20px; }
            a {
                color: white;
                text-decoration: none;
                padding: 10px 20px;
                border: 2px solid white;
                border-radius: 5px;
                display: inline-block;
                margin-top: 20px;
            }
            a:hover { background: white; color: #667eea; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>404</h1>
            <h2>Página não encontrada</h2>
            <p>A página que você está procurando não existe ou foi movida.</p>
            <a href="/">Voltar para início</a>
        </div>
    </body>
    </html>
    """, 404

# ========== INSTALAÇÃO DE DEPENDÊNCIAS ==========
# Para gerar PDF, instale: pip install fpdf

if __name__ == '__main__':
    print("="*50)
    print("🚀 Aurora Mulher Segura - Sistema Iniciado!")
    print("📱 Acesse: http://localhost:5000")
    print("📝 Links disponíveis:")
    print("   - http://localhost:5000/")
    print("   - http://localhost:5000/trusted/login")
    print("   - http://localhost:5000/panel/login")
    print("   - http://localhost:5000/historico")
    print("   - http://localhost:5000/relatorio/pdf/geral")
    print("="*50)
    
    # Instala dependências se necessário
    try:
        from fpdf import FPDF
    except ImportError:
        print("⚠️ Instalando fpdf para gerar PDFs...")
        os.system("pip install fpdf")
    
    app.run(debug=True, port=5000)