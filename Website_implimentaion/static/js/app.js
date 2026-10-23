// Sunscrap Solar SCADA Application UI Controller & Financial Engine
document.addEventListener('DOMContentLoaded', () => {
    initAccessibilityDrawer();
    initFinancialRevenueCalculator();
    initCopyActions();
    initEmailModals();
    initPasswordToggles();
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
