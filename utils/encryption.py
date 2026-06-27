"""Encryption utilities for sensitive data."""

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from cryptography.hazmat.backends import default_backend
import base64
import os
from typing import Optional
from loguru import logger


class EncryptionManager:
    """Manage encryption and decryption of sensitive data."""
    
    def __init__(self, master_key: Optional[str] = None):
        """Initialize encryption manager.
        
        Args:
            master_key: Master encryption key (uses env var if not provided)
        """
        if master_key is None:
            master_key = os.getenv('API_KEY_ENCRYPTION_KEY')
            if not master_key:
                raise ValueError("Encryption key not provided and API_KEY_ENCRYPTION_KEY env var not set")
        
        self.master_key = master_key
        self._cipher_suite: Optional[Fernet] = None
    
    @property
    def cipher_suite(self) -> Fernet:
        """Get or create cipher suite.
        
        Returns:
            Fernet cipher suite
        """
        if self._cipher_suite is None:
            key = self._derive_key(self.master_key)
            self._cipher_suite = Fernet(key)
        
        return self._cipher_suite
    
    @staticmethod
    def _derive_key(password: str, salt: bytes = b'trading_bot_salt') -> bytes:
        """Derive encryption key from password.
        
        Args:
            password: Master password
            salt: Salt for key derivation
            
        Returns:
            Derived encryption key
        """
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key
    
    def encrypt(self, data: str) -> str:
        """Encrypt string data.
        
        Args:
            data: Data to encrypt
            
        Returns:
            Encrypted data (base64 encoded)
        """
        try:
            encrypted = self.cipher_suite.encrypt(data.encode())
            return base64.b64encode(encrypted).decode()
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt string data.
        
        Args:
            encrypted_data: Encrypted data (base64 encoded)
            
        Returns:
            Decrypted data
        """
        try:
            encrypted = base64.b64decode(encrypted_data.encode())
            decrypted = self.cipher_suite.decrypt(encrypted)
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise
    
    def encrypt_api_key(self, api_key: str, label: Optional[str] = None) -> dict:
        """Encrypt API key with optional label.
        
        Args:
            api_key: API key to encrypt
            label: Optional label for the key
            
        Returns:
            Dictionary with encrypted key and metadata
        """
        return {
            'encrypted_key': self.encrypt(api_key),
            'label': label,
            'algorithm': 'Fernet',
            'encrypted': True
        }
    
    def decrypt_api_key(self, encrypted_key_dict: dict) -> str:
        """Decrypt API key from encrypted dictionary.
        
        Args:
            encrypted_key_dict: Dictionary with encrypted key
            
        Returns:
            Decrypted API key
        """
        if not encrypted_key_dict.get('encrypted'):
            raise ValueError("Data is not marked as encrypted")
        
        return self.decrypt(encrypted_key_dict['encrypted_key'])
