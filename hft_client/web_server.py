#!/usr/bin/env python3
import sys
import os
import time
import random
import uuid
import threading
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from flask import Flask, render_template
from flask_socketio import SocketIO, emit

from src.protocol import OrderMessage, OrderSide, OrderType
from src.client import create_client


app = Flask(__name__)
app.config['SECRET_KEY'] = 'hft-trading-secret'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading',
                    logger=False, engineio_logger=False)

DEFAULT_HOST = os.environ.get('SERVER_HOST', '127.0.0.1')

# 히스토그램 버킷 경계 (μs)
HIST_BOUNDS = [100, 200, 300, 500, 1000]


class TradingManager:
    def __init__(self):
        self.running = False
        self.thread = None
        self.client = None
        self.protocol = 'tcp'
        self.condition_label = ''

        self._lock = threading.Lock()
        self._total = 0
        self._successful = 0
        self._timeouts = 0
        self._latencies_ns = []     # 최대 2000개 rolling window

        self._sec_count = 0
        self._last_stats_time = 0.0
        self._last_order_emit_time = 0.0

    def start(self, host, port, protocol, orders_per_sec, condition_label=''):
        if self.running:
            return
        self.protocol = protocol
        self.condition_label = condition_label
        with self._lock:
            self._total = 0
            self._successful = 0
            self._timeouts = 0
            self._latencies_ns = []
            self._sec_count = 0
        self.running = True
        self._last_stats_time = time.perf_counter()
        self._last_order_emit_time = 0.0

        self.thread = threading.Thread(
            target=self._run,
            args=(host, port, protocol, orders_per_sec),
            daemon=True,
        )
        self.thread.start()

    def stop(self):
        with self._lock:
            self.running = False
            client = self.client
            self.client = None
        if client:
            try:
                client.disconnect()
            except Exception:
                pass
        if self.thread:
            self.thread.join(timeout=2)

    def _build_stats(self, ops):
        with self._lock:
            window = list(self._latencies_ns)
            total = self._total
            successful = self._successful
            timeouts = self._timeouts

        hist = [0] * (len(HIST_BOUNDS) + 1)

        if window:
            sorted_w = sorted(window)
            n = len(sorted_w)

            def pct(p):
                return round(sorted_w[min(int(n * p / 100), n - 1)] / 1000, 2)

            for ns in window:
                us = ns / 1000
                placed = False
                for i, b in enumerate(HIST_BOUNDS):
                    if us < b:
                        hist[i] += 1
                        placed = True
                        break
                if not placed:
                    hist[-1] += 1

            return {
                'protocol': self.protocol.upper(),
                'conditionLabel': self.condition_label,
                'totalOrders': total,
                'successful': successful,
                'timeouts': timeouts,
                'lossRate': round(timeouts / max(total, 1) * 100, 2),
                'opsLastSec': round(ops, 1),
                'minUs': round(sorted_w[0] / 1000, 2),
                'maxUs': round(sorted_w[-1] / 1000, 2),
                'meanUs': round(sum(sorted_w) / n / 1000, 2),
                'medianUs': pct(50),
                'p95Us': pct(95),
                'p99Us': pct(99),
                'histogram': hist,
            }
        else:
            return {
                'protocol': self.protocol.upper(),
                'conditionLabel': self.condition_label,
                'totalOrders': total,
                'successful': successful,
                'timeouts': timeouts,
                'lossRate': 0.0,
                'opsLastSec': round(ops, 1),
                'minUs': 0, 'maxUs': 0, 'meanUs': 0,
                'medianUs': 0, 'p95Us': 0, 'p99Us': 0,
                'histogram': hist,
            }

    def _run(self, host, port, protocol, orders_per_sec):
        interval = 1.0 / orders_per_sec if orders_per_sec > 0 else 0
        symbols = ["BTC-USD", "ETH-USD", "AAPL", "GOOGL", "MSFT"]
        order_idx = 0

        try:
            client = create_client(host, port, protocol,
                                   nodelay=True, timeout_ms=2000)
            client.connect()
            # 연결 사이에 stop()이 호출됐으면 즉시 정리
            with self._lock:
                if not self.running:
                    try:
                        client.disconnect()
                    except Exception:
                        pass
                    return
                self.client = client
            socketio.emit('server_connected', {
                'host': host, 'port': port, 'protocol': protocol.upper(),
            })

            sec_count = 0

            while self.running:
                order = OrderMessage(
                    timestamp_ns=time.time_ns(),
                    order_id=f"{order_idx}_{uuid.uuid4().hex[:4]}",
                    symbol=random.choice(symbols),
                    side=random.choice(list(OrderSide)),
                    price=round(random.uniform(10.0, 1000.0), 2),
                    quantity=random.randint(1, 100),
                    order_type=random.choice(list(OrderType)),
                )

                try:
                    latency_ns = self.client.send_order(order)
                except Exception:
                    latency_ns = -1

                now = time.perf_counter()

                with self._lock:
                    self._total += 1
                    self._sec_count += 1
                    sec_count += 1
                    if latency_ns == -1:
                        self._timeouts += 1
                        status = 'LOST'
                        latency_us = 0.0
                    else:
                        self._successful += 1
                        latency_us = latency_ns / 1000
                        self._latencies_ns.append(latency_ns)
                        if len(self._latencies_ns) > 2000:
                            self._latencies_ns = self._latencies_ns[-2000:]
                        status = 'FILLED'

                # 개별 주문 이벤트: 최대 20회/초로 제한 (로그 표시용)
                if now - self._last_order_emit_time >= 0.05:
                    socketio.emit('order_result', {
                        'timestamp': datetime.now().isoformat(),
                        'orderId': order.order_id,
                        'symbol': order.symbol,
                        'side': order.side.value,
                        'price': order.price,
                        'quantity': order.quantity,
                        'orderType': order.order_type.value,
                        'status': status,
                        'latencyUs': round(latency_us, 2),
                        'protocol': protocol.upper(),
                    })
                    self._last_order_emit_time = now

                # 통계 업데이트: 1초마다
                elapsed = now - self._last_stats_time
                if elapsed >= 1.0:
                    ops = sec_count / elapsed
                    sec_count = 0
                    with self._lock:
                        self._sec_count = 0
                    self._last_stats_time = now
                    socketio.emit('stats_update', self._build_stats(ops))

                order_idx += 1

                if interval > 0:
                    time.sleep(interval)

        except (ConnectionRefusedError, ConnectionResetError, OSError) as e:
            socketio.emit('connection_error', {
                'message': f'{host}:{port} 연결 실패 ({protocol.upper()}): {e}'
            })
        except Exception as e:
            socketio.emit('connection_error', {'message': str(e)})
        finally:
            with self._lock:
                cli = self.client
                self.client = None
                self.running = False
            if cli:
                try:
                    cli.disconnect()
                except Exception:
                    pass
            socketio.emit('trading_stopped', {'status': 'stopped'})


trading_manager = TradingManager()


@app.route('/')
def index():
    return render_template('trading.html', default_host=DEFAULT_HOST)


@socketio.on('connect')
def handle_connect():
    emit('connected', {'status': 'ok'})


@socketio.on('disconnect')
def handle_disconnect():
    pass


@socketio.on('start_trading')
def handle_start_trading(data):
    trading_manager.start(
        host=data.get('host', '127.0.0.1'),
        port=int(data.get('port', 8888)),
        protocol=data.get('protocol', 'tcp'),
        orders_per_sec=int(data.get('ordersPerSec', 10)),
        condition_label=data.get('conditionLabel', ''),
    )
    emit('trading_started', {'status': 'running'})


@socketio.on('stop_trading')
def handle_stop_trading():
    trading_manager.stop()
    emit('trading_stopped', {'status': 'stopped'})


def main():
    print("=" * 60)
    print("HFT Trading Dashboard")
    print("=" * 60)
    print(f"Default server host: {DEFAULT_HOST}")
    print("Open: http://127.0.0.1:5000")
    print("=" * 60)
    socketio.run(app, host='0.0.0.0', port=5000, debug=False,
                 allow_unsafe_werkzeug=True)


if __name__ == '__main__':
    main()
