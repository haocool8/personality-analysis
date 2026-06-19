/**
 * 图表渲染模块 — 使用 Chart.js v4
 */

const ChartRenderer = {
    _charts: {},

    destroyAll() {
        Object.values(this._charts).forEach(c => c.destroy());
        this._charts = {};
    },

    _wrapData(chartData) {
        // chartData from server has {type, labels, datasets, options}
        // Chart.js needs {type, data: {labels, datasets}, options}
        return {
            type: chartData.type,
            data: {
                labels: chartData.labels || [],
                datasets: chartData.datasets || [],
            },
        };
    },

    renderRadar(canvasId, chartData) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;
        const ctx = canvas.getContext('2d');

        const cfg = this._wrapData(chartData);
        cfg.options = {
            responsive: true,
            maintainAspectRatio: true,
            scales: {
                r: {
                    min: 0,
                    max: 100,
                    ticks: { stepSize: 20, backdropColor: 'transparent' },
                    pointLabels: { font: { size: 13 } },
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: '大五人格剖面图（百分位）',
                    font: { size: 16 },
                },
            },
        };
        this._charts[canvasId] = new Chart(ctx, cfg);
    },

    renderHorizontalBar(canvasId, chartData) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;
        const ctx = canvas.getContext('2d');

        const cfg = this._wrapData(chartData);
        cfg.options = {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: { min: 1, max: 5, title: { display: true, text: '平均分' } },
            },
            plugins: {
                title: {
                    display: true,
                    text: '15个侧面详细得分',
                    font: { size: 16 },
                },
                legend: { display: false },
            },
        };
        canvas.style.height = (cfg.data.labels.length * 36 + 40) + 'px';
        this._charts[canvasId] = new Chart(ctx, cfg);
    },

    renderSD3Bar(canvasId, chartData) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;
        const ctx = canvas.getContext('2d');

        const cfg = this._wrapData(chartData);
        cfg.options = {
            responsive: true,
            maintainAspectRatio: true,
            scales: {
                y: { min: 1, max: 5, title: { display: true, text: '平均分' } },
            },
            plugins: {
                title: {
                    display: true,
                    text: '黑暗三联征得分',
                    font: { size: 16 },
                },
                legend: { display: false },
            },
        };
        this._charts[canvasId] = new Chart(ctx, cfg);
    },

    renderAttachmentScatter(canvasId, chartData) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;
        const ctx = canvas.getContext('2d');

        const point = chartData.point;

        this._charts[canvasId] = new Chart(ctx, {
            type: 'scatter',
            data: {
                datasets: [{
                    label: '你的位置',
                    data: [{ x: point.x, y: point.y }],
                    backgroundColor: 'rgba(233, 69, 96, 1)',
                    borderColor: 'rgba(233, 69, 96, 1)',
                    pointRadius: 10,
                    pointHoverRadius: 12,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        min: 1, max: 7,
                        title: { display: true, text: '焦虑维度 →' },
                    },
                    y: {
                        min: 1, max: 7,
                        title: { display: true, text: '回避维度 →' },
                    },
                },
                plugins: {
                    title: {
                        display: true,
                        text: `依恋风格：${chartData.quadrant || '未知'}`,
                        font: { size: 16 },
                    },
                },
            },
        });
    },
};
