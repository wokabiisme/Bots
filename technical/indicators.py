"""Technical indicators implementation."""

import numpy as np
import pandas as pd
from typing import Dict, Tuple, Optional
from loguru import logger


class TechnicalIndicators:
    """Calculate technical analysis indicators."""
    
    @staticmethod
    def rsi(prices: np.ndarray, period: int = 14) -> np.ndarray:
        """Calculate Relative Strength Index (RSI).
        
        Args:
            prices: Close prices array
            period: RSI period
            
        Returns:
            RSI values array
        """
        deltas = np.diff(prices)
        seed = deltas[:period + 1]
        up = seed[seed >= 0].sum() / period
        down = -seed[seed < 0].sum() / period
        rs = up / down if down != 0 else 0
        rsi = np.zeros_like(prices, dtype=float)
        rsi[:period] = 100 - 100 / (1 + rs)
        
        for i in range(period, len(prices)):
            delta = deltas[i - 1]
            if delta > 0:
                upval = delta
                downval = 0
            else:
                upval = 0
                downval = -delta
            
            up = (up * (period - 1) + upval) / period
            down = (down * (period - 1) + downval) / period
            rs = up / down if down != 0 else 0
            rsi[i] = 100 - 100 / (1 + rs)
        
        return rsi
    
    @staticmethod
    def macd(
        prices: np.ndarray,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Calculate MACD (Moving Average Convergence Divergence).
        
        Args:
            prices: Close prices array
            fast_period: Fast EMA period
            slow_period: Slow EMA period
            signal_period: Signal line EMA period
            
        Returns:
            Tuple of (MACD, Signal, Histogram)
        """
        ema_fast = TechnicalIndicators.ema(prices, fast_period)
        ema_slow = TechnicalIndicators.ema(prices, slow_period)
        macd = ema_fast - ema_slow
        signal = TechnicalIndicators.ema(macd, signal_period)
        histogram = macd - signal
        
        return macd, signal, histogram
    
    @staticmethod
    def ema(prices: np.ndarray, period: int) -> np.ndarray:
        """Calculate Exponential Moving Average (EMA).
        
        Args:
            prices: Prices array
            period: EMA period
            
        Returns:
            EMA values array
        """
        ema = np.zeros_like(prices, dtype=float)
        multiplier = 2 / (period + 1)
        ema[0] = prices[0]
        
        for i in range(1, len(prices)):
            ema[i] = prices[i] * multiplier + ema[i - 1] * (1 - multiplier)
        
        return ema
    
    @staticmethod
    def sma(prices: np.ndarray, period: int) -> np.ndarray:
        """Calculate Simple Moving Average (SMA).
        
        Args:
            prices: Prices array
            period: SMA period
            
        Returns:
            SMA values array
        """
        sma = np.zeros_like(prices, dtype=float)
        for i in range(period - 1, len(prices)):
            sma[i] = np.mean(prices[i - period + 1:i + 1])
        
        return sma
    
    @staticmethod
    def atr(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> np.ndarray:
        """Calculate Average True Range (ATR).
        
        Args:
            high: High prices array
            low: Low prices array
            close: Close prices array
            period: ATR period
            
        Returns:
            ATR values array
        """
        tr = np.zeros_like(high, dtype=float)
        tr[0] = high[0] - low[0]
        
        for i in range(1, len(high)):
            tr[i] = max(
                high[i] - low[i],
                abs(high[i] - close[i - 1]),
                abs(low[i] - close[i - 1])
            )
        
        atr = TechnicalIndicators.sma(tr, period)
        return atr
    
    @staticmethod
    def bollinger_bands(
        prices: np.ndarray,
        period: int = 20,
        std_dev: float = 2.0
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Calculate Bollinger Bands.
        
        Args:
            prices: Prices array
            period: Moving average period
            std_dev: Standard deviation multiplier
            
        Returns:
            Tuple of (Upper Band, Middle Band, Lower Band)
        """
        middle = TechnicalIndicators.sma(prices, period)
        std = np.zeros_like(prices, dtype=float)
        
        for i in range(period - 1, len(prices)):
            std[i] = np.std(prices[i - period + 1:i + 1])
        
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)
        
        return upper, middle, lower
    
    @staticmethod
    def adx(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> np.ndarray:
        """Calculate Average Directional Index (ADX).
        
        Args:
            high: High prices array
            low: Low prices array
            close: Close prices array
            period: ADX period
            
        Returns:
            ADX values array
        """
        plus_dm = np.zeros_like(high, dtype=float)
        minus_dm = np.zeros_like(high, dtype=float)
        
        for i in range(1, len(high)):
            up_move = high[i] - high[i - 1]
            down_move = low[i - 1] - low[i]
            
            if up_move > down_move and up_move > 0:
                plus_dm[i] = up_move
            if down_move > up_move and down_move > 0:
                minus_dm[i] = down_move
        
        atr = TechnicalIndicators.atr(high, low, close, period)
        plus_di = 100 * TechnicalIndicators.ema(plus_dm, period) / (atr + 1e-10)
        minus_di = 100 * TechnicalIndicators.ema(minus_dm, period) / (atr + 1e-10)
        
        di_diff = np.abs(plus_di - minus_di)
        di_sum = plus_di + minus_di
        di_ratio = di_diff / (di_sum + 1e-10)
        adx = TechnicalIndicators.ema(di_ratio * 100, period)
        
        return adx
    
    @staticmethod
    def vwap(
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray,
        volume: np.ndarray
    ) -> np.ndarray:
        """Calculate Volume Weighted Average Price (VWAP).
        
        Args:
            high: High prices array
            low: Low prices array
            close: Close prices array
            volume: Volume array
            
        Returns:
            VWAP values array
        """
        typical_price = (high + low + close) / 3
        vwap = np.cumsum(typical_price * volume) / np.cumsum(volume)
        
        return vwap
    
    @staticmethod
    def stochastic(
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray,
        period: int = 14,
        smooth_k: int = 3,
        smooth_d: int = 3
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Calculate Stochastic Oscillator.
        
        Args:
            high: High prices array
            low: Low prices array
            close: Close prices array
            period: Stochastic period
            smooth_k: K smoothing period
            smooth_d: D smoothing period
            
        Returns:
            Tuple of (K%, D%)
        """
        k = np.zeros_like(close, dtype=float)
        
        for i in range(period, len(close)):
            lowest_low = np.min(low[i - period:i])
            highest_high = np.max(high[i - period:i])
            k[i] = 100 * (close[i] - lowest_low) / (highest_high - lowest_low + 1e-10)
        
        k_smooth = TechnicalIndicators.sma(k, smooth_k)
        d = TechnicalIndicators.sma(k_smooth, smooth_d)
        
        return k_smooth, d
    
    @staticmethod
    def ichimoku(
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray
    ) -> Dict[str, np.ndarray]:
        """Calculate Ichimoku Cloud.
        
        Args:
            high: High prices array
            low: Low prices array
            close: Close prices array
            
        Returns:
            Dictionary with Ichimoku components
        """
        # Tenkan-sen (Conversion Line)
        tenkan = np.zeros_like(close, dtype=float)
        for i in range(9, len(close)):
            tenkan[i] = (np.max(high[i - 9:i]) + np.min(low[i - 9:i])) / 2
        
        # Kijun-sen (Base Line)
        kijun = np.zeros_like(close, dtype=float)
        for i in range(26, len(close)):
            kijun[i] = (np.max(high[i - 26:i]) + np.min(low[i - 26:i])) / 2
        
        # Senkou Span A
        senkou_a = (tenkan + kijun) / 2
        
        # Senkou Span B
        senkou_b = np.zeros_like(close, dtype=float)
        for i in range(52, len(close)):
            senkou_b[i] = (np.max(high[i - 52:i]) + np.min(low[i - 52:i])) / 2
        
        # Chikou Span
        chikou = np.zeros_like(close, dtype=float)
        chikou[:-26] = close[26:]
        
        return {
            'tenkan': tenkan,
            'kijun': kijun,
            'senkou_a': senkou_a,
            'senkou_b': senkou_b,
            'chikou': chikou
        }
    
    @staticmethod
    def pivot_points(
        high: float,
        low: float,
        close: float
    ) -> Dict[str, float]:
        """Calculate Pivot Points.
        
        Args:
            high: Previous period high
            low: Previous period low
            close: Previous period close
            
        Returns:
            Dictionary with pivot levels
        """
        pivot = (high + low + close) / 3
        r1 = 2 * pivot - low
        r2 = pivot + (high - low)
        s1 = 2 * pivot - high
        s2 = pivot - (high - low)
        
        return {
            'pivot': pivot,
            'r1': r1,
            'r2': r2,
            's1': s1,
            's2': s2
        }
    
    @staticmethod
    def fibonacci_levels(
        high: float,
        low: float
    ) -> Dict[str, float]:
        """Calculate Fibonacci Retracement Levels.
        
        Args:
            high: Swing high
            low: Swing low
            
        Returns:
            Dictionary with Fibonacci levels
        """
        diff = high - low
        
        return {
            'level_0': high,
            'level_236': high - diff * 0.236,
            'level_382': high - diff * 0.382,
            'level_500': high - diff * 0.5,
            'level_618': high - diff * 0.618,
            'level_786': high - diff * 0.786,
            'level_100': low
        }
    
    @staticmethod
    def volume_profile(
        prices: np.ndarray,
        volume: np.ndarray,
        bins: int = 20
    ) -> Dict[str, any]:
        """Calculate Volume Profile.
        
        Args:
            prices: Close prices array
            volume: Volume array
            bins: Number of price bins
            
        Returns:
            Dictionary with volume profile data
        """
        min_price = np.min(prices)
        max_price = np.max(prices)
        bin_edges = np.linspace(min_price, max_price, bins + 1)
        
        bin_volumes = np.zeros(bins)
        for i in range(len(prices)):
            bin_idx = np.digitize(prices[i], bin_edges) - 1
            if 0 <= bin_idx < bins:
                bin_volumes[bin_idx] += volume[i]
        
        poc_idx = np.argmax(bin_volumes)
        poc = (bin_edges[poc_idx] + bin_edges[poc_idx + 1]) / 2
        
        return {
            'bin_prices': bin_edges[:-1],
            'bin_volumes': bin_volumes,
            'poc': poc,
            'max_volume': np.max(bin_volumes)
        }
