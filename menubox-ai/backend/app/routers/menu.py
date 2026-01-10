"""
Menu router - handles restaurant search, menu scraping, and image upload.
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from uuid import UUID, uuid4

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
    3. Scrapes menu from restaurant website
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
    
    # Step 4: Try to scrape menu from website
    menu_items_data = []
    website = place_details.get("website")
    
    if website:
        print(f"Scraping menu from: {website}")
        menu_items_data = await scrape_restaurant_menu(website, restaurant.name)
        print(f"Found {len(menu_items_data)} items from website")
    
    # Step 5: If no menu found, extract dishes from reviews
    if not menu_items_data and place_details.get("reviews"):
        print("No menu found, extracting from reviews...")
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
        source="google_places" + ("+website" if website else "+reviews")
    )


@router.post("/upload", response_model=MenuUploadResponse)
async def upload_menu_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload a menu image for OCR processing.
    TODO: Implement OCR with Claude Vision API.
    """
    # Validate file type
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image"
        )
    
    # TODO: Implement OCR processing
    # For now, return a placeholder response
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Menu image upload coming soon! Please use restaurant search for now."
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