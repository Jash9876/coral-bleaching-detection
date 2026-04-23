import './style.css'

// Global Chart References
let bleachSparkline: any = null;
let redIndexGauge: any = null;

// UI Elements
const fileInput = document.getElementById('file-input') as HTMLInputElement;
const uploadTrigger = document.getElementById('upload-trigger') as HTMLDivElement;
const mainAnalysisImg = document.getElementById('main-analysis-img') as HTMLImageElement;
const loadingModal = document.getElementById('loading-modal') as HTMLDivElement;

const bleachVal = document.getElementById('bleach-val') as HTMLSpanElement;
const riVal = document.getElementById('ri-val') as HTMLDivElement;
const statusText = document.getElementById('status-text') as HTMLHeadingElement;
const statusContainer = document.getElementById('status-container') as HTMLDivElement;
const statusIcon = document.getElementById('status-icon-box') as HTMLDivElement;

// Initialization
document.addEventListener('DOMContentLoaded', () => {
    initCharts();
    updateDate();
});

uploadTrigger?.addEventListener('click', () => fileInput.click());

fileInput.addEventListener('change', (e) => {
    const file = (e.target as HTMLInputElement).files?.[0];
    if (file) handleUpload(file);
});

function updateDate() {
    const el = document.getElementById('current-date');
    if (el) {
        const d = new Date();
        el.textContent = d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
    }
}

async function handleUpload(file: File) {
    loadingModal.style.display = 'flex';
    
    const formData = new FormData();
    formData.append('image', file);

    try {
        const response = await fetch('/api/analyze', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) throw new Error('DIP Processing Timeout');

        const data = await response.json();
        updateDashboard(data);
    } catch (error: any) {
        console.error(error);
        alert(`Analysis Error: ${error.message}`);
    } finally {
        loadingModal.style.display = 'none';
    }
}

function updateDashboard(data: any) {
    // 1. Image
    const prompt = document.querySelector('.upload-prompt') as HTMLDivElement;
    if (prompt) prompt.style.display = 'none';
    
    mainAnalysisImg.src = `data:image/png;base64,${data.images.heatmap}`;
    mainAnalysisImg.style.display = 'block';

    // 2. Metrics
    bleachVal.textContent = `${data.bleach_pct.toFixed(1)}%`;
    riVal.textContent = data.red_index.toFixed(3);
    
    // 3. Status
    const status = data.status;
    statusText.textContent = status.toUpperCase();
    
    if (status.includes('Healthy')) {
        statusContainer.style.background = 'rgba(32, 201, 151, 0.08)';
        statusContainer.style.borderColor = '#20c997';
        statusText.style.color = '#20c997';
        statusIcon.textContent = '✅';
    } else {
        statusContainer.style.background = 'rgba(255, 95, 95, 0.08)';
        statusContainer.style.borderColor = '#ff5f5f';
        statusText.style.color = '#ff5f5f';
        statusIcon.textContent = '⚠️';
    }

    // 4. Update Charts
    updateCharts(data);

    // 5. Scientific Pipeline Gallery
    const stageMap: { [key: string]: string } = {
        'img-original': data.images.original,
        'img-preprocessed': data.images.preprocessed,
        'img-segmented': data.images.segmented,
        'img-mask': data.images.bleach_mask,
        'img-heatmap-full': data.images.heatmap,
        'img-edges': data.images.edges
    };

    Object.entries(stageMap).forEach(([id, base64]) => {
        const img = document.getElementById(id) as HTMLImageElement;
        if (img && base64) {
            img.src = `data:image/png;base64,${base64}`;
            img.style.display = 'block';
            const placeholder = img.parentElement?.querySelector('.stage-placeholder') as HTMLDivElement;
            if (placeholder) placeholder.style.display = 'none';
        }
    });
}

function initCharts() {
    const ApexCharts = (window as any).ApexCharts;
    if (!ApexCharts) return;

    // A. Sparkline
    const sparkOptions = {
        series: [{ data: [12, 14, 13, 15, 14, 17, 15] }],
        chart: { type: 'area', height: 40, sparkline: { enabled: true } },
        stroke: { curve: 'smooth', width: 2 },
        fill: { opacity: 0.3, colors: ['#ff5f5f'] },
        colors: ['#ff5f5f']
    };
    bleachSparkline = new ApexCharts(document.querySelector("#bleaching-mini-chart"), sparkOptions);
    bleachSparkline.render();

    // B. Red Index Gauge
    const gaugeOptions = {
        series: [0],
        chart: { height: 180, type: 'radialBar', offsetY: -10 },
        plotOptions: {
            radialBar: {
                startAngle: -135, endAngle: 135,
                dataLabels: { name: { show: false }, value: { show: false } },
                hollow: { size: '65%' },
                track: { background: '#1c2128', strokeWidth: '100%' }
            }
        },
        fill: {
            type: 'gradient',
            gradient: {
                shade: 'dark', type: 'horizontal',
                gradientToColors: ['#20c997'], stop: [0, 100]
            }
        },
        stroke: { lineCap: 'round' },
        colors: ['#ff5f5f']
    };
    redIndexGauge = new ApexCharts(document.querySelector("#red-index-gauge"), gaugeOptions);
    redIndexGauge.render();


}

function updateCharts(data: any) {
    const ApexCharts = (window as any).ApexCharts;
    if (!ApexCharts) return;

    bleachSparkline.updateSeries([{ data: [12, 14, 13, 15, 14, 17, data.bleach_pct] }]);
    
    let riPercent = ((data.red_index - 0.2) / 0.4) * 100;
    riPercent = Math.min(Math.max(riPercent, 0), 100);
    redIndexGauge.updateSeries([riPercent]);
}
