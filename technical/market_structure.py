"""Market structure and Smart Money Concepts analysis."""

import numpy as np
from typing import Dict, List, Optional, Tuple
from loguru import logger


class MarketStructureAnalyzer:
    """Analyze market structure using Smart Money Concepts."""
    
    @staticmethod
    def detect_change_of_character(
        opens: np.ndarray,
        highs: np.ndarray,
        lows: np.ndarray,
        closes: np.ndarray,
        lookback: int = 5
    ) -> List[Dict[str, any]]:
        """Detect Change of Character (CHoCH) in price action.
        
        Args:
            opens: Open prices array
            highs: High prices array
            lows: Low prices array
            closes: Close prices array
            lookback: Lookback period for swing identification
            
        Returns:
            List of CHoCH events
        """
        choch_events = []
        
        for i in range(lookback * 2, len(closes)):
            # Identify swings
            swing_high = np.max(highs[i - lookback:i])
            swing_low = np.min(lows[i - lookback:i])
            prev_swing_high = np.max(highs[i - lookback * 2:i - lookback])
            prev_swing_low = np.min(lows[i - lookback * 2:i - lookback])
            
            # Bullish CHoCH: New swing high > previous swing high
            if swing_high > prev_swing_high and closes[i] > swing_high:
                choch_events.append({
                    'type': 'bullish',
                    'index': i,
                    'level': swing_high,
                    'broken_level': prev_swing_high
                })
            
            # Bearish CHoCH: New swing low < previous swing low
            if swing_low < prev_swing_low and closes[i] < swing_low:
                choch_events.append({
                    'type': 'bearish',
                    'index': i,
                    'level': swing_low,
                    'broken_level': prev_swing_low
                })
        
        return choch_events
    
    @staticmethod
    def detect_bos(
        opens: np.ndarray,
        highs: np.ndarray,
        lows: np.ndarray,
        closes: np.ndarray,
        lookback: int = 10
    ) -> List[Dict[str, any]]:
        """Detect Break of Structure (BoS).
        
        Args:
            opens: Open prices array
            highs: High prices array
            lows: Low prices array
            closes: Close prices array
            lookback: Lookback period
            
        Returns:
            List of BOS events
        """
        bos_events = []
        
        for i in range(lookback, len(closes)):
            # Get recent high and low
            recent_high = np.max(highs[i - lookback:i])
            recent_low = np.min(lows[i - lookback:i])
            
            # Bullish BOS: Close above recent high
            if closes[i] > recent_high and closes[i - 1] <= recent_high:
                bos_events.append({
                    'type': 'bullish',
                    'index': i,
                    'level': recent_high,
                    'close': closes[i]
                })
            
            # Bearish BOS: Close below recent low
            if closes[i] < recent_low and closes[i - 1] >= recent_low:
                bos_events.append({
                    'type': 'bearish',
                    'index': i,
                    'level': recent_low,
                    'close': closes[i]
                })
        
        return bos_events
    
    @staticmethod
    def detect_liquidity_sweeps(
        opens: np.ndarray,
        highs: np.ndarray,
        lows: np.ndarray,
        closes: np.ndarray,
        lookback: int = 20
    ) -> List[Dict[str, any]]:
        """Detect liquidity sweeps.
        
        Args:
            opens: Open prices array
            highs: High prices array
            lows: Low prices array
            closes: Close prices array
            lookback: Lookback period
            
        Returns:
            List of liquidity sweep events
        """
        sweeps = []
        
        for i in range(lookback, len(closes)):
            # Find recent swings
            recent_high = np.max(highs[i - lookback:i])
            recent_low = np.min(lows[i - lookback:i])
            
            # Bullish sweep: Low below recent low, close above it
            if lows[i] < recent_low and closes[i] > recent_low:
                sweeps.append({
                    'type': 'bullish',
                    'index': i,
                    'sweep_level': recent_low,
                    'low': lows[i]
                })
            
            # Bearish sweep: High above recent high, close below it
            if highs[i] > recent_high and closes[i] < recent_high:
                sweeps.append({
                    'type': 'bearish',
                    'index': i,
                    'sweep_level': recent_high,
                    'high': highs[i]
                })
        
        return sweeps
    
    @staticmethod
    def detect_equal_highs_lows(
        highs: np.ndarray,
        lows: np.ndarray,
        lookback: int = 20,
        tolerance: float = 0.002
    ) -> Dict[str, List[Dict[str, any]]]:
        """Detect equal highs and equal lows.
        
        Args:
            highs: High prices array
            lows: Low prices array
            lookback: Lookback period
            tolerance: Tolerance level (as % of price)
            
        Returns:
            Dictionary with equal highs and lows
        """
        equal_levels = {'highs': [], 'lows': []}
        
        for i in range(1, len(highs)):
            # Equal highs
            for j in range(max(0, i - lookback), i):
                if abs(highs[i] - highs[j]) / highs[j] < tolerance:
                    equal_levels['highs'].append({
                        'level': highs[i],
                        'first_index': j,
                        'second_index': i
                    })
            
            # Equal lows
            for j in range(max(0, i - lookback), i):
                if abs(lows[i] - lows[j]) / lows[j] < tolerance:
                    equal_levels['lows'].append({
                        'level': lows[i],
                        'first_index': j,
                        'second_index': i
                    })
        
        return equal_levels
    
    @staticmethod
    def detect_supply_demand(
        opens: np.ndarray,
        highs: np.ndarray,
        lows: np.ndarray,
        closes: np.ndarray,
        volumes: np.ndarray,
        lookback: int = 20
    ) -> List[Dict[str, any]]:
        """Detect supply and demand zones.
        
        Args:
            opens: Open prices array
            highs: High prices array
            lows: Low prices array
            closes: Close prices array
            volumes: Volume array
            lookback: Lookback period
            
        Returns:
            List of supply/demand zones
        """
        zones = []
        
        for i in range(lookback, len(closes)):
            # Demand zone: Strong rejection from support with high volume
            if closes[i] > opens[i] and volumes[i] > np.mean(volumes[i-lookback:i]):
                zones.append({
                    'type': 'demand',
                    'high': highs[i],
                    'low': lows[i],
                    'index': i,
                    'volume': volumes[i]
                })
            
            # Supply zone: Strong rejection from resistance with high volume
            if closes[i] < opens[i] and volumes[i] > np.mean(volumes[i-lookback:i]):
                zones.append({
                    'type': 'supply',
                    'high': highs[i],
                    'low': lows[i],
                    'index': i,
                    'volume': volumes[i]
                })
        
        return zones
    
    @staticmethod
    def analyze_market_structure(
        highs: np.ndarray,
        lows: np.ndarray,
        closes: np.ndarray
    ) -> Dict[str, any]:
        """Comprehensive market structure analysis.
        
        Args:
            highs: High prices array
            lows: Low prices array
            closes: Close prices array
            
        Returns:
            Dictionary with complete market structure analysis
        """
        analysis = {}
        
        # Trend identification
        analysis['trend'] = MarketStructureAnalyzer._identify_trend(closes)
        
        # Support and resistance
        analysis['support_levels'] = MarketStructureAnalyzer._find_support_levels(lows)
        analysis['resistance_levels'] = MarketStructureAnalyzer._find_resistance_levels(highs)
        
        # Higher/Lower Highs and Lows
        analysis['higher_lows'] = closes[-1] > np.min(closes[-20:])
        analysis['higher_highs'] = closes[-1] > np.max(closes[-20:-1])
        
        return analysis
    
    @staticmethod
    def _identify_trend(prices: np.ndarray) -> str:
        """Identify price trend."""
        if len(prices) < 2:
            return 'unknown'
        
        recent_close = prices[-1]
        earlier_close = prices[-20] if len(prices) >= 20 else prices[0]
        
        if recent_close > earlier_close:
            return 'uptrend'
        elif recent_close < earlier_close:
            return 'downtrend'
        else:
            return 'sideways'
    
    @staticmethod
    def _find_support_levels(lows: np.ndarray, count: int = 3) -> List[float]:
        """Find key support levels."""
        return sorted(lows[-50:])[:count]
    
    @staticmethod
    def _find_resistance_levels(highs: np.ndarray, count: int = 3) -> List[float]:
        """Find key resistance levels."""
        return sorted(highs[-50:], reverse=True)[:count]
