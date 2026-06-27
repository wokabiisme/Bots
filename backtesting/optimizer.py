"""Strategy optimization using parameter tuning."""

import numpy as np
from typing import Dict, List, Tuple, Callable, Optional
from itertools import product
from loguru import logger
from backtesting.engine import BacktestEngine, BacktestResult


class StrategyOptimizer:
    """Optimize strategy parameters."""
    
    def __init__(self, engine: Optional[BacktestEngine] = None):
        """Initialize optimizer.
        
        Args:
            engine: Backtest engine instance
        """
        self.engine = engine or BacktestEngine()
        self.optimization_results: List[Tuple[Dict, BacktestResult]] = []
    
    def optimize(
        self,
        data,
        strategy_func: Callable,
        param_ranges: Dict[str, List],
        metric: str = 'sharpe_ratio',
        initial_capital: float = 10000
    ) -> Tuple[Dict, BacktestResult]:
        """Optimize strategy parameters using grid search.
        
        Args:
            data: OHLCV data
            strategy_func: Strategy function that takes data and params
            param_ranges: Dictionary of parameter ranges to test
            metric: Metric to optimize for
            initial_capital: Starting capital
            
        Returns:
            Tuple of (best_params, best_result)
        """
        try:
            param_names = list(param_ranges.keys())
            param_values = list(param_ranges.values())
            
            best_result = None
            best_params = None
            best_metric_value = -np.inf
            
            total_combinations = np.prod([len(v) for v in param_values])
            logger.info(f"Testing {total_combinations} parameter combinations")
            
            combination_count = 0
            
            for values in product(*param_values):
                combination_count += 1
                params = dict(zip(param_names, values))
                
                try:
                    # Create strategy function with parameters
                    def param_strategy(data, idx, p=params):
                        return strategy_func(data, idx, **p)
                    
                    # Run backtest
                    result = self.engine.run(
                        data=data,
                        strategy_func=param_strategy,
                        initial_capital=initial_capital
                    )
                    
                    # Get metric value
                    metric_value = result.metrics.get(metric, 0)
                    
                    self.optimization_results.append((params, result))
                    
                    if metric_value > best_metric_value:
                        best_metric_value = metric_value
                        best_result = result
                        best_params = params
                    
                    if combination_count % 10 == 0:
                        logger.debug(f"Tested {combination_count}/{int(total_combinations)} combinations")
                
                except Exception as e:
                    logger.warning(f"Error testing parameters {params}: {e}")
                    continue
            
            logger.info(f"Optimization complete. Best {metric}: {best_metric_value:.2f}")
            logger.info(f"Best parameters: {best_params}")
            
            return best_params or {}, best_result or BacktestResult()
        
        except Exception as e:
            logger.error(f"Optimization error: {e}")
            return {}, BacktestResult()
    
    def optimize_bayesian(
        self,
        data,
        strategy_func: Callable,
        param_ranges: Dict[str, Tuple[float, float]],
        metric: str = 'sharpe_ratio',
        initial_capital: float = 10000,
        n_calls: int = 50
    ) -> Tuple[Dict, BacktestResult]:
        """Optimize using Bayesian optimization (requires skopt).
        
        Args:
            data: OHLCV data
            strategy_func: Strategy function
            param_ranges: Dictionary of (min, max) parameter ranges
            metric: Metric to optimize
            initial_capital: Starting capital
            n_calls: Number of optimization iterations
            
        Returns:
            Tuple of (best_params, best_result)
        """
        try:
            from skopt import gp_minimize
            from skopt.space import Real, Integer
            
            param_names = list(param_ranges.keys())
            space = []
            
            for name, (min_val, max_val) in param_ranges.items():
                if isinstance(min_val, int):
                    space.append(Integer(min_val, max_val, name=name))
                else:
                    space.append(Real(min_val, max_val, name=name))
            
            def objective(values):
                params = dict(zip(param_names, values))
                
                try:
                    def param_strategy(data, idx, p=params):
                        return strategy_func(data, idx, **p)
                    
                    result = self.engine.run(
                        data=data,
                        strategy_func=param_strategy,
                        initial_capital=initial_capital
                    )
                    
                    # Return negative because minimizing
                    metric_value = result.metrics.get(metric, 0)
                    self.optimization_results.append((params, result))
                    
                    return -metric_value
                
                except Exception as e:
                    logger.warning(f"Error in objective: {e}")
                    return 0
            
            result = gp_minimize(
                objective,
                space,
                n_calls=n_calls,
                random_state=42
            )
            
            best_params = dict(zip(param_names, result.x))
            
            # Run final backtest with best params
            def param_strategy(data, idx, p=best_params):
                return strategy_func(data, idx, **p)
            
            best_result = self.engine.run(
                data=data,
                strategy_func=param_strategy,
                initial_capital=initial_capital
            )
            
            logger.info(f"Bayesian optimization complete")
            logger.info(f"Best parameters: {best_params}")
            
            return best_params, best_result
        
        except ImportError:
            logger.error("skopt not installed. Use pip install scikit-optimize")
            return {}, BacktestResult()
        except Exception as e:
            logger.error(f"Bayesian optimization error: {e}")
            return {}, BacktestResult()
    
    def get_results_sorted(
        self,
        metric: str = 'sharpe_ratio',
        top_n: int = 10
    ) -> List[Tuple[Dict, BacktestResult]]:
        """Get optimization results sorted by metric.
        
        Args:
            metric: Metric to sort by
            top_n: Number of top results to return
            
        Returns:
            List of (params, result) tuples sorted by metric
        """
        sorted_results = sorted(
            self.optimization_results,
            key=lambda x: x[1].metrics.get(metric, 0),
            reverse=True
        )
        
        return sorted_results[:top_n]
    
    def print_results(
        self,
        metric: str = 'sharpe_ratio',
        top_n: int = 10
    ) -> None:
        """Print optimization results.
        
        Args:
            metric: Metric to display
            top_n: Number of results to show
        """
        results = self.get_results_sorted(metric, top_n)
        
        print(f"\n=== Top {top_n} Results (sorted by {metric}) ===")
        print(f"{'Rank':<5} {metric:<15} {'Params':<50}")
        print("-" * 70)
        
        for i, (params, result) in enumerate(results, 1):
            metric_value = result.metrics.get(metric, 0)
            params_str = str(params)[:50]
            print(f"{i:<5} {metric_value:<15.2f} {params_str:<50}")
