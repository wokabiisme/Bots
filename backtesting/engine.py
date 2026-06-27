"""Backtesting engine for strategy evaluation."""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime, timedelta
from loguru import logger
from dataclasses import dataclass, field
from backtesting.metrics import PerformanceMetrics


@dataclass
class Trade:
    """Trade result."""
    symbol: str
    entry_time: datetime
    entry_price: float
    exit_time: Optional[datetime] = None
    exit_price: Optional[float] = None
    quantity: float = 0
    side: str = 'BUY'
    profit_loss: float = 0
    profit_loss_percent: float = 0
    commission: float = 0
    duration: Optional[timedelta] = None


@dataclass
class BacktestResult:
    """Backtest result summary."""
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0
    total_profit_loss: float = 0
    profit_factor: float = 0
    max_drawdown: float = 0
    sharpe_ratio: float = 0
    sortino_ratio: float = 0
    calmar_ratio: float = 0
    roi: float = 0
    trades: List[Trade] = field(default_factory=list)
    equity_curve: List[float] = field(default_factory=list)
    metrics: Dict[str, float] = field(default_factory=dict)


class BacktestEngine:
    """Backtest trading strategies."""
    
    def __init__(
        self,
        initial_capital: float = 10000,
        commission: float = 0.001
    ):
        """Initialize backtesting engine.
        
        Args:
            initial_capital: Starting capital
            commission: Commission per trade
        """
        self.initial_capital = initial_capital
        self.commission = commission
        self.capital = initial_capital
        self.equity = initial_capital
        self.peak_equity = initial_capital
        self.trades: List[Trade] = []
        self.equity_curve: List[float] = []
    
    def reset(self) -> None:
        """Reset backtest state."""
        self.capital = self.initial_capital
        self.equity = self.initial_capital
        self.peak_equity = self.initial_capital
        self.trades = []
        self.equity_curve = []
    
    def run(
        self,
        data: pd.DataFrame,
        strategy_func: Callable,
        initial_capital: Optional[float] = None
    ) -> BacktestResult:
        """Run backtest with strategy.
        
        Args:
            data: OHLCV data with columns [open, high, low, close, volume]
            strategy_func: Strategy function that returns signals
            initial_capital: Override initial capital
            
        Returns:
            Backtest results
        """
        if initial_capital:
            self.initial_capital = initial_capital
        
        self.reset()
        
        try:
            positions = {}  # Track open positions
            
            for idx in range(1, len(data)):
                bar = data.iloc[idx]
                prev_bar = data.iloc[idx - 1]
                symbol = data.index[idx] if hasattr(data.index, 'name') else 'SYMBOL'
                
                # Update equity
                self.equity = self.capital
                if positions:
                    for pos in positions.values():
                        unrealized_pnl = (bar['close'] - pos['entry_price']) * pos['quantity']
                        self.equity += unrealized_pnl
                
                self.equity_curve.append(self.equity)
                
                if self.equity > self.peak_equity:
                    self.peak_equity = self.equity
                
                # Get signal from strategy
                signal = strategy_func(data, idx)
                
                if signal == 'BUY' and 'position' not in positions:
                    # Calculate position size
                    quantity = (self.capital * 0.95) / bar['close']  # Risk 95% of capital
                    entry_cost = quantity * bar['close'] * (1 + self.commission)
                    
                    if entry_cost <= self.capital:
                        positions['position'] = {
                            'entry_time': bar.name if hasattr(bar, 'name') else idx,
                            'entry_price': bar['close'],
                            'quantity': quantity,
                            'side': 'BUY'
                        }
                        self.capital -= entry_cost
                
                elif signal == 'SELL' and 'position' in positions:
                    # Close position
                    pos = positions['position']
                    exit_value = pos['quantity'] * bar['close'] * (1 - self.commission)
                    profit_loss = exit_value - (pos['quantity'] * pos['entry_price'] * (1 + self.commission))
                    
                    trade = Trade(
                        symbol=symbol,
                        entry_time=pos['entry_time'],
                        entry_price=pos['entry_price'],
                        exit_time=bar.name if hasattr(bar, 'name') else idx,
                        exit_price=bar['close'],
                        quantity=pos['quantity'],
                        side=pos['side'],
                        profit_loss=profit_loss,
                        profit_loss_percent=(profit_loss / (pos['quantity'] * pos['entry_price'])) * 100,
                        commission=self.commission * 2
                    )
                    
                    self.trades.append(trade)
                    self.capital += exit_value
                    del positions['position']
            
            # Close any remaining positions at end
            if positions:
                last_price = data.iloc[-1]['close']
                for pos in positions.values():
                    exit_value = pos['quantity'] * last_price * (1 - self.commission)
                    profit_loss = exit_value - (pos['quantity'] * pos['entry_price'] * (1 + self.commission))
                    
                    trade = Trade(
                        symbol=symbol,
                        entry_time=pos['entry_time'],
                        entry_price=pos['entry_price'],
                        exit_time=data.index[-1],
                        exit_price=last_price,
                        quantity=pos['quantity'],
                        side=pos['side'],
                        profit_loss=profit_loss,
                        profit_loss_percent=(profit_loss / (pos['quantity'] * pos['entry_price'])) * 100
                    )
                    self.trades.append(trade)
            
            return self._generate_report()
        
        except Exception as e:
            logger.error(f"Backtest error: {e}")
            return BacktestResult()
    
    def _generate_report(self) -> BacktestResult:
        """Generate backtest report.
        
        Returns:
            Backtest result
        """
        total_trades = len(self.trades)
        winning_trades = len([t for t in self.trades if t.profit_loss > 0])
        losing_trades = total_trades - winning_trades
        
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        gross_profit = sum([t.profit_loss for t in self.trades if t.profit_loss > 0])
        gross_loss = abs(sum([t.profit_loss for t in self.trades if t.profit_loss < 0]))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
        
        total_pnl = sum([t.profit_loss for t in self.trades])
        roi = (total_pnl / self.initial_capital) * 100 if self.initial_capital > 0 else 0
        
        # Calculate drawdown
        peak = self.initial_capital
        max_drawdown = 0
        for equity in self.equity_curve:
            if equity > peak:
                peak = equity
            drawdown = (peak - equity) / peak if peak > 0 else 0
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        # Calculate Sharpe ratio
        returns = []
        for i in range(1, len(self.equity_curve)):
            ret = (self.equity_curve[i] - self.equity_curve[i-1]) / self.equity_curve[i-1]
            returns.append(ret)
        
        sharpe_ratio = 0
        if returns:
            mean_return = np.mean(returns)
            std_return = np.std(returns)
            sharpe_ratio = (mean_return * 252) / std_return if std_return > 0 else 0
        
        metrics = PerformanceMetrics.calculate(
            trades=self.trades,
            initial_capital=self.initial_capital,
            equity_curve=self.equity_curve
        )
        
        return BacktestResult(
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            total_profit_loss=total_pnl,
            profit_factor=profit_factor,
            max_drawdown=max_drawdown * 100,
            sharpe_ratio=sharpe_ratio,
            roi=roi,
            trades=self.trades,
            equity_curve=self.equity_curve,
            metrics=metrics
        )
