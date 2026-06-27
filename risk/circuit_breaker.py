"""Circuit breaker for emergency shutdown."""

from datetime import datetime, timedelta
from loguru import logger
from typing import Optional
import asyncio


class CircuitBreaker:
    """Circuit breaker for automatic emergency shutdown."""
    
    def __init__(
        self,
        loss_threshold: float = 10.0,  # % loss to trigger
        recovery_time: int = 300  # seconds to recover
    ):
        """Initialize circuit breaker.
        
        Args:
            loss_threshold: Loss threshold percentage
            recovery_time: Recovery time in seconds
        """
        self.loss_threshold = loss_threshold
        self.recovery_time = recovery_time
        self.is_open = False
        self.trip_time: Optional[datetime] = None
        self.trip_count = 0
    
    def check_loss(self, current_equity: float, starting_equity: float) -> bool:
        """Check if circuit should break due to loss.
        
        Args:
            current_equity: Current account equity
            starting_equity: Starting equity
            
        Returns:
            True if circuit should remain closed (trading allowed)
        """
        if current_equity == 0 or starting_equity == 0:
            return True
        
        loss_percent = ((starting_equity - current_equity) / starting_equity) * 100
        
        if loss_percent >= self.loss_threshold:
            self.trip()
            return False
        
        return True
    
    def trip(self) -> None:
        """Open the circuit (stop trading)."""
        if not self.is_open:
            self.is_open = True
            self.trip_time = datetime.utcnow()
            self.trip_count += 1
            logger.critical(f"Circuit breaker OPEN - Trading halted (trip #{self.trip_count})")
    
    def check_recovery(self) -> bool:
        """Check if circuit can recover.
        
        Returns:
            True if recovery time has passed
        """
        if not self.is_open:
            return True
        
        if self.trip_time is None:
            return True
        
        elapsed = (datetime.utcnow() - self.trip_time).total_seconds()
        
        if elapsed >= self.recovery_time:
            return True
        
        return False
    
    def reset(self) -> None:
        """Reset circuit to closed state."""
        self.is_open = False
        self.trip_time = None
        logger.info("Circuit breaker reset - Trading resumed")
    
    def auto_reset(self) -> bool:
        """Attempt auto recovery after recovery time.
        
        Returns:
            True if successfully reset
        """
        if self.check_recovery():
            self.reset()
            return True
        
        return False
    
    def get_status(self) -> dict:
        """Get circuit breaker status.
        
        Returns:
            Status dictionary
        """
        remaining_time = 0
        if self.is_open and self.trip_time:
            elapsed = (datetime.utcnow() - self.trip_time).total_seconds()
            remaining_time = max(0, self.recovery_time - elapsed)
        
        return {
            'is_open': self.is_open,
            'trip_count': self.trip_count,
            'trip_time': self.trip_time,
            'remaining_recovery_time': remaining_time,
            'loss_threshold': self.loss_threshold
        }
    
    async def wait_for_recovery(self) -> None:
        """Async wait for circuit recovery."""
        while self.is_open:
            await asyncio.sleep(1)
            self.auto_reset()
