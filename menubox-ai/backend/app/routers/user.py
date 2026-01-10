from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.preference import Preference
from app.schemas.auth import UserResponse
from app.schemas.preference import PreferenceUpdate, PreferenceResponse

router = APIRouter(prefix="/user", tags=["User"])


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current authenticated user's info."""
    return UserResponse.model_validate(current_user)


@router.get("/preferences", response_model=PreferenceResponse)
async def get_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's food preferences."""
    preferences = db.query(Preference).filter(Preference.user_id == current_user.id).first()
    
    if not preferences:
        # Create default preferences if they don't exist
        preferences = Preference(user_id=current_user.id)
        db.add(preferences)
        db.commit()
        db.refresh(preferences)
    
    return PreferenceResponse.model_validate(preferences)


@router.put("/preferences", response_model=PreferenceResponse)
async def update_preferences(
    data: PreferenceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user's food preferences."""
    preferences = db.query(Preference).filter(Preference.user_id == current_user.id).first()
    
    if not preferences:
        # Create preferences if they don't exist
        preferences = Preference(user_id=current_user.id)
        db.add(preferences)
    
    # Update only provided fields
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(preferences, field, value)
    
    db.commit()
    db.refresh(preferences)
    
    return PreferenceResponse.model_validate(preferences)
