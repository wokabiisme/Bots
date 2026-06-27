"""Trading signal prediction using machine learning."""

import numpy as np
from typing import Dict, List, Tuple, Optional
from sklearn.preprocessing import StandardScaler
from loguru import logger


class SignalPredictor:
    """Predict trading signals using ML models."""
    
    def __init__(self):
        """Initialize signal predictor."""
        self.scaler = StandardScaler()
        self.feature_names = []
    
    def prepare_features(
        self,
        indicators: Dict[str, np.ndarray],
        lookback: int = 50
    ) -> Tuple[np.ndarray, List[str]]:
        """Prepare features for model prediction.
        
        Args:
            indicators: Dictionary of technical indicators
            lookback: Lookback period
            
        Returns:
            Tuple of (features array, feature names)
        """
        features = []
        feature_names = []
        
        for indicator_name, values in indicators.items():
            if len(values) > 0:
                # Add indicator value
                features.append(values[-1])
                feature_names.append(indicator_name)
                
                # Add rate of change
                if len(values) > 1:
                    roc = (values[-1] - values[-2]) / max(abs(values[-2]), 1e-10)
                    features.append(roc)
                    feature_names.append(f"{indicator_name}_roc")
                
                # Add momentum (difference)
                if len(values) > lookback:
                    momentum = values[-1] - np.mean(values[-lookback:])
                    features.append(momentum)
                    feature_names.append(f"{indicator_name}_momentum")
        
        self.feature_names = feature_names
        return np.array(features).reshape(1, -1), feature_names
    
    def predict(
        self,
        model: any,
        indicators: Dict[str, np.ndarray],
        threshold: float = 0.5
    ) -> Dict[str, any]:
        """Predict trading signal.
        
        Args:
            model: Trained ML model
            indicators: Dictionary of technical indicators
            threshold: Confidence threshold
            
        Returns:
            Dictionary with signal prediction
        """
        try:
            features, feature_names = self.prepare_features(indicators)
            
            # Normalize features
            features_scaled = self.scaler.fit_transform(features)
            
            # Get prediction
            prediction = model.predict(features_scaled)[0]
            
            # Get probability if available
            probability = 0.5
            if hasattr(model, 'predict_proba'):
                proba = model.predict_proba(features_scaled)[0]
                probability = max(proba)
            elif hasattr(model, 'decision_function'):
                decision = model.decision_function(features_scaled)[0]
                # Convert to probability-like score
                probability = 1 / (1 + np.exp(-decision))
            
            # Determine signal
            signal = 'HOLD'
            confidence = probability
            
            if probability > threshold:
                signal = 'BUY' if prediction > 0.5 else 'SELL'
            
            return {
                'signal': signal,
                'confidence': confidence,
                'prediction': prediction,
                'probability': probability,
                'features': features[0],
                'feature_names': feature_names
            }
        
        except Exception as e:
            logger.error(f"Error making prediction: {e}")
            return {
                'signal': 'HOLD',
                'confidence': 0,
                'prediction': 0,
                'probability': 0,
                'error': str(e)
            }
    
    def batch_predict(
        self,
        model: any,
        indicators_list: List[Dict[str, np.ndarray]],
        threshold: float = 0.5
    ) -> List[Dict[str, any]]:
        """Predict signals for multiple sets of indicators.
        
        Args:
            model: Trained ML model
            indicators_list: List of indicator dictionaries
            threshold: Confidence threshold
            
        Returns:
            List of predictions
        """
        predictions = []
        
        for indicators in indicators_list:
            pred = self.predict(model, indicators, threshold)
            predictions.append(pred)
        
        return predictions
    
    def feature_importance(
        self,
        model: any,
        top_n: int = 10
    ) -> Dict[str, float]:
        """Get feature importance from model.
        
        Args:
            model: Trained ML model
            top_n: Number of top features to return
            
        Returns:
            Dictionary of feature importance scores
        """
        try:
            if hasattr(model, 'feature_importances_'):
                importance = model.feature_importances_
            elif hasattr(model, 'coef_'):
                importance = np.abs(model.coef_[0])
            else:
                logger.warning("Model doesn't have feature importance")
                return {}
            
            # Get top features
            top_indices = np.argsort(importance)[-top_n:][::-1]
            
            importance_dict = {}
            for idx in top_indices:
                if idx < len(self.feature_names):
                    importance_dict[self.feature_names[idx]] = float(importance[idx])
            
            return importance_dict
        
        except Exception as e:
            logger.error(f"Error getting feature importance: {e}")
            return {}
