from enum import Enum


class OrderSide(Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"


class OrderMessage:
    def __init__(
        self,
        timestamp_ns: int,
        order_id: str,
        symbol: str,
        side: OrderSide,
        price: float,
        quantity: int,
        order_type: OrderType,
    ):
        self.timestamp_ns = timestamp_ns
        self.order_id = order_id
        self.symbol = symbol
        self.side = side
        self.price = price
        self.quantity = quantity
        self.order_type = order_type

    def serialize(self) -> bytes:
        side_str = self.side.value if hasattr(self.side, 'value') else str(self.side)
        order_type_str = self.order_type.value if hasattr(self.order_type, 'value') else str(self.order_type)
        
        data = (
            f"{self.timestamp_ns}|"
            f"{self.order_id}|"
            f"{self.symbol}|"
            f"{side_str}|"
            f"{self.price}|"
            f"{self.quantity}|"
            f"{order_type_str}"
        )
        return data.encode('utf-8')

    @classmethod
    def deserialize(cls, data: bytes) -> "OrderMessage":
        parts = data.decode('utf-8').split('|')
        return cls(
            timestamp_ns=int(parts[0]),
            order_id=parts[1],
            symbol=parts[2],
            side=OrderSide(parts[3]),
            price=float(parts[4]),
            quantity=int(parts[5]),
            order_type=OrderType(parts[6]),
        )

    def __repr__(self):
        return (
            f"OrderMessage(timestamp={self.timestamp_ns}, id={self.order_id}, "
            f"symbol={self.symbol}, side={self.side}, price={self.price}, "
            f"qty={self.quantity}, type={self.order_type})"
        )


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
        data = (
            f"{self.timestamp_ns}|"
            f"{self.order_id}|"
            f"{self.status}|"
            f"{self.executed_price}|"
            f"{self.executed_qty}|"
            f"{self.message}"
        )
        return data.encode('utf-8')

    @classmethod
    def deserialize(cls, data: bytes) -> "OrderResponse":
        parts = data.decode('utf-8').split('|')
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
