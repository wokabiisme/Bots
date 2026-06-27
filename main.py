"""Main trading bot application."""

import asyncio
from typing import Dict, Optional, List
from datetime import datetime
from loguru import logger
from execution.brokers.base import BaseBroker, OrderSide, OrderType
from risk.manager import RiskManager, RiskLimits
from strategies.base_strategy import BaseStrategy
from ai.models import ModelManager


class TradingBot:
    """Main trading bot application."""
    
    def __init__(
        self,
        broker: BaseBroker,
        strategy: BaseStrategy,
        risk_manager: Optional[RiskManager] = None
    ):
        """Initialize trading bot.
        
        Args:
            broker: Broker connector
            strategy: Trading strategy
            risk_manager: Risk management system
        """
        self.broker = broker
        self.strategy = strategy
        self.risk_manager = risk_manager or RiskManager()
        self.is_running = False
        self.positions = {}
        self.trade_history = []
        self.model_manager = ModelManager()
    
    async def start(self) -> bool:
        """Start the trading bot.
        
        Returns:
            True if started successfully
        """
        try:
            # Connect to broker
            if not await self.broker.connect():
                logger.error("Failed to connect to broker")
                return False
            
            self.is_running = True
            logger.info(f"Trading bot started - Strategy: {self.strategy.name}")
            return True
        
        except Exception as e:
            logger.error(f"Error starting trading bot: {e}")
            return False
    
    async def stop(self) -> bool:
        """Stop the trading bot.
        
        Returns:
            True if stopped successfully
        """
        try:
            self.is_running = False
            
            # Close any open positions
            await self._close_all_positions()
            
            # Disconnect from broker
            await self.broker.disconnect()
            
            logger.info("Trading bot stopped")
            return True
        
        except Exception as e:
            logger.error(f"Error stopping trading bot: {e}")
            return False
    
    async def update(self, market_data: Dict) -> None:
        """Update bot with new market data.
        
        Args:
            market_data: Current market data
        """
        if not self.is_running:
            return
        
        try:
            # Update strategy
            signal = self.strategy.update(market_data)
            
            # Check risk limits
            account_info = await self.broker.get_account_info()
            self.risk_manager.update_equity(account_info.equity)
            
            all_ok, limits = self.risk_manager.check_all_limits(account_info.balance)
            
            if not all_ok:
                logger.warning(f"Risk limits exceeded: {limits}")
                await self._close_all_positions()
                return
            
            # Execute signal
            await self._execute_signal(signal, market_data)
        
        except Exception as e:
            logger.error(f"Error updating bot: {e}")
    
    async def _execute_signal(self, signal: str, market_data: Dict) -> None:
        """Execute trading signal.
        
        Args:
            signal: Trading signal
            market_data: Current market data
        """
        symbol = market_data.get('symbol', self.strategy.symbol)
        current_price = market_data.get('close', 0)
        
        if signal == 'BUY':
            await self._open_position(symbol, OrderSide.BUY, current_price)
        
        elif signal == 'SELL':
            await self._close_position(symbol)
    
    async def _open_position(
        self,
        symbol: str,
        side: OrderSide,
        current_price: float
    ) -> None:
        """Open new position.
        
        Args:
            symbol: Trading symbol
            side: Order side
            current_price: Current price
        """
        try:
            if symbol in self.positions:
                logger.info(f"Position already open: {symbol}")
                return
            
            # Check position limit
            if not self.risk_manager.check_position_limit():
                logger.warning("Position limit reached")
                return
            
            # Calculate position size
            account_info = await self.broker.get_account_info()
            risk_amount = self.risk_manager.limits.max_risk_per_trade / 100 * account_info.balance
            quantity = risk_amount / current_price
            
            # Place order
            order = await self.broker.place_order(
                symbol=symbol,
                side=side,
                quantity=quantity,
                order_type=OrderType.MARKET
            )
            
            if order.order_id != "error":
                self.positions[symbol] = {
                    'order_id': order.order_id,
                    'entry_price': current_price,
                    'quantity': quantity,
                    'side': side,
                    'entry_time': datetime.utcnow()
                }
                
                self.risk_manager.open_positions += 1
                logger.info(f"Position opened: {symbol} @ {current_price} x {quantity}")
        
        except Exception as e:
            logger.error(f"Error opening position: {e}")
    
    async def _close_position(self, symbol: str) -> None:
        """Close position.
        
        Args:
            symbol: Trading symbol
        """
        try:
            if symbol not in self.positions:
                logger.info(f"No open position: {symbol}")
                return
            
            position = self.positions[symbol]
            
            # Get current price
            ticker = await self.broker.get_ticker(symbol)
            current_price = ticker.get('last', 0)
            
            # Place close order
            close_side = OrderSide.SELL if position['side'] == OrderSide.BUY else OrderSide.BUY
            
            order = await self.broker.place_order(
                symbol=symbol,
                side=close_side,
                quantity=position['quantity'],
                order_type=OrderType.MARKET
            )
            
            if order.order_id != "error":
                profit_loss = (current_price - position['entry_price']) * position['quantity']
                
                self.trade_history.append({
                    'symbol': symbol,
                    'entry_price': position['entry_price'],
                    'exit_price': current_price,
                    'quantity': position['quantity'],
                    'profit_loss': profit_loss,
                    'duration': datetime.utcnow() - position['entry_time']
                })
                
                self.risk_manager.open_positions -= 1
                
                if profit_loss > 0:
                    self.risk_manager.record_trade_profit(profit_loss)
                else:
                    self.risk_manager.record_trade_loss(abs(profit_loss))
                
                del self.positions[symbol]
                
                logger.info(f"Position closed: {symbol} @ {current_price} PnL: {profit_loss:.2f}")
        
        except Exception as e:
            logger.error(f"Error closing position: {e}")
    
    async def _close_all_positions(self) -> None:
        """Close all open positions."""
        symbols = list(self.positions.keys())
        for symbol in symbols:
            await self._close_position(symbol)
    
    def get_status(self) -> Dict:
        """Get bot status.
        
        Returns:
            Status dictionary
        """
        return {
            'is_running': self.is_running,
            'strategy': self.strategy.name,
            'open_positions': len(self.positions),
            'total_trades': len(self.trade_history),
            'risk_summary': self.risk_manager.get_risk_summary(self.risk_manager.current_equity)
        }
