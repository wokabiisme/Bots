"""Asynchronous utilities and helpers."""

import asyncio
from typing import Callable, Any, List, Coroutine, Optional
from loguru import logger
import time
from functools import wraps


class AsyncManager:
    """Manage asynchronous operations."""
    
    @staticmethod
    async def run_with_timeout(
        coro: Coroutine,
        timeout: float = 30.0,
        error_message: str = "Operation timed out"
    ) -> Any:
        """Run coroutine with timeout.
        
        Args:
            coro: Coroutine to run
            timeout: Timeout in seconds
            error_message: Error message if timeout occurs
            
        Returns:
            Coroutine result
        """
        try:
            return await asyncio.wait_for(coro, timeout=timeout)
        except asyncio.TimeoutError:
            logger.error(f"{error_message} (timeout: {timeout}s)")
            raise
    
    @staticmethod
    async def retry_async(
        coro_func: Callable,
        max_retries: int = 3,
        delay: float = 1.0,
        backoff: float = 2.0,
        *args,
        **kwargs
    ) -> Any:
        """Retry async function with exponential backoff.
        
        Args:
            coro_func: Async function to call
            max_retries: Maximum number of retries
            delay: Initial delay between retries (seconds)
            backoff: Backoff multiplier for delay
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
        """
        current_delay = delay
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                return await coro_func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < max_retries - 1:
                    logger.warning(
                        f"Attempt {attempt + 1}/{max_retries} failed: {e}. "
                        f"Retrying in {current_delay}s..."
                    )
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff
                else:
                    logger.error(f"All {max_retries} attempts failed")
        
        raise last_exception
    
    @staticmethod
    async def gather_with_limit(
        tasks: List[Coroutine],
        limit: int = 10
    ) -> List[Any]:
        """Run tasks with concurrency limit.
        
        Args:
            tasks: List of coroutines
            limit: Maximum concurrent tasks
            
        Returns:
            List of results
        """
        semaphore = asyncio.Semaphore(limit)
        
        async def bounded_task(task):
            async with semaphore:
                return await task
        
        return await asyncio.gather(*[bounded_task(task) for task in tasks])
    
    @staticmethod
    def async_timer(func: Callable) -> Callable:
        """Decorator to time async function execution.
        
        Args:
            func: Async function to time
            
        Returns:
            Wrapped function
        """
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = await func(*args, **kwargs)
                elapsed = time.time() - start
                logger.debug(f"{func.__name__} completed in {elapsed:.3f}s")
                return result
            except Exception as e:
                elapsed = time.time() - start
                logger.error(f"{func.__name__} failed after {elapsed:.3f}s: {e}")
                raise
        
        return wrapper
    
    @staticmethod
    def async_retry(
        max_retries: int = 3,
        delay: float = 1.0,
        backoff: float = 2.0
    ) -> Callable:
        """Decorator for async function retry with backoff.
        
        Args:
            max_retries: Maximum number of retries
            delay: Initial delay between retries
            backoff: Backoff multiplier
            
        Returns:
            Decorator function
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                current_delay = delay
                last_exception = None
                
                for attempt in range(max_retries):
                    try:
                        return await func(*args, **kwargs)
                    except Exception as e:
                        last_exception = e
                        if attempt < max_retries - 1:
                            logger.warning(
                                f"{func.__name__} attempt {attempt + 1}/{max_retries} failed. "
                                f"Retrying in {current_delay}s..."
                            )
                            await asyncio.sleep(current_delay)
                            current_delay *= backoff
                
                raise last_exception
            
            return wrapper
        return decorator


async def create_task_with_name(coro, name: str) -> asyncio.Task:
    """Create named async task.
    
    Args:
        coro: Coroutine
        name: Task name
        
    Returns:
        Named task
    """
    task = asyncio.create_task(coro)
    task.set_name(name)
    return task
