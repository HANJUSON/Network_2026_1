from typing import List, Optional, Tuple
from src.order_book import Order, Trade, OrderBook, OrderSide, OrderStatus
import time


class OrderMatcher:
    def __init__(self, order_book: OrderBook):
        self.order_book = order_book
    
    def match_orders(self) -> List[Trade]:
        trades: List[Trade] = []
        
        while self._can_match():
            trade = self._execute_match()
            if trade:
                trades.append(trade)
            else:
                break
        
        return trades
    
    def _can_match(self) -> bool:
        if not self.order_book.bids or not self.order_book.asks:
            return False
        
        best_bid = self.order_book.get_best_bid()
        best_ask = self.order_book.get_best_ask()
        
        if not best_bid or not best_ask:
            return False
        
        return best_bid.price >= best_ask.price
    
    def _execute_match(self) -> Optional[Trade]:
        best_bid = self.order_book.get_best_bid()
        best_ask = self.order_book.get_best_ask()
        
        if not best_bid or not best_ask:
            return None
        
        if best_bid.price < best_ask.price:
            return None
        
        trade_price = best_ask.price
        trade_qty = min(best_bid.remaining_qty, best_ask.remaining_qty)
        
        if trade_qty <= 0:
            return None
        
        trade = Trade(
            timestamp_ns=time.time_ns(),
            buy_order_id=best_bid.order_id,
            sell_order_id=best_ask.order_id,
            symbol=self.order_book.symbol,
            price=trade_price,
            quantity=trade_qty,
        )
        
        best_bid.fill(trade_qty, trade_price)
        best_ask.fill(trade_qty, trade_price)
        
        if best_bid.is_fully_filled():
            self.order_book.bids.pop(0)
        
        if best_ask.is_fully_filled():
            self.order_book.asks.pop(0)
        
        return trade
    
    def match_market_order(self, order: Order) -> Tuple[List[Trade], Optional[Order]]:
        trades: List[Trade] = []

        if order.side == OrderSide.BUY:
            while self.order_book.asks and order.remaining_qty > 0:
                best_ask = self.order_book.get_best_ask()
                if not best_ask:
                    break

                trade_qty = min(order.remaining_qty, best_ask.remaining_qty)

                trade = Trade(
                    timestamp_ns=time.time_ns(),
                    buy_order_id=order.order_id,
                    sell_order_id=best_ask.order_id,
                    symbol=order.symbol,
                    price=best_ask.price,
                    quantity=trade_qty,
                )
                trades.append(trade)

                best_ask.fill(trade_qty, best_ask.price)
                order.fill(trade_qty, best_ask.price)

                if best_ask.is_fully_filled():
                    self.order_book.asks.pop(0)

        elif order.side == OrderSide.SELL:
            while self.order_book.bids and order.remaining_qty > 0:
                best_bid = self.order_book.get_best_bid()
                if not best_bid:
                    break

                trade_qty = min(order.remaining_qty, best_bid.remaining_qty)

                trade = Trade(
                    timestamp_ns=time.time_ns(),
                    buy_order_id=best_bid.order_id,
                    sell_order_id=order.order_id,
                    symbol=order.symbol,
                    price=best_bid.price,
                    quantity=trade_qty,
                )
                trades.append(trade)

                best_bid.fill(trade_qty, best_bid.price)
                order.fill(trade_qty, best_bid.price)

                if best_bid.is_fully_filled():
                    self.order_book.bids.pop(0)

        remaining_order = order if order.remaining_qty > 0 else None
        return trades, remaining_order

    def match_limit_order(self, order: Order) -> Tuple[List[Trade], Optional[Order]]:
        trades: List[Trade] = []
        
        if order.side == OrderSide.BUY:
            while (self.order_book.asks and 
                   order.remaining_qty > 0 and 
                   self.order_book.get_best_ask().price <= order.price):
                best_ask = self.order_book.get_best_ask()
                if not best_ask:
                    break
                
                trade_qty = min(order.remaining_qty, best_ask.remaining_qty)
                
                trade = Trade(
                    timestamp_ns=time.time_ns(),
                    buy_order_id=order.order_id,
                    sell_order_id=best_ask.order_id,
                    symbol=order.symbol,
                    price=best_ask.price,
                    quantity=trade_qty,
                )
                trades.append(trade)
                
                best_ask.fill(trade_qty, best_ask.price)
                order.fill(trade_qty, best_ask.price)
                
                if best_ask.is_fully_filled():
                    self.order_book.asks.pop(0)
        
        elif order.side == OrderSide.SELL:
            while (self.order_book.bids and 
                   order.remaining_qty > 0 and 
                   self.order_book.get_best_bid().price >= order.price):
                best_bid = self.order_book.get_best_bid()
                if not best_bid:
                    break
                
                trade_qty = min(order.remaining_qty, best_bid.remaining_qty)
                
                trade = Trade(
                    timestamp_ns=time.time_ns(),
                    buy_order_id=best_bid.order_id,
                    sell_order_id=order.order_id,
                    symbol=order.symbol,
                    price=best_bid.price,
                    quantity=trade_qty,
                )
                trades.append(trade)
                
                best_bid.fill(trade_qty, best_bid.price)
                order.fill(trade_qty, best_bid.price)
                
                if best_bid.is_fully_filled():
                    self.order_book.bids.pop(0)
        
        remaining_order = order if not order.is_fully_filled() else None
        
        return trades, remaining_order
