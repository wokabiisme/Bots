"""Base broker connector class."""

from abc import ABC, abstractmethod
from typing import Dict, Optional, List, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class OrderType(Enum):
    """Order type enumeration."""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"
    TRAILING_STOP = "trailing_stop"


class OrderSide(Enum):
    """Order side enumeration."""
    BUY = "buy"
    SELL = "sell"


class OrderStatus(Enum):
    """Order status enumeration."""
    PENDING = "pending"
    OPEN = "open"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


@dataclass
class Order:
    """Order data class."""
    order_id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    price: Optional[float] = None
    stop_price: Optional[float] = None
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: float = 0
    filled_price: Optional[float] = None
    created_at: Optional[datetime] = None
    filled_at: Optional[datetime] = None
    commission: float = 0
    commission_asset: str = "USD"


@dataclass
class Position:
    """Position data class."""
    symbol: str
    quantity: float
    entry_price: float
    current_price: float
    unrealized_pnl: float
    unrealized_pnl_percent: float
    side: OrderSide


@dataclass
class AccountInfo:
    """Account information data class."""
    balance: float
    equity: float
    free_balance: float
    used_balance: float
    margin: float
    free_margin: float
    margin_level: float
    currency: str = "USD"


class BaseBroker(ABC):
    """Base broker connector class."""
    
    def __init__(self, broker_name: str):
        """Initialize broker connector.
        
        Args:
            broker_name: Name of the broker
        """
        self.broker_name = broker_name
        self.is_connected = False
    
    @abstractmethod
    async def connect(self) -> bool:
        """Connect to broker.
        
        Returns:
            True if connection successful
        """
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """Disconnect from broker.
        
        Returns:
            True if disconnection successful
        """
        pass
    
    @abstractmethod
    async def get_account_info(self) -> AccountInfo:
        """Get account information.
        
        Returns:
            Account information
        """
        pass
    
    @abstractmethod
    async def get_balance(self) -> float:
        """Get current balance.
        
        Returns:
            Account balance
        """
        pass
    
    @abstractmethod
    async def get_positions(self) -> List[Position]:
        """Get all open positions.
        
        Returns:
            List of positions
        """
        pass
    
    @abstractmethod
    async def get_position(self, symbol: str) -> Optional[Position]:
        """Get specific position.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Position or None
        """
        pass
    
    @abstractmethod
    async def place_order(
        self,
        symbol: str,
        side: OrderSide,
        quantity: float,
        order_type: OrderType = OrderType.MARKET,
        price: Optional[float] = None,
        stop_price: Optional[float] = None
    ) -> Order:
        """Place an order.
        
        Args:
            symbol: Trading symbol
            side: Order side (BUY/SELL)
            quantity: Order quantity
            order_type: Order type
            price: Limit price
            stop_price: Stop price
            
        Returns:
            Order object
        """
        pass
    
    @abstractmethod
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an order.
        
        Args:
            order_id: Order ID
            
        Returns:
            True if cancelled successfully
        """
        pass
    
    @abstractmethod
    async def get_order(self, order_id: str) -> Optional[Order]:
        """Get order status.
        
        Args:
            order_id: Order ID
            
        Returns:
            Order object or None
        """
        pass
    
    @abstractmethod
    async def get_candles(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get candlestick data.
        
        Args:
            symbol: Trading symbol
            timeframe: Timeframe (1m, 5m, 1h, 1d, etc.)
            limit: Number of candles
            
        Returns:
            List of candle data
        """
        pass
    
    @abstractmethod
    async def get_ticker(self, symbol: str) -> Dict[str, float]:
        """Get current ticker data.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Ticker data with bid, ask, last, etc.
        """
        pass
