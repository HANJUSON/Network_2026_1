#!/usr/bin/env python3
import socket
import threading
import json
import sys
import time
import asyncio
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent))

from src.order_book import ExchangeState
from src.handler import OrderHandler, OrderValidator, DummyHandler, OrderResponse


class HFTPServer:
    def __init__(self, config: dict):
        self.host = config["server"]["host"]
        self.tcp_port = config["server"]["port"]
        self.udp_port = config["server"].get("udp_port", config["server"]["port"])
        self.backlog = config["server"].get("backlog", 100)
        self.max_connections = config["server"].get("max_connections", 1000)
        
        self.tcp_nodelay = config["performance"].get("tcp_nodelay", True)
        self.so_reuseaddr = config["performance"].get("so_reuseaddr", True)
        self.buffer_size = config["performance"].get("buffer_size", 65536)
        
        symbols = config["order_book"]["symbols"]
        max_order_size = config["order_book"].get("max_order_size", 10000)
        min_order_size = config["order_book"].get("min_order_size", 1)
        
        self.exchange = ExchangeState(symbols)
        validator = OrderValidator(symbols, max_order_size, min_order_size)
        self.handler = OrderHandler(self.exchange, validator)
        
        self.simulation = config["simulation"]
        self.use_dummy = self.simulation.get("enabled", False)
        
        if self.use_dummy:
            min_latency = self.simulation.get("min_latency_us", 100)
            max_latency = self.simulation.get("max_latency_us", 500)
            self.dummy_handler = DummyHandler(min_latency, max_latency)
        
        self.tcp_socket: Optional[socket.socket] = None
        self.udp_socket: Optional[socket.socket] = None
        self.running = False
        self.client_count = 0
        self.udp_stats = {"requests": 0, "errors": 0}
        self.lock = threading.Lock()

    def _process_data(self, data: bytes) -> bytes:
        if self.use_dummy:
            return self.dummy_handler.handle_order(data)
        response, _ = self.handler.handle_order(data)
        return response.serialize()
    
    def start(self):
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        if self.so_reuseaddr:
            self.tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        self.tcp_socket.bind((self.host, self.tcp_port))
        self.tcp_socket.listen(self.backlog)
        
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.udp_socket.bind((self.host, self.udp_port))
        self.udp_socket.settimeout(0.1)
        
        self.running = True
        
        print(f"=" * 60)
        print(f"HFTP Server Started")
        print(f"=" * 60)
        print(f"TCP Host: {self.host}:{self.tcp_port}")
        print(f"UDP Host: {self.host}:{self.udp_port}")
        print(f"Mode: {'DUMMY (Simulation)' if self.use_dummy else 'LIVE'}")
        print(f"Buffer Size: {self.buffer_size}")
        print(f"TCP Nodelay: {self.tcp_nodelay}")
        print(f"=" * 60)
        print(f"Waiting for connections...")
        
        if self.use_dummy:
            print(f"Simulated latency: {self.simulation.get('min_latency_us')}-{self.simulation.get('max_latency_us')}us")
        
        udp_thread = threading.Thread(target=self.handle_udp, daemon=True)
        udp_thread.start()
        print(f"UDP listener started on port {self.udp_port}")
        
        try:
            while self.running:
                try:
                    client_socket, address = self.tcp_socket.accept()
                except KeyboardInterrupt:
                    break
                
                with self.lock:
                    self.client_count += 1
                
                if self.client_count > self.max_connections:
                    print(f"Max connections reached ({self.max_connections}), rejecting {address}")
                    client_socket.close()
                    continue
                
                print(f"TCP Client connected: {address} (Total: {self.client_count})")
                
                if self.tcp_nodelay:
                    client_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                
                client_thread = threading.Thread(
                    target=self.handle_tcp_client,
                    args=(client_socket, address),
                    daemon=True
                )
                client_thread.start()
                
        except Exception as e:
            print(f"Server error: {e}")
        finally:
            self.stop()
    
    def handle_tcp_client(self, client_socket: socket.socket, address):
        try:
            client_socket.settimeout(30.0)
            
            while self.running:
                try:
                    data = client_socket.recv(self.buffer_size)
                    if not data:
                        break
                    
                    response_data = self._process_data(data)
                    client_socket.sendall(response_data)
                    
                except socket.timeout:
                    break
                except Exception as e:
                    print(f"Error handling client {address}: {e}")
                    break
                    
        except ConnectionResetError:
            pass
        except Exception as e:
            print(f"Client {address} error: {e}")
        finally:
            client_socket.close()
            with self.lock:
                self.client_count -= 1
            print(f"TCP Client disconnected: {address} (Total: {self.client_count})")
    
    def handle_udp(self):
        print(f"UDP handler started")
        while self.running:
            try:
                data, address = self.udp_socket.recvfrom(self.buffer_size)
                
                with self.lock:
                    self.udp_stats["requests"] += 1
                
                response_data = self._process_data(data)
                self.udp_socket.sendto(response_data, address)
                
            except socket.timeout:
                continue
            except Exception as e:
                with self.lock:
                    self.udp_stats["errors"] += 1
                continue
    
    def stop(self):
        print("\nStopping server...")
        self.running = False
        
        if self.tcp_socket:
            try:
                self.tcp_socket.close()
            except:
                pass
        
        if self.udp_socket:
            try:
                self.udp_socket.close()
            except:
                pass
        
        print("Server stopped.")
        
        if not self.use_dummy:
            stats = self.handler.get_stats()
            print(f"\nServer Statistics:")
            print(f"  TCP Orders Processed: {stats['count']}")
            print(f"  TCP Mean Processing: {stats['mean_us']:.3f}us")
            print(f"  TCP P99 Processing:  {stats['p99_us']:.3f}us")
            print(f"  TCP Min Processing:  {stats['min_us']:.3f}us")
            print(f"  TCP Max Processing:  {stats['max_us']:.3f}us")
        
        print(f"\nUDP Statistics:")
        print(f"  UDP Requests: {self.udp_stats['requests']}")
        print(f"  UDP Errors:   {self.udp_stats['errors']}")
    
    def get_status(self) -> dict:
        return {
            "running": self.running,
            "tcp_clients": self.client_count,
            "udp_requests": self.udp_stats["requests"],
            "symbols": list(self.exchange.order_books.keys()),
        }


class AsyncUDPProtocol(asyncio.DatagramProtocol):
    def __init__(self, handler: "OrderHandler"):
        self.handler = handler
        self.transport = None

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        try:
            response, _ = self.handler.handle_order(data)
            self.transport.sendto(response.serialize(), addr)
        except Exception:
            pass

    def error_received(self, exc):
        pass


class AsyncHFTPServer:
    def __init__(self, config: dict):
        self.host = config["server"]["host"]
        self.tcp_port = config["server"]["port"]
        self.udp_port = config["server"].get("udp_port", config["server"]["port"])
        self.buffer_size = config["performance"].get("buffer_size", 65536)
        self.tcp_nodelay = config["performance"].get("tcp_nodelay", True)

        symbols = config["order_book"]["symbols"]
        max_order_size = config["order_book"].get("max_order_size", 10000)
        min_order_size = config["order_book"].get("min_order_size", 1)

        self.exchange = ExchangeState(symbols)
        validator = OrderValidator(symbols, max_order_size, min_order_size)
        self.handler = OrderHandler(self.exchange, validator)

        self.server = None
        self.udp_transport = None
        self.running = False
        self.client_count = 0
        self.udp_stats = {"requests": 0, "errors": 0}
        self.client_count_lock: Optional[asyncio.Lock] = None

    async def handle_tcp_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        sock = writer.get_extra_info('socket')
        if sock and self.tcp_nodelay:
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

        address = writer.get_extra_info('peername')
        async with self.client_count_lock:
            self.client_count += 1
            count = self.client_count
        print(f"TCP Client connected: {address} (Total: {count})")

        try:
            while self.running:
                try:
                    data = await asyncio.wait_for(reader.read(self.buffer_size), timeout=30.0)
                    if not data:
                        break

                    response, proc_time = self.handler.handle_order(data)
                    writer.write(response.serialize())
                    await writer.drain()

                except asyncio.TimeoutError:
                    break
                except Exception as e:
                    print(f"Error: {e}")
                    break

        except ConnectionResetError:
            pass
        except Exception as e:
            print(f"Client {address} error: {e}")
        finally:
            writer.close()
            await writer.wait_closed()
            async with self.client_count_lock:
                self.client_count -= 1
                count = self.client_count
            print(f"TCP Client disconnected: {address} (Total: {count})")

    async def start(self):
        self.client_count_lock = asyncio.Lock()
        self.server = await asyncio.start_server(
            self.handle_tcp_client, self.host, self.tcp_port
        )

        loop = asyncio.get_event_loop()
        self.udp_transport, _ = await loop.create_datagram_endpoint(
            lambda: AsyncUDPProtocol(self.handler),
            local_addr=(self.host, self.udp_port),
        )

        self.running = True

        print(f"=" * 60)
        print(f"Async HFTP Server Started")
        print(f"TCP Host: {self.host}:{self.tcp_port}")
        print(f"UDP Host: {self.host}:{self.udp_port}")
        print(f"TCP Nodelay: {self.tcp_nodelay}")
        print(f"=" * 60)

        try:
            async with self.server:
                await self.server.serve_forever()
        except (asyncio.CancelledError, KeyboardInterrupt):
            pass
        finally:
            await self.stop()

    async def stop(self):
        self.running = False
        if self.udp_transport:
            self.udp_transport.close()
        if self.server:
            self.server.close()
        print("Server stopped.")


def load_config(config_path: str) -> dict:
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='HFT Exchange Server')
    parser.add_argument('--config', '-c', default='config/server_settings.json',
                        help='Path to config file')
    parser.add_argument('--mode', '-m', choices=['sync', 'async'], default='sync',
                        help='Server mode (sync/async)')
    parser.add_argument('--host', default=None,
                        help='Host to bind')
    parser.add_argument('--port', '-p', type=int, default=None,
                        help='TCP port to bind')
    parser.add_argument('--udp-port', type=int, default=None,
                        help='UDP port to bind')
    parser.add_argument('--dummy', action='store_true',
                        help='Use dummy mode (simulation)')
    
    args = parser.parse_args()
    
    config_path = Path(__file__).parent / args.config
    if config_path.exists():
        config = load_config(str(config_path))
    else:
        print(f"Config file not found: {config_path}")
        config = {
            "server": {"host": "0.0.0.0", "port": 8888, "backlog": 100},
            "performance": {"tcp_nodelay": True, "so_reuseaddr": True, "buffer_size": 65536},
            "order_book": {"symbols": ["BTC-USD", "ETH-USD", "AAPL"], "max_order_size": 10000, "min_order_size": 1},
            "simulation": {"enabled": False}
        }
    
    if args.host:
        config["server"]["host"] = args.host
    if args.port:
        config["server"]["port"] = args.port
    if args.udp_port:
        config["server"]["udp_port"] = args.udp_port
    
    udp_port = config["server"].get("udp_port", config["server"]["port"])
    if udp_port != config["server"]["port"]:
        print(f"Note: UDP will run on port {udp_port}")
    
    if args.dummy:
        config["simulation"]["enabled"] = True
    
    if args.mode == 'async':
        server = AsyncHFTPServer(config)
        try:
            asyncio.run(server.start())
        except KeyboardInterrupt:
            pass
    else:
        server = HFTPServer(config)
        try:
            server.start()
        except KeyboardInterrupt:
            server.stop()


if __name__ == "__main__":
    main()
