"""Binance broker connector."""

import asyncio
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceOrderException
from typing import List, Dict, Optional, Any
from datetime import datetime
from loguru import logger
from execution.brokers.base import (
    BaseBroker, Order, Position, AccountInfo,
    OrderType, OrderSide, OrderStatus
)


class BinanceConnector(BaseBroker):
    """Binance broker connector."""
    
    def __init__(
        self,
        api_key: str,
        api_secret: str,
        testnet: bool = False
    ):
        """Initialize Binance connector.
        
        Args:
            api_key: Binance API key
            api_secret: Binance API secret
            testnet: Use testnet if True
        """
        super().__init__("Binance")
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        self.client = None
    
    async def connect(self) -> bool:
        """Connect to Binance.
        
        Returns:
            True if connection successful
        """
        try:
            self.client = Client(
                api_key=self.api_key,
                api_secret=self.api_secret,
                testnet=self.testnet
            )
            
            # Test connection
            self.client.get_account()
            
            self.is_connected = True
            logger.info(f"Connected to Binance {'Testnet' if self.testnet else 'Live'}")
            return True
        
        except Exception as e:
            logger.error(f"Binance connection error: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """Disconnect from Binance.
        
        Returns:
            True if disconnection successful
        """
        try:
            if self.client:
                self.client.close_connection()
            self.is_connected = False
            logger.info("Disconnected from Binance")
            return True
        except Exception as e:
            logger.error(f"Binance disconnection error: {e}")
            return False
    
    async def get_account_info(self) -> AccountInfo:
        """Get Binance account information.
        
        Returns:
            Account information
        """
        try:
            account = self.client.get_account()
            balances = {b['asset']: float(b['free']) + float(b['locked']) for b in account['balances']}
            
            return AccountInfo(
                balance=balances.get('USDT', 0),
                equity=balances.get('USDT', 0),
                free_balance=float([b for b in account['balances'] if b['asset'] == 'USDT'][0]['free']),
                used_balance=float([b for b in account['balances'] if b['asset'] == 'USDT'][0]['locked']),
                margin=0,
                free_margin=float([b for b in account['balances'] if b['asset'] == 'USDT'][0]['free']),
                margin_level=0,
                currency='USDT'
            )
        except Exception as e:
            logger.error(f"Error getting Binance account info: {e}")
            return AccountInfo(balance=0, equity=0, free_balance=0,
                             used_balance=0, margin=0, free_margin=0, margin_level=0)
    
    async def get_balance(self) -> float:
        """Get Binance USDT balance.
        
        Returns:
            Account balance
        """
        try:
            account = self.client.get_account()
            usdt_balance = [b for b in account['balances'] if b['asset'] == 'USDT'][0]
            return float(usdt_balance['free']) + float(usdt_balance['locked'])
        except Exception as e:
            logger.error(f"Error getting Binance balance: {e}")
            return 0.0
    
    async def get_positions(self) -> List[Position]:
        """Get all Binance positions.
        
        Returns:
            List of positions
        """
        try:
            # For spot trading, positions are based on balances
            account = self.client.get_account()
            positions = []
            
            for balance in account['balances']:
                if float(balance['free']) > 0:
                    asset = balance['asset']
                    symbol = f"{asset}USDT"
                    
                    try:
                        ticker = self.client.get_symbol_info(symbol)
                        price = float(self.client.get_symbol_ticker(symbol=symbol)['price'])
                        
                        positions.append(Position(
                            symbol=symbol,
                            quantity=float(balance['free']),
                            entry_price=price,
                            current_price=price,
                            unrealized_pnl=0,
                            unrealized_pnl_percent=0,
                            side=OrderSide.BUY
                        ))
                    except:
                        pass
            
            return positions
        except Exception as e:
            logger.error(f"Error getting Binance positions: {e}")
            return []
    
    async def get_position(self, symbol: str) -> Optional[Position]:
        """Get specific Binance position.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Position or None
        """
        try:
            account = self.client.get_account()
            
            # Extract asset from symbol (e.g., BTC from BTCUSDT)
            asset = symbol.replace('USDT', '').replace('BUSD', '')
            
            balance_info = [b for b in account['balances'] if b['asset'] == asset]
            if not balance_info:
                return None
            
            quantity = float(balance_info[0]['free'])
            if quantity == 0:
                return None
            
            ticker = self.client.get_symbol_ticker(symbol=symbol)
            price = float(ticker['price'])
            
            return Position(
                symbol=symbol,
                quantity=quantity,
                entry_price=price,
                current_price=price,
                unrealized_pnl=0,
                unrealized_pnl_percent=0,
                side=OrderSide.BUY
            )
        except Exception as e:
            logger.error(f"Error getting Binance position: {e}")
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
        """Place Binance order.
        
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
            side_str = 'BUY' if side == OrderSide.BUY else 'SELL'
            type_str = 'MARKET' if order_type == OrderType.MARKET else 'LIMIT'
            
            if order_type == OrderType.MARKET:
                result = self.client.order_market(side=side_str, symbol=symbol, quantity=quantity)
            else:
                result = self.client.order_limit(side=side_str, symbol=symbol, quantity=quantity, price=price)
            
            return Order(
                order_id=str(result['orderId']),
                symbol=symbol,
                side=side,
                order_type=order_type,
                quantity=quantity,
                price=price,
                status=OrderStatus.FILLED if result['status'] == 'FILLED' else OrderStatus.OPEN,
                created_at=datetime.utcnow()
            )
        
        except BinanceOrderException as e:
            logger.error(f"Binance order error: {e}")
            return Order(
                order_id="error",
                symbol=symbol,
                side=side,
                order_type=order_type,
                quantity=quantity,
                status=OrderStatus.REJECTED
            )
    
    async def cancel_order(self, order_id: str, symbol: str) -> bool:
        """Cancel Binance order.
        
        Args:
            order_id: Order ID
            symbol: Trading symbol
            
        Returns:
            True if cancelled successfully
        """
        try:
            self.client.cancel_order(orderId=int(order_id), symbol=symbol)
            return True
        except Exception as e:
            logger.error(f"Error cancelling Binance order: {e}")
            return False
    
    async def get_order(self, order_id: str, symbol: str) -> Optional[Order]:
        """Get Binance order status.
        
        Args:
            order_id: Order ID
            symbol: Trading symbol
            
        Returns:
            Order object or None
        """
        try:
            result = self.client.get_order(orderId=int(order_id), symbol=symbol)
            
            return Order(
                order_id=str(result['orderId']),
                symbol=result['symbol'],
                side=OrderSide.BUY if result['side'] == 'BUY' else OrderSide.SELL,
                order_type=OrderType.MARKET if result['type'] == 'MARKET' else OrderType.LIMIT,
                quantity=float(result['origQty']),
                price=float(result['price']),
                filled_quantity=float(result['executedQty']),
                status=OrderStatus.FILLED if result['status'] == 'FILLED' else OrderStatus.OPEN
            )
        except Exception as e:
            logger.error(f"Error getting Binance order: {e}")
            return None
    
    async def get_candles(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get Binance candlestick data.
        
        Args:
            symbol: Trading symbol
            timeframe: Timeframe
            limit: Number of candles
            
        Returns:
            List of candle data
        """
        try:
            candles = self.client.get_klines(symbol=symbol, interval=timeframe, limit=limit)
            
            result = []
            for candle in candles:
                result.append({
                    'time': candle[0],
                    'open': float(candle[1]),
                    'high': float(candle[2]),
                    'low': float(candle[3]),
                    'close': float(candle[4]),
                    'volume': float(candle[7])
                })
            
            return result
        except Exception as e:
            logger.error(f"Error getting Binance candles: {e}")
            return []
    
    async def get_ticker(self, symbol: str) -> Dict[str, float]:
        """Get Binance ticker data.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Ticker data
        """
        try:
            ticker = self.client.get_symbol_ticker(symbol=symbol)
            return {
                'bid': float(ticker.get('bidPrice', 0)),
                'ask': float(ticker.get('askPrice', 0)),
                'last': float(ticker['price']),
                'volume': 0
            }
        except Exception as e:
            logger.error(f"Error getting Binance ticker: {e}")
            return {}
