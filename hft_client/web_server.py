#!/usr/bin/env python3
import sys
import time
import random
import uuid
import threading
import queue
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from flask import Flask, render_template
from flask_socketio import SocketIO, emit

from src.protocol import OrderMessage, OrderSide, OrderType
from src.client import create_client


app = Flask(__name__)
app.config['SECRET_KEY'] = 'hft-trading-secret'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading', logger=False, engineio_logger=False)


class TradingManager:
    def __init__(self):
        self.running = False
        self.thread = None
        self.client = None
        self.order_queue = queue.Queue()
        self.stats = {
            'total_orders': 0,
            'successful': 0,
            'failed': 0,
        }
    
    def start(self, host: str, port: int, protocol: str, orders_per_sec: int):
        if self.running:
            return
        
        self.running = True
        self.stats = {'total_orders': 0, 'successful': 0, 'failed': 0}
        
        self.thread = threading.Thread(
            target=self._run_trading,
            args=(host, port, protocol, orders_per_sec),
            daemon=True
        )
        self.thread.start()
        
        print(f"[SERVER] Trading started: {protocol} to {host}:{port}, {orders_per_sec} orders/sec")
    
    def stop(self):
        print("[SERVER] Stopping trading...")
        self.running = False
        
        if self.client:
            try:
                self.client.disconnect()
            except:
                pass
            self.client = None
        
        if self.thread:
            self.thread.join(timeout=2)
        
        print("[SERVER] Trading stopped")
    
    def _run_trading(self, host: str, port: int, protocol: str, orders_per_sec: int):
        interval = 1.0 / orders_per_sec if orders_per_sec > 0 else 0
        symbols = ["BTC-USD", "ETH-USD", "AAPL", "GOOGL", "MSFT"]
        
        try:
            self.client = create_client(
                host, port, protocol,
                nodelay=True,
                timeout_ms=1000
            )
            self.client.connect()
            print(f"[SERVER] Connected to {host}:{port}")
            
            order_count = 0
            while self.running:
                start_time = time.perf_counter_ns()
                
                order = OrderMessage(
                    timestamp_ns=time.time_ns(),
                    order_id=f"{datetime.now().strftime('%H%M%S')}_{order_count}_{uuid.uuid4().hex[:6]}",
                    symbol=random.choice(symbols),
                    side=random.choice(list(OrderSide)),
                    price=round(random.uniform(10.0, 1000.0), 2),
                    quantity=random.randint(1, 100),
                    order_type=random.choice(list(OrderType)),
                )
                
                try:
                    latency_ns = self.client.send_order(order)
                    latency_us = latency_ns / 1000
                    
                    self.stats['total_orders'] += 1
                    self.stats['successful'] += 1
                    status = 'FILLED'
                    
                except Exception as e:
                    latency_us = 0
                    self.stats['total_orders'] += 1
                    self.stats['failed'] += 1
                    status = 'REJECTED'
                    print(f"[SERVER] Order failed: {e}")
                
                end_time = time.perf_counter_ns()
                total_latency_us = (end_time - start_time) / 1000
                
                order_data = {
                    'timestamp': datetime.now().isoformat(),
                    'orderId': order.order_id,
                    'symbol': order.symbol,
                    'side': order.side.value if hasattr(order.side, 'value') else str(order.side),
                    'price': order.price,
                    'quantity': order.quantity,
                    'type': order.order_type.value if hasattr(order.order_type, 'value') else str(order.order_type),
                    'status': status,
                    'latency': latency_us,
                    'totalLatency': total_latency_us,
                }
                
                socketio.emit('order_result', order_data)
                
                order_count += 1
                
                if interval > 0:
                    time.sleep(interval)
                    
        except (ConnectionRefusedError, ConnectionResetError) as e:
            print(f"[SERVER] Connection failed: {e}")
            socketio.emit('error', {'message': f'Cannot connect to {host}:{port}'})
        except Exception as e:
            print(f"[SERVER] Error: {e}")
            socketio.emit('error', {'message': str(e)})
        finally:
            if self.client:
                try:
                    self.client.disconnect()
                except:
                    pass
            self.running = False
            socketio.emit('trading_stopped', {'status': 'stopped'})


trading_manager = TradingManager()


@app.route('/')
def index():
    return render_template('trading.html')


@socketio.on('connect')
def handle_connect():
    print('[SERVER] Client connected')
    emit('connected', {'message': 'Connected to server'})


@socketio.on('disconnect')
def handle_disconnect():
    print('[SERVER] Client disconnected')


@socketio.on('start_trading')
def handle_start_trading(data):
    host = data.get('host', '127.0.0.1')
    port = data.get('port', 8888)
    protocol = data.get('protocol', 'tcp')
    orders_per_sec = data.get('ordersPerSec', 100)
    
    trading_manager.start(host, port, protocol, orders_per_sec)
    emit('trading_started', {'status': 'running'})


@socketio.on('stop_trading')
def handle_stop_trading():
    trading_manager.stop()
    emit('trading_stopped', {'status': 'stopped'})


@socketio.on('ping')
def handle_ping():
    emit('pong', {'time': datetime.now().isoformat()})


def main():
    print("=" * 60)
    print("HFT Trading Web Server")
    print("=" * 60)
    print("Open your browser and go to: http://127.0.0.1:5000")
    print("=" * 60)
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)


if __name__ == '__main__':
    main()
