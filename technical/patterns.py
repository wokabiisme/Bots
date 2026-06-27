"""Market structure and price action patterns."""

import numpy as np
from typing import Dict, List, Tuple, Optional
from loguru import logger


class PatternAnalyzer:
    """Analyze candlestick and price action patterns."""
    
    @staticmethod
    def is_bullish_engulfing(
        prev_open: float,
        prev_close: float,
        curr_open: float,
        curr_close: float
    ) -> bool:
        """Detect bullish engulfing pattern.
        
        Args:
            prev_open: Previous candle open
            prev_close: Previous candle close
            curr_open: Current candle open
            curr_close: Current candle close
            
        Returns:
            True if bullish engulfing pattern detected
        """
        prev_body = abs(prev_close - prev_open)
        curr_body = abs(curr_close - curr_open)
        
        # Current candle should be bullish and engulf previous bearish candle
        return (
            prev_close < prev_open and  # Previous candle bearish
            curr_close > curr_open and  # Current candle bullish
            curr_open <= prev_close and  # Current open at/below previous close
            curr_close >= prev_open and  # Current close at/above previous open
            curr_body > prev_body  # Current body larger
        )
    
    @staticmethod
    def is_bearish_engulfing(
        prev_open: float,
        prev_close: float,
        curr_open: float,
        curr_close: float
    ) -> bool:
        """Detect bearish engulfing pattern.
        
        Args:
            prev_open: Previous candle open
            prev_close: Previous candle close
            curr_open: Current candle open
            curr_close: Current candle close
            
        Returns:
            True if bearish engulfing pattern detected
        """
        prev_body = abs(prev_close - prev_open)
        curr_body = abs(curr_close - curr_open)
        
        # Current candle should be bearish and engulf previous bullish candle
        return (
            prev_close > prev_open and  # Previous candle bullish
            curr_close < curr_open and  # Current candle bearish
            curr_open >= prev_close and  # Current open at/above previous close
            curr_close <= prev_open and  # Current close at/below previous open
            curr_body > prev_body  # Current body larger
        )
    
    @staticmethod
    def is_hammer(
        open_price: float,
        high: float,
        low: float,
        close: float
    ) -> bool:
        """Detect hammer pattern.
        
        Args:
            open_price: Candle open
            high: Candle high
            low: Candle low
            close: Candle close
            
        Returns:
            True if hammer pattern detected
        """
        body = abs(close - open_price)
        upper_wick = high - max(open_price, close)
        lower_wick = min(open_price, close) - low
        
        # Lower wick should be at least 2x the body
        return lower_wick >= body * 2 and upper_wick <= body * 0.5
    
    @staticmethod
    def is_shooting_star(
        open_price: float,
        high: float,
        low: float,
        close: float
    ) -> bool:
        """Detect shooting star pattern.
        
        Args:
            open_price: Candle open
            high: Candle high
            low: Candle low
            close: Candle close
            
        Returns:
            True if shooting star pattern detected
        """
        body = abs(close - open_price)
        upper_wick = high - max(open_price, close)
        lower_wick = min(open_price, close) - low
        
        # Upper wick should be at least 2x the body
        return upper_wick >= body * 2 and lower_wick <= body * 0.5
    
    @staticmethod
    def is_doji(
        open_price: float,
        high: float,
        low: float,
        close: float,
        threshold: float = 0.001
    ) -> bool:
        """Detect doji pattern.
        
        Args:
            open_price: Candle open
            high: Candle high
            low: Candle low
            close: Candle close
            threshold: Doji threshold (default 0.1% of range)
            
        Returns:
            True if doji pattern detected
        """
        range_val = high - low
        body = abs(close - open_price)
        
        return body <= range_val * threshold
    
    @staticmethod
    def detect_patterns(
        opens: np.ndarray,
        highs: np.ndarray,
        lows: np.ndarray,
        closes: np.ndarray
    ) -> Dict[int, List[str]]:
        """Detect all patterns in price data.
        
        Args:
            opens: Open prices array
            highs: High prices array
            lows: Low prices array
            closes: Close prices array
            
        Returns:
            Dictionary with patterns detected by candle index
        """
        patterns = {}
        
        for i in range(1, len(closes)):
            patterns[i] = []
            
            # Single candle patterns
            if PatternAnalyzer.is_hammer(opens[i], highs[i], lows[i], closes[i]):
                patterns[i].append('hammer')
            
            if PatternAnalyzer.is_shooting_star(opens[i], highs[i], lows[i], closes[i]):
                patterns[i].append('shooting_star')
            
            if PatternAnalyzer.is_doji(opens[i], highs[i], lows[i], closes[i]):
                patterns[i].append('doji')
            
            # Two candle patterns
            if PatternAnalyzer.is_bullish_engulfing(
                opens[i-1], closes[i-1],
                opens[i], closes[i]
            ):
                patterns[i].append('bullish_engulfing')
            
            if PatternAnalyzer.is_bearish_engulfing(
                opens[i-1], closes[i-1],
                opens[i], closes[i]
            ):
                patterns[i].append('bearish_engulfing')
        
        return patterns


class MarketStructureAnalyzer:
    """Analyze market structure and price levels."""
    
    @staticmethod
    def find_support_resistance(
        prices: np.ndarray,
        window: int = 20,
        threshold: float = 0.02
    ) -> Tuple[List[float], List[float]]:
        """Find support and resistance levels.
        
        Args:
            prices: Close prices array
            window: Window size for finding local extrema
            threshold: Minimum distance between levels (as % of price)
            
        Returns:
            Tuple of (support_levels, resistance_levels)
        """
        support_levels = []
        resistance_levels = []
        
        for i in range(window, len(prices) - window):
            # Find local minimum (support)
            if prices[i] == np.min(prices[i - window:i + window]):
                support_levels.append(prices[i])
            
            # Find local maximum (resistance)
            if prices[i] == np.max(prices[i - window:i + window]):
                resistance_levels.append(prices[i])
        
        # Remove duplicate levels (too close)
        support_levels = MarketStructureAnalyzer._remove_close_levels(
            support_levels, threshold
        )
        resistance_levels = MarketStructureAnalyzer._remove_close_levels(
            resistance_levels, threshold
        )
        
        return support_levels, resistance_levels
    
    @staticmethod
    def _remove_close_levels(
        levels: List[float],
        threshold: float
    ) -> List[float]:
        """Remove levels that are too close together.
        
        Args:
            levels: List of price levels
            threshold: Minimum distance (as % of price)
            
        Returns:
            Filtered levels
        """
        if not levels:
            return []
        
        sorted_levels = sorted(levels)
        filtered = [sorted_levels[0]]
        
        for level in sorted_levels[1:]:
            if abs(level - filtered[-1]) / filtered[-1] > threshold:
                filtered.append(level)
        
        return filtered
    
    @staticmethod
    def identify_trend(
        prices: np.ndarray,
        period: int = 20
    ) -> str:
        """Identify overall trend direction.
        
        Args:
            prices: Close prices array
            period: Period for trend calculation
            
        Returns:
            Trend direction: 'uptrend', 'downtrend', or 'sideways'
        """
        if len(prices) < period:
            return 'unknown'
        
        recent_prices = prices[-period:]
        higher_highs = sum(1 for i in range(1, len(recent_prices)) 
                          if recent_prices[i] > recent_prices[i - 1])
        
        if higher_highs > period * 0.6:
            return 'uptrend'
        elif higher_highs < period * 0.4:
            return 'downtrend'
        else:
            return 'sideways'
    
    @staticmethod
    def detect_breakout(
        prices: np.ndarray,
        support: float,
        resistance: float,
        breakout_threshold: float = 0.01
    ) -> Optional[str]:
        """Detect potential breakout.
        
        Args:
            prices: Close prices array
            support: Support level
            resistance: Resistance level
            breakout_threshold: Breakout threshold (default 1%)
            
        Returns:
            'upside' for upside breakout, 'downside' for downside breakout, None otherwise
        """
        current_price = prices[-1]
        support_breakout = (current_price - support) / support
        resistance_breakout = (resistance - current_price) / resistance
        
        if support_breakout < -breakout_threshold:
            return 'downside'
        elif resistance_breakout < -breakout_threshold:
            return 'upside'
        
        return None
    
    @staticmethod
    def detect_fvg(
        opens: np.ndarray,
        highs: np.ndarray,
        lows: np.ndarray
    ) -> List[Dict[str, float]]:
        """Detect Fair Value Gaps (FVG).
        
        Args:
            opens: Open prices array
            highs: High prices array
            lows: Low prices array
            
        Returns:
            List of FVG zones
        """
        fvgs = []
        
        for i in range(2, len(closes)):
            # Bullish FVG: Gap up from previous candle
            if lows[i] > highs[i - 2]:
                fvgs.append({
                    'type': 'bullish',
                    'top': highs[i - 2],
                    'bottom': lows[i],
                    'index': i
                })
            
            # Bearish FVG: Gap down from previous candle
            if highs[i] < lows[i - 2]:
                fvgs.append({
                    'type': 'bearish',
                    'top': highs[i],
                    'bottom': lows[i - 2],
                    'index': i
                })
        
        return fvgs
    
    @staticmethod
    def detect_order_blocks(
        opens: np.ndarray,
        highs: np.ndarray,
        lows: np.ndarray,
        closes: np.ndarray,
        lookback: int = 20
    ) -> List[Dict[str, float]]:
        """Detect Smart Money order blocks.
        
        Args:
            opens: Open prices array
            highs: High prices array
            lows: Low prices array
            closes: Close prices array
            lookback: Lookback period
            
        Returns:
            List of order block zones
        """
        order_blocks = []
        
        for i in range(lookback, len(closes)):
            # Bullish order block: Price rejects and goes higher
            if closes[i] > highs[i - 1] and closes[i - 1] < opens[i - 1]:
                order_blocks.append({
                    'type': 'bullish',
                    'high': highs[i - 1],
                    'low': lows[i - 1],
                    'index': i
                })
            
            # Bearish order block: Price rejects and goes lower
            if closes[i] < lows[i - 1] and closes[i - 1] > opens[i - 1]:
                order_blocks.append({
                    'type': 'bearish',
                    'high': highs[i - 1],
                    'low': lows[i - 1],
                    'index': i
                })
        
        return order_blocks
