import uuid
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext

from ..config import settings
from ..models.database import User
from ..models.schemas import UserCreate, UserLogin, Token
from .storage_service import StorageService

class AuthService:
    """
    Service class for handling authentication operations
    """
    
    def __init__(self):
        self.storage_service = StorageService()
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a plain password against a hashed password"""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Generate password hash"""
        return self.pwd_context.hash(password)
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.jwt_algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[dict]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
            username: str = payload.get("sub")
            
            if username is None:
                return None
                
            return {"username": username, "user_id": payload.get("user_id")}
            
        except JWTError:
            return None
    
    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password"""
        user = self.storage_service.get_user_by_email(email)
        
        if not user:
            return None
            
        if not self.verify_password(password, user.hashed_password):
            return None
            
        # Update last active
        self.storage_service.update_user_last_active(user.id)
        
        return user
    
    def register_user(self, user_data: UserCreate) -> User:
        """Register a new user"""
        # Check if user already exists
        existing_user = self.storage_service.get_user_by_email(user_data.email)
        if existing_user:
            raise ValueError("User with this email already exists")
        
        # Hash password
        hashed_password = self.get_password_hash(user_data.password)
        
        # Create user data
        user_dict = {
            "email": user_data.email,
            "hashed_password": hashed_password,
            "timezone": user_data.timezone
        }
        
        # Create user in database
        user = self.storage_service.create_user(user_dict)
        return user
    
    def login_user(self, login_data: UserLogin) -> dict:
        """Login user and return access token"""
        user = self.authenticate_user(login_data.email, login_data.password)
        
        if not user:
            raise ValueError("Incorrect email or password")
        
        # Create access token
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = self.create_access_token(
            data={"sub": user.email, "user_id": str(user.id)},
            expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": str(user.id),
                "email": user.email,
                "timezone": user.timezone,
                "created_at": user.created_at,
                "last_active": user.last_active
            }
        }
    
    def get_current_user(self, token: str) -> Optional[User]:
        """Get current user from JWT token"""
        token_data = self.verify_token(token)
        
        if not token_data:
            return None
        
        user_id = token_data.get("user_id")
        if not user_id:
            return None
        
        try:
            user = self.storage_service.get_user_by_id(uuid.UUID(user_id))
            return user
        except (ValueError, TypeError):
            return None
    
    def refresh_token(self, token: str) -> Optional[dict]:
        """Refresh an access token"""
        token_data = self.verify_token(token)
        
        if not token_data:
            return None
        
        user_id = token_data.get("user_id")
        username = token_data.get("username")
        
        if not user_id or not username:
            return None
        
        # Create new token
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = self.create_access_token(
            data={"sub": username, "user_id": user_id},
            expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer"
        }
    
    def logout_user(self, token: str) -> bool:
        """Logout user (in a full implementation, this would blacklist the token)"""
        # In a production system, you would typically:
        # 1. Add the token to a blacklist/redis store
        # 2. Set token expiration
        # For now, we'll just return True as logout is handled client-side
        return True
    
    def change_password(self, user_id: uuid.UUID, old_password: str, new_password: str) -> bool:
        """Change user password"""
        user = self.storage_service.get_user_by_id(user_id)
        
        if not user:
            return False
        
        # Verify old password
        if not self.verify_password(old_password, user.hashed_password):
            return False
        
        # Hash new password
        new_hashed_password = self.get_password_hash(new_password)
        
        # Update password in database
        try:
            update_data = {"hashed_password": new_hashed_password}
            updated_user = self.storage_service.update_user(user_id, update_data)
            return updated_user is not None
        except Exception:
            return False
    
    def update_user_profile(self, user_id: uuid.UUID, update_data: dict) -> Optional[User]:
        """Update user profile information"""
        try:
            # Only allow certain fields to be updated
            allowed_fields = {"timezone"}
            filtered_data = {k: v for k, v in update_data.items() if k in allowed_fields}
            
            if not filtered_data:
                return None
            
            return self.storage_service.update_user(user_id, filtered_data)
        except Exception:
            return None 