"""Momentum trading strategy."""

import numpy as np
from typing import Dict
from strategies.base_strategy import BaseStrategy
from loguru import logger


class MomentumStrategy(BaseStrategy):
    """Momentum trading strategy."""
    
    def __init__(self, symbol: str = "EURUSD"):
        """Initialize momentum strategy.
        
        Args:
            symbol: Trading symbol
        """
        super().__init__("Momentum", symbol)
        self.set_parameters({
            'sma_fast': 10,
            'sma_slow': 30,
            'rsi_period': 14,
            'rsi_overbought': 70,
            'rsi_oversold': 30,
            'atr_period': 14,
            'atr_threshold': 1.5
        })
    
    def calculate_indicators(self, data: Dict) -> None:
        """Calculate momentum indicators.
        
        Args:
            data: OHLCV data
        """
        closes = np.array(data.get('close', []))
        
        if len(closes) < self.get_parameter('sma_slow'):
            return
        
        # SMA
        sma_fast_period = self.get_parameter('sma_fast')
        sma_slow_period = self.get_parameter('sma_slow')
        
        self.indicators['sma_fast'] = np.mean(closes[-sma_fast_period:])
        self.indicators['sma_slow'] = np.mean(closes[-sma_slow_period:])
        
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
        
        # ATR
        atr_period = self.get_parameter('atr_period')
        if len(closes) >= atr_period:
            highs = np.array(data.get('high', closes))
            lows = np.array(data.get('low', closes))
            
            tr_values = []
            for i in range(1, len(closes)):
                tr = max(highs[i] - lows[i], abs(highs[i] - closes[i-1]), abs(lows[i] - closes[i-1]))
                tr_values.append(tr)
            
            self.indicators['atr'] = np.mean(tr_values[-atr_period:]) if tr_values else 0
        else:
            self.indicators['atr'] = 0
    
    def generate_signal(self) -> str:
        """Generate momentum signal.
        
        Returns:
            Trading signal
        """
        if 'sma_fast' not in self.indicators or 'sma_slow' not in self.indicators:
            return 'HOLD'
        
        sma_fast = self.indicators['sma_fast']
        sma_slow = self.indicators['sma_slow']
        rsi = self.indicators.get('rsi', 50)
        atr_threshold = self.get_parameter('atr_threshold')
        atr = self.indicators.get('atr', 0)
        
        # Check volatility
        if atr > 0:  # High volatility
            vol_factor = 1.0
        else:
            vol_factor = 0.8
        
        rsi_overbought = self.get_parameter('rsi_overbought')
        rsi_oversold = self.get_parameter('rsi_oversold')
        
        # Bullish momentum
        if sma_fast > sma_slow * 1.01 and rsi < rsi_overbought and atr > atr_threshold:
            return 'BUY'
        
        # Bearish momentum
        if sma_fast < sma_slow * 0.99 and rsi > rsi_oversold and atr > atr_threshold:
            return 'SELL'
        
        return 'HOLD'
