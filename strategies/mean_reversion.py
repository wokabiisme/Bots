"""Mean reversion trading strategy."""

import numpy as np
from typing import Dict
from strategies.base_strategy import BaseStrategy
from loguru import logger


class MeanReversionStrategy(BaseStrategy):
    """Mean reversion trading strategy."""
    
    def __init__(self, symbol: str = "EURUSD"):
        """Initialize mean reversion strategy.
        
        Args:
            symbol: Trading symbol
        """
        super().__init__("MeanReversion", symbol)
        self.set_parameters({
            'lookback': 20,
            'std_dev': 2.0,
            'rsi_period': 14,
            'rsi_threshold': 30
        })
    
    def calculate_indicators(self, data: Dict) -> None:
        """Calculate mean reversion indicators.
        
        Args:
            data: OHLCV data
        """
        closes = np.array(data.get('close', []))
        lookback = self.get_parameter('lookback')
        
        if len(closes) < lookback:
            return
        
        # Bollinger Bands
        sma = np.mean(closes[-lookback:])
        std = np.std(closes[-lookback:])
        std_dev = self.get_parameter('std_dev')
        
        self.indicators['sma'] = sma
        self.indicators['upper_band'] = sma + (std * std_dev)
        self.indicators['lower_band'] = sma - (std * std_dev)
        self.indicators['current_price'] = closes[-1]
        
        # RSI
        rsi_period = self.get_parameter('rsi_period')
        if len(closes) >= rsi_period:
            deltas = np.diff(closes[-rsi_period-1:])
            seed = deltas[:1]
            up = seed[seed >= 0].sum() / rsi_period
            down = -seed[seed < 0].sum() / rsi_period
            
            for delta in deltas[1:]:
                if delta >= 0:
                    up = (up * (rsi_period - 1) + delta) / rsi_period
                    down = down * (rsi_period - 1) / rsi_period
                else:
                    up = up * (rsi_period - 1) / rsi_period
                    down = (down * (rsi_period - 1) - delta) / rsi_period
            
            rs = up / (down + 1e-10)
            self.indicators['rsi'] = 100 - (100 / (1 + rs))
    
    def generate_signal(self) -> str:
        """Generate mean reversion signal.
        
        Returns:
            Trading signal
        """
        if 'upper_band' not in self.indicators:
            return 'HOLD'
        
        current_price = self.indicators.get('current_price', 0)
        upper_band = self.indicators.get('upper_band', 0)
        lower_band = self.indicators.get('lower_band', 0)
        rsi = self.indicators.get('rsi', 50)
        rsi_threshold = self.get_parameter('rsi_threshold')
        
        # Oversold - mean reversion BUY
        if current_price < lower_band and rsi < rsi_threshold:
            return 'BUY'
        
        # Overbought - mean reversion SELL
        if current_price > upper_band and rsi > (100 - rsi_threshold):
            return 'SELL'
        
        return 'HOLD'
