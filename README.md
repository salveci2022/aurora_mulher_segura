# 🌸 Aurora Mulher Segura v2.0

Sistema de botão de pânico para segurança feminina com localização GPS em tempo real.

## 🚀 Funcionalidades

- ✅ Botão SOS com toque e segure (1 segundo)
- ✅ Envio de alerta com localização GPS em tempo real
- ✅ Sirene automática no painel da pessoa de confiança
- ✅ Mapa integrado com Google Maps
- ✅ Histórico de alertas
- ✅ Relatórios em PDF
- ✅ Diagnóstico do sistema
- ✅ PWA (Progressive Web App) para uso offline
- ✅ Modo de disfarce (calculadora)
- ✅ Plano de segurança pessoal

## 📱 Como Usar

### Localmente

```bash
# 1. Instalar dependências
pip install -r requirements.txt

# 2. Rodar o servidor
python app.py

# 3. Acessar no navegador
http://localhost:5000

# 4. Login Admin
Usuário: admin
Senha: admin123
🌸 Aurora Mulher Segura
# 🌸 Aurora Mulher Segura

> **Sistema de Emergência SOS com GPS em Tempo Real para Proteção Feminina**

[![Versão](https://img.shields.io/badge/versão-3.0-purple)](https://github.com/seu-usuario/aurora-mulher-segura)
[![Python](https://img.shields.io/badge/python-3.11-blue)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/flask-3.0-green)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![PWA](https://img.shields.io/badge/PWA-ready-orange)](https://web.dev/progressive-web-apps/)

---

## 📖 Sobre o Projeto

**Aurora Mulher Segura** é um sistema de botão de pânico desenvolvido para proteger mulheres em situações de risco. Através de um clique, a usuária pode enviar alertas de emergência com sua localização GPS em tempo real para pessoas de confiança previamente cadastradas.

### 🎯 Objetivo

Fornecer uma ferramenta tecnológica **acessível, rápida e eficiente** que possa:

- ✅ **Salvar vidas** em situações de violência doméstica, assédio ou perseguição
- ✅ **Notificar rapidamente** pessoas de confiança sobre emergências
- ✅ **Registrar evidências** com localização exata e timestamp
- ✅ **Funcionar offline** quando não há conexão com a internet
- ✅ **Ser acessível** em qualquer dispositivo móvel sem necessidade de instalação

### 👥 Público-Alvo

- Mulheres em situação de violência doméstica
- Estudantes universitárias
- Trabalhadoras noturnas
- Qualquer pessoa que deseje maior segurança pessoal

---

## 🚀 Funcionalidades

### 🔐 Segurança e Autenticação
- [x] Login com criptografia **bcrypt**
- [x] Rate limiting contra ataques de força bruta
- [x] Session management seguro
- [x] Proteção CSRF
- [x] LGPD compliant (dados mínimos coletados)

### 🚨 Sistema de Emergência
- [x] Botão SOS com toque e segure (1 segundo)
- [x] GPS de **alta precisão** (±3-10 metros)
- [x] Múltiplas leituras de GPS para maior exatidão
- [x] Envio automático de alertas
- [x] Modo offline com envio automático quando online
- [x] Histórico completo de alertas

### 🔔 Painel da Pessoa de Confiança
- [x] **Sirene automática** ao receber alerta
- [x] Notificações em tempo real
- [x] Localização exata no Google Maps
- [x] Auto-refresh a cada 5 segundos
- [x] Vibração e notificação push

### 📊 Painel Administrativo
- [x] Estatísticas de alertas (total, hoje, com GPS)
- [x] Gerenciamento de pessoas de confiança (máx. 3)
- [x] Relatórios em PDF para download
- [x] Histórico completo de todos os alertas
- [x] Health check do sistema

### 📱 Progressive Web App (PWA)
- [x] Instalável na tela inicial do celular
- [x] Funciona offline (Service Worker)
- [x] Ícones em 9 tamanhos diferentes
- [x] Manifest.json configurado
- [x] Cache de arquivos estáticos

### 🎨 Interface e UX
- [x] Design responsivo (mobile-first)
- [x] Tema escuro com cores suaves
- [x] Acessibilidade (ARIA labels, teclado)
- [x] Feedback tátil (vibração)
- [x] Calculadora como disfarce (saída rápida)

---

## 🛠️ Tecnologias Utilizadas

| Categoria | Tecnologia |
|-----------|-----------|
| **Backend** | Python 3.11, Flask 3.0 |
| **Frontend** | HTML5, CSS3, JavaScript (Vanilla) |
| **Banco de Dados** | JSON files (users.json, alerts.log, state.json) |
| **Segurança** | bcrypt, Flask-Limiter, CORS |
| **PWA** | Service Worker, Manifest.json |
| **PDF** | FPDF |
| **Deploy** | Render, Cloudflare |
| **Timezone** | pytz (America/Sao_Paulo) |

---

## 📁 Estrutura do Projeto
