import os
import hashlib
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import logging

logger = logging.getLogger(__name__)

class EncryptionService:
    def __init__(self, master_key: str):
        """Initialize encryption service with master key"""
        self.master_key = master_key.encode()
        
    def generate_user_key(self, user_id: str, user_password_hash: str) -> bytes:
        """Generate user-specific encryption key using PBKDF2"""
        try:
            # Use user_id as salt combined with part of password hash
            salt = hashlib.sha256(f"{user_id}:{user_password_hash[:32]}".encode()).digest()
            
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(self.master_key))
            return key
        except Exception as e:
            logger.error(f"Error generating user key: {e}")
            raise
    
    def encrypt_fact(self, fact_value: str, user_id: str, user_password_hash: str) -> str:
        """Encrypt fact value using user-specific key"""
        try:
            user_key = self.generate_user_key(user_id, user_password_hash)
            f = Fernet(user_key)
            encrypted_value = f.encrypt(fact_value.encode())
            return base64.urlsafe_b64encode(encrypted_value).decode()
        except Exception as e:
            logger.error(f"Error encrypting fact: {e}")
            raise
    
    def decrypt_fact(self, encrypted_fact: str, user_id: str, user_password_hash: str) -> str:
        """Decrypt fact value using user-specific key"""
        try:
            user_key = self.generate_user_key(user_id, user_password_hash)
            f = Fernet(user_key)
            
            # Decode the base64 encoded encrypted data
            encrypted_data = base64.urlsafe_b64decode(encrypted_fact.encode())
            decrypted_value = f.decrypt(encrypted_data)
            return decrypted_value.decode()
        except Exception as e:
            logger.error(f"Error decrypting fact: {e}")
            raise
    
    def encrypt_sensitive_fact(self, fact_value: str, user_id: str, user_password_hash: str) -> str:
        """Double encrypt sensitive facts"""
        try:
            # First encryption with user key
            first_encryption = self.encrypt_fact(fact_value, user_id, user_password_hash)
            
            # Second encryption with master key
            master_f = Fernet(base64.urlsafe_b64encode(self.master_key[:32]))
            double_encrypted = master_f.encrypt(first_encryption.encode())
            return base64.urlsafe_b64encode(double_encrypted).decode()
        except Exception as e:
            logger.error(f"Error double encrypting sensitive fact: {e}")
            raise
    
    def decrypt_sensitive_fact(self, double_encrypted_fact: str, user_id: str, user_password_hash: str) -> str:
        """Decrypt double encrypted sensitive facts"""
        try:
            # First decryption with master key
            master_f = Fernet(base64.urlsafe_b64encode(self.master_key[:32]))
            encrypted_data = base64.urlsafe_b64decode(double_encrypted_fact.encode())
            first_decryption = master_f.decrypt(encrypted_data).decode()
            
            # Second decryption with user key
            return self.decrypt_fact(first_decryption, user_id, user_password_hash)
        except Exception as e:
            logger.error(f"Error decrypting sensitive fact: {e}")
            raise
    
    def rotate_user_key(self, old_password_hash: str, new_password_hash: str, user_id: str, encrypted_facts: list) -> list:
        """Rotate user encryption key by re-encrypting facts with new key"""
        try:
            rotated_facts = []
            
            for encrypted_fact in encrypted_facts:
                # Decrypt with old key
                decrypted_value = self.decrypt_fact(encrypted_fact, user_id, old_password_hash)
                
                # Re-encrypt with new key
                new_encrypted_value = self.encrypt_fact(decrypted_value, user_id, new_password_hash)
                rotated_facts.append(new_encrypted_value)
                
            return rotated_facts
        except Exception as e:
            logger.error(f"Error rotating user key: {e}")
            raise 