"""Data validation utilities."""

import re
from typing import Any, Optional, List
from decimal import Decimal
from datetime import datetime
from loguru import logger


class Validators:
    """Data validation utilities."""
    
    @staticmethod
    def is_valid_api_key(api_key: str) -> bool:
        """Validate API key format.
        
        Args:
            api_key: API key to validate
            
        Returns:
            True if valid
        """
        if not api_key or not isinstance(api_key, str):
            return False
        
        # Basic validation: should be at least 20 chars and alphanumeric
        return len(api_key) >= 20 and re.match(r'^[a-zA-Z0-9_-]+$', api_key)
    
    @staticmethod
    def is_valid_email(email: str) -> bool:
        """Validate email address.
        
        Args:
            email: Email to validate
            
        Returns:
            True if valid
        """
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def is_valid_symbol(symbol: str) -> bool:
        """Validate trading symbol.
        
        Args:
            symbol: Symbol to validate (e.g., EURUSD, BTCUSDT)
            
        Returns:
            True if valid
        """
        if not symbol or not isinstance(symbol, str):
            return False
        
        # Allow alphanumeric, underscores, and hyphens
        return re.match(r'^[A-Z0-9_-]{2,20}$', symbol) is not None
    
    @staticmethod
    def is_valid_timeframe(timeframe: str) -> bool:
        """Validate trading timeframe.
        
        Args:
            timeframe: Timeframe (e.g., 1m, 5m, 1h, 1d)
            
        Returns:
            True if valid
        """
        valid_timeframes = ['1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w', '1M']
        return timeframe in valid_timeframes
    
    @staticmethod
    def is_valid_price(price: Any) -> bool:
        """Validate price value.
        
        Args:
            price: Price to validate
            
        Returns:
            True if valid positive number
        """
        try:
            price_decimal = Decimal(str(price))
            return price_decimal > 0
        except:
            return False
    
    @staticmethod
    def is_valid_quantity(quantity: Any) -> bool:
        """Validate quantity value.
        
        Args:
            quantity: Quantity to validate
            
        Returns:
            True if valid positive number
        """
        try:
            qty_decimal = Decimal(str(quantity))
            return qty_decimal > 0
        except:
            return False
    
    @staticmethod
    def is_valid_percentage(percentage: Any) -> bool:
        """Validate percentage value.
        
        Args:
            percentage: Percentage to validate
            
        Returns:
            True if 0-100
        """
        try:
            pct = float(percentage)
            return 0 <= pct <= 100
        except:
            return False
    
    @staticmethod
    def is_valid_datetime(dt_string: str, format: str = "%Y-%m-%d %H:%M:%S") -> bool:
        """Validate datetime string.
        
        Args:
            dt_string: Datetime string
            format: Expected datetime format
            
        Returns:
            True if valid
        """
        try:
            datetime.strptime(dt_string, format)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def is_valid_leverage(leverage: Any) -> bool:
        """Validate leverage value.
        
        Args:
            leverage: Leverage to validate
            
        Returns:
            True if valid
        """
        try:
            lev = float(leverage)
            return 1 <= lev <= 500
        except:
            return False
    
    @staticmethod
    def validate_trade_params(
        symbol: str,
        price: float,
        quantity: float,
        leverage: float = 1.0
    ) -> bool:
        """Validate complete trade parameters.
        
        Args:
            symbol: Trading symbol
            price: Entry price
            quantity: Trade quantity
            leverage: Trade leverage
            
        Returns:
            True if all parameters valid
        """
        validations = [
            ("symbol", Validators.is_valid_symbol(symbol)),
            ("price", Validators.is_valid_price(price)),
            ("quantity", Validators.is_valid_quantity(quantity)),
            ("leverage", Validators.is_valid_leverage(leverage))
        ]
        
        all_valid = all(valid for _, valid in validations)
        
        if not all_valid:
            invalid = [name for name, valid in validations if not valid]
            logger.error(f"Invalid trade parameters: {invalid}")
        
        return all_valid
