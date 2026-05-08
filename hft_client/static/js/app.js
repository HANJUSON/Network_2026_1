const socket = io();
let isRunning = false;
let latencyChart = null;
let histChart = null;

const HIST_LABELS  = ['< 100', '100–200', '200–300', '300–500', '500–1000', '> 1000'];
const HIST_COLORS  = ['#00ff88', '#00d4ff', '#88d400', '#ffaa00', '#ff7722', '#ff4757'];

// ── 차트 초기화 ──────────────────────────────────────────────────────────────

function initCharts() {
    latencyChart = new Chart(
        document.getElementById('latency-chart').getContext('2d'),
        {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'Mean (μs)',
                        data: [],
                        borderColor: '#00d4ff',
                        backgroundColor: 'rgba(0,212,255,0.08)',
                        fill: true,
                        tension: 0.3,
                        pointRadius: 0,
                        borderWidth: 2,
                    },
                    {
                        label: 'P99 (μs)',
                        data: [],
                        borderColor: '#ff4757',
                        backgroundColor: 'transparent',
                        borderDash: [5, 4],
                        tension: 0.3,
                        pointRadius: 0,
                        borderWidth: 2,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: false,
                scales: {
                    x: { grid: { color: '#1e2836' }, ticks: { color: '#666', maxTicksLimit: 8 } },
                    y: { grid: { color: '#1e2836' }, ticks: { color: '#666' }, beginAtZero: true },
                },
                plugins: { legend: { labels: { color: '#888', boxWidth: 12 } } },
            },
        }
    );

    histChart = new Chart(
        document.getElementById('hist-chart').getContext('2d'),
        {
            type: 'bar',
            data: {
                labels: HIST_LABELS,
                datasets: [{
                    label: 'Orders',
                    data: [0, 0, 0, 0, 0, 0],
                    backgroundColor: HIST_COLORS,
                    borderRadius: 4,
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: false,
                scales: {
                    x: { grid: { color: '#1e2836' }, ticks: { color: '#666' } },
                    y: { grid: { color: '#1e2836' }, ticks: { color: '#666' }, beginAtZero: true },
                },
                plugins: { legend: { display: false } },
            },
        }
    );
}

// ── 헬퍼 ──────────────────────────────────────────────────────────────────────

function setConnStatus(state) {
    const ind = document.getElementById('conn-indicator');
    const txt = document.getElementById('conn-text');
    ind.className = 'indicator ' + (state || '');
    txt.textContent = { connected: 'Connected', connecting: 'Connecting…', error: 'Error' }[state] || 'Disconnected';
}

function latencyClass(us) {
    if (!us || us <= 0) return '';
    if (us < 300)  return 'lat-ok';
    if (us < 1000) return 'lat-warn';
    return 'lat-crit';
}

function fmtUs(val) {
    if (val === null || val === undefined || val === 0) return '—';
    return val >= 1000
        ? `${(val / 1000).toFixed(2)} ms`
        : `${val.toFixed(1)} μs`;
}

function setStatHtml(id, val, unit) {
    const el = document.getElementById(id);
    if (!el) return;
    el.innerHTML = unit
        ? `${val} <span class="unit">${unit}</span>`
        : `${val}`;
}

// ── 소켓 이벤트 ───────────────────────────────────────────────────────────────

socket.on('connect',    () => setConnStatus('connected'));
socket.on('disconnect', () => {
    setConnStatus('error');
    isRunning = false;
    document.getElementById('start-btn').disabled = false;
    document.getElementById('stop-btn').disabled  = true;
});

socket.on('server_connected', (d) => {
    const badge = document.getElementById('protocol-badge');
    badge.textContent  = d.protocol;
    badge.className    = `protocol-badge proto-${d.protocol.toLowerCase()}`;
});

socket.on('trading_started', () => {
    isRunning = true;
    document.getElementById('start-btn').disabled = true;
    document.getElementById('stop-btn').disabled  = false;

    // 네트워크 조건 태그 표시
    const label = document.getElementById('condition-label').value.trim();
    const tag   = document.getElementById('condition-tag');
    if (label) {
        tag.textContent = '⬡ ' + label;
        tag.classList.remove('hidden');
    } else {
        tag.classList.add('hidden');
    }

    // 차트 초기화
    latencyChart.data.labels = [];
    latencyChart.data.datasets.forEach(ds => ds.data = []);
    latencyChart.update('none');

    histChart.data.datasets[0].data = [0, 0, 0, 0, 0, 0];
    histChart.update('none');

    // stat 초기화
    ['stat-total','stat-loss','stat-ops','stat-p99',
     'stat-min','stat-mean','stat-median','stat-p95'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.innerHTML = '—';
    });
    const sub = document.getElementById('stat-sub-succ');
    if (sub) sub.textContent = 'Success: 0  |  Lost: 0';
});

socket.on('trading_stopped', () => {
    isRunning = false;
    document.getElementById('start-btn').disabled = false;
    document.getElementById('stop-btn').disabled  = true;
});

// 1초마다 서버에서 전송되는 집계 통계
socket.on('stats_update', (d) => {
    // ── 카드 1행 ──
    document.getElementById('stat-total').textContent = d.totalOrders.toLocaleString();
    const sub = document.getElementById('stat-sub-succ');
    if (sub) sub.textContent = `Success: ${d.successful.toLocaleString()}  |  Lost: ${d.timeouts.toLocaleString()}`;

    const lossEl   = document.getElementById('stat-loss');
    const lossCard = document.getElementById('card-loss');
    lossEl.innerHTML = `${d.lossRate.toFixed(2)} <span class="unit">%</span>`;
    lossCard.classList.toggle('danger', d.lossRate > 0);

    setStatHtml('stat-ops',  d.opsLastSec.toFixed(0), 'ops');

    const p99El   = document.getElementById('stat-p99');
    const p99Card = document.getElementById('card-p99');
    p99El.innerHTML = `${fmtUs(d.p99Us)}`;
    p99Card.classList.toggle('danger', d.p99Us >= 1000);

    // ── 카드 2행 ──
    document.getElementById('stat-min').innerHTML    = fmtUs(d.minUs);
    document.getElementById('stat-mean').innerHTML   = fmtUs(d.meanUs);
    document.getElementById('stat-median').innerHTML = fmtUs(d.medianUs);
    document.getElementById('stat-p95').innerHTML    = fmtUs(d.p95Us);

    // ── 지연시간 추세 차트 ──
    const now = new Date().toLocaleTimeString('ko-KR', { hour12: false });
    latencyChart.data.labels.push(now);
    latencyChart.data.datasets[0].data.push(d.meanUs);
    latencyChart.data.datasets[1].data.push(d.p99Us);
    if (latencyChart.data.labels.length > 60) {
        latencyChart.data.labels.shift();
        latencyChart.data.datasets.forEach(ds => ds.data.shift());
    }
    latencyChart.update('none');

    // ── 히스토그램 ──
    if (d.histogram && d.histogram.length === 6) {
        histChart.data.datasets[0].data = d.histogram;
        histChart.update('none');
    }
});

// 개별 주문 결과 (최대 20회/초, 로그 표시 전용)
socket.on('order_result', (d) => {
    const tbody = document.getElementById('log-body');
    const row   = document.createElement('tr');
    const t     = new Date(d.timestamp).toLocaleTimeString('ko-KR', { hour12: false });

    const isLost   = d.status === 'LOST';
    const latClass = isLost ? 'lat-crit' : latencyClass(d.latencyUs);
    const latText  = isLost ? '<span class="lat-crit">LOST</span>' : `${fmtUs(d.latencyUs)}`;

    row.innerHTML = `
        <td class="mono">${t}</td>
        <td><b>${d.symbol}</b></td>
        <td class="side-${d.side}">${d.side}</td>
        <td class="mono">${parseFloat(d.price).toFixed(2)}</td>
        <td>${d.quantity}</td>
        <td class="muted">${d.orderType}</td>
        <td class="status-${d.status}">${d.status}</td>
        <td class="mono ${latClass}">${latText}</td>
    `;

    tbody.insertBefore(row, tbody.firstChild);
    while (tbody.children.length > 100) tbody.removeChild(tbody.lastChild);
});

socket.on('connection_error', (d) => {
    setConnStatus('error');
    alert('연결 오류: ' + d.message);
    document.getElementById('start-btn').disabled = false;
    document.getElementById('stop-btn').disabled  = true;
});

// ── 컨트롤 버튼 ───────────────────────────────────────────────────────────────

document.getElementById('start-btn').addEventListener('click', () => {
    setConnStatus('connecting');
    socket.emit('start_trading', {
        host:           document.getElementById('server-host').value.trim(),
        port:           parseInt(document.getElementById('server-port').value),
        protocol:       document.getElementById('protocol').value,
        ordersPerSec:   parseInt(document.getElementById('orders-per-sec').value),
        conditionLabel: document.getElementById('condition-label').value.trim(),
    });
});

document.getElementById('stop-btn').addEventListener('click', () => {
    socket.emit('stop_trading');
});

// ── 초기화 ────────────────────────────────────────────────────────────────────
initCharts();
