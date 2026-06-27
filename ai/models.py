"""Machine learning model management."""

import os
import pickle
import numpy as np
from typing import Dict, Optional, Tuple
from datetime import datetime
from loguru import logger
from pathlib import Path


class ModelManager:
    """Manage AI/ML model lifecycle."""
    
    def __init__(self, models_dir: str = "models"):
        """Initialize model manager.
        
        Args:
            models_dir: Directory to store models
        """
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.models: Dict[str, any] = {}
        self.model_metadata: Dict[str, dict] = {}
    
    def save_model(
        self,
        model: any,
        model_name: str,
        metadata: Optional[dict] = None
    ) -> bool:
        """Save model to disk.
        
        Args:
            model: Model object to save
            model_name: Name of the model
            metadata: Optional metadata dictionary
            
        Returns:
            True if saved successfully
        """
        try:
            model_path = self.models_dir / f"{model_name}.pkl"
            
            with open(model_path, 'wb') as f:
                pickle.dump(model, f)
            
            self.model_metadata[model_name] = {
                'saved_at': datetime.utcnow().isoformat(),
                'path': str(model_path),
                'metadata': metadata or {}
            }
            
            logger.info(f"Model saved: {model_name}")
            return True
        
        except Exception as e:
            logger.error(f"Error saving model {model_name}: {e}")
            return False
    
    def load_model(self, model_name: str) -> Optional[any]:
        """Load model from disk.
        
        Args:
            model_name: Name of the model
            
        Returns:
            Model object or None
        """
        try:
            model_path = self.models_dir / f"{model_name}.pkl"
            
            if not model_path.exists():
                logger.warning(f"Model not found: {model_name}")
                return None
            
            with open(model_path, 'rb') as f:
                model = pickle.load(f)
            
            self.models[model_name] = model
            logger.info(f"Model loaded: {model_name}")
            return model
        
        except Exception as e:
            logger.error(f"Error loading model {model_name}: {e}")
            return None
    
    def delete_model(self, model_name: str) -> bool:
        """Delete model from disk.
        
        Args:
            model_name: Name of the model
            
        Returns:
            True if deleted successfully
        """
        try:
            model_path = self.models_dir / f"{model_name}.pkl"
            
            if model_path.exists():
                model_path.unlink()
            
            if model_name in self.models:
                del self.models[model_name]
            
            if model_name in self.model_metadata:
                del self.model_metadata[model_name]
            
            logger.info(f"Model deleted: {model_name}")
            return True
        
        except Exception as e:
            logger.error(f"Error deleting model {model_name}: {e}")
            return False
    
    def get_model_metadata(self, model_name: str) -> Optional[dict]:
        """Get model metadata.
        
        Args:
            model_name: Name of the model
            
        Returns:
            Metadata dictionary or None
        """
        return self.model_metadata.get(model_name)
    
    def list_models(self) -> list:
        """List all available models.
        
        Returns:
            List of model names
        """
        models = [f.stem for f in self.models_dir.glob('*.pkl')]
        return models
    
    def get_model(
        self,
        model_name: str,
        load_if_missing: bool = True
    ) -> Optional[any]:
        """Get model, loading if necessary.
        
        Args:
            model_name: Name of the model
            load_if_missing: Load from disk if not in memory
            
        Returns:
            Model object or None
        """
        if model_name in self.models:
            return self.models[model_name]
        
        if load_if_missing:
            return self.load_model(model_name)
        
        return None
    
    def cache_model(self, model_name: str, model: any) -> None:
        """Cache model in memory.
        
        Args:
            model_name: Name of the model
            model: Model object
        """
        self.models[model_name] = model
        logger.debug(f"Model cached: {model_name}")
    
    def clear_cache(self) -> None:
        """Clear all cached models."""
        self.models.clear()
        logger.info("Model cache cleared")
