"""
Google Places API integration for restaurant search and data.
"""

import httpx
from typing import Optional
from app.core.config import get_settings

settings = get_settings()

PLACES_BASE_URL = "https://maps.googleapis.com/maps/api/place"


async def search_restaurant(name: str, location: Optional[str] = None) -> dict | None:
    """
    Search for a restaurant using Google Places API.
    
    Returns place details including place_id, name, address, rating, etc.
    """
    if not settings.google_places_api_key:
        raise ValueError("Google Places API key not configured")
    
    # Build search query
    query = name
    if location:
        query = f"{name} {location}"
    
    # Text Search API
    search_url = f"{PLACES_BASE_URL}/textsearch/json"
    params = {
        "query": f"{query} restaurant",
        "type": "restaurant",
        "key": settings.google_places_api_key
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(search_url, params=params)
        data = response.json()
        
        if data.get("status") != "OK" or not data.get("results"):
            return None
        
        # Get the first (most relevant) result
        place = data["results"][0]
        
        return {
            "place_id": place.get("place_id"),
            "name": place.get("name"),
            "address": place.get("formatted_address"),
            "rating": place.get("rating"),
            "price_level": place.get("price_level"),  # 0-4
            "total_ratings": place.get("user_ratings_total"),
            "types": place.get("types", []),
            "location": place.get("geometry", {}).get("location", {})
        }


async def get_place_details(place_id: str) -> dict | None:
    """
    Get detailed information about a place including reviews.
    """
    if not settings.google_places_api_key:
        raise ValueError("Google Places API key not configured")
    
    details_url = f"{PLACES_BASE_URL}/details/json"
    params = {
        "place_id": place_id,
        "fields": "name,formatted_address,formatted_phone_number,website,rating,reviews,price_level,opening_hours,photos,types,editorial_summary",
        "key": settings.google_places_api_key
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(details_url, params=params)
        data = response.json()
        
        if data.get("status") != "OK":
            return None
        
        result = data.get("result", {})
        
        return {
            "name": result.get("name"),
            "address": result.get("formatted_address"),
            "phone": result.get("formatted_phone_number"),
            "website": result.get("website"),
            "rating": result.get("rating"),
            "price_level": result.get("price_level"),
            "reviews": result.get("reviews", []),
            "hours": result.get("opening_hours", {}).get("weekday_text", []),
            "summary": result.get("editorial_summary", {}).get("overview"),
            "types": result.get("types", [])
        }


def price_level_to_string(level: int | None) -> str:
    """Convert Google's price level (0-4) to string."""
    mapping = {
        0: "$",
        1: "$",
        2: "$$",
        3: "$$$",
        4: "$$$$"
    }
    return mapping.get(level, "$$")


def extract_cuisine_type(types: list[str], name: str) -> str:
    """Extract cuisine type from Google place types."""
    cuisine_keywords = {
        "italian": "Italian",
        "mexican": "Mexican", 
        "chinese": "Chinese",
        "japanese": "Japanese",
        "indian": "Indian",
        "thai": "Thai",
        "vietnamese": "Vietnamese",
        "korean": "Korean",
        "french": "French",
        "mediterranean": "Mediterranean",
        "american": "American",
        "pizza": "Italian",
        "sushi": "Japanese",
        "taco": "Mexican",
        "burger": "American",
        "seafood": "Seafood",
        "steakhouse": "Steakhouse",
        "cafe": "Cafe",
        "bakery": "Bakery"
    }
    
    # Check types
    for t in types:
        t_lower = t.lower().replace("_", " ")
        for keyword, cuisine in cuisine_keywords.items():
            if keyword in t_lower:
                return cuisine
            
    # Check name
    name_lower = name.lower()
    for keyword, cuisine in cuisine_keywords.items():
        if keyword in name_lower:
            return cuisine
    
    return "Restaurant"