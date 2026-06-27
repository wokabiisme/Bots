"""Risk management system."""

from typing import Dict, Optional, Tuple
from decimal import Decimal
from datetime import datetime, timedelta
from loguru import logger
from dataclasses import dataclass


@dataclass
class RiskLimits:
    """Risk limit configuration."""
    max_risk_per_trade: float = 1.0  # % of account
    max_daily_loss: float = 2.0  # % of account
    max_weekly_loss: float = 5.0  # % of account
    max_monthly_loss: float = 10.0  # % of account
    max_drawdown: float = 15.0  # % of peak equity
    max_open_positions: int = 10
    max_correlation: float = 0.7  # Max correlation between positions
    min_win_rate: float = 0.45  # Minimum acceptable win rate
    min_profit_factor: float = 2.0  # Minimum profit factor


class RiskManager:
    """Manage trading risks and limits."""
    
    def __init__(self, limits: Optional[RiskLimits] = None):
        """Initialize risk manager.
        
        Args:
            limits: Risk limit configuration
        """
        self.limits = limits or RiskLimits()
        self.daily_loss = 0.0
        self.weekly_loss = 0.0
        self.monthly_loss = 0.0
        self.peak_equity = 0.0
        self.current_equity = 0.0
        self.open_positions = 0
        self.daily_reset_time = datetime.utcnow()
        self.weekly_reset_time = datetime.utcnow()
        self.monthly_reset_time = datetime.utcnow()
    
    def update_equity(self, equity: float) -> None:
        """Update current equity.
        
        Args:
            equity: Current account equity
        """
        self.current_equity = equity
        
        if equity > self.peak_equity:
            self.peak_equity = equity
    
    def check_daily_loss_limit(self, account_size: float) -> bool:
        """Check if daily loss limit exceeded.
        
        Args:
            account_size: Account size
            
        Returns:
            True if within limit
        """
        loss_percent = (self.daily_loss / account_size) * 100
        
        if loss_percent >= self.limits.max_daily_loss:
            logger.warning(f"Daily loss limit exceeded: {loss_percent:.2f}% >= {self.limits.max_daily_loss}%")
            return False
        
        return True
    
    def check_weekly_loss_limit(self, account_size: float) -> bool:
        """Check if weekly loss limit exceeded.
        
        Args:
            account_size: Account size
            
        Returns:
            True if within limit
        """
        loss_percent = (self.weekly_loss / account_size) * 100
        
        if loss_percent >= self.limits.max_weekly_loss:
            logger.warning(f"Weekly loss limit exceeded: {loss_percent:.2f}% >= {self.limits.max_weekly_loss}%")
            return False
        
        return True
    
    def check_monthly_loss_limit(self, account_size: float) -> bool:
        """Check if monthly loss limit exceeded.
        
        Args:
            account_size: Account size
            
        Returns:
            True if within limit
        """
        loss_percent = (self.monthly_loss / account_size) * 100
        
        if loss_percent >= self.limits.max_monthly_loss:
            logger.warning(f"Monthly loss limit exceeded: {loss_percent:.2f}% >= {self.limits.max_monthly_loss}%")
            return False
        
        return True
    
    def check_drawdown_limit(self) -> bool:
        """Check if maximum drawdown exceeded.
        
        Returns:
            True if within limit
        """
        if self.peak_equity == 0:
            return True
        
        drawdown_percent = ((self.peak_equity - self.current_equity) / self.peak_equity) * 100
        
        if drawdown_percent >= self.limits.max_drawdown:
            logger.warning(f"Maximum drawdown exceeded: {drawdown_percent:.2f}% >= {self.limits.max_drawdown}%")
            return False
        
        return True
    
    def check_position_limit(self) -> bool:
        """Check if maximum open positions limit exceeded.
        
        Returns:
            True if within limit
        """
        if self.open_positions >= self.limits.max_open_positions:
            logger.warning(f"Max open positions limit reached: {self.open_positions} >= {self.limits.max_open_positions}")
            return False
        
        return True
    
    def check_all_limits(self, account_size: float) -> Tuple[bool, Dict[str, bool]]:
        """Check all risk limits.
        
        Args:
            account_size: Account size
            
        Returns:
            Tuple of (all_ok, limits_dict)
        """
        limits_check = {
            'daily_loss': self.check_daily_loss_limit(account_size),
            'weekly_loss': self.check_weekly_loss_limit(account_size),
            'monthly_loss': self.check_monthly_loss_limit(account_size),
            'drawdown': self.check_drawdown_limit(),
            'positions': self.check_position_limit()
        }
        
        all_ok = all(limits_check.values())
        return all_ok, limits_check
    
    def record_trade_loss(self, loss_amount: float) -> None:
        """Record a trade loss.
        
        Args:
            loss_amount: Loss amount
        """
        self.daily_loss += loss_amount
        self.weekly_loss += loss_amount
        self.monthly_loss += loss_amount
    
    def record_trade_profit(self, profit_amount: float) -> None:
        """Record a trade profit.
        
        Args:
            profit_amount: Profit amount
        """
        self.daily_loss = max(0, self.daily_loss - profit_amount)
        self.weekly_loss = max(0, self.weekly_loss - profit_amount)
        self.monthly_loss = max(0, self.monthly_loss - profit_amount)
    
    def reset_daily(self) -> None:
        """Reset daily counters."""
        self.daily_loss = 0.0
        self.daily_reset_time = datetime.utcnow()
        logger.info("Daily limits reset")
    
    def reset_weekly(self) -> None:
        """Reset weekly counters."""
        self.weekly_loss = 0.0
        self.weekly_reset_time = datetime.utcnow()
        logger.info("Weekly limits reset")
    
    def reset_monthly(self) -> None:
        """Reset monthly counters."""
        self.monthly_loss = 0.0
        self.monthly_reset_time = datetime.utcnow()
        logger.info("Monthly limits reset")
    
    def get_risk_summary(self, account_size: float) -> Dict[str, float]:
        """Get risk summary.
        
        Args:
            account_size: Account size
            
        Returns:
            Dictionary with risk metrics
        """
        drawdown_percent = ((self.peak_equity - self.current_equity) / max(self.peak_equity, 1)) * 100
        
        return {
            'daily_loss_percent': (self.daily_loss / account_size) * 100,
            'weekly_loss_percent': (self.weekly_loss / account_size) * 100,
            'monthly_loss_percent': (self.monthly_loss / account_size) * 100,
            'drawdown_percent': max(0, drawdown_percent),
            'open_positions': self.open_positions,
            'current_equity': self.current_equity,
            'peak_equity': self.peak_equity
        }
