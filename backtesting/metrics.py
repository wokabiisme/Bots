"""Performance metrics calculation."""

import numpy as np
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from loguru import logger
from dataclasses import dataclass


@dataclass
class PerformanceMetrics:
    """Performance metrics."""
    
    @staticmethod
    def calculate(
        trades: List,
        initial_capital: float,
        equity_curve: List[float]
    ) -> Dict[str, float]:
        """Calculate all performance metrics.
        
        Args:
            trades: List of trades
            initial_capital: Starting capital
            equity_curve: Equity curve over time
            
        Returns:
            Dictionary of metrics
        """
        metrics = {}
        
        if not trades or not equity_curve:
            return {
                'total_return': 0,
                'annual_return': 0,
                'volatility': 0,
                'sharpe_ratio': 0,
                'sortino_ratio': 0,
                'max_drawdown': 0,
                'calmar_ratio': 0,
                'win_rate': 0,
                'profit_factor': 0,
                'consecutive_wins': 0,
                'consecutive_losses': 0,
                'average_win': 0,
                'average_loss': 0
            }
        
        # Total return
        final_value = equity_curve[-1] if equity_curve else initial_capital
        total_return = ((final_value - initial_capital) / initial_capital) * 100
        metrics['total_return'] = total_return
        
        # Annual return (assuming 252 trading days)
        days = len(equity_curve)
        years = days / 252 if days > 0 else 1
        annual_return = (total_return / years) if years > 0 else 0
        metrics['annual_return'] = annual_return
        
        # Volatility
        returns = []
        for i in range(1, len(equity_curve)):
            ret = (equity_curve[i] - equity_curve[i-1]) / equity_curve[i-1]
            returns.append(ret)
        
        volatility = np.std(returns) * np.sqrt(252) if returns else 0
        metrics['volatility'] = volatility * 100
        
        # Sharpe Ratio
        mean_return = np.mean(returns) if returns else 0
        sharpe_ratio = (mean_return * 252) / (volatility + 1e-10) if volatility > 0 else 0
        metrics['sharpe_ratio'] = sharpe_ratio
        
        # Sortino Ratio (only downside volatility)
        downside_returns = [r for r in returns if r < 0]
        downside_volatility = np.std(downside_returns) * np.sqrt(252) if downside_returns else 0
        sortino_ratio = (mean_return * 252) / (downside_volatility + 1e-10) if downside_volatility > 0 else 0
        metrics['sortino_ratio'] = sortino_ratio
        
        # Maximum Drawdown
        peak = initial_capital
        max_drawdown = 0
        for equity in equity_curve:
            if equity > peak:
                peak = equity
            drawdown = (peak - equity) / peak if peak > 0 else 0
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        metrics['max_drawdown'] = max_drawdown * 100
        
        # Calmar Ratio
        calmar_ratio = annual_return / (max_drawdown * 100 + 1e-10) if max_drawdown > 0 else 0
        metrics['calmar_ratio'] = calmar_ratio
        
        # Trade metrics
        winning_trades = [t for t in trades if t.profit_loss > 0]
        losing_trades = [t for t in trades if t.profit_loss < 0]
        
        win_rate = len(winning_trades) / len(trades) * 100 if trades else 0
        metrics['win_rate'] = win_rate
        
        gross_profit = sum([t.profit_loss for t in winning_trades])
        gross_loss = abs(sum([t.profit_loss for t in losing_trades]))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
        metrics['profit_factor'] = profit_factor
        
        # Consecutive wins/losses
        consecutive_wins = 0
        max_consecutive_wins = 0
        consecutive_losses = 0
        max_consecutive_losses = 0
        
        for trade in trades:
            if trade.profit_loss > 0:
                consecutive_wins += 1
                consecutive_losses = 0
                max_consecutive_wins = max(max_consecutive_wins, consecutive_wins)
            else:
                consecutive_losses += 1
                consecutive_wins = 0
                max_consecutive_losses = max(max_consecutive_losses, consecutive_losses)
        
        metrics['consecutive_wins'] = max_consecutive_wins
        metrics['consecutive_losses'] = max_consecutive_losses
        
        # Average win/loss
        avg_win = np.mean([t.profit_loss for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t.profit_loss for t in losing_trades]) if losing_trades else 0
        
        metrics['average_win'] = avg_win
        metrics['average_loss'] = avg_loss
        
        return metrics
    
    @staticmethod
    def print_report(metrics: Dict[str, float]) -> None:
        """Print metrics report.
        
        Args:
            metrics: Metrics dictionary
        """
        print("\n=== Performance Metrics ===")
        print(f"Total Return: {metrics.get('total_return', 0):.2f}%")
        print(f"Annual Return: {metrics.get('annual_return', 0):.2f}%")
        print(f"Volatility: {metrics.get('volatility', 0):.2f}%")
        print(f"Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.2f}")
        print(f"Sortino Ratio: {metrics.get('sortino_ratio', 0):.2f}")
        print(f"Max Drawdown: {metrics.get('max_drawdown', 0):.2f}%")
        print(f"Calmar Ratio: {metrics.get('calmar_ratio', 0):.2f}")
        print(f"\nTrade Metrics:")
        print(f"Win Rate: {metrics.get('win_rate', 0):.2f}%")
        print(f"Profit Factor: {metrics.get('profit_factor', 0):.2f}")
        print(f"Average Win: ${metrics.get('average_win', 0):.2f}")
        print(f"Average Loss: ${metrics.get('average_loss', 0):.2f}")
