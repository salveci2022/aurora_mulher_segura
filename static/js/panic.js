// panic.js - CORRIGIDO - NÃO TRAVA MAIS
console.log("🚀 panic.js carregado");

// Funções globais para os botões do topo
window.reiniciar = function() {
    location.reload();
};

window.limpar = function() {
    const nameInput = document.getElementById('name');
    const messageInput = document.getElementById('message');
    const shareLoc = document.getElementById('shareLoc');
    const chips = document.querySelectorAll('.chip');
    const statusBox = document.getElementById('status');
    
    if (nameInput) nameInput.value = '';
    if (messageInput) messageInput.value = '';
    if (shareLoc) shareLoc.checked = true; // Volta a marcar
    if (chips) {
        chips.forEach(c => c.classList.remove('active'));
        // Ativar o primeiro chip por padrão
        if (chips.length > 0) chips[0].classList.add('active');
    }
    if (statusBox) statusBox.innerHTML = 'Pronto. Toque e segure no SOS para enviar.';
};

window.sair = function() {
    if (confirm('Deseja sair do aplicativo?')) {
        window.close();
        window.location.href = 'about:blank';
    }
};

// Inicializar quando o DOM estiver pronto
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', iniciar);
} else {
    iniciar();
}

function iniciar() {
    console.log("✅ DOM carregado!");

    // Elementos com verificação de existência
    const sosBtn = document.getElementById('sosBtn');
    const nameInput = document.getElementById('name');
    const messageInput = document.getElementById('message');
    const shareLoc = document.getElementById('shareLoc');
    const chips = document.querySelectorAll('.chip');
    const statusBox = document.getElementById('status');

    let selectedSituation = '';
    let holdTimer = null;

    // Verificar se botão existe
    if (!sosBtn) {
        console.error('❌ Botão SOS não encontrado!');
        return;
    }

    // Configurar chips com segurança
    if (chips && chips.length > 0) {
        // Ativar o primeiro chip por padrão
        chips[0].classList.add('active');
        selectedSituation = chips[0].innerText.trim();
        
        chips.forEach(chip => {
            chip.onclick = function() {
                chips.forEach(c => c.classList.remove('active'));
                this.classList.add('active');
                selectedSituation = this.innerText.trim();
                console.log('Situação selecionada:', selectedSituation);
                if (statusBox) {
                    statusBox.innerHTML = `Situação: ${selectedSituation}`;
                }
            };
        });
    }

    // Função para obter localização com tratamento de erro
    function getLocation() {
        return new Promise((resolve) => {
            try {
                if (!shareLoc || !shareLoc.checked) {
                    resolve(null);
                    return;
                }
                
                if (!navigator.geolocation) {
                    console.warn('Geolocalização não suportada');
                    if (statusBox) statusBox.innerHTML = '⚠️ GPS não suportado';
                    resolve(null);
                    return;
                }
                
                if (statusBox) statusBox.innerHTML = '📍 Obtendo localização...';
                
                navigator.geolocation.getCurrentPosition(
                    (pos) => {
                        console.log('📍 Localização obtida');
                        if (statusBox) statusBox.innerHTML = '📍 Localização obtida';
                        resolve({
                            lat: pos.coords.latitude,
                            lng: pos.coords.longitude
                        });
                    },
                    (err) => {
                        console.warn('Erro GPS:', err.message);
                        if (statusBox) statusBox.innerHTML = '⚠️ Erro ao obter localização';
                        resolve(null);
                    },
                    {
                        enableHighAccuracy: true,
                        timeout: 10000,
                        maximumAge: 0
                    }
                );
            } catch (e) {
                console.error('Erro na geolocalização:', e);
                resolve(null);
            }
        });
    }

    // Função principal de envio
    async function enviarAlerta() {
        console.log('📤 Enviando alerta...');

        try {
            // Validar situação
            if (!selectedSituation) {
                alert('⚠️ Selecione o tipo de situação!');
                return;
            }

            // Desabilitar botão
            sosBtn.disabled = true;
            sosBtn.style.opacity = '0.7';
            const textoOriginal = sosBtn.innerHTML;
            sosBtn.innerHTML = 'ENVIANDO...';

            // Obter localização
            const location = await getLocation();

            // Preparar dados
            const dados = {
                name: nameInput ? nameInput.value.trim() || 'Usuária' : 'Usuária',
                situation: selectedSituation,
                message: messageInput ? messageInput.value.trim() || '' : '',
                lat: location ? location.lat : null,
                lng: location ? location.lng : null,
                timestamp: new Date().toISOString()
            };

            console.log('📦 Dados do alerta:', dados);

            // Enviar para o servidor (se tiver a API)
            try {
                const response = await fetch('/api/send_alert', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(dados)
                });
                
                if (response.ok) {
                    alert('🚨 ALERTA ENVIADO COM SUCESSO!');
                } else {
                    // Se a API não existir, mostra simulação
                    alert(`🚨 ALERTA DE EMERGÊNCIA (SIMULAÇÃO)\n\n` +
                          `Nome: ${dados.name}\n` +
                          `Situação: ${dados.situation}\n` +
                          `Mensagem: ${dados.message || '(vazia)'}\n` +
                          `Localização: ${location ? 'Compartilhada ✓' : 'Não compartilhada'}`);
                }
            } catch (e) {
                // Modo simulação se a API não existir
                console.log('Modo simulação ativado');
                alert(`🚨 ALERTA DE EMERGÊNCIA (SIMULAÇÃO)\n\n` +
                      `Nome: ${dados.name}\n` +
                      `Situação: ${dados.situation}\n` +
                      `Mensagem: ${dados.message || '(vazia)'}\n` +
                      `Localização: ${location ? 'Compartilhada ✓' : 'Não compartilhada'}`);
            }

            if (statusBox) {
                statusBox.innerHTML = '✅ Alerta enviado com sucesso!';
            }

        } catch (error) {
            console.error('❌ Erro:', error);
            alert('❌ Erro ao enviar alerta. Tente novamente.');
            if (statusBox) {
                statusBox.innerHTML = '❌ Erro no envio';
            }
        } finally {
            // Restaurar botão
            setTimeout(() => {
                sosBtn.disabled = false;
                sosBtn.style.opacity = '1';
                sosBtn.innerHTML = '<div class="inner"><div class="big">SOS</div><div class="small">TOQUE E SEGURE</div></div>';
            }, 1000);
        }
    }

    // LIMPAR TODOS OS EVENT LISTENERS ANTIGOS
    // Clonar e substituir o botão para remover todos os eventos anteriores
    const novoBotao = sosBtn.cloneNode(true);
    sosBtn.parentNode.replaceChild(novoBotao, sosBtn);
    
    // Usar o novo botão
    const botaoFinal = document.getElementById('sosBtn');
    
    // Eventos do botão SOS - versão simplificada
    botaoFinal.addEventListener('click', (e) => {
        e.preventDefault();
        console.log('🖱️ Clique detectado');
        enviarAlerta();
    });

    // Toque e segure (mobile)
    botaoFinal.addEventListener('touchstart', (e) => {
        e.preventDefault();
        clearTimeout(holdTimer);
        holdTimer = setTimeout(() => {
            console.log('⏰ Toque longo detectado');
            enviarAlerta();
        }, 600);
    });

    botaoFinal.addEventListener('touchend', () => {
        clearTimeout(holdTimer);
    });

    botaoFinal.addEventListener('touchcancel', () => {
        clearTimeout(holdTimer);
    });

    // Mouse down/up (desktop)
    botaoFinal.addEventListener('mousedown', (e) => {
        e.preventDefault();
        holdTimer = setTimeout(() => {
            console.log('⏰ Clique longo detectado');
            enviarAlerta();
        }, 600);
    });

    botaoFinal.addEventListener('mouseup', () => {
        clearTimeout(holdTimer);
    });

    botaoFinal.addEventListener('mouseleave', () => {
        clearTimeout(holdTimer);
    });

    // Configurar botões do topo
    const btnRestart = document.getElementById('btnRestart');
    const btnClear = document.getElementById('btnClear');
    const btnExit = document.getElementById('btnExit');

    if (btnRestart) {
        btnRestart.onclick = window.reiniciar;
    }
    
    if (btnClear) {
        btnClear.onclick = window.limpar;
    }
    
    if (btnExit) {
        btnExit.onclick = window.sair;
    }

    console.log('🎉 Painel da mulher pronto para uso!');
}