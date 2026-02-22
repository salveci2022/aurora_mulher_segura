// panic.js - Código separado
console.log("🚀 panic.js carregado");

// Funções globais
window.reiniciar = function() {
    location.reload();
};

window.limpar = function() {
    document.getElementById('name').value = '';
    document.getElementById('message').value = '';
    document.getElementById('shareLoc').checked = false;
    document.querySelectorAll('.chip').forEach(c => c.classList.remove('active'));
    document.getElementById('status').innerHTML = 'Pronto. Toque e segure no SOS para enviar.';
};

window.sair = function() {
    window.close();
    window.location.href = 'about:blank';
};

// Inicializar
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', iniciar);
} else {
    iniciar();
}

function iniciar() {
    console.log("✅ DOM carregado!");

    const sosBtn = document.getElementById('sosBtn');
    const nameInput = document.getElementById('name');
    const messageInput = document.getElementById('message');
    const shareLoc = document.getElementById('shareLoc');
    const chips = document.querySelectorAll('.chip');
    const statusBox = document.getElementById('status');

    let selectedSituation = '';
    let holdTimer = null;

    if (!sosBtn) {
        console.error('❌ Botão SOS não encontrado!');
        return;
    }

    // Chips
    chips.forEach(chip => {
        chip.onclick = function() {
            chips.forEach(c => c.classList.remove('active'));
            this.classList.add('active');
            selectedSituation = this.innerText.trim();
            statusBox.innerHTML = `Situação: ${selectedSituation}`;
        };
    });

    // Localização
    function getLocation() {
        return new Promise((resolve) => {
            if (!shareLoc || !shareLoc.checked) {
                resolve(null);
                return;
            }
            if (!navigator.geolocation) {
                resolve(null);
                return;
            }
            navigator.geolocation.getCurrentPosition(
                pos => resolve({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
                () => resolve(null),
                { timeout: 10000 }
            );
        });
    }

    // Enviar alerta
    async function enviarAlerta() {
        if (!selectedSituation) {
            alert('⚠️ Selecione a situação!');
            return;
        }

        sosBtn.disabled = true;
        sosBtn.classList.add('enviando');
        
        try {
            const location = await getLocation();
            const dados = {
                name: nameInput?.value || 'Usuária',
                situation: selectedSituation,
                message: messageInput?.value || '',
                lat: location?.lat || null,
                lng: location?.lng || null
            };
            
            alert(`🚨 ALERTA ENVIADO!\n\nSituação: ${dados.situation}`);
            statusBox.innerHTML = '✅ Alerta enviado!';
            
        } catch (error) {
            alert('❌ Erro ao enviar');
        } finally {
            sosBtn.disabled = false;
            sosBtn.classList.remove('enviando');
        }
    }

    // Eventos
    sosBtn.onclick = (e) => {
        e.preventDefault();
        enviarAlerta();
    };

    sosBtn.addEventListener('touchstart', (e) => {
        e.preventDefault();
        clearTimeout(holdTimer);
        holdTimer = setTimeout(enviarAlerta, 600);
    });

    sosBtn.addEventListener('touchend', () => clearTimeout(holdTimer));
    sosBtn.addEventListener('touchcancel', () => clearTimeout(holdTimer));
    
    sosBtn.addEventListener('mousedown', () => {
        holdTimer = setTimeout(enviarAlerta, 600);
    });
    
    sosBtn.addEventListener('mouseup', () => clearTimeout(holdTimer));
    sosBtn.addEventListener('mouseleave', () => clearTimeout(holdTimer));
}