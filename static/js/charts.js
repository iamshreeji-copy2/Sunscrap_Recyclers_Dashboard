// Apache ECharts Manager for Sunscrap Solar SCADA
const ChartRegistry = {
    instances: new Map(),

    init(domId, options) {
        const dom = document.getElementById(domId);
        if (!dom) return null;

        // Dispose previous instance to prevent memory leaks and duplicate timer/listener attachments
        this.dispose(domId);

        const chart = echarts.init(dom, null, { renderer: 'canvas' });
        chart.setOption(options);
        this.instances.set(domId, chart);

        // Auto-resize on container size change
        const resizeObserver = new ResizeObserver(() => {
            chart.resize();
        });
        resizeObserver.observe(dom);

        return chart;
    },

    dispose(domId) {
        if (this.instances.has(domId)) {
            const chart = this.instances.get(domId);
            chart.dispose();
            this.instances.delete(domId);
        }
    },

    disposeAll() {
        this.instances.forEach((chart, domId) => {
            chart.dispose();
        });
        this.instances.clear();
    }
};

window.addEventListener('resize', () => {
    ChartRegistry.instances.forEach(chart => chart.resize());
});
