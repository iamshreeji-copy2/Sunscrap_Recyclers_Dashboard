// Apache ECharts Manager for SATs Solar SCADA
// Provides centralized instance lifecycle, auto-resizing, and dynamic Light/Dark mode font color adaptation

function getChartThemeColors() {
    const isDark = document.body.classList.contains('dark-mode');
    return {
        isDark: isDark,
        // Legend font color: NEVER white in light mode, NEVER dark in dark mode
        legendColor: isDark ? '#F1F5F9' : '#1E293B',
        axisLabelColor: isDark ? '#94A3B8' : '#475569',
        axisNameColor: isDark ? '#CBD5E1' : '#1E293B',
        axisLineColor: isDark ? 'rgba(255, 255, 255, 0.2)' : 'rgba(0, 0, 0, 0.15)',
        splitLineColor: isDark ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.06)',
        gaugeDetailColor: isDark ? '#F1F5F9' : '#1E293B',
        tooltipBg: isDark ? '#102623' : '#FFFFFF',
        tooltipBorder: isDark ? '#234E47' : '#CBD5E1',
        tooltipText: isDark ? '#F1F8F6' : '#0F172A'
    };
}

function enhanceChartOptions(opts, colors) {
    if (!opts || typeof opts !== 'object') return opts;

    // 1. Legend Font Styling (high contrast in both light & dark modes)
    if (opts.legend) {
        if (Array.isArray(opts.legend)) {
            opts.legend = opts.legend.map(leg => {
                const ts = Object.assign({}, leg.textStyle || {}, {
                    color: colors.legendColor,
                    fontSize: (leg.textStyle && leg.textStyle.fontSize) || 12,
                    fontWeight: (leg.textStyle && leg.textStyle.fontWeight) || 600
                });
                return Object.assign({}, leg, { textStyle: ts });
            });
        } else {
            const ts = Object.assign({}, opts.legend.textStyle || {}, {
                color: colors.legendColor,
                fontSize: (opts.legend.textStyle && opts.legend.textStyle.fontSize) || 12,
                fontWeight: (opts.legend.textStyle && opts.legend.textStyle.fontWeight) || 600
            });
            opts.legend = Object.assign({}, opts.legend, { textStyle: ts });
        }
    }

    // 2. Helper to enhance a single axis (xAxis or yAxis)
    function enhanceAxis(axis) {
        if (!axis) return axis;
        const out = Object.assign({}, axis);

        // Axis labels
        out.axisLabel = Object.assign({}, out.axisLabel || {});
        if (!out.axisLabel.color || String(out.axisLabel.color).includes('var(')) {
            out.axisLabel.color = colors.axisLabelColor;
        } else if (out.axisLabel.color === '#FFF' || out.axisLabel.color === '#FFFFFF' || out.axisLabel.color === '#000' || out.axisLabel.color === '#000000') {
            out.axisLabel.color = colors.axisLabelColor;
        }

        // Axis Name / Title
        if (out.name) {
            out.nameTextStyle = Object.assign({}, out.nameTextStyle || {});
            if (!out.nameTextStyle.color || String(out.nameTextStyle.color).includes('var(')) {
                out.nameTextStyle.color = colors.axisNameColor;
            }
        }

        // Split line
        if (!out.splitLine) out.splitLine = {};
        out.splitLine = Object.assign({}, out.splitLine, {
            lineStyle: Object.assign({}, (out.splitLine && out.splitLine.lineStyle) || {}, {
                color: colors.splitLineColor
            })
        });

        // Axis line
        if (!out.axisLine) out.axisLine = {};
        out.axisLine = Object.assign({}, out.axisLine, {
            lineStyle: Object.assign({}, (out.axisLine && out.axisLine.lineStyle) || {}, {
                color: colors.axisLineColor
            })
        });

        return out;
    }

    // 3. X-Axis
    if (opts.xAxis) {
        if (Array.isArray(opts.xAxis)) {
            opts.xAxis = opts.xAxis.map(enhanceAxis);
        } else {
            opts.xAxis = enhanceAxis(opts.xAxis);
        }
    }

    // 4. Y-Axis
    if (opts.yAxis) {
        if (Array.isArray(opts.yAxis)) {
            opts.yAxis = opts.yAxis.map(enhanceAxis);
        } else {
            opts.yAxis = enhanceAxis(opts.yAxis);
        }
    }

    // 5. Gauge Series
    if (opts.series && Array.isArray(opts.series)) {
        opts.series = opts.series.map(s => {
            if (s && s.type === 'gauge') {
                const updated = Object.assign({}, s);
                if (updated.detail) {
                    updated.detail = Object.assign({}, updated.detail, {
                        color: colors.gaugeDetailColor
                    });
                }
                if (updated.axisLabel) {
                    updated.axisLabel = Object.assign({}, updated.axisLabel, {
                        color: colors.axisLabelColor
                    });
                }
                return updated;
            }
            return s;
        });
    }

    // 6. Tooltip styling
    if (opts.tooltip) {
        opts.tooltip = Object.assign({
            backgroundColor: colors.tooltipBg,
            borderColor: colors.tooltipBorder,
            textStyle: { color: colors.tooltipText }
        }, opts.tooltip);
    }

    return opts;
}

const ChartRegistry = {
    instances: new Map(),
    rawOptions: new Map(),

    init(domId, options) {
        const dom = document.getElementById(domId);
        if (!dom) return null;

        // Dispose previous instance to prevent memory leaks and duplicate timer/listener attachments
        this.dispose(domId);

        // Store deep copy of original options for dynamic theme re-rendering
        try {
            this.rawOptions.set(domId, JSON.parse(JSON.stringify(options)));
        } catch (e) {
            this.rawOptions.set(domId, options);
        }

        const chart = echarts.init(dom, null, { renderer: 'canvas' });
        const colors = getChartThemeColors();
        const enhanced = enhanceChartOptions(JSON.parse(JSON.stringify(options)), colors);

        chart.setOption(enhanced);
        this.instances.set(domId, chart);

        // Auto-resize on container size change
        const resizeObserver = new ResizeObserver(() => {
            chart.resize();
        });
        resizeObserver.observe(dom);

        return chart;
    },

    updateAllThemeColors() {
        const colors = getChartThemeColors();
        this.instances.forEach((chart, domId) => {
            const raw = this.rawOptions.get(domId);
            if (raw) {
                try {
                    const enhanced = enhanceChartOptions(JSON.parse(JSON.stringify(raw)), colors);
                    chart.setOption(enhanced);
                } catch (e) {
                    chart.setOption({
                        legend: { textStyle: { color: colors.legendColor, fontSize: 12, fontWeight: 600 } }
                    });
                }
            } else {
                chart.setOption({
                    legend: { textStyle: { color: colors.legendColor, fontSize: 12, fontWeight: 600 } }
                });
            }
        });
    },

    dispose(domId) {
        if (this.instances.has(domId)) {
            const chart = this.instances.get(domId);
            chart.dispose();
            this.instances.delete(domId);
            this.rawOptions.delete(domId);
        }
    },

    disposeAll() {
        this.instances.forEach((chart, domId) => {
            chart.dispose();
        });
        this.instances.clear();
        this.rawOptions.clear();
    }
};

window.ChartRegistry = ChartRegistry;
window.getChartThemeColors = getChartThemeColors;
window.enhanceChartOptions = enhanceChartOptions;

window.addEventListener('resize', () => {
    ChartRegistry.instances.forEach(chart => chart.resize());
});
