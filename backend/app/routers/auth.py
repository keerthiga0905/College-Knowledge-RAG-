import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.user import UserLogin, AdminLogin, UserResponse
from app.services.auth_service import verify_admin_login

router = APIRouter(prefix="/auth", tags=["Authentication & Users"])

@router.post("/login", response_model=UserResponse)
def login_or_register_student(payload: UserLogin, db: Session = Depends(get_db)):
    """
    Logs in an existing student by email or registers a new student automatically.
    Returns the student profile with internal user_id.
    
    Student accounts are always created with role="student".
    """
    email_clean = payload.email.lower().strip()
    name_clean = payload.name.strip()

    if not name_clean:
        raise HTTPException(status_code=400, detail="Name cannot be empty.")
    if not email_clean:
        raise HTTPException(status_code=400, detail="Email cannot be empty.")

    # Check if user already exists
    user = db.query(User).filter(User.email == email_clean).first()
    if user:
        # Verify this is a student account (not admin trying to use student login)
        if user.role != "student":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This account is not a student account. Please use admin login."
            )
        # Update name if user provided a newer name
        if user.name != name_clean:
            user.name = name_clean
            db.commit()
            db.refresh(user)
        return user

    # Create new student user (always role="student")
    new_user = User(
        user_id=str(uuid.uuid4()),
        name=name_clean,
        email=email_clean,
        role="student"  # Always student for public registration
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user

@router.post("/admin-login", response_model=UserResponse)
def login_admin(payload: AdminLogin, db: Session = Depends(get_db)):
    """
    Admin-only login endpoint.
    Authenticates admin credentials and returns admin user profile.
    
    Admin credentials are verified against environment variables (ADMIN_EMAIL, ADMIN_PASSWORD_HASH).
    """
    email_clean = payload.email.lower().strip()
    
    # Verify admin credentials
    if not verify_admin_login(email_clean, payload.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin email or password"
        )
    
    # Find or create admin user in database
    admin_user = db.query(User).filter(User.email == email_clean).first()
    
    if not admin_user:
        # First-time admin login - create the account
        admin_user = User(
            user_id=str(uuid.uuid4()),
            name="Administrator",
            email=email_clean,
            role="admin",
            password_hash=""  # Password stored in environment, not in DB
        )
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
    elif admin_user.role != "admin":
        # Prevent student accounts from becoming admin
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account is not an admin account"
        )
    
    return admin_user

@router.get("/user/{user_id}", response_model=UserResponse)
def get_user_profile(user_id: str, db: Session = Depends(get_db)):
    """Retrieves user profile by internal user_id."""
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return user
