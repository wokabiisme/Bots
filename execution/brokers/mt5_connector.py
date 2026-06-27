"""MetaTrader 5 broker connector."""

import asyncio
import MetaTrader5 as mt5
from typing import List, Dict, Optional, Any
from datetime import datetime
from loguru import logger
from execution.brokers.base import (
    BaseBroker, Order, Position, AccountInfo, 
    OrderType, OrderSide, OrderStatus
)


class MT5Connector(BaseBroker):
    """MetaTrader 5 broker connector."""
    
    def __init__(
        self,
        login: int,
        password: str,
        server: str,
        path: Optional[str] = None
    ):
        """Initialize MT5 connector.
        
        Args:
            login: MT5 login
            password: MT5 password
            server: MT5 server name
            path: Path to MT5 terminal (optional)
        """
        super().__init__("MetaTrader5")
        self.login = login
        self.password = password
        self.server = server
        self.path = path
    
    async def connect(self) -> bool:
        """Connect to MT5.
        
        Returns:
            True if connection successful
        """
        try:
            # Initialize MT5
            if not mt5.initialize(path=self.path):
                logger.error(f"Failed to initialize MT5: {mt5.last_error()}")
                return False
            
            # Login
            if not mt5.login(self.login, self.password, self.server):
                logger.error(f"Failed to login to MT5: {mt5.last_error()}")
                return False
            
            self.is_connected = True
            logger.info(f"Connected to MT5 - Login: {self.login}")
            return True
        
        except Exception as e:
            logger.error(f"MT5 connection error: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """Disconnect from MT5.
        
        Returns:
            True if disconnection successful
        """
        try:
            mt5.shutdown()
            self.is_connected = False
            logger.info("Disconnected from MT5")
            return True
        except Exception as e:
            logger.error(f"MT5 disconnection error: {e}")
            return False
    
    async def get_account_info(self) -> AccountInfo:
        """Get MT5 account information.
        
        Returns:
            Account information
        """
        try:
            info = mt5.account_info()
            return AccountInfo(
                balance=info.balance,
                equity=info.equity,
                free_balance=info.balance - info.equity,
                used_balance=info.equity,
                margin=info.margin,
                free_margin=info.margin_free,
                margin_level=info.margin_level,
                currency=info.currency
            )
        except Exception as e:
            logger.error(f"Error getting MT5 account info: {e}")
            return AccountInfo(balance=0, equity=0, free_balance=0, 
                             used_balance=0, margin=0, free_margin=0, margin_level=0)
    
    async def get_balance(self) -> float:
        """Get MT5 balance.
        
        Returns:
            Account balance
        """
        try:
            info = mt5.account_info()
            return info.balance
        except Exception as e:
            logger.error(f"Error getting MT5 balance: {e}")
            return 0.0
    
    async def get_positions(self) -> List[Position]:
        """Get all MT5 positions.
        
        Returns:
            List of positions
        """
        try:
            positions = mt5.positions_get()
            result = []
            
            for pos in positions:
                result.append(Position(
                    symbol=pos.symbol,
                    quantity=pos.volume,
                    entry_price=pos.price_open,
                    current_price=pos.price_current,
                    unrealized_pnl=pos.profit,
                    unrealized_pnl_percent=(pos.profit / (pos.price_open * pos.volume)) * 100,
                    side=OrderSide.BUY if pos.type == 0 else OrderSide.SELL
                ))
            
            return result
        except Exception as e:
            logger.error(f"Error getting MT5 positions: {e}")
            return []
    
    async def get_position(self, symbol: str) -> Optional[Position]:
        """Get specific MT5 position.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Position or None
        """
        try:
            positions = mt5.positions_get(symbol=symbol)
            if positions and len(positions) > 0:
                pos = positions[0]
                return Position(
                    symbol=pos.symbol,
                    quantity=pos.volume,
                    entry_price=pos.price_open,
                    current_price=pos.price_current,
                    unrealized_pnl=pos.profit,
                    unrealized_pnl_percent=(pos.profit / (pos.price_open * pos.volume)) * 100,
                    side=OrderSide.BUY if pos.type == 0 else OrderSide.SELL
                )
            return None
        except Exception as e:
            logger.error(f"Error getting MT5 position for {symbol}: {e}")
            return None
    
    async def place_order(
        self,
        symbol: str,
        side: OrderSide,
        quantity: float,
        order_type: OrderType = OrderType.MARKET,
        price: Optional[float] = None,
        stop_price: Optional[float] = None
    ) -> Order:
        """Place MT5 order.
        
        Args:
            symbol: Trading symbol
            side: Order side
            quantity: Order quantity
            order_type: Order type
            price: Limit price
            stop_price: Stop price
            
        Returns:
            Order object
        """
        try:
            # Map order type
            mt5_type = mt5.ORDER_TYPE_BUY if side == OrderSide.BUY else mt5.ORDER_TYPE_SELL
            
            if order_type == OrderType.LIMIT:
                mt5_type = mt5.ORDER_TYPE_BUY_LIMIT if side == OrderSide.BUY else mt5.ORDER_TYPE_SELL_LIMIT
            
            # Create order request
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": quantity,
                "type": mt5_type,
                "price": price or 0,
                "comment": "Python Trading Bot",
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            # Send order
            result = mt5.order_send(request)
            
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                logger.error(f"Order failed: {result.comment}")
                return Order(
                    order_id="error",
                    symbol=symbol,
                    side=side,
                    order_type=order_type,
                    quantity=quantity,
                    status=OrderStatus.REJECTED
                )
            
            return Order(
                order_id=str(result.order),
                symbol=symbol,
                side=side,
                order_type=order_type,
                quantity=quantity,
                price=price,
                status=OrderStatus.FILLED,
                created_at=datetime.utcnow()
            )
        
        except Exception as e:
            logger.error(f"Error placing MT5 order: {e}")
            return Order(
                order_id="error",
                symbol=symbol,
                side=side,
                order_type=order_type,
                quantity=quantity,
                status=OrderStatus.REJECTED
            )
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel MT5 order.
        
        Args:
            order_id: Order ID
            
        Returns:
            True if cancelled successfully
        """
        try:
            request = {
                "action": mt5.TRADE_ACTION_REMOVE,
                "order": int(order_id)
            }
            result = mt5.order_send(request)
            return result.retcode == mt5.TRADE_RETCODE_DONE
        except Exception as e:
            logger.error(f"Error cancelling MT5 order: {e}")
            return False
    
    async def get_order(self, order_id: str) -> Optional[Order]:
        """Get MT5 order status.
        
        Args:
            order_id: Order ID
            
        Returns:
            Order object or None
        """
        try:
            orders = mt5.orders_get(ticket=int(order_id))
            if orders and len(orders) > 0:
                order = orders[0]
                return Order(
                    order_id=str(order.ticket),
                    symbol=order.symbol,
                    side=OrderSide.BUY if order.type in [0, 2] else OrderSide.SELL,
                    order_type=OrderType.MARKET,
                    quantity=order.volume_initial,
                    price=order.price_open,
                    filled_quantity=order.volume_current
                )
            return None
        except Exception as e:
            logger.error(f"Error getting MT5 order: {e}")
            return None
    
    async def get_candles(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get MT5 candlestick data.
        
        Args:
            symbol: Trading symbol
            timeframe: Timeframe
            limit: Number of candles
            
        Returns:
            List of candle data
        """
        try:
            # Map timeframe
            tf_map = {
                '1m': mt5.TIMEFRAME_M1,
                '5m': mt5.TIMEFRAME_M5,
                '15m': mt5.TIMEFRAME_M15,
                '30m': mt5.TIMEFRAME_M30,
                '1h': mt5.TIMEFRAME_H1,
                '4h': mt5.TIMEFRAME_H4,
                '1d': mt5.TIMEFRAME_D1,
                '1w': mt5.TIMEFRAME_W1,
                '1M': mt5.TIMEFRAME_MN1
            }
            
            tf = tf_map.get(timeframe, mt5.TIMEFRAME_H1)
            candles = mt5.copy_rates_from_pos(symbol, tf, 0, limit)
            
            result = []
            for candle in candles:
                result.append({
                    'time': candle[0],
                    'open': candle[1],
                    'high': candle[2],
                    'low': candle[3],
                    'close': candle[4],
                    'volume': candle[5]
                })
            
            return result
        except Exception as e:
            logger.error(f"Error getting MT5 candles: {e}")
            return []
    
    async def get_ticker(self, symbol: str) -> Dict[str, float]:
        """Get MT5 ticker data.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Ticker data
        """
        try:
            tick = mt5.symbol_info_tick(symbol)
            return {
                'bid': tick.bid,
                'ask': tick.ask,
                'last': tick.last,
                'volume': tick.volume
            }
        except Exception as e:
            logger.error(f"Error getting MT5 ticker: {e}")
            return {}
