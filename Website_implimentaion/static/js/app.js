// Sunscrap Solar SCADA Application UI Controller & Financial Engine
document.addEventListener('DOMContentLoaded', () => {
    initUserSessionController();
    initAccessibilityDrawer();
    initFinancialRevenueCalculator();
    initCopyActions();
    initEmailModals();
    initPasswordToggles();
    initEmergencyAlarmSystem();
    initTableSorting();
    initWhatsAppSharing();
    initZipDownload();
    initAlertLogsManager();
    initBackToTopButton();
    initExpiringShareSystem();
    initPlantMetadataManager();
    initRoleSwitcher();
    initPlantCommentsSystem();
    initInverterOverviewHelper();
});

// =========================================================================
// 1. Accessibility Hub: Color Themes, Font Size, Light & Dark Mode
// =========================================================================
function initAccessibilityDrawer() {
    const drawer = document.getElementById('accessibility-drawer');
    const openBtn = document.getElementById('btn-open-accessibility');
    const closeBtn = document.getElementById('btn-close-accessibility');
    const overlay = document.getElementById('accessibility-backdrop');

    if (openBtn && drawer) {
        openBtn.addEventListener('click', () => {
            drawer.classList.add('active');
            if (overlay) overlay.style.display = 'block';
        });
    }

    const closeDrawer = () => {
        if (drawer) drawer.classList.remove('active');
        if (overlay) overlay.style.display = 'none';
    };

    if (closeBtn) closeBtn.addEventListener('click', closeDrawer);
    if (overlay) overlay.addEventListener('click', closeDrawer);

    // --- A. Theme Mode (Light / Dark) ---
    const savedTheme = localStorage.getItem('sunscrap_theme_mode') || 'light';
    applyThemeMode(savedTheme);

    document.querySelectorAll('.btn-theme-mode').forEach(btn => {
        btn.addEventListener('click', () => {
            const mode = btn.getAttribute('data-theme');
            applyThemeMode(mode);
            localStorage.setItem('sunscrap_theme_mode', mode);
            showToast(`Display mode set to ${mode === 'dark' ? 'Dark Mode' : 'Light Mode'}`);
        });
    });

    // --- B. Color Vision (Vibrant / Grayscale / High Contrast) ---
    const savedColor = localStorage.getItem('sunscrap_color_mode') || 'vibrant';
    applyColorMode(savedColor);

    document.querySelectorAll('.btn-color-mode').forEach(btn => {
        btn.addEventListener('click', () => {
            const mode = btn.getAttribute('data-color');
            applyColorMode(mode);
            localStorage.setItem('sunscrap_color_mode', mode);
            showToast(`Color style updated: ${btn.innerText.trim()}`);
        });
    });

    // --- C. Font Size Scaling (85%, 100%, 115%, 125%) ---
    const scales = [0.85, 1.0, 1.15, 1.25];
    let currentScale = parseFloat(localStorage.getItem('sunscrap_font_scale') || '1.0');
    applyFontScale(currentScale);

    document.querySelectorAll('.btn-font-preset').forEach(btn => {
        btn.addEventListener('click', () => {
            const scale = parseFloat(btn.getAttribute('data-scale'));
            applyFontScale(scale);
            localStorage.setItem('sunscrap_font_scale', scale.toString());
            showToast(`Typography size: ${Math.round(scale * 100)}%`);
        });
    });

    const btnDecrease = document.getElementById('btn-font-decrease');
    const btnReset = document.getElementById('btn-font-reset');
    const btnIncrease = document.getElementById('btn-font-increase');

    if (btnDecrease) {
        btnDecrease.addEventListener('click', () => {
            let idx = scales.findIndex(s => Math.abs(s - currentScale) < 0.05);
            if (idx > 0) {
                currentScale = scales[idx - 1];
                applyFontScale(currentScale);
                localStorage.setItem('sunscrap_font_scale', currentScale.toString());
                showToast(`Font size: ${Math.round(currentScale * 100)}%`);
            }
        });
    }

    if (btnReset) {
        btnReset.addEventListener('click', () => {
            currentScale = 1.0;
            applyFontScale(currentScale);
            localStorage.setItem('sunscrap_font_scale', '1.0');
            showToast('Font size reset to default (100%)');
        });
    }

    if (btnIncrease) {
        btnIncrease.addEventListener('click', () => {
            let idx = scales.findIndex(s => Math.abs(s - currentScale) < 0.05);
            if (idx >= 0 && idx < scales.length - 1) {
                currentScale = scales[idx + 1];
                applyFontScale(currentScale);
                localStorage.setItem('sunscrap_font_scale', currentScale.toString());
                showToast(`Font size: ${Math.round(currentScale * 100)}%`);
            }
        });
    }

    // --- D. Motion Preference ---
    const savedMotion = localStorage.getItem('sunscrap_reduced_motion') === 'true';
    if (savedMotion) document.body.classList.add('reduced-motion');
    const motionToggle = document.getElementById('toggle-reduced-motion');
    if (motionToggle) {
        motionToggle.checked = savedMotion;
        motionToggle.addEventListener('change', () => {
            if (motionToggle.checked) {
                document.body.classList.add('reduced-motion');
                localStorage.setItem('sunscrap_reduced_motion', 'true');
                showToast('Reduced motion enabled');
            } else {
                document.body.classList.remove('reduced-motion');
                localStorage.setItem('sunscrap_reduced_motion', 'false');
                showToast('Smooth animations enabled');
            }
        });
    }
}

function applyThemeMode(mode) {
    if (mode === 'dark') {
        document.body.classList.add('dark-mode');
    } else {
        document.body.classList.remove('dark-mode');
    }
    document.querySelectorAll('.btn-theme-mode').forEach(btn => {
        btn.classList.toggle('active', btn.getAttribute('data-theme') === mode);
    });
}

function applyColorMode(mode) {
    document.body.classList.remove('grayscale-mode', 'high-contrast-mode');
    if (mode === 'grayscale') {
        document.body.classList.add('grayscale-mode');
    } else if (mode === 'high-contrast') {
        document.body.classList.add('high-contrast-mode');
    }
    document.querySelectorAll('.btn-color-mode').forEach(btn => {
        btn.classList.toggle('active', btn.getAttribute('data-color') === mode);
    });
}

function applyFontScale(scale) {
    document.documentElement.style.setProperty('--font-scale', scale.toString());
    const label = document.getElementById('font-scale-display');
    if (label) label.innerText = `${Math.round(scale * 100)}%`;
    document.querySelectorAll('.btn-font-preset').forEach(btn => {
        btn.classList.toggle('active', Math.abs(parseFloat(btn.getAttribute('data-scale')) - scale) < 0.05);
    });
}

// =========================================================================
// 2. Financial Revenue & Multi-Currency Tariff Engine
// =========================================================================
const CURRENCY_CONFIG = {
    INR: { symbol: '₹', code: 'INR', defaultRate: 3.00, locale: 'en-IN', label: 'Indian Rupee (INR ₹)' },
    USD: { symbol: '$', code: 'USD', defaultRate: 0.035, locale: 'en-US', label: 'US Dollar (USD $)' },
    EUR: { symbol: '€', code: 'EUR', defaultRate: 0.033, locale: 'de-DE', label: 'Euro (EUR €)' },
    GBP: { symbol: '£', code: 'GBP', defaultRate: 0.028, locale: 'en-GB', label: 'British Pound (GBP £)' }
};

function initFinancialRevenueCalculator() {
    const currencySelect = document.getElementById('revenue-currency-select');
    const tariffInput = document.getElementById('revenue-tariff-input');
    const presetButtons = document.querySelectorAll('.btn-tariff-preset');

    if (!currencySelect && !tariffInput) return;

    let currentCurrency = localStorage.getItem('sunscrap_currency') || 'INR';
    let currentRate = parseFloat(localStorage.getItem('sunscrap_tariff_rate') || '3.00');

    if (currencySelect) {
        currencySelect.value = currentCurrency;
        currencySelect.addEventListener('change', () => {
            currentCurrency = currencySelect.value;
            // Set sensible default rate for that currency if switching
            currentRate = CURRENCY_CONFIG[currentCurrency].defaultRate;
            if (tariffInput) tariffInput.value = currentRate.toFixed(3);
            localStorage.setItem('sunscrap_currency', currentCurrency);
            localStorage.setItem('sunscrap_tariff_rate', currentRate.toString());
            recalculateFinancials(currentCurrency, currentRate);
            showToast(`Currency changed to ${CURRENCY_CONFIG[currentCurrency].label}`);
        });
    }

    if (tariffInput) {
        tariffInput.value = currentRate;
        tariffInput.addEventListener('input', () => {
            const val = parseFloat(tariffInput.value);
            if (!isNaN(val) && val >= 0) {
                currentRate = val;
                localStorage.setItem('sunscrap_tariff_rate', currentRate.toString());
                recalculateFinancials(currentCurrency, currentRate);
            }
        });
    }

    presetButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const val = parseFloat(btn.getAttribute('data-rate'));
            if (!isNaN(val)) {
                currentRate = val;
                if (tariffInput) tariffInput.value = currentRate.toFixed(2);
                localStorage.setItem('sunscrap_tariff_rate', currentRate.toString());
                recalculateFinancials(currentCurrency, currentRate);
                showToast(`Tariff set to ${CURRENCY_CONFIG[currentCurrency].symbol}${currentRate}/unit`);
            }
        });
    });

    // Initial calculation
    recalculateFinancials(currentCurrency, currentRate);
}

function recalculateFinancials(currencyCode, ratePerKwh) {
    const config = CURRENCY_CONFIG[currencyCode] || CURRENCY_CONFIG.INR;

    // Grab raw kWh values from data attributes in the dashboard HTML
    const todayKwhElem = document.getElementById('val-revenue-today-kwh');
    const lifeKwhElem = document.getElementById('val-revenue-life-kwh');
    const exportKwhElem = document.getElementById('val-revenue-export-kwh');

    const todayKwh = todayKwhElem ? parseFloat(todayKwhElem.getAttribute('data-kwh') || '11921.30') : 11921.30;
    const lifeKwh = lifeKwhElem ? parseFloat(lifeKwhElem.getAttribute('data-kwh') || '1567546.00') : 1567546.00;
    const exportKwh = exportKwhElem ? parseFloat(exportKwhElem.getAttribute('data-kwh') || '11778.24') : 11778.24;

    const todayRevenue = todayKwh * ratePerKwh;
    const lifeRevenue = lifeKwh * ratePerKwh;
    const exportRevenue = exportKwh * ratePerKwh;

    // Update displays
    updateCurrencyDisplay('display-revenue-today', todayRevenue, config);
    updateCurrencyDisplay('display-revenue-lifetime', lifeRevenue, config);
    updateCurrencyDisplay('display-revenue-export', exportRevenue, config);

    // Update symbol badges
    document.querySelectorAll('.currency-symbol-label').forEach(el => {
        el.innerText = config.symbol;
    });

    const rateDisplay = document.getElementById('display-rate-unit');
    if (rateDisplay) {
        rateDisplay.innerText = `${config.symbol}${ratePerKwh.toFixed(2)} / unit (kWh)`;
    }
}

function updateCurrencyDisplay(elemId, amount, config) {
    const el = document.getElementById(elemId);
    if (!el) return;

    let formatted;
    if (config.code === 'INR') {
        // Indian numbering system format (e.g., ₹ 35,763.90 or ₹ 47,02,638.00)
        formatted = amount.toLocaleString('en-IN', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
    } else {
        formatted = amount.toLocaleString(config.locale, {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
    }
    el.innerText = `${config.symbol} ${formatted}`;
}

// =========================================================================
// 3. Output Contract: Copy table data to clipboard
// =========================================================================
function initCopyActions() {
    document.querySelectorAll('.btn-copy-table').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            const targetTableId = btn.getAttribute('data-target-table');
            const table = document.getElementById(targetTableId);
            if (!table) {
                showToast('Table not found for copying.');
                return;
            }

            let tsvContent = '';
            // Headers
            const headers = Array.from(table.querySelectorAll('thead th')).map(th => th.innerText.trim());
            tsvContent += headers.join('\t') + '\n';

            // Rows
            table.querySelectorAll('tbody tr').forEach(tr => {
                const cells = Array.from(tr.querySelectorAll('td')).map(td => td.innerText.trim());
                tsvContent += cells.join('\t') + '\n';
            });

            navigator.clipboard.writeText(tsvContent).then(() => {
                showToast('Table copied to clipboard in TSV format.');
            }).catch(err => {
                showToast('Clipboard copy failed. Please select text manually.');
            });
        });
    });

    // Client-side instant download fallback for static hosting (GitHub Pages)
    document.addEventListener('click', (e) => {
        const csvBtn = e.target.closest('.btn-client-csv');
        const xlsxBtn = e.target.closest('.btn-client-xlsx');
        const pdfBtn = e.target.closest('.btn-client-pdf');

        if (csvBtn || xlsxBtn) {
            e.preventDefault();
            const table = document.querySelector('.scada-table');
            if (!table) {
                showToast('No tabular data found to export.');
                return;
            }

            let csv = '';
            table.querySelectorAll('tr').forEach(tr => {
                const cells = Array.from(tr.querySelectorAll('th, td')).map(td => {
                    let text = td.innerText.replace(/"/g, '""').trim();
                    return `"${text}"`;
                });
                csv += cells.join(',') + '\n';
            });

            const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = xlsxBtn ? 'sunscrap_telemetry_export.csv' : 'sunscrap_telemetry_export.csv';
            link.click();
            showToast(xlsxBtn ? 'Exported table dataset in Excel-compatible CSV format' : 'CSV download generated successfully.');
        } else if (pdfBtn) {
            e.preventDefault();
            window.print();
        }
    });
}

// =========================================================================
// 4. Output Contract: Email Modal
// =========================================================================
function initEmailModals() {
    const modal = document.getElementById('email-report-modal');
    const openBtns = document.querySelectorAll('.btn-open-email-modal');
    const closeBtns = document.querySelectorAll('.btn-close-modal');
    const form = document.getElementById('email-report-form');

    if (!modal) return;

    openBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            const snapId = btn.getAttribute('data-snapshot-id');
            const reportName = btn.getAttribute('data-report-name') || 'Report';
            
            const snapInput = document.getElementById('email-snapshot-id');
            const subjInput = document.getElementById('email-subject');
            if (snapInput) snapInput.value = snapId;
            if (subjInput) subjInput.value = `Sunscrap SCADA - ${reportName}`;
            
            modal.classList.add('active');
        });
    });

    closeBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            modal.classList.remove('active');
        });
    });

    if (form) {
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            const formData = new FormData(form);
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerText = 'Dispatching Email...';
            }

            fetch('/api/exports/email', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                }
            })
            .then(res => res.json())
            .then(data => {
                modal.classList.remove('active');
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.innerText = 'Send Report';
                }
                showToast(data.message || 'Report email dispatched successfully.');
            })
            .catch(err => {
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.innerText = 'Send Report';
                }
                showToast('Error dispatching email report.');
            });
        });
    }
}

// =========================================================================
// 5. Password visibility toggles
// =========================================================================
function initPasswordToggles() {
    document.querySelectorAll('.btn-toggle-pwd').forEach(btn => {
        btn.addEventListener('click', () => {
            const inputId = btn.getAttribute('data-target');
            const input = document.getElementById(inputId);
            if (input) {
                if (input.type === 'password') {
                    input.type = 'text';
                    btn.innerText = 'Hide';
                } else {
                    input.type = 'password';
                    btn.innerText = 'Show';
                }
            }
        });
    });
}

// =========================================================================
// Helper Utilities: Toast & CSRF
// =========================================================================
function showToast(message) {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.innerHTML = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#38BDF8" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/></svg> <span>${message}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(10px)';
        toast.style.transition = 'all 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3500);
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// =========================================================================
// 6. Emergency Critical Alarm Siren, Blinking Red Screen & Alert Logs
// =========================================================================
let audioCtx = null;
let sirenOsc1 = null;
let sirenOsc2 = null;
let sirenGain = null;
let sirenTimer = null;

function playSirenSound() {
    try {
        const AudioContext = window.AudioContext || window.webkitAudioContext;
        if (!AudioContext) return;
        if (!audioCtx) audioCtx = new AudioContext();
        if (audioCtx.state === 'suspended') audioCtx.resume();

        stopSirenSound();

        // Dual-tone industrial acoustic alarm generator
        sirenOsc1 = audioCtx.createOscillator();
        sirenOsc2 = audioCtx.createOscillator();
        sirenGain = audioCtx.createGain();

        sirenOsc1.type = 'sawtooth';
        sirenOsc2.type = 'sine';

        sirenOsc1.frequency.setValueAtTime(880, audioCtx.currentTime);
        sirenOsc2.frequency.setValueAtTime(440, audioCtx.currentTime);

        sirenGain.gain.setValueAtTime(0.25, audioCtx.currentTime);

        sirenOsc1.connect(sirenGain);
        sirenOsc2.connect(sirenGain);
        sirenGain.connect(audioCtx.destination);

        sirenOsc1.start();
        sirenOsc2.start();

        let toggle = false;
        sirenTimer = setInterval(() => {
            if (!sirenOsc1 || !audioCtx) return;
            toggle = !toggle;
            const targetFreq1 = toggle ? 960 : 640;
            const targetFreq2 = toggle ? 480 : 320;
            sirenOsc1.frequency.setValueAtTime(targetFreq1, audioCtx.currentTime);
            sirenOsc2.frequency.setValueAtTime(targetFreq2, audioCtx.currentTime);
        }, 260);
    } catch (err) {
        console.warn('Web Audio Siren unavailable:', err);
    }
}

function stopSirenSound() {
    if (sirenTimer) {
        clearInterval(sirenTimer);
        sirenTimer = null;
    }
    if (sirenOsc1) {
        try { sirenOsc1.stop(); sirenOsc1.disconnect(); } catch (e) {}
        sirenOsc1 = null;
    }
    if (sirenOsc2) {
        try { sirenOsc2.stop(); sirenOsc2.disconnect(); } catch (e) {}
        sirenOsc2 = null;
    }
}

function initEmergencyAlarmSystem() {
    // Top-bar Alert History Center Trigger
    const btnOpenAlerts = document.getElementById('btn-open-alerts');
    const modalHistory = document.getElementById('modal-alert-history-backdrop');
    const btnCloseHistory = document.getElementById('btn-close-alert-history');
    const btnDismissHistory = document.getElementById('btn-dismiss-alert-history');
    const btnTriggerTest = document.getElementById('btn-trigger-emergency-test');
    const btnAckAll = document.getElementById('btn-ack-all-alarms');
    const btnShareAlertsWa = document.getElementById('btn-share-alerts-wa');

    const openAlertHistory = () => {
        if (modalHistory) {
            modalHistory.classList.remove('hidden');
            renderModalAlertHistoryTable();
        }
    };

    const closeAlertHistory = () => {
        if (modalHistory) modalHistory.classList.add('hidden');
    };

    if (btnOpenAlerts) btnOpenAlerts.addEventListener('click', openAlertHistory);
    if (btnCloseHistory) btnCloseHistory.addEventListener('click', closeAlertHistory);
    if (btnDismissHistory) btnDismissHistory.addEventListener('click', closeAlertHistory);
    if (modalHistory) {
        modalHistory.addEventListener('click', (e) => {
            if (e.target === modalHistory) closeAlertHistory();
        });
    }

    if (btnTriggerTest) {
        btnTriggerTest.addEventListener('click', () => {
            closeAlertHistory();
            window.triggerEmergencyAlarm();
        });
    }

    if (btnAckAll) {
        btnAckAll.addEventListener('click', () => {
            try {
                let logs = JSON.parse(localStorage.getItem('sunscrap_alarm_logs') || '[]');
                logs.forEach(l => { l.state = 'Acknowledged'; });
                localStorage.setItem('sunscrap_alarm_logs', JSON.stringify(logs));
                renderModalAlertHistoryTable();
                renderAlarmLogsTable();
                const badge = document.getElementById('alert-counter-badge');
                if (badge) badge.style.display = 'none';
                showToast('All active SCADA alarm incidents acknowledged by operator.');
            } catch(e) {}
        });
    }

    if (btnShareAlertsWa) {
        btnShareAlertsWa.addEventListener('click', () => {
            const logs = JSON.parse(localStorage.getItem('sunscrap_alarm_logs') || '[]');
            const activeAlarms = logs.slice(0, 3).map(l => `• ${l.device}: ${l.code} (${l.description}) [${l.state}]`).join('\n');
            const text = `🚨 *Sunscrap Solar SCADA — Critical Plant Alarm Incident Report*\n📍 Site: Sanand GIDC Phase II, Gujarat (3,900 kW AC)\n⏰ Event Time: 01:32:05 PM IST\n⚡ Fault:\n${activeAlarms}\n⚠️ Action Required: Inspect Inverter 08 (Inv-08 / 320 kWp)\n🔗 Live Diagnostics: ${window.location.origin}${window.location.pathname}`;
            window.open(`https://api.whatsapp.com/send?text=${encodeURIComponent(text)}`, '_blank');
        });
    }

    // Modal Cancel and Go buttons
    const btnCancel = document.getElementById('btn-emergency-cancel');
    const btnGo = document.getElementById('btn-emergency-go');

    if (btnCancel) {
        btnCancel.addEventListener('click', () => {
            window.dismissEmergencyAlarm();
            // Automatically open previous alert history as requested
            openAlertHistory();
        });
    }
    if (btnGo) {
        btnGo.addEventListener('click', () => {
            window.goToTargetDevice();
        });
    }
}

window.triggerEmergencyAlarm = function(customData) {
    const alarm = Object.assign({
        device: 'Inverter 08 (Inv-08 / 320 kWp)',
        code: 'ERR-402 (Grid Under-voltage)',
        title: 'CRITICAL PLANT ALARM DETECTED',
        message: 'Grid Under-voltage Trip — AC active power dropped to 0.00 kW.',
        subMessage: 'Inverter output disconnect triggered. Immediate operator acknowledgment required.',
        fault: 'Grid Frequency / Voltage Fault',
        date: '2026-10-23',
        time: '01:32:05 PM IST',
        state: 'ACTIVE / UNACKNOWLEDGED'
    }, customData || {});

    const strobe = document.getElementById('alert-strobe-overlay');
    const modalBackdrop = document.getElementById('emergency-modal-backdrop');
    if (strobe) strobe.classList.remove('hidden');
    if (modalBackdrop) modalBackdrop.classList.remove('hidden');

    const devEl = document.getElementById('alarm-modal-device');
    const codeEl = document.getElementById('alarm-modal-code');
    const msgEl = document.getElementById('alarm-modal-desc');
    const timeEl = document.getElementById('alarm-modal-time');
    const stateEl = document.getElementById('alarm-modal-state');
    if (devEl) devEl.innerText = alarm.device;
    if (codeEl) codeEl.innerText = alarm.code;
    if (msgEl) msgEl.innerText = alarm.message;
    if (timeEl) timeEl.innerText = alarm.time;
    if (stateEl) stateEl.innerText = alarm.state;

    const badge = document.getElementById('alert-counter-badge');
    if (badge) {
        badge.innerText = '1';
        badge.style.display = 'inline-block';
    }

    playSirenSound();
    recordAlarmToStorage(alarm);
};

window.dismissEmergencyAlarm = function() {
    stopSirenSound();
    const strobe = document.getElementById('alert-strobe-overlay');
    const modalBackdrop = document.getElementById('emergency-modal-backdrop');
    if (strobe) strobe.classList.add('hidden');
    if (modalBackdrop) modalBackdrop.classList.add('hidden');
    showToast('Emergency alarm siren silenced. Opening Alarm History Log...');
};

window.goToTargetDevice = function() {
    stopSirenSound();
    const strobe = document.getElementById('alert-strobe-overlay');
    const modalBackdrop = document.getElementById('emergency-modal-backdrop');
    if (strobe) strobe.classList.add('hidden');
    if (modalBackdrop) modalBackdrop.classList.add('hidden');

    const isStatic = window.location.pathname.endsWith('.html') || 
                     window.location.hostname.includes('github.io') || 
                     window.location.pathname.includes('/iamshreeji-copy2/') || 
                     window.location.pathname.includes('/Sunscrap_Recyclers_Dashboard/');
    
    // Route directly to Inverter 08 (Inv-08 / 320 kWp) telemetry & plots
    if (isStatic) {
        const prefix = window.location.pathname.includes('Sunscrap_Recyclers_Dashboard') ? 
                       '/Sunscrap_Recyclers_Dashboard/' : './';
        window.location.href = prefix + 'inverter_overview.html?inverter=INV-08';
    } else {
        window.location.href = '/inverters?device=INV-08';
    }
};

function recordAlarmToStorage(alarm) {
    try {
        let logs = JSON.parse(localStorage.getItem('sunscrap_alarm_logs') || '[]');
        // Don't duplicate if already present as first entry
        if (logs.length === 0 || logs[0].code !== alarm.code || logs[0].startTime !== alarm.time) {
            logs.unshift({
                id: 'ALM-' + Date.now().toString().slice(-6),
                dateTime: `${alarm.date} ${alarm.time}`,
                device: alarm.device,
                code: alarm.code,
                description: alarm.message,
                fault: alarm.fault,
                startTime: alarm.time,
                endTime: '--',
                state: alarm.state || 'Active / Unacknowledged'
            });
            localStorage.setItem('sunscrap_alarm_logs', JSON.stringify(logs.slice(0, 50)));
        }
        if (typeof renderAlarmLogsTable === 'function') renderAlarmLogsTable();
        renderModalAlertHistoryTable();
    } catch(e) {
        console.warn('Could not save alarm to storage:', e);
    }
}

function renderModalAlertHistoryTable() {
    const tbody = document.getElementById('modal-alert-history-tbody');
    if (!tbody) return;

    const defaultAlarms = [
        {
            dateTime: '2026-10-23 01:32:05 PM IST',
            device: 'Inverter 08 (Inv-08 / 320 kWp)',
            code: 'ERR-402',
            description: 'Grid Under-voltage Trip — AC active power dropped to 0.00 kW',
            state: 'Active / Unack'
        },
        {
            dateTime: '2026-10-23 09:14:02 AM IST',
            device: 'Inverter 08 (Inv-08 / 320 kWp)',
            code: 'ERR-402',
            description: 'Grid Under-voltage Trip (Phase voltage dip < 370V)',
            state: 'Acknowledged'
        },
        {
            dateTime: '2026-10-23 07:45:10 AM IST',
            device: 'WMS Sensor Node',
            code: 'COMM-005',
            description: 'RS485 Communication Timeout on GTI Pyranometer',
            state: 'Cleared'
        }
    ];

    let logs = JSON.parse(localStorage.getItem('sunscrap_alarm_logs') || '[]');
    if (logs.length === 0) {
        logs = defaultAlarms;
    }

    const isStatic = window.location.pathname.endsWith('.html') || 
                     window.location.hostname.includes('github.io');
    const invUrl = isStatic ? 'inverter_overview.html?inverter=INV-08' : '/inverters?device=INV-08';

    tbody.innerHTML = logs.map(item => `
        <tr>
            <td class="font-mono" style="font-size:0.8rem;">${item.dateTime || item.startTime}</td>
            <td><strong>${item.device}</strong></td>
            <td><span class="badge ${item.code.startsWith('ERR') ? 'badge-danger' : 'badge-warning'} font-mono">${item.code}</span></td>
            <td style="font-size:0.82rem;">${item.description}</td>
            <td>
                <span class="status-badge ${(item.state || '').includes('Active') ? 'offline' : ((item.state || '').includes('Ack') ? 'stale' : 'online')}">
                    ${item.state || 'Active'}
                </span>
            </td>
            <td style="text-align:right;">
                <a href="${invUrl}" class="export-btn export-btn-primary" style="padding:3px 8px; font-size:0.72rem;">
                    Inspect Inverter ➔
                </a>
            </td>
        </tr>
    `).join('');
}

// =========================================================================
// 7. Universal Interactive Table Sorting
// =========================================================================
function initTableSorting() {
    document.querySelectorAll('table.sortable, table.table-striped, table.report-table').forEach(table => {
        const headers = table.querySelectorAll('thead th');
        headers.forEach((th, colIdx) => {
            if (th.classList.contains('no-sort')) return;
            th.classList.add('sortable-th');
            if (!th.querySelector('.sort-indicator')) {
                const span = document.createElement('span');
                span.className = 'sort-indicator';
                span.innerHTML = '⇅';
                th.appendChild(span);
            }
            th.addEventListener('click', () => sortTable(table, colIdx, th));
        });
    });
}

function sortTable(table, colIdx, clickedTh) {
    const tbody = table.querySelector('tbody');
    if (!tbody) return;
    const rows = Array.from(tbody.querySelectorAll('tr'));
    if (rows.length <= 1) return;

    const currentDirection = clickedTh.getAttribute('data-sort-dir') || 'none';
    const newDirection = currentDirection === 'asc' ? 'desc' : 'asc';

    // Clear indicator on sibling headers
    table.querySelectorAll('thead th').forEach(th => {
        th.removeAttribute('data-sort-dir');
        const ind = th.querySelector('.sort-indicator');
        if (ind) ind.innerHTML = '⇅';
    });

    clickedTh.setAttribute('data-sort-dir', newDirection);
    const ind = clickedTh.querySelector('.sort-indicator');
    if (ind) ind.innerHTML = newDirection === 'asc' ? '▲' : '▼';

    rows.sort((a, b) => {
        const aCell = a.children[colIdx] ? a.children[colIdx].innerText.trim() : '';
        const bCell = b.children[colIdx] ? b.children[colIdx].innerText.trim() : '';

        // Clean currency & units
        const cleanA = aCell.replace(/[₹$€£,%\s°CkWhMWpMWhkVarVA]/gi, '');
        const cleanB = bCell.replace(/[₹$€£,%\s°CkWhMWpMWhkVarVA]/gi, '');

        const numA = parseFloat(cleanA);
        const numB = parseFloat(cleanB);

        if (!isNaN(numA) && !isNaN(numB) && cleanA !== '' && cleanB !== '') {
            return newDirection === 'asc' ? numA - numB : numB - numA;
        }

        // Try date comparison
        const dateA = Date.parse(aCell);
        const dateB = Date.parse(bCell);
        if (!isNaN(dateA) && !isNaN(dateB)) {
            return newDirection === 'asc' ? dateA - dateB : dateB - dateA;
        }

        // Standard string comparison
        return newDirection === 'asc' ? aCell.localeCompare(bCell) : bCell.localeCompare(aCell);
    });

    rows.forEach(r => tbody.appendChild(r));
}

// =========================================================================
// 8. Share on WhatsApp Feature
// =========================================================================
function initWhatsAppSharing() {
    document.querySelectorAll('.btn-whatsapp').forEach(btn => {
        btn.addEventListener('click', () => {
            const reportName = btn.getAttribute('data-report-name') || document.title || 'Plant Report';
            window.shareOnWhatsApp(reportName);
        });
    });
}

window.shareOnWhatsApp = function(reportTitle) {
    const title = reportTitle || document.title || 'Sunscrap Solar SCADA Report';
    const liveUrl = window.location.href;
    const dateStr = new Date().toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' });
    
    const message = 
`☀️ *Sunscrap Recyclers PVT LTD (3,900 kW AC / 4,640 kWp DC)*
📊 *${title}*
🗓️ Date: ${dateStr}
⚡ Plant Status: 13 / 13 Inverters Online (100% Operational)
📈 Today Generation: 18,350.40 kWh | Grid Export: 11,778.24 kWh
💰 Commercial Yield Today: ₹ 35,763.90 (@ ₹3.00/unit)
🔗 View Live SCADA: ${liveUrl}`;

    const waUrl = `https://api.whatsapp.com/send?text=${encodeURIComponent(message)}`;
    window.open(waUrl, '_blank');
};

// =========================================================================
// 9. Pure Client-Side ZIP Generator & Downloader
// =========================================================================
function initZipDownload() {
    document.querySelectorAll('.btn-zip').forEach(btn => {
        btn.addEventListener('click', () => {
            const reportName = btn.getAttribute('data-report-name') || 'Plant_Report';
            window.downloadReportAsZip(reportName);
        });
    });
}

window.downloadReportAsZip = function(reportName) {
    const cleanName = (reportName || 'Sunscrap_Report').replace(/\s+/g, '_');
    const today = new Date().toISOString().split('T')[0];

    // Extract table content to CSV
    let csvContent = '';
    const table = document.querySelector('table');
    if (table) {
        const rows = table.querySelectorAll('tr');
        rows.forEach(r => {
            const cols = Array.from(r.querySelectorAll('th, td')).map(cell => {
                let text = cell.innerText.replace(/"/g, '""').trim();
                return `"${text}"`;
            });
            csvContent += cols.join(',') + '\r\n';
        });
    } else {
        csvContent = 'Timestamp,Device,Status,Yield_kWh\r\n2026-10-23 13:00,Inverter 01,Run,1467.00\r\n';
    }

    const metadataContent = 
`Organization: Sunscrap Recyclers PVT LTD
Plant Rating: 3,900 kW AC / 4,640 kWp DC
Report Name: ${cleanName}
Generated At: ${new Date().toISOString()}
Timezone: Asia/Kolkata
Export Package: Genuine ZIP Bundle containing CSV, TSV & Metadata Audit Log
Total Inverters: 13 (Online: 13)
Export Energy: 11,778.24 kWh
Tariff Base: INR 3.00 / kWh
`;

    // Package files into a client-side ZIP
    const files = [
        { name: `${cleanName}_${today}.csv`, content: csvContent },
        { name: `${cleanName}_${today}.tsv`, content: csvContent.replace(/,/g, '\t') },
        { name: 'Audit_Metadata.txt', content: metadataContent }
    ];

    const zipBlob = buildZipBlob(files);
    const link = document.createElement('a');
    link.href = URL.createObjectURL(zipBlob);
    link.download = `${cleanName}_${today}.zip`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    showToast(`ZIP package downloaded: ${cleanName}_${today}.zip`);
};

// Pure JavaScript ZIP Writer using standard PKZIP specification
function buildZipBlob(files) {
    const textEncoder = new TextEncoder();
    const localHeaders = [];
    const centralHeaders = [];
    let offset = 0;

    // CRC32 table
    const crcTable = [];
    for (let n = 0; n < 256; n++) {
        let c = n;
        for (let k = 0; k < 8; k++) {
            c = ((c & 1) ? (0xEDB88320 ^ (c >>> 1)) : (c >>> 1));
        }
        crcTable[n] = c;
    }

    function crc32(bytes) {
        let crc = -1;
        for (let i = 0; i < bytes.length; i++) {
            crc = (crc >>> 8) ^ crcTable[(crc ^ bytes[i]) & 0xFF];
        }
        return (crc ^ (-1)) >>> 0;
    }

    files.forEach(file => {
        const fileData = textEncoder.encode(file.content);
        const fileNameBytes = textEncoder.encode(file.name);
        const crc = crc32(fileData);
        const size = fileData.length;

        // Local file header (30 bytes + filename)
        const localHeader = new Uint8Array(30 + fileNameBytes.length);
        const v = new DataView(localHeader.buffer);
        v.setUint32(0, 0x04034b50, true); // signature
        v.setUint16(4, 20, true);         // version needed (2.0)
        v.setUint16(6, 0, true);          // flags
        v.setUint16(8, 0, true);          // compression (0 = stored)
        v.setUint16(10, 0, true);         // mod time
        v.setUint16(12, 0, true);         // mod date
        v.setUint32(14, crc, true);       // crc32
        v.setUint32(18, size, true);      // compressed size
        v.setUint32(22, size, true);      // uncompressed size
        v.setUint16(26, fileNameBytes.length, true);
        v.setUint16(28, 0, true);         // extra field length
        localHeader.set(fileNameBytes, 30);

        localHeaders.push(localHeader);
        localHeaders.push(fileData);

        // Central directory file header (46 bytes + filename)
        const centralHeader = new Uint8Array(46 + fileNameBytes.length);
        const cv = new DataView(centralHeader.buffer);
        cv.setUint32(0, 0x02014b50, true); // central header signature
        cv.setUint16(4, 20, true);         // version made by
        cv.setUint16(6, 20, true);         // version needed
        cv.setUint16(8, 0, true);          // flags
        cv.setUint16(10, 0, true);         // compression (stored)
        cv.setUint16(12, 0, true);         // mod time
        cv.setUint14 ? null : cv.setUint16(14, 0, true); // mod date
        cv.setUint32(16, crc, true);
        cv.setUint32(20, size, true);
        cv.setUint32(24, size, true);
        cv.setUint16(28, fileNameBytes.length, true);
        cv.setUint16(30, 0, true);         // extra field len
        cv.setUint16(32, 0, true);         // comment len
        cv.setUint16(34, 0, true);         // disk number
        cv.setUint16(36, 0, true);         // internal attrs
        cv.setUint32(38, 0, true);         // external attrs
        cv.setUint32(42, offset, true);    // relative offset of local header
        centralHeader.set(fileNameBytes, 46);

        centralHeaders.push(centralHeader);
        offset += localHeader.length + fileData.length;
    });

    const centralDirOffset = offset;
    let centralDirSize = 0;
    centralHeaders.forEach(ch => { centralDirSize += ch.length; });

    // End of central directory record (22 bytes)
    const eocd = new Uint8Array(22);
    const ev = new DataView(eocd.buffer);
    ev.setUint32(0, 0x06054b50, true); // EOCD signature
    ev.setUint16(4, 0, true);          // disk number
    ev.setUint16(6, 0, true);          // start disk
    ev.setUint16(8, files.length, true); // entries on disk
    ev.setUint16(10, files.length, true);// total entries
    ev.setUint32(12, centralDirSize, true);
    ev.setUint32(16, centralDirOffset, true);
    ev.setUint16(20, 0, true);         // comment len

    const blobParts = [...localHeaders, ...centralHeaders, eocd];
    return new Blob(blobParts, { type: 'application/zip' });
}

// =========================================================================
// 10. Alarm Logs State Manager
// =========================================================================
function initAlertLogsManager() {
    // Default alarms seed
    const defaultAlarms = [
        {
            id: 'ALM-100234',
            dateTime: '2026-10-23 09:14:02 AM IST',
            device: 'Inverter 08',
            code: 'ERR-402',
            description: 'Grid Under-voltage Trip (Grid side phase voltage below 370V)',
            fault: 'Grid Frequency / Voltage Fault',
            startTime: '09:14:02 AM',
            endTime: '09:28:15 AM',
            state: 'Acknowledged'
        },
        {
            id: 'ALM-100231',
            dateTime: '2026-10-23 07:45:10 AM IST',
            device: 'WMS Sensor Node',
            code: 'COMM-005',
            description: 'RS485 Communication Timeout on GTI Pyranometer',
            fault: 'Communication Outage',
            startTime: '07:45:10 AM',
            endTime: '07:48:30 AM',
            state: 'Cleared'
        }
    ];

    if (!localStorage.getItem('sunscrap_alarm_logs')) {
        localStorage.setItem('sunscrap_alarm_logs', JSON.stringify(defaultAlarms));
    }

    renderAlarmLogsTable();
}

function renderAlarmLogsTable() {
    const tbody = document.getElementById('alert-logs-tbody');
    if (!tbody) return;

    const logs = JSON.parse(localStorage.getItem('sunscrap_alarm_logs') || '[]');
    if (logs.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="text-center py-4 text-muted">No active alarms or historical alerts recorded.</td></tr>';
        return;
    }

    tbody.innerHTML = logs.map(item => `
        <tr>
            <td class="font-mono">${item.dateTime}</td>
            <td><strong>${item.device}</strong></td>
            <td><span class="badge ${item.code.startsWith('ERR') ? 'badge-danger' : 'badge-warning'} font-mono">${item.code}</span></td>
            <td>${item.description}</td>
            <td>${item.fault}</td>
            <td class="font-mono">${item.startTime}</td>
            <td class="font-mono">${item.endTime || '--'}</td>
            <td>
                <span class="status-badge ${item.state === 'Active' ? 'offline' : (item.state === 'Acknowledged' ? 'stale' : 'online')}">
                    ${item.state}
                </span>
            </td>
        </tr>
    `).join('');
}

// =========================================================================
// 11. Version v2: Floating Back-to-Top Circular Button
// =========================================================================
function initBackToTopButton() {
    const btn = document.getElementById('btn-back-to-top');
    if (!btn) return;

    window.addEventListener('scroll', () => {
        if (window.scrollY > 280) {
            btn.classList.add('visible');
        } else {
            btn.classList.remove('visible');
        }
    });

    btn.addEventListener('click', () => {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });
}

// =========================================================================
// 12. Version v2: Expiring Share Link Generator with Privacy Controls
// =========================================================================
let currentShareExpiryHours = 1;

function initExpiringShareSystem() {
    const btnOpen = document.getElementById('btn-open-share-modal');
    const modalBackdrop = document.getElementById('modal-expiring-share-backdrop');
    const btnClose = document.getElementById('btn-close-share-modal');
    const btnCopy = document.getElementById('btn-copy-share-url');
    const btnWhatsAppDirect = document.getElementById('btn-share-whatsapp-direct');

    if (btnOpen && modalBackdrop) {
        btnOpen.addEventListener('click', () => {
            modalBackdrop.classList.remove('hidden');
            generateExpiringShareUrl();
        });
    }

    const closeModal = () => {
        if (modalBackdrop) modalBackdrop.classList.add('hidden');
    };

    if (btnClose) btnClose.addEventListener('click', closeModal);
    if (modalBackdrop) {
        modalBackdrop.addEventListener('click', (e) => {
            if (e.target === modalBackdrop) closeModal();
        });
    }

    // Expiry duration chips
    document.querySelectorAll('.btn-share-expiry').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.btn-share-expiry').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            const exp = btn.getAttribute('data-expiry');
            if (exp === '1h') currentShareExpiryHours = 1;
            else if (exp === '24h') currentShareExpiryHours = 24;
            else if (exp === '7d') currentShareExpiryHours = 168;
            else if (exp === '30d') currentShareExpiryHours = 720;
            else currentShareExpiryHours = 48;

            generateExpiringShareUrl();
        });
    });

    // Checkbox triggers
    ['mask-financial', 'mask-mppt', 'mask-admin-settings'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.addEventListener('change', generateExpiringShareUrl);
    });

    // Copy action
    if (btnCopy) {
        btnCopy.addEventListener('click', () => {
            const displayEl = document.getElementById('display-share-url');
            if (displayEl) {
                const url = displayEl.innerText;
                navigator.clipboard.writeText(url).then(() => {
                    showToast('Expiring share link copied to clipboard!');
                }).catch(() => {
                    showToast('Link copied!');
                });
            }
        });
    }

    // Direct WhatsApp share of expiring link
    if (btnWhatsAppDirect) {
        btnWhatsAppDirect.addEventListener('click', () => {
            const displayEl = document.getElementById('display-share-url');
            const url = displayEl ? displayEl.innerText : window.location.href;
            const text = `☀️ *Sunscrap Solar SCADA — Temporary Access Portal*\n🔗 Secure Link: ${url}\n⏳ Valid for: ${currentShareExpiryHours} Hours\n🔒 Authorized by Plant Administration`;
            window.open(`https://api.whatsapp.com/send?text=${encodeURIComponent(text)}`, '_blank');
        });
    }

    // Check inbound share token & expiration on page load
    checkInboundShareLink();
}

function generateExpiringShareUrl() {
    const displayEl = document.getElementById('display-share-url');
    const indicatorEl = document.getElementById('share-expiry-indicator');
    if (!displayEl) return;

    const maskFin = document.getElementById('mask-financial')?.checked ?? true;
    const maskMppt = document.getElementById('mask-mppt')?.checked ?? false;
    const maskAdm = document.getElementById('mask-admin-settings')?.checked ?? true;

    const expiresAt = Date.now() + (currentShareExpiryHours * 3600 * 1000);
    const token = 'SCADA-' + Math.random().toString(36).substring(2, 10).toUpperCase();

    const baseUrl = window.location.origin + window.location.pathname;
    const shareUrl = `${baseUrl}?share_token=${token}&exp=${expiresAt}&mask_fin=${maskFin}&mask_mppt=${maskMppt}&mask_adm=${maskAdm}`;

    displayEl.innerText = shareUrl;
    if (indicatorEl) {
        const expDate = new Date(expiresAt).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', day: '2-digit', month: 'short' });
        indicatorEl.innerHTML = `✓ Link active until <strong>${expDate}</strong> (${currentShareExpiryHours}h limit)`;
    }
}

function checkInboundShareLink() {
    const params = new URLSearchParams(window.location.search);
    const shareToken = params.get('share_token');
    const exp = params.get('exp');

    if (shareToken && exp) {
        const expTimestamp = parseInt(exp, 10);
        if (Date.now() > expTimestamp) {
            // Expired link banner
            const banner = document.createElement('div');
            banner.style.cssText = 'position:fixed; top:0; left:0; right:0; background:#DC2626; color:#FFF; padding:12px; text-align:center; font-weight:700; z-index:99999; box-shadow:0 4px 12px rgba(0,0,0,0.3);';
            banner.innerHTML = '⚠️ This temporary SCADA share link has EXPIRED. Please request an updated link from the plant administrator.';
            document.body.prepend(banner);
        } else {
            // Apply privacy masking
            if (params.get('mask_adm') === 'true') {
                document.body.classList.add('viewer-mode');
            }
            if (params.get('mask_fin') === 'true') {
                document.querySelectorAll('#display-revenue-today, #display-revenue-export, #display-revenue-lifetime, .revenue-currency-select').forEach(el => {
                    el.style.filter = 'blur(5px)';
                    el.title = 'Masked by Link Owner';
                });
            }
            showToast('Loaded via Guest Share Link with customized privacy mask');
        }
    }
}

// =========================================================================
// 13. Version v2: Plant Metadata, Owner Details & GPS Location Editor
// =========================================================================
function initPlantMetadataManager() {
    const btnOpen = document.getElementById('btn-open-plant-details');
    const modalBackdrop = document.getElementById('modal-plant-metadata-backdrop');
    const btnClose = document.getElementById('btn-close-plant-metadata');

    if (btnOpen && modalBackdrop) {
        btnOpen.addEventListener('click', () => {
            modalBackdrop.classList.remove('hidden');
            loadSavedPlantMetadataToForm();
        });
    }

    const closeModal = () => {
        if (modalBackdrop) modalBackdrop.classList.add('hidden');
    };

    if (btnClose) btnClose.addEventListener('click', closeModal);
    if (modalBackdrop) {
        modalBackdrop.addEventListener('click', (e) => {
            if (e.target === modalBackdrop) closeModal();
        });
    }

    // Apply saved metadata to page on boot
    applySavedPlantMetadataToDOM();
}

function loadSavedPlantMetadataToForm() {
    try {
        const saved = JSON.parse(localStorage.getItem('sunscrap_plant_metadata') || '{}');
        if (saved.name) document.getElementById('plant-meta-name').value = saved.name;
        if (saved.capacity) document.getElementById('plant-meta-capacity').value = saved.capacity;
        if (saved.location) document.getElementById('plant-meta-location').value = saved.location;
        if (saved.owner) document.getElementById('plant-meta-owner').value = saved.owner;
        if (saved.contact) document.getElementById('plant-meta-contact').value = saved.contact;
        if (saved.lat) document.getElementById('plant-meta-lat').value = saved.lat;
        if (saved.lng) document.getElementById('plant-meta-lng').value = saved.lng;
        if (saved.timezone) document.getElementById('plant-meta-tz').value = saved.timezone;
        if (saved.grid) document.getElementById('plant-meta-grid').value = saved.grid;
    } catch(e) {}
}

function applySavedPlantMetadataToDOM() {
    try {
        const saved = JSON.parse(localStorage.getItem('sunscrap_plant_metadata') || '{}');
        if (saved.name) {
            document.querySelectorAll('.plant-title').forEach(el => {
                el.firstChild.textContent = saved.name + ' ';
            });
        }
        if (saved.lat && saved.lng) {
            const link = document.getElementById('plant-gmaps-link');
            if (link) {
                link.href = `https://maps.google.com/?q=${saved.lat},${saved.lng}`;
                link.innerText = `${saved.lat}° N, ${saved.lng}° E (View on Map)`;
            }
        }
    } catch(e) {}
}

window.savePlantMetadata = function(event) {
    if (event) event.preventDefault();

    const metadata = {
        name: document.getElementById('plant-meta-name')?.value || 'Sunscrap Recyclers PVT LTD',
        capacity: document.getElementById('plant-meta-capacity')?.value || '3,900 kW AC / 4,640 kWp DC',
        location: document.getElementById('plant-meta-location')?.value || 'Sanand GIDC Phase II, Gujarat',
        owner: document.getElementById('plant-meta-owner')?.value || 'Darshan Patel',
        contact: document.getElementById('plant-meta-contact')?.value || 'darshan@sunscrap.local',
        lat: document.getElementById('plant-meta-lat')?.value || '22.9868',
        lng: document.getElementById('plant-meta-lng')?.value || '72.3787',
        timezone: document.getElementById('plant-meta-tz')?.value || 'Asia/Kolkata',
        grid: document.getElementById('plant-meta-grid')?.value || '11 kV Feeder / GETCO 66 kV Substation',
        updatedAt: new Date().toISOString()
    };

    localStorage.setItem('sunscrap_plant_metadata', JSON.stringify(metadata));
    applySavedPlantMetadataToDOM();

    const modalBackdrop = document.getElementById('modal-plant-metadata-backdrop');
    if (modalBackdrop) modalBackdrop.classList.add('hidden');

    showToast('Plant details and GPS location updated & persisted!');
};

window.detectGPSLocation = function() {
    if (navigator.geolocation) {
        showToast('Acquiring high-accuracy GPS coordinates...');
        navigator.geolocation.getCurrentPosition(
            (pos) => {
                const lat = pos.coords.latitude.toFixed(4);
                const lng = pos.coords.longitude.toFixed(4);
                const latInput = document.getElementById('plant-meta-lat');
                const lngInput = document.getElementById('plant-meta-lng');
                if (latInput) latInput.value = lat;
                if (lngInput) lngInput.value = lng;
                showToast(`GPS Position detected: ${lat}° N, ${lng}° E`);
            },
            (err) => {
                showToast('Using factory default calibrated coordinates (22.9868, 72.3787).');
            },
            { timeout: 6000 }
        );
    } else {
        showToast('Geolocation not supported on this device.');
    }
};

// =========================================================================
// 14. Version v2: Operator Role Switcher (Admin vs Restricted Viewer)
// =========================================================================
function initRoleSwitcher() {
    const btn = document.getElementById('btn-toggle-role');
    const badge = document.getElementById('role-display-badge');
    if (!btn || !badge) return;

    let isViewer = localStorage.getItem('scada_role_mode') === 'viewer';
    applyRoleMode(isViewer);

    btn.addEventListener('click', () => {
        isViewer = !isViewer;
        applyRoleMode(isViewer);
        localStorage.setItem('scada_role_mode', isViewer ? 'viewer' : 'admin');
        showToast(isViewer ? 'Switched to Viewer Mode (Sensitive settings masked)' : 'Switched to Administrator Mode (Full permissions)');
    });
}

function applyRoleMode(isViewer) {
    const badge = document.getElementById('role-display-badge');
    if (isViewer) {
        document.body.classList.add('viewer-mode');
        if (badge) {
            badge.innerText = 'Viewer (Restricted)';
            badge.style.background = '#F59E0B';
        }
    } else {
        document.body.classList.remove('viewer-mode');
        if (badge) {
            badge.innerText = 'Admin (Full Access)';
            badge.style.background = '#1D5BF1';
        }
    }
}

// =========================================================================
// 15. User Session & Workstation Authentication Controller
// =========================================================================
function initUserSessionController() {
    const isStatic = window.location.protocol === 'file:' || 
                     window.location.hostname.includes('github.io') || 
                     window.location.pathname.endsWith('.html');
                     
    let currentUser = localStorage.getItem('scada_session_user');
    let currentRole = localStorage.getItem('scada_session_role') || 'administrator';

    // Update avatar and username in top header
    const avatarEl = document.getElementById('header-user-avatar');
    const nameEl = document.getElementById('header-username-display');
    const roleBadge = document.getElementById('role-display-badge');

    if (currentUser) {
        if (avatarEl) avatarEl.innerText = currentUser.charAt(0).toUpperCase();
        if (nameEl) nameEl.innerText = currentUser;
        if (roleBadge) {
            let roleLabel = 'Administrator';
            let roleBg = '#1D5BF1';
            if (currentRole === 'developer') {
                roleLabel = 'Developer';
                roleBg = '#6366F1';
            } else if (currentRole === 'plant_owner') {
                roleLabel = 'Plant Owner';
                roleBg = '#D97706';
            } else if (currentRole === 'third_party' || currentRole === 'viewer') {
                roleLabel = 'Third-Party Viewer';
                roleBg = '#10B981';
                document.body.classList.add('viewer-mode');
            }
            roleBadge.innerText = roleLabel;
            roleBadge.style.background = roleBg;
        }
    }

    // Workstation Logout action
    const btnLogout = document.getElementById('btn-workstation-logout');
    if (btnLogout) {
        btnLogout.addEventListener('click', (e) => {
            // Record developer audit telemetry
            try {
                const auditLog = {
                    action: 'USER_LOGOUT',
                    user: currentUser || 'operator',
                    role: currentRole || 'administrator',
                    details: `Operator workstation session cleanly logged out (${currentRole})`,
                    timestamp: new Date().toLocaleDateString('en-GB') + ' ' + new Date().toLocaleTimeString('en-GB') + ' IST',
                    device: navigator.platform + ' Terminal',
                    browser: navigator.userAgent.split(' ')[0],
                    approx_location: 'Ahmedabad, Gujarat, India (22.9868° N, 72.3787° E)',
                    network_provider: 'Jio Fiber High-Speed Gateway',
                    ip: '192.168.1.100'
                };
                let logs = JSON.parse(localStorage.getItem('scada_developer_audit_logs') || '[]');
                logs.unshift(auditLog);
                localStorage.setItem('scada_developer_audit_logs', JSON.stringify(logs.slice(0, 100)));
            } catch(err) {}

            localStorage.removeItem('scada_session_user');
            localStorage.removeItem('scada_session_role');
            localStorage.removeItem('scada_session_name');

            if (isStatic) {
                e.preventDefault();
                const prefix = window.location.pathname.includes('Sunscrap_Recyclers_Dashboard') ? 
                               '/Sunscrap_Recyclers_Dashboard/' : './';
                window.location.replace(prefix + 'login.html');
            }
        });
    }
}

// =========================================================================
// 16. Plant Operations Discussion & Collaboration (Role 4: Third Party)
// =========================================================================
function initPlantCommentsSystem() {
    const btnOpen = document.getElementById('btn-open-plant-notes');
    const modal = document.getElementById('modal-plant-comments-backdrop');
    const btnClose = document.getElementById('btn-close-plant-notes');
    const authorBadge = document.getElementById('comment-author-badge');

    const defaultComments = [
        {
            author: 'darshan_owner',
            role: 'Plant Owner',
            time: '11:20 AM IST',
            text: 'Generation today is performing 4.8% above the seasonal model. Grid export revenue on track to exceed ₹35,000 for the day.'
        },
        {
            author: 'developer',
            role: 'Developer',
            time: '09:30 AM IST',
            text: 'Deployed low-latency telemetry patch v2.4 with explicit middle-aligned coordinate axes and emergency siren audio synthesis.'
        },
        {
            author: 'viewer',
            role: 'Third-Party Auditor',
            time: '08:45 AM IST',
            text: 'Verified 13 / 13 inverter string insulation resistance (> 500 kΩ). No DC ground faults detected across 325 total PV strings.'
        }
    ];

    if (!localStorage.getItem('sunscrap_plant_comments')) {
        localStorage.setItem('sunscrap_plant_comments', JSON.stringify(defaultComments));
    }

    if (btnOpen && modal) {
        btnOpen.addEventListener('click', () => {
            modal.classList.remove('hidden');
            renderPlantCommentsFeed();
            if (authorBadge) {
                const u = localStorage.getItem('scada_session_user') || 'operator';
                const r = localStorage.getItem('scada_session_role') || 'third_party';
                authorBadge.innerText = `${u} (${r})`;
            }
        });
    }

    const closeModal = () => { if (modal) modal.classList.add('hidden'); };
    if (btnClose) btnClose.addEventListener('click', closeModal);
    if (modal) {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) closeModal();
        });
    }
}

function renderPlantCommentsFeed() {
    const container = document.getElementById('comments-feed-container');
    if (!container) return;

    const comments = JSON.parse(localStorage.getItem('sunscrap_plant_comments') || '[]');
    container.innerHTML = comments.map(c => `
        <div style="background:var(--surface-alt); border:1px solid var(--border); border-radius:var(--radius-sm); padding:10px 14px;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                <div style="display:flex; align-items:center; gap:6px;">
                    <strong style="font-size:0.85rem; color:var(--text-main);">${c.author}</strong>
                    <span class="status-badge" style="font-size:0.68rem;">${c.role}</span>
                </div>
                <span class="font-mono" style="font-size:0.75rem; color:var(--text-muted);">${c.time}</span>
            </div>
            <div style="font-size:0.84rem; color:var(--text-main); line-height:1.4;">${c.text}</div>
        </div>
    `).join('');
}

window.postPlantComment = function(event) {
    if (event) event.preventDefault();
    const input = document.getElementById('comment-text-input');
    if (!input || !input.value.trim()) return;

    const u = localStorage.getItem('scada_session_user') || 'operator';
    const r = localStorage.getItem('scada_session_role') || 'third_party';

    const newComment = {
        author: u,
        role: r,
        time: new Date().toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', hour12: true }) + ' IST',
        text: input.value.trim()
    };

    let comments = JSON.parse(localStorage.getItem('sunscrap_plant_comments') || '[]');
    comments.unshift(newComment);
    localStorage.setItem('sunscrap_plant_comments', JSON.stringify(comments.slice(0, 50)));

    input.value = '';
    renderPlantCommentsFeed();
    showToast('Comment posted to plant operations discussion log.');
};

// =========================================================================
// 17. Target Device Selector Helper (Inverter 08 Auto-Selection & Alerts)
// =========================================================================
function initInverterOverviewHelper() {
    const params = new URLSearchParams(window.location.search);
    const inv = params.get('inverter') || params.get('device');
    if (!inv) return;

    const sel = document.getElementById('inv-select');
    if (sel) {
        for (let i = 0; i < sel.options.length; i++) {
            const optVal = sel.options[i].value.toLowerCase();
            const optText = sel.options[i].text.toLowerCase();
            const target = inv.toLowerCase();
            if (optVal === target || optVal.replace('-', '') === target.replace('-', '') || optText.includes(target)) {
                sel.selectedIndex = i;
                break;
            }
        }
    }

    // If Inverter 08 was specifically targeted by alarm, show diagnostic banner
    if (inv.includes('08') || inv.includes('8')) {
        const content = document.querySelector('.app-content');
        if (content && !document.getElementById('inverter-alarm-notice')) {
            const notice = document.createElement('div');
            notice.id = 'inverter-alarm-notice';
            notice.style.cssText = 'background:rgba(220, 38, 38, 0.08); border:1px solid #DC2626; border-radius:var(--radius-sm); padding:12px 18px; margin-bottom:20px; display:flex; justify-content:space-between; align-items:center;';
            notice.innerHTML = `
                <div style="display:flex; align-items:center; gap:12px;">
                    <div style="background:#DC2626; color:#FFF; width:28px; height:28px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-weight:800; font-size:1rem;">!</div>
                    <div>
                        <strong style="color:#DC2626; font-size:0.92rem;">Target Device Alarm Active: Inverter 08 (Inv-08 / 320 kWp)</strong>
                        <div style="font-size:0.8rem; color:var(--text-muted); margin-top:2px;">Status: <strong>ERR-402 (Grid Under-voltage Trip)</strong> • AC Power dropped to 0.00 kW • Inspect MPPT string voltages below.</div>
                    </div>
                </div>
                <button type="button" class="export-btn" onclick="this.parentElement.remove()" style="font-size:0.75rem;">Dismiss</button>
            `;
            content.prepend(notice);
        }
    }
}
