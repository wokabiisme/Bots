"""Ensemble machine learning model."""

import numpy as np
from typing import Dict, List, Optional, Tuple
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from loguru import logger


class EnsembleModel:
    """Ensemble of multiple ML models for signal prediction."""
    
    def __init__(self, models: Optional[Dict[str, any]] = None):
        """Initialize ensemble model.
        
        Args:
            models: Dictionary of models to ensemble
        """
        self.models = models or {}
        self.weights = {}
        self.model_scores = {}
    
    def add_model(self, name: str, model: any, weight: float = 1.0) -> None:
        """Add model to ensemble.
        
        Args:
            name: Model name
            model: Model object
            weight: Model weight in voting
        """
        self.models[name] = model
        self.weights[name] = weight
        logger.info(f"Added model to ensemble: {name} (weight: {weight})")
    
    def remove_model(self, name: str) -> None:
        """Remove model from ensemble.
        
        Args:
            name: Model name
        """
        if name in self.models:
            del self.models[name]
            if name in self.weights:
                del self.weights[name]
            if name in self.model_scores:
                del self.model_scores[name]
            logger.info(f"Removed model from ensemble: {name}")
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Make ensemble prediction.
        
        Args:
            X: Input features
            
        Returns:
            Ensemble predictions
        """
        if not self.models:
            logger.warning("No models in ensemble")
            return np.array([])
        
        predictions = []
        total_weight = sum(self.weights.values())
        
        for name, model in self.models.items():
            try:
                pred = model.predict(X)
                weight = self.weights.get(name, 1.0) / total_weight
                predictions.append(pred * weight)
            except Exception as e:
                logger.error(f"Error predicting with model {name}: {e}")
        
        if predictions:
            ensemble_pred = np.sum(predictions, axis=0)
            return np.round(ensemble_pred)
        
        return np.array([])
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Get ensemble prediction probabilities.
        
        Args:
            X: Input features
            
        Returns:
            Ensemble probabilities
        """
        if not self.models:
            logger.warning("No models in ensemble")
            return np.array([])
        
        probabilities = []
        total_weight = sum(self.weights.values())
        
        for name, model in self.models.items():
            try:
                if hasattr(model, 'predict_proba'):
                    proba = model.predict_proba(X)
                    weight = self.weights.get(name, 1.0) / total_weight
                    probabilities.append(proba * weight)
                else:
                    logger.warning(f"Model {name} doesn't have predict_proba")
            except Exception as e:
                logger.error(f"Error getting probabilities from {name}: {e}")
        
        if probabilities:
            ensemble_proba = np.sum(probabilities, axis=0)
            # Normalize to sum to 1
            return ensemble_proba / ensemble_proba.sum(axis=1, keepdims=True)
        
        return np.array([])
    
    def evaluate(
        self,
        X: np.ndarray,
        y: np.ndarray
    ) -> Dict[str, float]:
        """Evaluate ensemble model.
        
        Args:
            X: Test features
            y: Test labels
            
        Returns:
            Dictionary of evaluation metrics
        """
        try:
            y_pred = self.predict(X)
            
            metrics = {
                'accuracy': accuracy_score(y, y_pred),
                'precision': precision_score(y, y_pred, zero_division=0),
                'recall': recall_score(y, y_pred, zero_division=0),
                'f1': f1_score(y, y_pred, zero_division=0)
            }
            
            # Try to get AUC
            try:
                y_proba = self.predict_proba(X)
                if y_proba.size > 0:
                    metrics['auc_roc'] = roc_auc_score(y, y_proba[:, 1])
            except:
                pass
            
            return metrics
        
        except Exception as e:
            logger.error(f"Error evaluating ensemble: {e}")
            return {}
    
    def calibrate_weights(
        self,
        X_val: np.ndarray,
        y_val: np.ndarray,
        metric: str = 'f1'
    ) -> None:
        """Calibrate model weights based on validation performance.
        
        Args:
            X_val: Validation features
            y_val: Validation labels
            metric: Metric to use for calibration
        """
        try:
            for name, model in self.models.items():
                try:
                    y_pred = model.predict(X_val)
                    
                    if metric == 'accuracy':
                        score = accuracy_score(y_val, y_pred)
                    elif metric == 'f1':
                        score = f1_score(y_val, y_pred, zero_division=0)
                    elif metric == 'precision':
                        score = precision_score(y_val, y_pred, zero_division=0)
                    elif metric == 'recall':
                        score = recall_score(y_val, y_pred, zero_division=0)
                    else:
                        score = accuracy_score(y_val, y_pred)
                    
                    self.model_scores[name] = score
                    self.weights[name] = max(0.1, score)  # Min weight 0.1
                    
                except Exception as e:
                    logger.error(f"Error calibrating weight for {name}: {e}")
            
            logger.info(f"Model weights calibrated using {metric}")
        
        except Exception as e:
            logger.error(f"Error calibrating weights: {e}")
    
    def get_model_scores(self) -> Dict[str, float]:
        """Get scores for all models.
        
        Returns:
            Dictionary of model scores
        """
        return self.model_scores.copy()
    
    def get_weights(self) -> Dict[str, float]:
        """Get current model weights.
        
        Returns:
            Dictionary of model weights
        """
        return self.weights.copy()
    
    def set_weights(self, weights: Dict[str, float]) -> None:
        """Set model weights.
        
        Args:
            weights: Dictionary of model weights
        """
        for name, weight in weights.items():
            if name in self.models:
                self.weights[name] = weight
        logger.info("Model weights updated")
