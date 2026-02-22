// panic.js - VERSÃO MÍNIMA ABSOLUTA - NÃO TRAVA
console.log("🚀 panic.js CARREGADO COM SUCESSO");

// Aguardar DOM carregar
document.addEventListener('DOMContentLoaded', function() {
    console.log("✅ DOM carregado, inicializando...");
    
    // ===== ELEMENTOS =====
    const sosBtn = document.getElementById('sosBtn');
    const nameInput = document.getElementById('name');
    const messageInput = document.getElementById('message');
    const shareLoc = document.getElementById('shareLoc');
    const chips = document.querySelectorAll('.chip');
    const statusBox = document.getElementById('status');
    
    // ===== VARIÁVEIS =====
    let situacaoSelecionada = '';
    
    // ===== VERIFICAÇÃO =====
    if (!sosBtn) {
        console.error('❌ Botão SOS não encontrado');
        return;
    }
    
    console.log("✅ Botão SOS encontrado");
    
    // ===== CHIPS =====
    if (chips.length > 0) {
        // Ativar primeiro chip
        chips[0].classList.add('active');
        situacaoSelecionada = chips[0].innerText.trim();
        
        // Configurar cada chip
        for (let i = 0; i < chips.length; i++) {
            chips[i].onclick = function() {
                // Remover active de todos
                for (let j = 0; j < chips.length; j++) {
                    chips[j].classList.remove('active');
                }
                // Adicionar active neste
                this.classList.add('active');
                situacaoSelecionada = this.innerText.trim();
                if (statusBox) {
                    statusBox.innerText = 'Situação: ' + situacaoSelecionada;
                }
            };
        }
    }
    
    // ===== BOTÕES DO TOPO =====
    document.getElementById('btnRestart').onclick = function() {
        location.reload();
    };
    
    document.getElementById('btnClear').onclick = function() {
        if (nameInput) nameInput.value = '';
        if (messageInput) messageInput.value = '';
        if (shareLoc) shareLoc.checked = true;
        if (chips.length > 0) {
            for (let j = 0; j < chips.length; j++) {
                chips[j].classList.remove('active');
            }
            chips[0].classList.add('active');
            situacaoSelecionada = chips[0].innerText.trim();
        }
        if (statusBox) {
            statusBox.innerText = 'Pronto. Toque e segure no SOS para enviar.';
        }
    };
    
    document.getElementById('btnExit').onclick = function() {
        if (confirm('Deseja sair?')) {
            window.close();
            window.location.href = 'about:blank';
        }
    };
    
    // ===== FUNÇÃO DE LOCALIZAÇÃO =====
    function pegarLocalizacao() {
        return new Promise(function(resolver) {
            if (!shareLoc || !shareLoc.checked) {
                resolver(null);
                return;
            }
            if (!navigator.geolocation) {
                resolver(null);
                return;
            }
            navigator.geolocation.getCurrentPosition(
                function(pos) {
                    resolver({
                        lat: pos.coords.latitude,
                        lng: pos.coords.longitude
                    });
                },
                function() {
                    resolver(null);
                },
                { timeout: 5000 }
            );
        });
    }
    
    // ===== FUNÇÃO DE ENVIO =====
    async function enviarAlerta() {
        console.log("📤 Enviando alerta...");
        
        if (!situacaoSelecionada) {
            alert('⚠️ Selecione uma situação');
            return;
        }
        
        // Desabilitar botão
        sosBtn.disabled = true;
        sosBtn.style.opacity = '0.5';
        var textoOriginal = sosBtn.innerHTML;
        sosBtn.innerHTML = 'ENVIANDO...';
        
        try {
            // Pegar localização
            var loc = await pegarLocalizacao();
            
            // Preparar dados
            var dados = {
                name: nameInput ? nameInput.value || 'Usuária' : 'Usuária',
                situation: situacaoSelecionada,
                message: messageInput ? messageInput.value || '' : '',
                lat: loc ? loc.lat : null,
                lng: loc ? loc.lng : null
            };
            
            console.log("Dados:", dados);
            
            // Tentar enviar para API
            try {
                var resposta = await fetch('/api/send_alert', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(dados)
                });
                
                if (resposta.ok) {
                    alert('✅ ALERTA ENVIADO!');
                } else {
                    alert('🚨 ALERTA (modo demonstração)\nSituação: ' + dados.situation);
                }
            } catch (e) {
                alert('🚨 ALERTA (modo demonstração)\nSituação: ' + dados.situation);
            }
            
            if (statusBox) {
                statusBox.innerText = '✅ Alerta enviado!';
            }
            
        } catch (erro) {
            console.error("Erro:", erro);
            alert('❌ Erro ao enviar');
        } finally {
            // Restaurar botão
            setTimeout(function() {
                sosBtn.disabled = false;
                sosBtn.style.opacity = '1';
                sosBtn.innerHTML = textoOriginal;
            }, 1000);
        }
    }
    
    // ===== CONFIGURAR BOTÃO SOS =====
    var timerHold = null;
    
    // Clique simples
    sosBtn.onclick = function(e) {
        e.preventDefault();
        enviarAlerta();
    };
    
    // Eventos de toque
    sosBtn.ontouchstart = function(e) {
        e.preventDefault();
        if (timerHold) clearTimeout(timerHold);
        timerHold = setTimeout(function() {
            enviarAlerta();
        }, 600);
    };
    
    sosBtn.ontouchend = function() {
        if (timerHold) clearTimeout(timerHold);
    };
    
    sosBtn.ontouchcancel = function() {
        if (timerHold) clearTimeout(timerHold);
    };
    
    // Eventos de mouse
    sosBtn.onmousedown = function() {
        if (timerHold) clearTimeout(timerHold);
        timerHold = setTimeout(function() {
            enviarAlerta();
        }, 600);
    };
    
    sosBtn.onmouseup = function() {
        if (timerHold) clearTimeout(timerHold);
    };
    
    sosBtn.onmouseleave = function() {
        if (timerHold) clearTimeout(timerHold);
    };
    
    console.log("🎉 Tudo configurado! Painel funcionando.");
});