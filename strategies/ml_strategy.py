"""Machine learning based trading strategy."""

import numpy as np
from typing import Dict, Optional
from strategies.base_strategy import BaseStrategy
from loguru import logger


class MLStrategy(BaseStrategy):
    """ML-based trading strategy."""
    
    def __init__(self, symbol: str = "EURUSD", model: Optional[any] = None):
        """Initialize ML strategy.
        
        Args:
            symbol: Trading symbol
            model: Trained ML model
        """
        super().__init__("MLStrategy", symbol)
        self.model = model
        self.set_parameters({
            'confidence_threshold': 0.65,
            'lookback': 50
        })
    
    def calculate_indicators(self, data: Dict) -> None:
        """Calculate indicators for ML model.
        
        Args:
            data: OHLCV data
        """
        closes = np.array(data.get('close', []))
        lookback = self.get_parameter('lookback')
        
        if len(closes) < lookback:
            return
        
        # Calculate features
        self.indicators['returns'] = np.diff(closes[-lookback:]) / closes[-lookback:-1]
        self.indicators['price_momentum'] = (closes[-1] - closes[-lookback]) / closes[-lookback]
        self.indicators['volatility'] = np.std(self.indicators['returns'])
        self.indicators['sma_ratio'] = closes[-1] / np.mean(closes[-lookback:])
    
    def generate_signal(self) -> str:
        """Generate ML-based signal.
        
        Returns:
            Trading signal
        """
        if not self.model:
            logger.warning("No model loaded for ML strategy")
            return 'HOLD'
        
        if 'returns' not in self.indicators:
            return 'HOLD'
        
        try:
            # Prepare features
            features = np.array([
                self.indicators.get('price_momentum', 0),
                self.indicators.get('volatility', 0),
                self.indicators.get('sma_ratio', 1.0),
                np.mean(self.indicators.get('returns', [0]))
            ]).reshape(1, -1)
            
            # Get prediction
            prediction = self.model.predict(features)[0]
            
            # Get probability if available
            confidence = 0.5
            if hasattr(self.model, 'predict_proba'):
                proba = self.model.predict_proba(features)[0]
                confidence = max(proba)
            
            threshold = self.get_parameter('confidence_threshold')
            
            if confidence > threshold:
                return 'BUY' if prediction > 0.5 else 'SELL'
            
            return 'HOLD'
        
        except Exception as e:
            logger.error(f"Error generating ML signal: {e}")
            return 'HOLD'
    
    def set_model(self, model: any) -> None:
        """Set ML model.
        
        Args:
            model: Trained ML model
        """
        self.model = model
        logger.info("ML model updated")
