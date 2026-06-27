"""Position sizing strategies."""

from typing import Dict, Optional
from loguru import logger
import math


class PositionSizer:
    """Calculate optimal position sizes."""
    
    @staticmethod
    def kelly_criterion(
        win_rate: float,
        profit_loss_ratio: float,
        max_fraction: float = 0.25
    ) -> float:
        """Calculate position size using Kelly Criterion.
        
        Args:
            win_rate: Historical win rate (0-1)
            profit_loss_ratio: Avg profit / Avg loss ratio
            max_fraction: Maximum fraction of Kelly (usually 0.25)
            
        Returns:
            Recommended risk fraction (0-1)
        """
        if win_rate == 0 or win_rate == 1:
            return 0.0
        
        loss_rate = 1 - win_rate
        kelly = (win_rate * profit_loss_ratio - loss_rate) / profit_loss_ratio
        kelly = max(0, min(kelly, 1))  # Clamp to 0-1
        
        # Use fractional Kelly for safety
        return kelly * max_fraction
    
    @staticmethod
    def fixed_fractional(
        account_size: float,
        risk_percent: float = 1.0
    ) -> float:
        """Calculate position size using fixed fractional method.
        
        Args:
            account_size: Account size
            risk_percent: Risk percentage per trade (default 1%)
            
        Returns:
            Amount to risk per trade
        """
        return account_size * (risk_percent / 100)
    
    @staticmethod
    def optimal_f(
        trades: list,
        account_size: float
    ) -> float:
        """Calculate optimal f using Ralph Vince's method.
        
        Args:
            trades: List of trade P&L values
            account_size: Account size
            
        Returns:
            Recommended f value
        """
        if not trades or len(trades) == 0:
            return 0.02  # Default 2%
        
        max_loss = min(trades)  # Most negative (largest loss)
        largest_win = max(trades)  # Largest profit
        
        if max_loss == 0:
            return 0.02
        
        avg_trade = sum(trades) / len(trades)
        
        # Simple calculation
        win_percent = len([t for t in trades if t > 0]) / len(trades)
        
        if win_percent == 0 or win_percent == 1:
            return 0.02
        
        # Simplified optimal f
        f = (win_percent / abs(max_loss / account_size)) - (1 - win_percent) / (largest_win / account_size)
        f = max(0.01, min(f, 0.25))  # Clamp between 1-25%
        
        return f
    
    @staticmethod
    def volatility_adjusted(
        account_size: float,
        volatility: float,
        risk_percent: float = 1.0
    ) -> float:
        """Calculate position size adjusted for volatility.
        
        Args:
            account_size: Account size
            volatility: Current volatility (ATR or similar)
            risk_percent: Target risk percentage
            
        Returns:
            Adjusted position size risk
        """
        base_risk = account_size * (risk_percent / 100)
        
        # Higher volatility = smaller position
        volatility_factor = 0.1 / max(volatility, 0.01)
        adjusted_risk = base_risk * volatility_factor
        
        return max(adjusted_risk, base_risk * 0.5)  # Don't go below 50% of base
    
    @staticmethod
    def calculate_position_quantity(
        account_size: float,
        entry_price: float,
        stop_loss_price: float,
        risk_percent: float = 1.0
    ) -> float:
        """Calculate position quantity based on stop loss.
        
        Args:
            account_size: Account size
            entry_price: Entry price
            stop_loss_price: Stop loss price
            risk_percent: Risk percentage per trade
            
        Returns:
            Position quantity
        """
        risk_amount = account_size * (risk_percent / 100)
        price_difference = abs(entry_price - stop_loss_price)
        
        if price_difference == 0:
            return 0
        
        quantity = risk_amount / price_difference
        return quantity
    
    @staticmethod
    def calculate_stop_loss(
        entry_price: float,
        account_size: float,
        quantity: float,
        risk_percent: float = 1.0,
        direction: str = 'long'
    ) -> float:
        """Calculate stop loss level based on risk.
        
        Args:
            entry_price: Entry price
            account_size: Account size
            quantity: Position quantity
            risk_percent: Risk percentage per trade
            direction: 'long' or 'short'
            
        Returns:
            Stop loss price
        """
        risk_amount = account_size * (risk_percent / 100)
        risk_per_unit = risk_amount / quantity
        
        if direction.lower() == 'long':
            stop_loss = entry_price - risk_per_unit
        else:
            stop_loss = entry_price + risk_per_unit
        
        return stop_loss
    
    @staticmethod
    def calculate_take_profit(
        entry_price: float,
        stop_loss: float,
        reward_ratio: float = 2.0,
        direction: str = 'long'
    ) -> float:
        """Calculate take profit based on risk/reward ratio.
        
        Args:
            entry_price: Entry price
            stop_loss: Stop loss price
            reward_ratio: Risk/reward ratio (e.g., 2.0 for 1:2)
            direction: 'long' or 'short'
            
        Returns:
            Take profit price
        """
        risk = abs(entry_price - stop_loss)
        reward = risk * reward_ratio
        
        if direction.lower() == 'long':
            take_profit = entry_price + reward
        else:
            take_profit = entry_price - reward
        
        return take_profit
    
    @staticmethod
    def multi_level_tp(
        entry_price: float,
        stop_loss: float,
        reward_ratio: float = 2.0,
        levels: int = 3,
        direction: str = 'long'
    ) -> Dict[int, float]:
        """Calculate multi-level take profit prices.
        
        Args:
            entry_price: Entry price
            stop_loss: Stop loss price
            reward_ratio: Total risk/reward ratio
            levels: Number of TP levels
            direction: 'long' or 'short'
            
        Returns:
            Dictionary with TP levels
        """
        risk = abs(entry_price - stop_loss)
        total_reward = risk * reward_ratio
        reward_per_level = total_reward / levels
        
        tp_levels = {}
        for i in range(1, levels + 1):
            if direction.lower() == 'long':
                tp_levels[i] = entry_price + (reward_per_level * i)
            else:
                tp_levels[i] = entry_price - (reward_per_level * i)
        
        return tp_levels
    
    @staticmethod
    def correlation_adjusted_size(
        base_size: float,
        correlations: Dict[str, float],
        max_correlation_threshold: float = 0.7
    ) -> float:
        """Adjust position size based on correlation with existing positions.
        
        Args:
            base_size: Base position size
            correlations: Dictionary of symbol correlations
            max_correlation_threshold: Maximum acceptable correlation
            
        Returns:
            Adjusted position size
        """
        if not correlations:
            return base_size
        
        avg_correlation = sum(correlations.values()) / len(correlations)
        
        if avg_correlation > max_correlation_threshold:
            # Reduce size based on correlation
            reduction_factor = 1 - (avg_correlation - max_correlation_threshold)
            adjusted_size = base_size * reduction_factor
            logger.info(f"Position size reduced due to high correlation: {base_size} -> {adjusted_size}")
            return adjusted_size
        
        return base_size
