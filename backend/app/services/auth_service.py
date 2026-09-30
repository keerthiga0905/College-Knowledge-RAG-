"""
Authentication service for password hashing and admin verification.
"""

from passlib.context import CryptContext
from dotenv import load_dotenv
from pathlib import Path
import os

# Load backend/.env explicitly
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BACKEND_DIR / ".env")

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a plain text password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain text password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


def get_admin_credentials_from_env():
    """
    Get admin credentials from backend/.env.

    Returns:
        tuple: (admin_email, admin_password_hash)
    """
    admin_email = os.getenv("ADMIN_EMAIL")
    admin_password_hash = os.getenv("ADMIN_PASSWORD_HASH")

    if not admin_email or not admin_password_hash:
        return None, None

    return admin_email, admin_password_hash


def create_admin_password_hash(password: str) -> str:
    """Create a bcrypt password hash for admin setup."""
    return hash_password(password)


def verify_admin_login(email: str, password: str) -> bool:
    """
    Verify admin credentials from backend/.env.
    """
    admin_email, admin_password_hash = get_admin_credentials_from_env()

    if not admin_email or not admin_password_hash:
        return False

    if email.lower().strip() != admin_email.lower().strip():
        return False

    try:
        return verify_password(password, admin_password_hash)
    except Exception:
        return False