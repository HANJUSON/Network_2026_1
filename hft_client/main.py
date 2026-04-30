#!/usr/bin/env python3
import sys
import json
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.benchmark import LatencyBenchmark
from src.utils import ResultLogger


def load_config(config_path: str) -> dict:
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser(description='HFT Client Latency Benchmark')
    parser.add_argument('--config', '-c', default='config/settings.json',
                        help='Path to config file')
    parser.add_argument('--protocol', '-p', choices=['tcp', 'udp', 'both'],
                        default='both', help='Protocol to test')
    parser.add_argument('--orders', '-n', type=int,
                        help='Number of test orders')
    parser.add_argument('--interval', '-i', type=float,
                        help='Interval between orders in microseconds')
    parser.add_argument('--warmup', '-w', type=int,
                        help='Number of warmup orders')
    
    args = parser.parse_args()
    
    config_path = Path(__file__).parent / args.config
    if config_path.exists():
        config = load_config(str(config_path))
    else:
        print(f"Warning: Config file not found at {config_path}, using defaults")
        config = {
            "server": {"host": "127.0.0.1", "port": 8888, "protocol": "tcp"},
            "client": {"buffer_size": 65536, "tcp_nodelay": True, "socket_timeout_ms": 1000},
            "benchmark": {"warmup_orders": 100, "test_orders": 10000, "interval_us": 100},
            "symbols": ["BTC-USD", "ETH-USD", "AAPL"],
        }
    
    server_config = config.get("server", {})
    client_config = config.get("client", {})
    benchmark_config = config.get("benchmark", {})
    
    host = server_config.get("host", "127.0.0.1")
    port = server_config.get("port", 8888)
    default_protocol = server_config.get("protocol", "tcp")
    
    warmup_orders = args.warmup if args.warmup is not None else benchmark_config.get("warmup_orders", 100)
    test_orders = args.orders if args.orders is not None else benchmark_config.get("test_orders", 10000)
    interval_us = args.interval if args.interval is not None else benchmark_config.get("interval_us", 100)
    
    symbols = config.get("symbols", ["BTC-USD"])
    nodelay = client_config.get("tcp_nodelay", True)
    timeout_ms = client_config.get("socket_timeout_ms", 1000)
    
    benchmark = LatencyBenchmark(
        host=host,
        port=port,
        protocol=default_protocol,
        warmup_orders=warmup_orders,
        test_orders=test_orders,
        interval_us=interval_us,
        symbols=symbols,
        nodelay=nodelay,
        timeout_ms=timeout_ms,
    )
    
    if args.protocol == 'both':
        results = benchmark.run_comparison(['tcp', 'udp'])
    else:
        benchmark.protocol = args.protocol
        results = {'single': benchmark.run()}
    
    save_results = benchmark_config.get("save_results", True)
    if save_results:
        results_dir = Path(__file__).parent / benchmark_config.get("results_dir", "results")
        results_dir.mkdir(exist_ok=True)
        benchmark.logger.results_dir = str(results_dir)
        filepath = benchmark.logger.save()
        print(f"\nResults saved to: {filepath}")


if __name__ == "__main__":
    main()
