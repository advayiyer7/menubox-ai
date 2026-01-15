from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.preference import Preference
from app.models.restaurant import Restaurant
from app.models.menu_item import MenuItem
from app.models.recommendation import Recommendation
from app.schemas.recommendation import (
    RecommendationRequest,
    RecommendationResponse,
    RecommendedItem,
)
from app.services.ai_service import generate_recommendations
from app.services.yelp_service import get_yelp_data, format_yelp_for_recommendations

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


@router.post("/generate", response_model=RecommendationResponse)
async def create_recommendation(
    data: RecommendationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate AI-powered menu recommendations.
    
    Analyzes restaurant menu items against user preferences
    and review data from Yelp/Google, returns personalized recommendations.
    """
    # Get restaurant
    restaurant = db.query(Restaurant).filter(Restaurant.id == data.restaurant_id).first()
    if not restaurant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant not found"
        )
    
    # Get menu items
    menu_items = db.query(MenuItem).filter(MenuItem.restaurant_id == data.restaurant_id).all()
    if not menu_items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Restaurant has no menu items"
        )
    
    # Get user preferences
    preferences = db.query(Preference).filter(Preference.user_id == current_user.id).first()
    
    # Fetch review data from Yelp (if restaurant has a real location)
    review_context = ""
    if restaurant.location and restaurant.location != "Uploaded via photo":
        print(f"Fetching Yelp reviews for {restaurant.name}...")
        try:
            yelp_data = await get_yelp_data(restaurant.name, restaurant.location)
            if yelp_data.get("found"):
                review_context = format_yelp_for_recommendations(yelp_data)
                print(f"Got Yelp data: {yelp_data['business'].get('rating')}/5 ({yelp_data['business'].get('review_count')} reviews)")
            else:
                print("Restaurant not found on Yelp")
        except Exception as e:
            print(f"Yelp fetch error (continuing without): {e}")
    
    # Generate recommendations using AI with review context
    recommended_items = await generate_recommendations(
        menu_items=menu_items,
        preferences=preferences,
        max_items=data.max_items,
        review_context=review_context
    )
    
    # Save recommendation to history
    recommendation = Recommendation(
        user_id=current_user.id,
        restaurant_id=restaurant.id,
        recommended_items=[item.model_dump() for item in recommended_items],
        preferences_snapshot={
            "dietary_restrictions": preferences.dietary_restrictions if preferences else [],
            "favorite_cuisines": preferences.favorite_cuisines if preferences else [],
            "disliked_ingredients": preferences.disliked_ingredients if preferences else [],
            "spice_preference": preferences.spice_preference if preferences else "medium",
            "price_preference": preferences.price_preference if preferences else "any",
            "custom_notes": preferences.custom_notes if preferences else None,
        }
    )
    db.add(recommendation)
    db.commit()
    db.refresh(recommendation)
    
    return RecommendationResponse(
        id=recommendation.id,
        user_id=recommendation.user_id,
        restaurant_id=recommendation.restaurant_id,
        recommended_items=recommended_items,
        created_at=recommendation.created_at
    )


@router.get("/{recommendation_id}", response_model=RecommendationResponse)
async def get_recommendation(
    recommendation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific recommendation by ID."""
    recommendation = db.query(Recommendation).filter(
        Recommendation.id == recommendation_id,
        Recommendation.user_id == current_user.id
    ).first()
    
    if not recommendation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recommendation not found"
        )
    
    return RecommendationResponse(
        id=recommendation.id,
        user_id=recommendation.user_id,
        restaurant_id=recommendation.restaurant_id,
        recommended_items=[RecommendedItem(**item) for item in recommendation.recommended_items],
        created_at=recommendation.created_at
    )


@router.get("/", response_model=list[RecommendationResponse])
async def list_recommendations(
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's recommendation history."""
    recommendations = db.query(Recommendation).filter(
        Recommendation.user_id == current_user.id
    ).order_by(Recommendation.created_at.desc()).limit(limit).all()
    
    return [
        RecommendationResponse(
            id=rec.id,
            user_id=rec.user_id,
            restaurant_id=rec.restaurant_id,
            recommended_items=[RecommendedItem(**item) for item in rec.recommended_items],
            created_at=rec.created_at
        )
        for rec in recommendations
    ]