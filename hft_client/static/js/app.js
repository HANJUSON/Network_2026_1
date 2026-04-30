const socket = io();

let isRunning = false;
let statsInterval = null;

let totalOrders = 0;
let ordersThisSecond = 0;
let latencies = [];
let opsHistory = [];
let lastUpdateTime = Date.now();

let latencyChart = null;
let opsChart = null;

const latencyCtx = document.getElementById('latency-chart').getContext('2d');
const opsCtx = document.getElementById('ops-chart').getContext('2d');

console.log('[CLIENT] Initializing charts...');
initCharts();

function initCharts() {
    latencyChart = new Chart(latencyCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Avg Latency (μs)',
                data: [],
                borderColor: '#00d4ff',
                backgroundColor: 'rgba(0, 212, 255, 0.1)',
                fill: true,
                tension: 0.4,
                pointRadius: 0
            }, {
                label: 'P99 Latency (μs)',
                data: [],
                borderColor: '#ff4757',
                backgroundColor: 'transparent',
                borderDash: [5, 5],
                tension: 0.4,
                pointRadius: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: false,
            interaction: {
                intersect: false,
                mode: 'index'
            },
            scales: {
                x: {
                    display: true,
                    grid: { color: '#1e2836' },
                    ticks: { color: '#666', maxTicksLimit: 10 }
                },
                y: {
                    display: true,
                    grid: { color: '#1e2836' },
                    ticks: { color: '#666' },
                    beginAtZero: true
                }
            },
            plugins: {
                legend: {
                    labels: { color: '#888' }
                }
            }
        }
    });

    opsChart = new Chart(opsCtx, {
        type: 'bar',
        data: {
            labels: [],
            datasets: [{
                label: 'Orders/sec',
                data: [],
                backgroundColor: '#00ff88',
                borderRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: false,
            scales: {
                x: {
                    display: true,
                    grid: { color: '#1e2836' },
                    ticks: { color: '#666', maxTicksLimit: 10 }
                },
                y: {
                    display: true,
                    grid: { color: '#1e2836' },
                    ticks: { color: '#666' },
                    beginAtZero: true
                }
            },
            plugins: {
                legend: {
                    labels: { color: '#888' }
                }
            }
        }
    });
    
    console.log('[CLIENT] Charts initialized');
}

function updateConnectionStatus(status) {
    const indicator = document.getElementById('connection-indicator');
    const text = document.getElementById('connection-text');
    
    indicator.className = 'indicator ' + status;
    
    switch (status) {
        case 'connected':
            text.textContent = 'Connected';
            break;
        case 'connecting':
            text.textContent = 'Connecting...';
            break;
        case 'error':
            text.textContent = 'Connection Error';
            break;
        default:
            text.textContent = 'Disconnected';
    }
}

function updateStats(data) {
    document.getElementById('total-orders').textContent = data.totalOrders.toLocaleString();
    document.getElementById('avg-latency').innerHTML = `${data.avgLatency.toFixed(2)} <span class="unit">μs</span>`;
    document.getElementById('p99-latency').innerHTML = `${data.p99Latency.toFixed(2)} <span class="unit">μs</span>`;
    document.getElementById('success-rate').innerHTML = `${data.successRate.toFixed(1)}<span class="unit">%</span>`;
}

function updateOrdersPerSec(ops) {
    document.getElementById('orders-per-sec-display').textContent = ops.toFixed(0);
}

function addLogEntry(entry) {
    const tbody = document.getElementById('log-body');
    if (!tbody) return;
    
    const row = document.createElement('tr');
    
    const time = new Date(entry.timestamp);
    const timeStr = time.toLocaleTimeString('ko-KR', { 
        hour12: false, 
        hour: '2-digit', 
        minute: '2-digit', 
        second: '2-digit'
    });
    
    row.innerHTML = `
        <td class="time">${timeStr}</td>
        <td>${String(entry.orderId).substring(0, 12)}...</td>
        <td>${entry.symbol}</td>
        <td class="status-${entry.side}">${entry.side}</td>
        <td>${parseFloat(entry.price).toFixed(2)}</td>
        <td>${entry.quantity}</td>
        <td class="status-${entry.status}">${entry.status}</td>
        <td class="latency">${parseFloat(entry.latency).toFixed(2)} μs</td>
    `;
    
    tbody.insertBefore(row, tbody.firstRow);
    
    while (tbody.children.length > 100) {
        tbody.removeChild(tbody.lastChild);
    }
}

function startTrading() {
    const host = document.getElementById('server-host').value;
    const port = document.getElementById('server-port').value;
    const protocol = document.getElementById('protocol').value;
    const ordersPerSec = parseInt(document.getElementById('orders-per-sec').value);
    
    console.log(`[CLIENT] Starting trading: ${protocol} to ${host}:${port}, ${ordersPerSec} orders/sec`);
    updateConnectionStatus('connecting');
    
    socket.emit('start_trading', {
        host: host,
        port: parseInt(port),
        protocol: protocol,
        ordersPerSec: ordersPerSec
    });
}

function stopTrading() {
    console.log('[CLIENT] Stopping trading...');
    socket.emit('stop_trading');
}

document.getElementById('start-btn').addEventListener('click', startTrading);
document.getElementById('stop-btn').addEventListener('click', stopTrading);

socket.on('connect', () => {
    console.log('[CLIENT] Connected to server');
    updateConnectionStatus('connected');
});

socket.on('disconnect', () => {
    console.log('[CLIENT] Disconnected from server');
    updateConnectionStatus('error');
    isRunning = false;
    document.getElementById('start-btn').disabled = false;
    document.getElementById('stop-btn').disabled = true;
    stopStatsUpdate();
});

socket.on('connected', (data) => {
    console.log('[CLIENT] Server confirmed connection:', data);
});

socket.on('trading_started', (data) => {
    console.log('[CLIENT] Trading started:', data);
    isRunning = true;
    totalOrders = 0;
    ordersThisSecond = 0;
    latencies = [];
    opsHistory = [];
    
    document.getElementById('start-btn').disabled = true;
    document.getElementById('stop-btn').disabled = false;
    document.getElementById('server-status').textContent = 'Running';
    
    startStatsUpdate();
});

socket.on('trading_stopped', (data) => {
    console.log('[CLIENT] Trading stopped:', data);
    isRunning = false;
    
    document.getElementById('start-btn').disabled = false;
    document.getElementById('stop-btn').disabled = true;
    document.getElementById('server-status').textContent = 'Stopped';
    
    stopStatsUpdate();
});

socket.on('order_result', (data) => {
    console.log('[CLIENT] Order result:', data.latency, 'μs');
    
    const latency = parseFloat(data.latency) || 0;
    
    totalOrders++;
    ordersThisSecond++;
    latencies.push(latency);
    
    if (latencies.length > 1000) {
        latencies = latencies.slice(-1000);
    }
    
    addLogEntry(data);
});

socket.on('error', (data) => {
    console.error('[CLIENT] Error:', data.message);
    alert('Error: ' + data.message);
});

socket.on('pong', (data) => {
    console.log('[CLIENT] Pong received:', data);
});

function startStatsUpdate() {
    lastUpdateTime = Date.now();
    
    console.log('[CLIENT] Starting stats update interval');
    
    statsInterval = setInterval(() => {
        const now = Date.now();
        const elapsed = (now - lastUpdateTime) / 1000;
        lastUpdateTime = now;
        
        const ops = ordersThisSecond / Math.max(elapsed, 0.001);
        opsHistory.push(ops);
        if (opsHistory.length > 60) {
            opsHistory.shift();
        }
        
        ordersThisSecond = 0;
        
        const sortedLatencies = [...latencies].sort((a, b) => a - b);
        const avg = latencies.length > 0 ? latencies.reduce((a, b) => a + b, 0) / latencies.length : 0;
        const p99 = sortedLatencies[Math.floor(sortedLatencies.length * 0.99)] || 0;
        const successRate = totalOrders > 0 ? (latencies.length / totalOrders * 100) : 100;
        
        updateStats({
            totalOrders: totalOrders,
            avgLatency: avg,
            p99Latency: p99,
            successRate: successRate
        });
        
        updateOrdersPerSec(ops);
        updateCharts(avg, p99, ops);
        
        console.log(`[CLIENT] Stats: orders=${totalOrders}, avg=${avg.toFixed(2)}μs, ops=${ops.toFixed(0)}`);
    }, 1000);
}

function stopStatsUpdate() {
    if (statsInterval) {
        clearInterval(statsInterval);
        statsInterval = null;
        console.log('[CLIENT] Stats update interval stopped');
    }
}

function updateCharts(avgLatency, p99Latency, ops) {
    const now = new Date().toLocaleTimeString('ko-KR', { 
        hour12: false, 
        hour: '2-digit', 
        minute: '2-digit', 
        second: '2-digit'
    });
    
    latencyChart.data.labels.push(now);
    latencyChart.data.datasets[0].data.push(avgLatency);
    latencyChart.data.datasets[1].data.push(p99Latency);
    
    if (latencyChart.data.labels.length > 60) {
        latencyChart.data.labels.shift();
        latencyChart.data.datasets[0].data.shift();
        latencyChart.data.datasets[1].data.shift();
    }
    latencyChart.update('none');
    
    opsChart.data.labels.push(now);
    opsChart.data.datasets[0].data.push(ops);
    
    if (opsChart.data.labels.length > 60) {
        opsChart.data.labels.shift();
        opsChart.data.datasets[0].data.shift();
    }
    opsChart.update('none');
}

console.log('[CLIENT] App initialized');
