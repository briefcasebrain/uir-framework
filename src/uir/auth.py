"""Authentication and authorization module"""

import hashlib
import secrets
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
import structlog

logger = structlog.get_logger()


class AuthManager:
    """Manages authentication and authorization"""
    
    def __init__(
        self,
        secret_key: str = None,
        algorithm: str = "HS256",
        access_token_expire_minutes: int = 30
    ):
        self.secret_key = secret_key or secrets.token_urlsafe(32)
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.api_keys: Dict[str, Dict[str, Any]] = {}
        self.users: Dict[str, Dict[str, Any]] = {}
        self.logger = logger.bind(component="auth")
    
    def create_api_key(
        self,
        user_id: str,
        name: str = "default",
        permissions: Optional[List[str]] = None,
        rate_limit: Optional[int] = None,
        expires_at: Optional[datetime] = None
    ) -> str:
        """Create new API key"""
        api_key = f"uir_{secrets.token_urlsafe(32)}"
        api_key_hash = self._hash_api_key(api_key)
        
        self.api_keys[api_key_hash] = {
            "user_id": user_id,
            "name": name,
            "permissions": permissions or ["search", "vector_search"],
            "rate_limit": rate_limit,
            "expires_at": expires_at,
            "created_at": datetime.now(),
            "last_used": None,
            "usage_count": 0
        }
        
        self.logger.info(f"Created API key for user {user_id}")
        return api_key
    
    def validate_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Validate API key and return associated data"""
        api_key_hash = self._hash_api_key(api_key)
        
        if api_key_hash not in self.api_keys:
            return None
        
        key_data = self.api_keys[api_key_hash]
        
        # Check expiration
        if key_data.get("expires_at") and key_data["expires_at"] < datetime.now():
            self.logger.warning(f"Expired API key used: {api_key_hash[:8]}...")
            return None
        
        # Update usage stats
        key_data["last_used"] = datetime.now()
        key_data["usage_count"] += 1
        
        return key_data
    
    def create_access_token(
        self,
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError as e:
            self.logger.error(f"Token verification failed: {e}")
            return None
    
    def check_permission(
        self,
        key_data: Dict[str, Any],
        required_permission: str
    ) -> bool:
        """Check if API key has required permission"""
        permissions = key_data.get("permissions", [])
        
        # Check for wildcard permission
        if "*" in permissions or "admin" in permissions:
            return True
        
        return required_permission in permissions
    
    def get_rate_limit(self, key_data: Dict[str, Any]) -> Optional[int]:
        """Get rate limit for API key"""
        return key_data.get("rate_limit")
    
    def _hash_api_key(self, api_key: str) -> str:
        """Hash API key for storage"""
        return self.pwd_context.hash(api_key)
    
    def create_user(
        self,
        email: str,
        password: str,
        role: str = "user",
        organization: Optional[str] = None
    ) -> str:
        """Create new user"""
        user_id = secrets.token_urlsafe(16)
        password_hash = self.pwd_context.hash(password)
        
        self.users[email] = {
            "user_id": user_id,
            "email": email,
            "password_hash": password_hash,
            "role": role,
            "organization": organization,
            "created_at": datetime.now(),
            "last_login": None
        }
        
        self.logger.info(f"Created user: {email}")
        return user_id
    
    def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user with email and password"""
        user = self.users.get(email)
        
        if not user:
            return None
        
        if not self.pwd_context.verify(password, user["password_hash"]):
            return None
        
        user["last_login"] = datetime.now()
        return user
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        for user in self.users.values():
            if user["user_id"] == user_id:
                return user
        return None


class RateLimitManager:
    """Manages rate limiting for API requests"""
    
    def __init__(self):
        self.request_counts: Dict[str, List[datetime]] = {}
        self.logger = logger.bind(component="rate_limiter")
    
    def check_rate_limit(
        self,
        identifier: str,
        limit: int,
        window_seconds: int = 60
    ) -> bool:
        """Check if request is within rate limit"""
        now = datetime.now()
        
        # Initialize if first request
        if identifier not in self.request_counts:
            self.request_counts[identifier] = []
        
        # Remove old requests outside window
        cutoff = now - timedelta(seconds=window_seconds)
        self.request_counts[identifier] = [
            ts for ts in self.request_counts[identifier]
            if ts > cutoff
        ]
        
        # Check if within limit
        if len(self.request_counts[identifier]) >= limit:
            self.logger.warning(
                f"Rate limit exceeded for {identifier}: "
                f"{len(self.request_counts[identifier])}/{limit}"
            )
            return False
        
        # Add current request
        self.request_counts[identifier].append(now)
        return True
    
    def get_remaining_requests(
        self,
        identifier: str,
        limit: int,
        window_seconds: int = 60
    ) -> int:
        """Get number of remaining requests in current window"""
        now = datetime.now()
        
        if identifier not in self.request_counts:
            return limit
        
        # Count requests in current window
        cutoff = now - timedelta(seconds=window_seconds)
        current_count = sum(
            1 for ts in self.request_counts[identifier]
            if ts > cutoff
        )
        
        return max(0, limit - current_count)
    
    def get_reset_time(
        self,
        identifier: str,
        window_seconds: int = 60
    ) -> Optional[datetime]:
        """Get time when rate limit resets"""
        if identifier not in self.request_counts or not self.request_counts[identifier]:
            return None
        
        # Find oldest request in window
        oldest = min(self.request_counts[identifier])
        return oldest + timedelta(seconds=window_seconds)