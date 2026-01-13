"""
Menu router - handles restaurant search, menu scraping, and image upload.
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from uuid import UUID, uuid4
from typing import Optional

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.restaurant import Restaurant
from app.models.menu_item import MenuItem
from app.schemas.menu import (
    RestaurantSearch,
    RestaurantWithMenuResponse,
    MenuItemResponse,
    MenuUploadResponse,
)
from app.services.google_places_service import (
    search_restaurant as google_search,
    get_place_details,
    price_level_to_string,
    extract_cuisine_type,
)
from app.services.scraping_service import scrape_restaurant_menu
from app.services.review_analyzer import get_popular_dishes_from_reviews
from app.services.ocr_service import extract_menu_from_image

router = APIRouter(prefix="/menu", tags=["Menu"])


@router.post("/search", response_model=RestaurantWithMenuResponse)
async def search_restaurant(
    data: RestaurantSearch,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Search for a restaurant and fetch its menu.
    
    1. Searches Google Places for the restaurant
    2. Gets restaurant details and reviews
    3. Uses Claude web search to find menu items
    4. Falls back to extracting dishes from reviews if no menu found
    5. Saves everything to database
    """
    
    # Step 1: Search Google Places
    print(f"Searching for: {data.name} in {data.location or 'any location'}")
    
    try:
        place_result = await google_search(data.name, data.location)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )
    
    if not place_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Restaurant '{data.name}' not found"
        )
    
    # Step 2: Get detailed info including reviews
    place_details = await get_place_details(place_result["place_id"])
    
    if not place_details:
        place_details = {
            "name": place_result["name"],
            "address": place_result["address"],
            "rating": place_result.get("rating"),
            "website": None,
            "reviews": [],
            "price_level": place_result.get("price_level"),
            "types": place_result.get("types", [])
        }
    
    # Step 3: Check if restaurant exists in DB or create new
    existing_restaurant = db.query(Restaurant).filter(
        Restaurant.google_place_id == place_result["place_id"]
    ).first()
    
    if existing_restaurant:
        restaurant = existing_restaurant
        # Check if we already have menu items
        existing_items = db.query(MenuItem).filter(
            MenuItem.restaurant_id == restaurant.id
        ).count()
        
        if existing_items > 0:
            # Return existing data
            menu_items = db.query(MenuItem).filter(
                MenuItem.restaurant_id == restaurant.id
            ).all()
            
            return RestaurantWithMenuResponse(
                id=restaurant.id,
                name=restaurant.name,
                location=restaurant.location,
                cuisine_type=restaurant.cuisine_type,
                price_range=restaurant.price_range,
                rating=place_details.get("rating"),
                menu_items=[
                    MenuItemResponse(
                        id=item.id,
                        item_name=item.item_name,
                        description=item.description,
                        price=item.price,
                        category=item.category
                    )
                    for item in menu_items
                ],
                reviews_analyzed=len(place_details.get("reviews", [])),
                source="cached"
            )
    else:
        # Create new restaurant
        restaurant = Restaurant(
            id=uuid4(),
            name=place_details.get("name", place_result["name"]),
            location=place_details.get("address", place_result["address"]),
            cuisine_type=extract_cuisine_type(
                place_details.get("types", []),
                place_result["name"]
            ),
            price_range=price_level_to_string(place_details.get("price_level")),
            google_place_id=place_result["place_id"]
        )
        db.add(restaurant)
        db.flush()
    
    # Step 4: Use Claude web search to find menu (no website needed!)
    print(f"Searching web for {restaurant.name} menu...")
    menu_items_data = await scrape_restaurant_menu(
        website_url=place_details.get("website"),  # Optional, not required anymore
        restaurant_name=restaurant.name,
        location=data.location or restaurant.location
    )
    print(f"Found {len(menu_items_data)} items from web search")
    
    # Step 5: If no menu found, extract dishes from reviews as fallback
    if not menu_items_data and place_details.get("reviews"):
        print("No menu found via web search, extracting from reviews...")
        popular_dishes = await get_popular_dishes_from_reviews(place_details["reviews"])
        menu_items_data = [
            {
                "name": dish["name"],
                "description": dish.get("description"),
                "price": None,
                "category": "Popular Items"
            }
            for dish in popular_dishes
        ]
        print(f"Extracted {len(menu_items_data)} dishes from reviews")
    
    # Step 6: Save menu items to database
    saved_items = []
    for item_data in menu_items_data:
        menu_item = MenuItem(
            id=uuid4(),
            restaurant_id=restaurant.id,
            item_name=item_data.get("name", "Unknown Item"),
            description=item_data.get("description"),
            price=item_data.get("price"),
            category=item_data.get("category")
        )
        db.add(menu_item)
        saved_items.append(menu_item)
    
    db.commit()
    
    # Determine source for response
    source = "google_places+web_search"
    if not menu_items_data:
        source = "google_places+reviews"
    
    # Step 7: Return response
    return RestaurantWithMenuResponse(
        id=restaurant.id,
        name=restaurant.name,
        location=restaurant.location,
        cuisine_type=restaurant.cuisine_type,
        price_range=restaurant.price_range,
        rating=place_details.get("rating"),
        menu_items=[
            MenuItemResponse(
                id=item.id,
                item_name=item.item_name,
                description=item.description,
                price=item.price,
                category=item.category
            )
            for item in saved_items
        ],
        reviews_analyzed=len(place_details.get("reviews", [])),
        source=source
    )


@router.post("/upload", response_model=MenuUploadResponse)
async def upload_menu_image(
    file: UploadFile = File(...),
    restaurant_name: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload a menu image for OCR processing.
    
    1. Validates the uploaded file
    2. Uses Claude Vision to extract menu items
    3. Creates a restaurant entry for the uploaded menu
    4. Saves extracted menu items to database
    """
    # Validate file type
    allowed_types = ["image/jpeg", "image/jpg", "image/png", "image/webp", "image/gif"]
    if not file.content_type or file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File must be an image (JPEG, PNG, WebP, or GIF). Got: {file.content_type}"
        )
    
    # Read file content
    try:
        image_data = await file.read()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read uploaded file: {str(e)}"
        )
    
    # Validate file size (max 10MB)
    max_size = 10 * 1024 * 1024  # 10MB
    if len(image_data) > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File too large. Maximum size is 10MB."
        )
    
    # Extract menu items using OCR
    print(f"Processing menu image: {file.filename} ({len(image_data)} bytes)")
    
    try:
        ocr_result = await extract_menu_from_image(image_data, file.content_type)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )
    except Exception as e:
        print(f"OCR processing error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process menu image. Please try again with a clearer image."
        )
    
    menu_items_data = ocr_result.get("menu_items", [])
    detected_name = ocr_result.get("restaurant_name")
    
    if not menu_items_data:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Could not extract any menu items from the image. Please try a clearer photo."
        )
    
    # Determine restaurant name
    final_name = restaurant_name or detected_name or "Uploaded Menu"
    
    # Create restaurant entry for uploaded menu
    restaurant = Restaurant(
        id=uuid4(),
        name=final_name,
        location="Uploaded via photo",
        cuisine_type="Various",
        price_range="$$",
        google_place_id=None  # No Google Place ID for uploaded menus
    )
    db.add(restaurant)
    db.flush()
    
    # Save menu items
    saved_count = 0
    for item_data in menu_items_data:
        menu_item = MenuItem(
            id=uuid4(),
            restaurant_id=restaurant.id,
            item_name=item_data.get("name", "Unknown Item"),
            description=item_data.get("description"),
            price=item_data.get("price"),
            category=item_data.get("category")
        )
        db.add(menu_item)
        saved_count += 1
    
    db.commit()
    
    print(f"Saved {saved_count} menu items for restaurant: {final_name}")
    
    return MenuUploadResponse(
        restaurant_id=restaurant.id,
        restaurant_name=final_name,
        menu_items_count=saved_count,
        message=f"Successfully extracted {saved_count} menu items from your photo!"
    )


@router.get("/{restaurant_id}", response_model=RestaurantWithMenuResponse)
async def get_restaurant_menu(
    restaurant_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a restaurant and its menu items by ID."""
    restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    
    if not restaurant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant not found"
        )
    
    menu_items = db.query(MenuItem).filter(
        MenuItem.restaurant_id == restaurant_id
    ).all()
    
    return RestaurantWithMenuResponse(
        id=restaurant.id,
        name=restaurant.name,
        location=restaurant.location,
        cuisine_type=restaurant.cuisine_type,
        price_range=restaurant.price_range,
        rating=None,
        menu_items=[
            MenuItemResponse(
                id=item.id,
                item_name=item.item_name,
                description=item.description,
                price=item.price,
                category=item.category
            )
            for item in menu_items
        ],
        reviews_analyzed=0,
        source="database"
    )