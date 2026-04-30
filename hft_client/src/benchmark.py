import time
import random
import uuid
from typing import List, Optional
from src.protocol import OrderMessage, OrderSide, OrderType
from src.client import create_client, HFTClientBase
from src.utils import LatencyStats, ResultLogger, get_timestamp_ns


class LatencyBenchmark:
    def __init__(
        self,
        host: str,
        port: int,
        protocol: str = 'tcp',
        warmup_orders: int = 100,
        test_orders: int = 10000,
        interval_us: float = 100,
        symbols: Optional[List[str]] = None,
        nodelay: bool = True,
        timeout_ms: int = 1000,
    ):
        self.host = host
        self.port = port
        self.protocol = protocol
        self.warmup_orders = warmup_orders
        self.test_orders = test_orders
        self.interval_us = interval_us
        self.symbols = symbols or ["BTC-USD", "ETH-USD", "AAPL"]
        self.nodelay = nodelay
        self.timeout_ms = timeout_ms
        self.client: Optional[HFTClientBase] = None
        self.logger = ResultLogger()

    def _create_random_order(self, order_id: str) -> OrderMessage:
        return OrderMessage(
            timestamp_ns=get_timestamp_ns(),
            order_id=order_id,
            symbol=random.choice(self.symbols),
            side=random.choice(list(OrderSide)),
            price=round(random.uniform(10.0, 1000.0), 2),
            quantity=random.randint(1, 100),
            order_type=random.choice(list(OrderType)),
        )

    def _warmup(self):
        print(f"Warming up with {self.warmup_orders} orders...")
        for i in range(self.warmup_orders):
            order = self._create_random_order(f"WARMUP_{i}")
            try:
                self.client.send_order(order)
            except Exception:
                pass
        print("Warmup complete.")

    def run_single_test(self, num_orders: int, interval_us: float) -> LatencyStats:
        latencies: List[int] = []
        
        for i in range(num_orders):
            order = self._create_random_order(f"ORDER_{i}")
            try:
                latency_ns = self.client.send_order(order)
                latencies.append(latency_ns)
            except Exception as e:
                latencies.append(-1)
            
            if interval_us > 0:
                time.sleep(interval_us / 1_000_000)
        
        valid_latencies = [l for l in latencies if l > 0]
        return LatencyStats(valid_latencies)

    def run(self):
        print(f"\n{'='*60}")
        print(f"Starting HFT Latency Benchmark")
        print(f"{'='*60}")
        print(f"Server: {self.host}:{self.port}")
        print(f"Protocol: {self.protocol.upper()}")
        print(f"Test Orders: {self.test_orders}")
        print(f"Interval: {self.interval_us}us")
        print(f"{'='*60}\n")

        self.client = create_client(
            self.host,
            self.port,
            protocol=self.protocol,
            nodelay=self.nodelay,
            timeout_ms=self.timeout_ms,
        )
        
        try:
            self.client.connect()
            print("Connected to server.\n")
            
            if self.warmup_orders > 0:
                self._warmup()
            
            print(f"Running benchmark with {self.test_orders} orders...\n")
            stats = self.run_single_test(self.test_orders, self.interval_us)
            
            print(stats.summary())
            
            self.logger.add_result(
                protocol=self.protocol,
                num_orders=self.test_orders,
                interval_us=self.interval_us,
                stats=stats,
                metadata={
                    "host": self.host,
                    "port": self.port,
                    "symbols": self.symbols,
                }
            )
            
            return stats
            
        except ConnectionRefusedError:
            print("ERROR: Could not connect to server. Make sure the server is running.")
            return None
        except Exception as e:
            print(f"ERROR: {e}")
            return None
        finally:
            if self.client:
                self.client.disconnect()
            print("\nDisconnected.")

    def run_comparison(self, protocols: List[str] = None):
        if protocols is None:
            protocols = ['tcp', 'udp']
        
        results = {}
        
        for proto in protocols:
            print(f"\n{'#'*60}")
            print(f"# Testing {proto.upper()}")
            print(f"{'#'*60}")
            
            self.protocol = proto
            stats = self.run()
            
            if stats:
                results[proto] = stats
        
        print(f"\n{'='*60}")
        print("COMPARISON SUMMARY")
        print(f"{'='*60}")
        
        for proto, stats in results.items():
            print(f"\n{proto.upper()}:")
            print(f"  Mean:   {stats.mean_ns/1000:.3f}us")
            print(f"  Median: {stats.median_ns/1000:.3f}us")
            print(f"  P99:    {stats.p99/1000:.3f}us")
        
        return results
