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
from app.services.review_analyzer import analyze_reviews_for_dishes

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


async def get_dish_reviews_from_yelp(
    restaurant_name: str,
    location: str,
    menu_item_names: list[str]
) -> str:
    """
    Cross-reference menu items with Yelp reviews.
    Returns formatted string with what reviewers say about specific dishes.
    """
    try:
        yelp_data = await get_yelp_data(restaurant_name, location)
        
        if not yelp_data.get("found"):
            return ""
        
        business = yelp_data.get("business", {})
        reviews = yelp_data.get("reviews", [])
        
        if not reviews:
            # Return just the rating if no review text
            rating = business.get("rating")
            review_count = business.get("review_count")
            if rating:
                return f"Yelp Rating: {rating}/5 ({review_count} reviews)"
            return ""
        
        # Analyze which dishes are mentioned in reviews
        reviews_formatted = [{"text": r.get("text", ""), "rating": r.get("rating")} for r in reviews]
        dish_mentions = await analyze_reviews_for_dishes(reviews_formatted, menu_item_names)
        
        parts = []
        parts.append(f"Yelp Rating: {business.get('rating', 'N/A')}/5 ({business.get('review_count', 0)} reviews)")
        
        if dish_mentions:
            parts.append("\nDishes mentioned in reviews:")
            for dish_name, info in dish_mentions.items():
                sentiment = info.get("sentiment", "unknown")
                mentions = info.get("mentions", 0)
                emoji = "👍" if sentiment == "positive" else "👎" if sentiment == "negative" else "🤷"
                parts.append(f"  {emoji} {dish_name}: {sentiment} ({mentions} mention{'s' if mentions > 1 else ''})")
                quotes = info.get("quotes", [])
                for quote in quotes[:1]:  # Just first quote
                    parts.append(f"     \"{quote}\"")
        
        # Add general review snippets
        parts.append("\nRecent review highlights:")
        for review in reviews[:2]:
            rating = review.get("rating", "?")
            text = review.get("text", "")[:150]
            parts.append(f"  ({rating}/5) \"{text}...\"")
        
        return "\n".join(parts)
        
    except Exception as e:
        print(f"Error getting dish reviews from Yelp: {e}")
        return ""


@router.post("/generate", response_model=RecommendationResponse)
async def create_recommendation(
    data: RecommendationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate AI-powered menu recommendations.
    
    For searched restaurants: Uses full Yelp review data
    For OCR uploads: Only uses parsed menu items, but cross-references
                     those specific dishes with Yelp reviews
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
    
    # Determine if this is an OCR-uploaded restaurant
    is_ocr_upload = restaurant.google_place_id is None
    
    review_context = ""
    
    if is_ocr_upload:
        # OCR MODE: Only use parsed menu items, but cross-reference with Yelp
        print(f"OCR mode for {restaurant.name} - cross-referencing dishes with Yelp...")
        
        # Only try Yelp if we have a real location (not "Uploaded via photo")
        if restaurant.location and restaurant.location != "Uploaded via photo":
            menu_item_names = [item.item_name for item in menu_items]
            review_context = await get_dish_reviews_from_yelp(
                restaurant.name,
                restaurant.location,
                menu_item_names
            )
            if review_context:
                print(f"Found Yelp data for dish cross-reference")
            else:
                print(f"No Yelp data found for {restaurant.name}")
    else:
        # SEARCH MODE: Use full Yelp review data
        print(f"Search mode for {restaurant.name} - fetching Yelp reviews...")
        try:
            yelp_data = await get_yelp_data(restaurant.name, restaurant.location)
            if yelp_data.get("found"):
                review_context = format_yelp_for_recommendations(yelp_data)
                print(f"Got Yelp data: {yelp_data['business'].get('rating')}/5 ({yelp_data['business'].get('review_count')} reviews)")
            else:
                print("Restaurant not found on Yelp")
        except Exception as e:
            print(f"Yelp fetch error (continuing without): {e}")
    
    # Generate recommendations using AI
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