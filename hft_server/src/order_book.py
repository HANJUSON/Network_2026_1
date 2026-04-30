from dataclasses import dataclass, field
from typing import List, Optional, Dict
from enum import Enum
import time


class OrderSide(Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"


class OrderStatus(Enum):
    PENDING = "PENDING"
    FILLED = "FILLED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


@dataclass
class Order:
    timestamp_ns: int
    order_id: str
    symbol: str
    side: OrderSide
    price: float
    quantity: int
    order_type: OrderType
    filled_qty: int = 0
    status: OrderStatus = OrderStatus.PENDING
    
    @property
    def remaining_qty(self) -> int:
        return self.quantity - self.filled_qty
    
    def is_fully_filled(self) -> bool:
        return self.filled_qty >= self.quantity
    
    def fill(self, qty: int, exec_price: float):
        self.filled_qty += qty
        if self.is_fully_filled():
            self.status = OrderStatus.FILLED
        else:
            self.status = OrderStatus.PARTIALLY_FILLED
    
    def __repr__(self):
        return (
            f"Order(id={self.order_id}, {self.side.value} {self.symbol} "
            f"@{self.price} x {self.quantity}, filled={self.filled_qty})"
        )


@dataclass
class Trade:
    timestamp_ns: int
    buy_order_id: str
    sell_order_id: str
    symbol: str
    price: float
    quantity: int
    
    def __repr__(self):
        return (
            f"Trade({self.symbol} @{self.price} x {self.quantity}, "
            f"buy={self.buy_order_id}, sell={self.sell_order_id})"
        )


@dataclass
class OrderBook:
    symbol: str
    bids: List[Order] = field(default_factory=list)
    asks: List[Order] = field(default_factory=list)
    trades: List[Trade] = field(default_factory=list)
    
    def add_bid(self, order: Order):
        order.side = OrderSide.BUY
        self.bids.append(order)
        self.bids.sort(key=lambda x: (-x.price, x.timestamp_ns))
    
    def add_ask(self, order: Order):
        order.side = OrderSide.SELL
        self.asks.append(order)
        self.asks.sort(key=lambda x: (x.price, x.timestamp_ns))
    
    def add_order(self, order: Order):
        if order.side == OrderSide.BUY:
            self.add_bid(order)
        else:
            self.add_ask(order)
    
    def get_best_bid(self) -> Optional[Order]:
        return self.bids[0] if self.bids else None
    
    def get_best_ask(self) -> Optional[Order]:
        return self.asks[0] if self.asks else None
    
    def get_spread(self) -> Optional[float]:
        best_bid = self.get_best_bid()
        best_ask = self.get_best_ask()
        if best_bid and best_ask:
            return best_ask.price - best_bid.price
        return None
    
    def remove_order(self, order_id: str) -> bool:
        for order_list in [self.bids, self.asks]:
            for i, order in enumerate(order_list):
                if order.order_id == order_id:
                    order_list.pop(i)
                    return True
        return False
    
    def __repr__(self):
        spread = self.get_spread()
        return (
            f"OrderBook({self.symbol}): "
            f"bids={len(self.bids)}, asks={len(self.asks)}, "
            f"spread={spread}"
        )


class ExchangeState:
    def __init__(self, symbols: List[str]):
        self.symbols = symbols
        self.order_books: Dict[str, OrderBook] = {
            symbol: OrderBook(symbol=symbol) for symbol in symbols
        }
        self.orders: Dict[str, Order] = {}
        self.trades: List[Trade] = []
        self.order_counter: int = 0
    
    def get_order_book(self, symbol: str) -> Optional[OrderBook]:
        return self.order_books.get(symbol)
    
    def add_order(self, order: Order) -> Order:
        self.orders[order.order_id] = order
        book = self.get_order_book(order.symbol)
        if book:
            book.add_order(order)
        return order
    
    def get_order(self, order_id: str) -> Optional[Order]:
        return self.orders.get(order_id)
    
    def remove_order(self, order_id: str) -> bool:
        order = self.orders.get(order_id)
        if order:
            book = self.get_order_book(order.symbol)
            if book:
                book.remove_order(order_id)
            del self.orders[order_id]
            return True
        return False
    
    def add_trade(self, trade: Trade):
        self.trades.append(trade)
        book = self.get_order_book(trade.symbol)
        if book:
            book.trades.append(trade)
    
    def get_order_book_summary(self, symbol: str) -> str:
        book = self.get_order_book(symbol)
        if not book:
            return f"No order book for {symbol}"
        
        lines = [f"=== {symbol} Order Book ==="]
        lines.append(f"Best Bid: {book.get_best_bid()}")
        lines.append(f"Best Ask: {book.get_best_ask()}")
        lines.append(f"Spread: {book.get_spread()}")
        lines.append(f"Bids: {len(book.bids)}, Asks: {len(book.asks)}")
        return "\n".join(lines)
