"""
JWT Authentication Module for Synth Mind Dashboard.
Provides secure token-based authentication for production deployment.
"""

import hashlib
import secrets
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum

try:
    import jwt
except ImportError:
    import subprocess
    import sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "PyJWT"])
    import jwt


class UserRole(Enum):
    """User permission levels."""
    ADMIN = "admin"          # Full access
    OPERATOR = "operator"    # Can control, no user management
    VIEWER = "viewer"        # Read-only access


@dataclass
class User:
    """User account data."""
    username: str
    password_hash: str
    salt: str
    role: UserRole
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_login: Optional[str] = None
    active: bool = True

    def to_dict(self) -> dict:
        return {
            "username": self.username,
            "password_hash": self.password_hash,
            "salt": self.salt,
            "role": self.role.value,
            "created_at": self.created_at,
            "last_login": self.last_login,
            "active": self.active
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'User':
        return cls(
            username=data["username"],
            password_hash=data["password_hash"],
            salt=data["salt"],
            role=UserRole(data["role"]),
            created_at=data.get("created_at", datetime.now().isoformat()),
            last_login=data.get("last_login"),
            active=data.get("active", True)
        )


class AuthManager:
    """
    JWT Authentication Manager.
    Handles user authentication, token generation, and validation.
    """

    # Token expiration times
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    REFRESH_TOKEN_EXPIRE_DAYS = 7

    def __init__(self, data_dir: Optional[Path] = None, secret_key: Optional[str] = None):
        """
        Initialize authentication manager.

        Args:
            data_dir: Directory to store user data
            secret_key: JWT signing key (generated if not provided)
        """
        self.data_dir = data_dir or Path.home() / ".synth_mind" / "auth"
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.users_file = self.data_dir / "users.json"
        self.config_file = self.data_dir / "auth_config.json"

        # Load or generate secret key
        self.secret_key = secret_key or self._load_or_create_secret()

        # Load users
        self.users: Dict[str, User] = {}
        self._load_users()

        # Token blacklist (for logout)
        self.blacklisted_tokens: set = set()

    def _load_or_create_secret(self) -> str:
        """Load existing secret key or create new one."""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                return config.get("secret_key", secrets.token_hex(32))

        # Generate new secret
        secret = secrets.token_hex(32)
        self._save_config({"secret_key": secret})
        return secret

    def _save_config(self, config: dict):
        """Save authentication configuration."""
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
        os.chmod(self.config_file, 0o600)  # Secure permissions

    def _load_users(self):
        """Load users from storage."""
        if self.users_file.exists():
            with open(self.users_file, 'r') as f:
                data = json.load(f)
                self.users = {
                    username: User.from_dict(user_data)
                    for username, user_data in data.items()
                }

    def _save_users(self):
        """Save users to storage."""
        data = {username: user.to_dict() for username, user in self.users.items()}
        with open(self.users_file, 'w') as f:
            json.dump(data, f, indent=2)
        os.chmod(self.users_file, 0o600)  # Secure permissions

    def _hash_password(self, password: str, salt: Optional[str] = None) -> Tuple[str, str]:
        """
        Hash password with salt using PBKDF2.

        Returns:
            Tuple of (hash, salt)
        """
        if salt is None:
            salt = secrets.token_hex(16)

        # Use PBKDF2 with SHA256
        password_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000  # iterations
        ).hex()

        return password_hash, salt

    def _verify_password(self, password: str, password_hash: str, salt: str) -> bool:
        """Verify password against hash."""
        computed_hash, _ = self._hash_password(password, salt)
        return secrets.compare_digest(computed_hash, password_hash)

    # User Management

    def create_user(self, username: str, password: str, role: UserRole = UserRole.VIEWER) -> Tuple[bool, str]:
        """
        Create a new user account.

        Returns:
            Tuple of (success, message)
        """
        if username in self.users:
            return False, "Username already exists"

        if len(password) < 8:
            return False, "Password must be at least 8 characters"

        password_hash, salt = self._hash_password(password)

        self.users[username] = User(
            username=username,
            password_hash=password_hash,
            salt=salt,
            role=role
        )
        self._save_users()

        return True, f"User '{username}' created successfully"

    def delete_user(self, username: str) -> Tuple[bool, str]:
        """Delete a user account."""
        if username not in self.users:
            return False, "User not found"

        del self.users[username]
        self._save_users()

        return True, f"User '{username}' deleted"

    def update_password(self, username: str, new_password: str) -> Tuple[bool, str]:
        """Update user password."""
        if username not in self.users:
            return False, "User not found"

        if len(new_password) < 8:
            return False, "Password must be at least 8 characters"

        password_hash, salt = self._hash_password(new_password)
        self.users[username].password_hash = password_hash
        self.users[username].salt = salt
        self._save_users()

        return True, "Password updated"

    def update_role(self, username: str, new_role: UserRole) -> Tuple[bool, str]:
        """Update user role."""
        if username not in self.users:
            return False, "User not found"

        self.users[username].role = new_role
        self._save_users()

        return True, f"Role updated to {new_role.value}"

    def list_users(self) -> list:
        """List all users (without sensitive data)."""
        return [
            {
                "username": user.username,
                "role": user.role.value,
                "created_at": user.created_at,
                "last_login": user.last_login,
                "active": user.active
            }
            for user in self.users.values()
        ]

    def has_admin(self) -> bool:
        """Check if any admin user exists."""
        return any(user.role == UserRole.ADMIN for user in self.users.values())

    # Authentication

    def authenticate(self, username: str, password: str) -> Tuple[bool, Optional[Dict]]:
        """
        Authenticate user credentials.

        Returns:
            Tuple of (success, tokens_dict or None)
        """
        if username not in self.users:
            return False, None

        user = self.users[username]

        if not user.active:
            return False, None

        if not self._verify_password(password, user.password_hash, user.salt):
            return False, None

        # Update last login
        user.last_login = datetime.now().isoformat()
        self._save_users()

        # Generate tokens
        access_token = self._generate_access_token(user)
        refresh_token = self._generate_refresh_token(user)

        return True, {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": self.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": {
                "username": user.username,
                "role": user.role.value
            }
        }

    def _generate_access_token(self, user: User) -> str:
        """Generate JWT access token."""
        payload = {
            "sub": user.username,
            "role": user.role.value,
            "type": "access",
            "exp": datetime.utcnow() + timedelta(minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES),
            "iat": datetime.utcnow(),
            "jti": secrets.token_hex(16)  # Unique token ID
        }
        return jwt.encode(payload, self.secret_key, algorithm="HS256")

    def _generate_refresh_token(self, user: User) -> str:
        """Generate JWT refresh token."""
        payload = {
            "sub": user.username,
            "type": "refresh",
            "exp": datetime.utcnow() + timedelta(days=self.REFRESH_TOKEN_EXPIRE_DAYS),
            "iat": datetime.utcnow(),
            "jti": secrets.token_hex(16)
        }
        return jwt.encode(payload, self.secret_key, algorithm="HS256")

    def validate_token(self, token: str, token_type: str = "access") -> Tuple[bool, Optional[Dict]]:
        """
        Validate JWT token.

        Returns:
            Tuple of (valid, payload or None)
        """
        if token in self.blacklisted_tokens:
            return False, None

        try:
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])

            if payload.get("type") != token_type:
                return False, None

            # Check if user still exists and is active
            username = payload.get("sub")
            if username not in self.users or not self.users[username].active:
                return False, None

            return True, payload

        except jwt.ExpiredSignatureError:
            return False, None
        except jwt.InvalidTokenError:
            return False, None

    def refresh_access_token(self, refresh_token: str) -> Tuple[bool, Optional[Dict]]:
        """
        Generate new access token from refresh token.

        Returns:
            Tuple of (success, new_tokens or None)
        """
        valid, payload = self.validate_token(refresh_token, token_type="refresh")

        if not valid:
            return False, None

        username = payload["sub"]
        user = self.users[username]

        # Generate new access token
        access_token = self._generate_access_token(user)

        return True, {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": self.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }

    def logout(self, token: str):
        """Blacklist a token (logout)."""
        self.blacklisted_tokens.add(token)

    # Permission Checking

    def check_permission(self, token: str, required_role: UserRole) -> Tuple[bool, Optional[str]]:
        """
        Check if token has required permission level.

        Returns:
            Tuple of (authorized, username or None)
        """
        valid, payload = self.validate_token(token)

        if not valid:
            return False, None

        user_role = UserRole(payload["role"])

        # Role hierarchy: ADMIN > OPERATOR > VIEWER
        role_levels = {
            UserRole.ADMIN: 3,
            UserRole.OPERATOR: 2,
            UserRole.VIEWER: 1
        }

        if role_levels[user_role] >= role_levels[required_role]:
            return True, payload["sub"]

        return False, None

    # Initial Setup

    def setup_initial_admin(self, username: str, password: str) -> Tuple[bool, str]:
        """
        Create initial admin user (only works if no admin exists).

        Returns:
            Tuple of (success, message)
        """
        if self.has_admin():
            return False, "Admin user already exists"

        return self.create_user(username, password, UserRole.ADMIN)

    def get_setup_required(self) -> bool:
        """Check if initial setup is required."""
        return not self.has_admin()


# Middleware helper for aiohttp
def create_auth_middleware(auth_manager: AuthManager, public_paths: list = None):
    """
    Create aiohttp middleware for JWT authentication.

    Args:
        auth_manager: AuthManager instance
        public_paths: List of paths that don't require authentication
    """
    public_paths = public_paths or ['/api/auth/login', '/api/auth/setup', '/api/auth/status']

    @aiohttp.web.middleware
    async def auth_middleware(request, handler):
        # Skip auth for public paths
        if any(request.path.startswith(p) for p in public_paths):
            return await handler(request)

        # Skip auth for static files and WebSocket upgrade
        if request.path == '/' or request.path == '/ws':
            return await handler(request)

        # Extract token from Authorization header
        auth_header = request.headers.get('Authorization', '')

        if not auth_header.startswith('Bearer '):
            return aiohttp.web.json_response(
                {"error": "Missing or invalid authorization header"},
                status=401
            )

        token = auth_header[7:]  # Remove 'Bearer ' prefix
        valid, payload = auth_manager.validate_token(token)

        if not valid:
            return aiohttp.web.json_response(
                {"error": "Invalid or expired token"},
                status=401
            )

        # Add user info to request
        request['user'] = payload
        return await handler(request)

    return auth_middleware


# Need to import aiohttp for middleware
try:
    import aiohttp.web
except ImportError:
    pass  # Will be available when server imports this
