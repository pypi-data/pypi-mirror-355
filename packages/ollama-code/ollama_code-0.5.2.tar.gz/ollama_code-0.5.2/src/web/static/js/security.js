// SECURITY MODE MANAGEMENT
// Globale Variable für aktuellen Modus
let currentSecurityMode = 'safe';
let selectedMode = 'safe';

// Security Mode Dialog Functions
function openSecurityModeDialog() {
    document.getElementById('security-mode-dialog').style.display = 'flex';
    
    // Markiere aktuellen Modus
    document.querySelectorAll('.security-mode-option').forEach(option => {
        option.classList.remove('selected');
        if (option.dataset.mode === currentSecurityMode) {
            option.classList.add('selected');
            selectedMode = currentSecurityMode;
        }
    });
    
    updateSelectButton();
}

function closeSecurityModeDialog() {
    document.getElementById('security-mode-dialog').style.display = 'none';
    selectedMode = currentSecurityMode; // Reset selection
}

// Mode Selection Handling
document.addEventListener('click', function(e) {
    if (e.target.closest('.security-mode-option')) {
        const option = e.target.closest('.security-mode-option');
        const mode = option.dataset.mode;
        
        // Remove previous selection
        document.querySelectorAll('.security-mode-option').forEach(opt => {
            opt.classList.remove('selected');
        });
        
        // Add selection to clicked option
        option.classList.add('selected');
        selectedMode = mode;
        updateSelectButton();
    }
});

function updateSelectButton() {
    const btn = document.getElementById('mode-select-btn');
    if (selectedMode === currentSecurityMode) {
        btn.textContent = 'Aktueller Modus';
        btn.disabled = true;
    } else {
        btn.textContent = 'Modus wechseln';
        btn.disabled = false;
    }
}

function selectSecurityMode() {
    if (selectedMode === 'hell-out') {
        // Zeige Hell-Out Warnung
        closeSecurityModeDialog();
        showHellOutWarning();
    } else {
        // Aktiviere Safe oder Base Mode direkt
        activateSecurityMode(selectedMode);
        closeSecurityModeDialog();
    }
}

// Hell-Out Warning Dialog
function showHellOutWarning() {
    document.getElementById('hell-out-warning-dialog').style.display = 'flex';
    
    // Reset form
    document.getElementById('confirmation-input').value = '';
    document.getElementById('disclaimer-checkbox').checked = false;
    document.getElementById('step2').style.display = 'none';
    document.getElementById('hell-out-confirm-btn').disabled = true;
    
    // Setup input validation
    setupHellOutValidation();
}

function closeHellOutWarning() {
    document.getElementById('hell-out-warning-dialog').style.display = 'none';
    selectedMode = currentSecurityMode; // Reset
}

function setupHellOutValidation() {
    const input = document.getElementById('confirmation-input');
    const checkbox = document.getElementById('disclaimer-checkbox');
    const step1Status = document.getElementById('step1-status');
    const step2Status = document.getElementById('step2-status');
    const confirmBtn = document.getElementById('hell-out-confirm-btn');
    
    input.addEventListener('input', function() {
        if (this.value.toLowerCase() === 'bestätigen') {
            step1Status.innerHTML = '✅ Korrekt eingegeben';
            step1Status.className = 'step-status success';
            document.getElementById('step2').style.display = 'block';
        } else {
            step1Status.innerHTML = this.value ? '❌ Falsches Wort' : '';
            step1Status.className = 'step-status error';
            document.getElementById('step2').style.display = 'none';
            confirmBtn.disabled = true;
        }
        updateConfirmButton();
    });
    
    checkbox.addEventListener('change', function() {
        if (this.checked) {
            step2Status.innerHTML = '✅ Haftungsausschluss akzeptiert';
            step2Status.className = 'step-status success';
        } else {
            step2Status.innerHTML = '';
            step2Status.className = 'step-status';
        }
        updateConfirmButton();
    });
    
    function updateConfirmButton() {
        const inputValid = input.value.toLowerCase() === 'bestätigen';
        const checkboxValid = checkbox.checked;
        confirmBtn.disabled = !(inputValid && checkboxValid);
    }
}

function confirmHellOutMode() {
    activateSecurityMode('hell-out');
    closeHellOutWarning();
}

// Security Mode Activation
async function activateSecurityMode(mode) {
    try {
        // Sende Mode-Change an Backend
        const result = await eel.change_security_mode(mode)();
        
        if (result.success) {
            currentSecurityMode = mode;
            updateSecurityUI(mode);
            
            // Zeige Erfolg im Terminal
            const modeNames = {
                'safe': '🔒 Safe Mode (Simulation)',
                'base': '🔓 Base Mode (Begrenzte echte Zugriffe)',
                'hell-out': '⚠️ Hell-Out Mode (VOLLZUGRIFF)'
            };
            
            if (window.atlasApp) {
                window.atlasApp.addMessageToTerminal({
                    role: 'assistant',
                    type: 'message',
                    content: `🔄 Sicherheitsmodus gewechselt zu: ${modeNames[mode]}`
                });
            }
        } else {
            throw new Error(result.error || 'Unbekannter Fehler');
        }
    } catch (error) {
        console.error('Fehler beim Wechseln des Sicherheitsmodus:', error);
        
        if (window.atlasApp) {
            window.atlasApp.addMessageToTerminal({
                role: 'assistant',
                type: 'error',
                content: `❌ Fehler beim Wechseln des Sicherheitsmodus: ${error}`
            });
        }
    }
}

function updateSecurityUI(mode) {
    // Update Button
    const btn = document.getElementById('security-mode-btn');
    const modeText = document.getElementById('security-mode-text');
    const securityLed = document.getElementById('security-led');
    
    // Remove all mode classes from button
    btn.className = 'security-mode-btn';
    securityLed.className = 'security-led';
    
    // Remove all security mode classes from body
    document.body.classList.remove('safe-mode', 'base-mode', 'hell-out-mode');
    
    switch (mode) {
        case 'safe':
            btn.classList.add('safe-mode');
            securityLed.classList.add('safe');
            document.body.classList.add('safe-mode');
            modeText.textContent = '🔒 Safe Mode';
            break;
        case 'base':
            btn.classList.add('base-mode');
            securityLed.classList.add('base');
            document.body.classList.add('base-mode');
            modeText.textContent = '🔓 Base Mode';
            break;
        case 'hell-out':
            btn.classList.add('hell-out-mode');
            securityLed.classList.add('hell-out');
            document.body.classList.add('hell-out-mode');
            modeText.textContent = '⚠️ Hell-Out Mode';
            break;
    }
}

// Initialize Security UI on page load
document.addEventListener('DOMContentLoaded', async function() {
    try {
        const systemInfo = await eel.get_system_info()();
        if (systemInfo.security_mode) {
            currentSecurityMode = systemInfo.security_mode;
            updateSecurityUI(currentSecurityMode);
        }
    } catch (error) {
        console.error('Fehler beim Laden der Systeminfo:', error);
    }
});

// Globale Funktionen für HTML onclick Events
window.openSecurityModeDialog = openSecurityModeDialog;
window.closeSecurityModeDialog = closeSecurityModeDialog;
window.selectSecurityMode = selectSecurityMode;
window.showHellOutWarning = showHellOutWarning;
window.closeHellOutWarning = closeHellOutWarning;
window.confirmHellOutMode = confirmHellOutMode;