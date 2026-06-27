"""Base strategy template."""

from abc import ABC, abstractmethod
from typing import Dict, Optional, List
import numpy as np
from loguru import logger


class BaseStrategy(ABC):
    """Base trading strategy class."""
    
    def __init__(self, name: str, symbol: str):
        """Initialize strategy.
        
        Args:
            name: Strategy name
            symbol: Trading symbol
        """
        self.name = name
        self.symbol = symbol
        self.parameters = {}
        self.indicators = {}
        self.signal = 'HOLD'
    
    @abstractmethod
    def calculate_indicators(self, data: Dict) -> None:
        """Calculate technical indicators.
        
        Args:
            data: OHLCV data
        """
        pass
    
    @abstractmethod
    def generate_signal(self) -> str:
        """Generate trading signal.
        
        Returns:
            Signal: 'BUY', 'SELL', or 'HOLD'
        """
        pass
    
    def update(self, data: Dict) -> str:
        """Update strategy with new data.
        
        Args:
            data: OHLCV data
            
        Returns:
            Trading signal
        """
        try:
            self.calculate_indicators(data)
            self.signal = self.generate_signal()
            return self.signal
        except Exception as e:
            logger.error(f"Error updating strategy {self.name}: {e}")
            return 'HOLD'
    
    def set_parameter(self, key: str, value: any) -> None:
        """Set strategy parameter.
        
        Args:
            key: Parameter name
            value: Parameter value
        """
        self.parameters[key] = value
    
    def get_parameter(self, key: str, default: any = None) -> any:
        """Get strategy parameter.
        
        Args:
            key: Parameter name
            default: Default value
            
        Returns:
            Parameter value
        """
        return self.parameters.get(key, default)
    
    def set_parameters(self, params: Dict) -> None:
        """Set multiple parameters.
        
        Args:
            params: Dictionary of parameters
        """
        self.parameters.update(params)
    
    def get_signal(self) -> str:
        """Get current signal.
        
        Returns:
            Current signal
        """
        return self.signal
