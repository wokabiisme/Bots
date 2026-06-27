"""Bybit broker connector."""

import asyncio
from pybit import HTTP
from typing import List, Dict, Optional, Any
from datetime import datetime
from loguru import logger
from execution.brokers.base import (
    BaseBroker, Order, Position, AccountInfo,
    OrderType, OrderSide, OrderStatus
)


class BybitConnector(BaseBroker):
    """Bybit broker connector."""
    
    def __init__(
        self,
        api_key: str,
        api_secret: str,
        testnet: bool = False
    ):
        """Initialize Bybit connector.
        
        Args:
            api_key: Bybit API key
            api_secret: Bybit API secret
            testnet: Use testnet if True
        """
        super().__init__("Bybit")
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        self.session = None
    
    async def connect(self) -> bool:
        """Connect to Bybit.
        
        Returns:
            True if connection successful
        """
        try:
            endpoint = "https://api-testnet.bybit.com" if self.testnet else "https://api.bybit.com"
            self.session = HTTP(endpoint=endpoint, api_key=self.api_key, api_secret=self.api_secret)
            
            # Test connection
            self.session.get_wallet_balance()
            
            self.is_connected = True
            logger.info(f"Connected to Bybit {'Testnet' if self.testnet else 'Live'}")
            return True
        
        except Exception as e:
            logger.error(f"Bybit connection error: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """Disconnect from Bybit.
        
        Returns:
            True if disconnection successful
        """
        try:
            self.is_connected = False
            logger.info("Disconnected from Bybit")
            return True
        except Exception as e:
            logger.error(f"Bybit disconnection error: {e}")
            return False
    
    async def get_account_info(self) -> AccountInfo:
        """Get Bybit account information.
        
        Returns:
            Account information
        """
        try:
            wallet = self.session.get_wallet_balance()
            balance = float(wallet['result']['USDT']['wallet_balance'])
            equity = float(wallet['result']['USDT']['equity'])
            
            return AccountInfo(
                balance=balance,
                equity=equity,
                free_balance=balance - equity,
                used_balance=equity,
                margin=0,
                free_margin=balance - equity,
                margin_level=0,
                currency='USDT'
            )
        except Exception as e:
            logger.error(f"Error getting Bybit account info: {e}")
            return AccountInfo(balance=0, equity=0, free_balance=0,
                             used_balance=0, margin=0, free_margin=0, margin_level=0)
    
    async def get_balance(self) -> float:
        """Get Bybit USDT balance.
        
        Returns:
            Account balance
        """
        try:
            wallet = self.session.get_wallet_balance()
            return float(wallet['result']['USDT']['wallet_balance'])
        except Exception as e:
            logger.error(f"Error getting Bybit balance: {e}")
            return 0.0
    
    async def get_positions(self) -> List[Position]:
        """Get all Bybit positions.
        
        Returns:
            List of positions
        """
        try:
            positions_data = self.session.get_positions(category="spot")
            positions = []
            
            for pos in positions_data['result']['list']:
                if float(pos['size']) > 0:
                    positions.append(Position(
                        symbol=pos['symbol'],
                        quantity=float(pos['size']),
                        entry_price=float(pos['avgPrice']),
                        current_price=float(pos['markPrice']),
                        unrealized_pnl=float(pos['unrealisedPnl']),
                        unrealized_pnl_percent=float(pos['unrealisedPnlPct']),
                        side=OrderSide.BUY if pos['side'] == 'Buy' else OrderSide.SELL
                    ))
            
            return positions
        except Exception as e:
            logger.error(f"Error getting Bybit positions: {e}")
            return []
    
    async def get_position(self, symbol: str) -> Optional[Position]:
        """Get specific Bybit position.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Position or None
        """
        try:
            positions_data = self.session.get_positions(category="spot", symbol=symbol)
            
            if positions_data['result']['list']:
                pos = positions_data['result']['list'][0]
                if float(pos['size']) > 0:
                    return Position(
                        symbol=pos['symbol'],
                        quantity=float(pos['size']),
                        entry_price=float(pos['avgPrice']),
                        current_price=float(pos['markPrice']),
                        unrealized_pnl=float(pos['unrealisedPnl']),
                        unrealized_pnl_percent=float(pos['unrealisedPnlPct']),
                        side=OrderSide.BUY if pos['side'] == 'Buy' else OrderSide.SELL
                    )
            
            return None
        except Exception as e:
            logger.error(f"Error getting Bybit position: {e}")
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
        """Place Bybit order.
        
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
            side_str = 'Buy' if side == OrderSide.BUY else 'Sell'
            type_str = 'Market' if order_type == OrderType.MARKET else 'Limit'
            
            params = {
                'category': 'spot',
                'symbol': symbol,
                'side': side_str,
                'orderType': type_str,
                'qty': str(quantity)
            }
            
            if order_type == OrderType.LIMIT and price:
                params['price'] = str(price)
            
            result = self.session.place_order(**params)
            
            return Order(
                order_id=result['result']['orderId'],
                symbol=symbol,
                side=side,
                order_type=order_type,
                quantity=quantity,
                price=price,
                status=OrderStatus.OPEN,
                created_at=datetime.utcnow()
            )
        
        except Exception as e:
            logger.error(f"Error placing Bybit order: {e}")
            return Order(
                order_id="error",
                symbol=symbol,
                side=side,
                order_type=order_type,
                quantity=quantity,
                status=OrderStatus.REJECTED
            )
    
    async def cancel_order(self, order_id: str, symbol: str) -> bool:
        """Cancel Bybit order.
        
        Args:
            order_id: Order ID
            symbol: Trading symbol
            
        Returns:
            True if cancelled successfully
        """
        try:
            self.session.cancel_order(category="spot", symbol=symbol, orderId=order_id)
            return True
        except Exception as e:
            logger.error(f"Error cancelling Bybit order: {e}")
            return False
    
    async def get_order(self, order_id: str, symbol: str) -> Optional[Order]:
        """Get Bybit order status.
        
        Args:
            order_id: Order ID
            symbol: Trading symbol
            
        Returns:
            Order object or None
        """
        try:
            result = self.session.get_order_history(category="spot", symbol=symbol, orderId=order_id)
            
            if result['result']['list']:
                order = result['result']['list'][0]
                return Order(
                    order_id=order['orderId'],
                    symbol=order['symbol'],
                    side=OrderSide.BUY if order['side'] == 'Buy' else OrderSide.SELL,
                    order_type=OrderType.MARKET if order['orderType'] == 'Market' else OrderType.LIMIT,
                    quantity=float(order['qty']),
                    price=float(order['price']) if order['price'] else None,
                    filled_quantity=float(order['cumExecQty']),
                    status=OrderStatus.FILLED if order['orderStatus'] == 'Filled' else OrderStatus.OPEN
                )
            
            return None
        except Exception as e:
            logger.error(f"Error getting Bybit order: {e}")
            return None
    
    async def get_candles(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get Bybit candlestick data.
        
        Args:
            symbol: Trading symbol
            timeframe: Timeframe
            limit: Number of candles
            
        Returns:
            List of candle data
        """
        try:
            candles_data = self.session.get_kline(category="spot", symbol=symbol, interval=timeframe, limit=limit)
            
            result = []
            for candle in candles_data['result']['list']:
                result.append({
                    'time': int(candle[0]),
                    'open': float(candle[1]),
                    'high': float(candle[2]),
                    'low': float(candle[3]),
                    'close': float(candle[4]),
                    'volume': float(candle[5])
                })
            
            return result
        except Exception as e:
            logger.error(f"Error getting Bybit candles: {e}")
            return []
    
    async def get_ticker(self, symbol: str) -> Dict[str, float]:
        """Get Bybit ticker data.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Ticker data
        """
        try:
            ticker = self.session.get_tickers(category="spot", symbol=symbol)
            data = ticker['result']['list'][0]
            
            return {
                'bid': float(data['bid1Price']),
                'ask': float(data['ask1Price']),
                'last': float(data['lastPrice']),
                'volume': float(data['volume24h'])
            }
        except Exception as e:
            logger.error(f"Error getting Bybit ticker: {e}")
            return {}
