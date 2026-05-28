from typing import Optional, Tuple, List
import time
import uuid
from src.order_book import (
    Order, OrderStatus, OrderSide, 
    OrderType, ExchangeState
)
from src.matcher import OrderMatcher


class OrderValidator:
    def __init__(self, symbols: List[str], max_order_size: int, min_order_size: int):
        self.symbols = symbols
        self.max_order_size = max_order_size
        self.min_order_size = min_order_size
    
    def validate(self, order: Order) -> Tuple[bool, str]:
        if not order.symbol or order.symbol not in self.symbols:
            return False, f"Invalid symbol: {order.symbol}"
        
        if order.price <= 0:
            return False, "Price must be positive"
        
        if order.quantity < self.min_order_size:
            return False, f"Quantity must be at least {self.min_order_size}"
        
        if order.quantity > self.max_order_size:
            return False, f"Quantity exceeds maximum: {self.max_order_size}"
        
        if order.order_type not in [OrderType.MARKET, OrderType.LIMIT]:
            return False, f"Invalid order type: {order.order_type}"
        
        if order.side not in [OrderSide.BUY, OrderSide.SELL]:
            return False, f"Invalid side: {order.side}"
        
        return True, "OK"


class OrderResponse:
    def __init__(
        self,
        timestamp_ns: int,
        order_id: str,
        status: str,
        executed_price: float = 0.0,
        executed_qty: int = 0,
        message: str = "",
    ):
        self.timestamp_ns = timestamp_ns
        self.order_id = order_id
        self.status = status
        self.executed_price = executed_price
        self.executed_qty = executed_qty
        self.message = message
    
    def serialize(self) -> bytes:
        safe_msg = self.message.replace('|', '/')
        data = (
            f"{self.timestamp_ns}|"
            f"{self.order_id}|"
            f"{self.status}|"
            f"{self.executed_price}|"
            f"{self.executed_qty}|"
            f"{safe_msg}"
        )
        return data.encode('utf-8')

    @classmethod
    def deserialize(cls, data: bytes) -> "OrderResponse":
        parts = data.decode('utf-8').split('|', 5)
        return cls(
            timestamp_ns=int(parts[0]),
            order_id=parts[1],
            status=parts[2],
            executed_price=float(parts[3]) if parts[3] else 0.0,
            executed_qty=int(parts[4]) if parts[4] else 0,
            message=parts[5] if len(parts) > 5 else "",
        )
    
    def __repr__(self):
        return (
            f"OrderResponse(id={self.order_id}, status={self.status}, "
            f"exec_price={self.executed_price}, exec_qty={self.executed_qty})"
        )


class OrderHandler:
    def __init__(self, exchange_state: ExchangeState, validator: OrderValidator):
        self.exchange = exchange_state
        self.validator = validator
        self.order_counter = 0
        self.processing_times: List[int] = []
    
    def parse_order(self, data: bytes) -> Optional[Order]:
        try:
            parts = data.decode('utf-8').split('|')
            if len(parts) < 7:
                return None
            
            order = Order(
                timestamp_ns=int(parts[0]),
                order_id=parts[1],
                symbol=parts[2],
                side=OrderSide(parts[3]),
                price=float(parts[4]),
                quantity=int(parts[5]),
                order_type=OrderType(parts[6]),
            )
            return order
        except Exception as e:
            print(f"Failed to parse order: {e}")
            return None
    
    def handle_order(self, data: bytes) -> Tuple[OrderResponse, int]:
        recv_time = time.perf_counter_ns()
        
        order = self.parse_order(data)
        if not order:
            response = OrderResponse(
                timestamp_ns=time.time_ns(),
                order_id="UNKNOWN",
                status="REJECTED",
                message="Failed to parse order",
            )
            return response, 0
        
        is_valid, msg = self.validator.validate(order)
        if not is_valid:
            order.status = OrderStatus.REJECTED
            response = OrderResponse(
                timestamp_ns=time.time_ns(),
                order_id=order.order_id,
                status="REJECTED",
                message=msg,
            )
            return response, 0
        
        response, exec_info = self._execute_order(order)
        
        end_time = time.perf_counter_ns()
        processing_time = end_time - recv_time
        self.processing_times.append(processing_time)
        
        return response, processing_time
    
    def _execute_order(self, order: Order) -> Tuple[OrderResponse, dict]:
        book = self.exchange.get_order_book(order.symbol)
        if not book:
            return OrderResponse(
                timestamp_ns=time.time_ns(),
                order_id=order.order_id,
                status="REJECTED",
                message=f"No order book for {order.symbol}",
            ), {}
        
        matcher = OrderMatcher(book)
        
        if order.order_type == OrderType.MARKET:
            trades, remaining = matcher.match_market_order(order)
        else:
            trades, remaining = matcher.match_limit_order(order)
        
        exec_price = 0.0
        exec_qty = 0
        for trade in trades:
            self.exchange.add_trade(trade)
            exec_price = trade.price
            exec_qty += trade.quantity
        
        if order.order_type == OrderType.MARKET:
            # MARKET 주문 잔량은 호가창에 등록하지 않고 취소
            if exec_qty == 0:
                status = "REJECTED"
            elif exec_qty < order.quantity:
                status = "PARTIALLY_FILLED"
            else:
                status = "FILLED"
        elif remaining:
            self.exchange.add_order(order)
            status = "PARTIALLY_FILLED" if exec_qty > 0 else "PENDING"
        else:
            status = "FILLED"

        response = OrderResponse(
            timestamp_ns=time.time_ns(),
            order_id=order.order_id,
            status=status,
            executed_price=exec_price,
            executed_qty=exec_qty,
            message=f"Trades: {len(trades)}",
        )
        
        return response, {"trades": len(trades), "exec_qty": exec_qty}
    
    def get_stats(self) -> dict:
        if not self.processing_times:
            return {"count": 0, "mean_us": 0, "p99_us": 0}
        
        sorted_times = sorted(self.processing_times)
        p99_idx = int(len(sorted_times) * 0.99)
        
        return {
            "count": len(self.processing_times),
            "mean_us": sum(self.processing_times) / len(self.processing_times) / 1000,
            "p99_us": sorted_times[p99_idx] / 1000 if sorted_times else 0,
            "min_us": min(self.processing_times) / 1000 if self.processing_times else 0,
            "max_us": max(self.processing_times) / 1000 if self.processing_times else 0,
        }


class DummyHandler:
    def __init__(self, min_latency_us: float = 0, max_latency_us: float = 0):
        self.min_latency_us = min_latency_us
        self.max_latency_us = max_latency_us
        self.order_count = 0
    
    def parse_order(self, data: bytes) -> Optional[Order]:
        try:
            parts = data.decode('utf-8').split('|')
            if len(parts) < 7:
                return None
            
            order = Order(
                timestamp_ns=int(parts[0]),
                order_id=parts[1],
                symbol=parts[2],
                side=OrderSide(parts[3]),
                price=float(parts[4]),
                quantity=int(parts[5]),
                order_type=OrderType(parts[6]),
            )
            return order
        except Exception:
            return None
    
    def handle_order(self, data: bytes) -> bytes:
        order = self.parse_order(data)
        if not order:
            response = OrderResponse(
                timestamp_ns=time.time_ns(),
                order_id="UNKNOWN",
                status="REJECTED",
                message="Parse error",
            )
        else:
            import random
            latency_us = random.uniform(self.min_latency_us, self.max_latency_us)
            # Windows time.sleep()는 sub-ms 정밀도가 부정확 → busy-wait 하이브리드
            target = time.perf_counter() + latency_us / 1_000_000
            if latency_us > 1000:
                time.sleep((latency_us - 1000) / 1_000_000)
            while time.perf_counter() < target:
                pass
            
            self.order_count += 1
            response = OrderResponse(
                timestamp_ns=time.time_ns(),
                order_id=order.order_id,
                status="FILLED",
                executed_price=order.price,
                executed_qty=order.quantity,
            )
        
        return response.serialize()
