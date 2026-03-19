# 🌸 Aurora Mulher Segura

> Sistema de emergência SOS para proteção de mulheres em situação de risco, com botão de pânico, GPS em tempo real, chat com IA de apoio e painel para pessoas de confiança.

---

## 📱 Funcionalidades

- 🚨 **Botão de Pânico SOS** — segure por 1 segundo para disparar alerta imediato
- 📍 **GPS em tempo real** — envia localização exata para pessoas de confiança
- 🔔 **Painel da Pessoa de Confiança** — recebe alertas com mapa Leaflet e sirene automática
- 🤖 **Aurora IA** — chat de apoio sobre violência doméstica, direitos e orientações
- ⚙️ **Painel Admin** — gerencia pessoas de confiança e histórico de alertas
- 📄 **Relatório PDF** — exporta histórico completo de alertas
- 📋 **Histórico de Alertas** — com filtros e links diretos para o Google Maps
- 📜 **Termo de Responsabilidade** — obrigatório antes de usar o sistema (LGPD)
- ⚡ **Saída Rápida** — disfarça o app como calculadora em situação de perigo
- 📱 **PWA** — instala como aplicativo na tela inicial do celular
- 🔐 **Senhas criptografadas** — bcrypt via Werkzeug

---

## 🗂️ Estrutura do Projeto

```
aurora/
├── app.py                        ← Servidor Flask principal
├── requirements.txt              ← Dependências Python
├── render.yaml                   ← Configuração de deploy (Render.com)
├── README.md                     ← Este arquivo
│
├── templates/                    ← Páginas HTML (20 arquivos)
│   ├── index.html                ← Página inicial
│   ├── panic_button.html         ← Botão de pânico SOS
│   ├── aurora_ia.html            ← Chat com Aurora IA
│   ├── panel_admin.html          ← Painel administrativo
│   ├── panel_trusted.html        ← Painel pessoa de confiança
│   ├── login_admin.html          ← Login admin
│   ├── login_trusted.html        ← Login pessoa de confiança
│   ├── historico.html            ← Histórico de alertas
│   ├── ajuda.html                ← Números de emergência
│   ├── plano_seguranca.html      ← Plano de segurança pessoal
│   ├── termo_responsabilidade.html ← Termo de uso (LGPD)
│   ├── saida_rapida.html         ← Saída rápida (calculadora)
│   ├── offline.html              ← Página sem internet
│   ├── legal.html                ← Termos e privacidade
│   ├── trusted_change_password.html
│   ├── trusted_recover.html
│   ├── pagamentos.html
│   ├── recibo_entrega.html
│   ├── central_aurora.html
│   └── anual_aurora.html
│
└── static/
    ├── css/style.css             ← Estilos globais Aurora
    ├── js/panic.js               ← Lógica do botão SOS + GPS
    ├── js/sw.js                  ← Service Worker (PWA offline)
    ├── audio/sirene.mp3          ← Sirene de alerta
    ├── manifest.json             ← PWA manifest
    └── img/
        ├── favicon.png
        ├── icon-192.png
        └── icon-512.png
```

---

## ⚙️ Instalação Local

### Pré-requisitos
- Python 3.10 ou superior
- pip

### Passo a passo

```bash
# 1. Clone o repositório
git clone https://github.com/seu-usuario/aurora.git
cd aurora

# 2. Crie o ambiente virtual
python -m venv venv

# 3. Ative o ambiente virtual
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 4. Instale as dependências
pip install -r requirements.txt

# 5. Configure as variáveis de ambiente (opcional para teste local)
set ANTHROPIC_API_KEY=sk-ant-XXXXXXXXXXXXXXXX   # Windows
export ANTHROPIC_API_KEY=sk-ant-XXXXXXXXXXXXXXXX # Linux/Mac

# 6. Inicie o servidor
python app.py
```

### Acesse no navegador
```
http://localhost:5000
```

---

## 🔐 Credenciais padrão

| Acesso | Usuário | Senha |
|--------|---------|-------|
| Admin | `admin` | `admin123` |

> ⚠️ **Troque a senha do admin imediatamente após o primeiro acesso!**

Para criar uma **Pessoa de Confiança**:
1. Acesse `/panel/login`
2. Entre com admin / admin123
3. Preencha o formulário "Cadastrar Pessoa de Confiança"

---

## 🚀 Deploy no Render.com

### Passo a passo

1. Faça push do projeto para o GitHub
2. Acesse [render.com](https://render.com) → **New** → **Web Service**
3. Conecte seu repositório GitHub
4. O `render.yaml` configura tudo automaticamente
5. Adicione as variáveis de ambiente:

| Variável | Valor |
|----------|-------|
| `SECRET_KEY` | Texto longo e aleatório (ex: `aurora-prod-2026-xYz...`) |
| `ANTHROPIC_API_KEY` | Sua chave da API Anthropic |

6. Clique em **Deploy** e aguarde 2-3 minutos

### URLs após o deploy

| Página | URL |
|--------|-----|
| Página inicial | `https://seusite.onrender.com/` |
| Botão SOS | `https://seusite.onrender.com/panic` |
| Aurora IA | `https://seusite.onrender.com/aurora-ia` |
| Painel Admin | `https://seusite.onrender.com/panel/login` |
| Pessoa de Confiança | `https://seusite.onrender.com/trusted/login` |

---

## 🤖 Aurora IA

O chat de apoio usa a API da Anthropic (Claude). Para ativar:

1. Crie uma conta em [console.anthropic.com](https://console.anthropic.com)
2. Gere uma API Key
3. Adicione como variável de ambiente: `ANTHROPIC_API_KEY`

A IA é especializada em:
- Lei Maria da Penha (Lei 11.340/2006)
- Medidas protetivas de urgência
- Canais de ajuda: 180, 190, DEAM, CRAM, CRAS
- Reconhecimento de relacionamento abusivo
- Ciclo da violência doméstica
- Como sair de uma situação de perigo com segurança

---

## 📞 Números de Emergência

| Número | Serviço |
|--------|---------|
| **180** | Central da Mulher — 24h, gratuito |
| **190** | Polícia Militar |
| **192** | SAMU |
| **193** | Bombeiros |
| **197** | Polícia Civil |
| **100** | Direitos Humanos |

---

## 🔒 Privacidade e LGPD

- Senhas armazenadas com hash bcrypt (Werkzeug)
- Localização GPS coletada **somente com consentimento explícito**
- Conversa com a Aurora IA **não é gravada**
- Termo de Responsabilidade obrigatório (LGPD — Lei 13.709/2018)
- Dados não compartilhados com terceiros

---

## 🛠️ Tecnologias

| Tecnologia | Uso |
|-----------|-----|
| Python + Flask | Backend e servidor web |
| Jinja2 | Templates HTML |
| Werkzeug | Segurança e senhas |
| fpdf2 | Geração de PDF |
| Leaflet.js | Mapas interativos |
| Claude API (Anthropic) | Aurora IA |
| Service Worker | PWA e modo offline |

---

## 📄 Licença

Este projeto é de uso comercial. Todos os direitos reservados.

© 2026 Aurora Mulher Segura

---

<p align="center">
🌸 <strong>Aurora Mulher Segura</strong> — Protegendo vidas desde 2024
</p>
