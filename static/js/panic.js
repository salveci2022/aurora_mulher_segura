/* ===============================
   AURORA MULHER SEGURA - panic.js
   ULTRA SIMPLIFICADO - SEM TRAVAS
================================ */

(function() {
  console.log("🔵 INICIANDO SCRIPT...");
  
  // Executar quando o DOM estiver pronto
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', iniciar);
  } else {
    iniciar();
  }
  
  function iniciar() {
    console.log("🟢 DOM pronto, configurando...");
    
    // 1. CRIAR BOTÃO DE TESTE DIRETO NO CONSOLE
    window.testarImediato = function() {
      console.log("✅ Função de teste executada!");
      alert("✅ JavaScript está funcionando!");
      return "OK";
    };
    
    // 2. TENTAR ENCONTRAR O BOTÃO
    const sosBtn = document.getElementById("sosBtn");
    console.log("Botão SOS encontrado?", sosBtn ? "SIM" : "NÃO", sosBtn);
    
    if (!sosBtn) {
      console.error("❌ BOTÃO NÃO ENCONTRADO! Verifique se o ID 'sosBtn' existe no HTML");
      criarBotaoEmergencia();
      return;
    }
    
    // 3. DESABILITAR COMPLETAMENTE O COMPORTAMENTO ANTIGO
    // Remover todos os event listeners clonando e substituindo
    const novoBotao = sosBtn.cloneNode(true);
    sosBtn.parentNode.replaceChild(novoBotao, sosBtn);
    
    // 4. CONFIGURAR BOTÃO NOVO DE FORMA SIMPLES
    const botao = document.getElementById("sosBtn");
    
    // Estilo visual para debug
    botao.style.backgroundColor = "#4CAF50";
    botao.style.color = "white";
    botao.style.padding = "15px";
    botao.style.fontSize = "20px";
    botao.style.border = "2px solid red"; // Borda vermelha para debug
    
    // Função simples de clique
    botao.onclick = function(evento) {
      evento.preventDefault();
      evento.stopPropagation();
      
      console.log("🖱️ CLIQUE DETECTADO NO BOTÃO!");
      console.log("Timestamp:", new Date().toISOString());
      
      // Mudar cor para feedback visual
      this.style.backgroundColor = "#ff4444";
      
      // Coletar dados básicos
      const nome = document.getElementById("name")?.value || "Não preenchido";
      const mensagem = document.getElementById("message")?.value || "";
      const compartilharLocal = document.getElementById("shareLoc")?.checked || false;
      
      // Mostrar dados no console
      console.log("📋 Dados do formulário:", {
        nome: nome,
        mensagem: mensagem,
        compartilharLocal: compartilharLocal,
        situacao: obterSituacaoSelecionada()
      });
      
      // Enviar alerta de forma SIMPLES
      enviarAlertaSimples();
    };
    
    // 5. CONFIGURAR CHIPS DE FORMA SIMPLES
    configurarChipsSimples();
    
    // 6. FUNÇÃO PARA OBTER SITUAÇÃO SELECIONADA
    function obterSituacaoSelecionada() {
      const chipAtivo = document.querySelector(".chip.active");
      return chipAtivo ? chipAtivo.innerText.trim() : "Nenhuma situação selecionada";
    }
    
    // 7. FUNÇÃO DE ENVIO SIMPLES
    async function enviarAlertaSimples() {
      console.log("📤 Iniciando envio do alerta...");
      
      const botao = document.getElementById("sosBtn");
      const textoOriginal = botao.innerText;
      
      try {
        botao.disabled = true;
        botao.innerText = "⏳ ENVIANDO...";
        
        // Preparar payload
        const payload = {
          name: document.getElementById("name")?.value || "",
          situation: obterSituacaoSelecionada(),
          message: document.getElementById("message")?.value || "",
          lat: null,
          lng: null,
          timestamp: new Date().toISOString(),
          test_mode: true // Indicar que é um teste
        };
        
        console.log("📦 Payload preparado:", payload);
        
        // TENTATIVA 1: Enviar para o servidor com timeout
        console.log("📡 Tentando enviar para /api/send_alert...");
        
        // Criar promise com timeout
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 5000); // 5 segundos
        
        try {
          const resposta = await fetch("/api/send_alert", {
            method: "POST",
            headers: { 
              "Content-Type": "application/json",
              "Accept": "application/json"
            },
            body: JSON.stringify(payload),
            signal: controller.signal
          });
          
          clearTimeout(timeoutId);
          
          console.log("📥 Resposta recebida! Status:", resposta.status);
          
          let dadosResposta;
          try {
            dadosResposta = await resposta.json();
            console.log("📥 Dados da resposta:", dadosResposta);
          } catch (e) {
            console.log("Resposta não é JSON válido");
          }
          
          if (resposta.ok) {
            alert("✅ Alerta enviado com sucesso!");
          } else {
            alert(`❌ Erro no servidor: ${resposta.status}`);
          }
          
        } catch (erroFetch) {
          clearTimeout(timeoutId);
          
          console.error("❌ Erro no fetch:", erroFetch);
          
          if (erroFetch.name === 'AbortError') {
            alert("❌ Tempo limite excedido. O servidor não respondeu.");
          } else {
            alert(`❌ Erro de conexão: ${erroFetch.message}`);
          }
        }
        
      } catch (erro) {
        console.error("❌ Erro geral:", erro);
        alert("❌ Erro inesperado. Verifique o console (F12)");
      } finally {
        // Restaurar botão
        botao.disabled = false;
        botao.innerText = textoOriginal;
        botao.style.backgroundColor = "#4CAF50";
      }
    }
    
    console.log("✅ Configuração básica concluída!");
  }
  
  function configurarChipsSimples() {
    const chips = document.querySelectorAll(".chip");
    console.log(`Encontrados ${chips.length} chips`);
    
    chips.forEach((chip, index) => {
      chip.onclick = function() {
        console.log(`Chip ${index} clicado:`, this.innerText);
        
        // Remover classe active de todos
        chips.forEach(c => c.classList.remove("active"));
        
        // Adicionar classe active neste
        this.classList.add("active");
        
        console.log("Situação selecionada:", this.innerText.trim());
      };
    });
  }
  
  function criarBotaoEmergencia() {
    console.log("🆘 CRIANDO BOTÃO DE EMERGÊNCIA...");
    
    const div = document.createElement('div');
    div.style.cssText = `
      position: fixed;
      bottom: 20px;
      left: 20px;
      right: 20px;
      z-index: 9999;
    `;
    
    const botao = document.createElement('button');
    botao.innerText = "🚨 BOTÃO SOS DE EMERGÊNCIA 🚨";
    botao.style.cssText = `
      width: 100%;
      padding: 30px;
      background-color: #ff4444;
      color: white;
      font-size: 24px;
      font-weight: bold;
      border: 5px solid yellow;
      border-radius: 20px;
      cursor: pointer;
      animation: piscar 1s infinite;
    `;
    
    // Adicionar animação
    const style = document.createElement('style');
    style.textContent = `
      @keyframes piscar {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
      }
    `;
    document.head.appendChild(style);
    
    botao.onclick = function() {
      alert("🚨 BOTÃO DE EMERGÊNCIA FUNCIONANDO!");
      console.log("Botão de emergência clicado!");
    };
    
    div.appendChild(botao);
    document.body.appendChild(div);
    
    console.log("✅ Botão de emergência criado!");
  }
  
  // Executar teste automático
  setTimeout(() => {
    console.log("⏰ Teste automático: JavaScript ainda está funcionando!");
  }, 2000);
  
})();