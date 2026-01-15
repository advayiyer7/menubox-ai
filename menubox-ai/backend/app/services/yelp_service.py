"""
Yelp Fusion API integration for restaurant reviews and popular dishes.
"""

import httpx
from typing import Optional
from app.core.config import get_settings

settings = get_settings()

YELP_BASE_URL = "https://api.yelp.com/v3"


async def search_yelp_business(name: str, location: str) -> dict | None:
    """
    Search for a business on Yelp.
    
    Returns business details including ID, rating, review count, etc.
    """
    api_key = getattr(settings, 'yelp_api_key', None)
    if not api_key:
        print("Yelp API key not configured, skipping Yelp search")
        return None
    
    search_url = f"{YELP_BASE_URL}/businesses/search"
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    params = {
        "term": name,
        "location": location,
        "categories": "restaurants,food",
        "limit": 1
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(search_url, headers=headers, params=params, timeout=10.0)
            
            if response.status_code != 200:
                print(f"Yelp search error: {response.status_code}")
                return None
            
            data = response.json()
            businesses = data.get("businesses", [])
            
            if not businesses:
                return None
            
            business = businesses[0]
            return {
                "yelp_id": business.get("id"),
                "name": business.get("name"),
                "rating": business.get("rating"),
                "review_count": business.get("review_count"),
                "price": business.get("price"),
                "categories": [c.get("title") for c in business.get("categories", [])],
                "location": business.get("location", {}).get("display_address", []),
                "phone": business.get("phone"),
                "url": business.get("url")
            }
    except Exception as e:
        print(f"Yelp search error: {e}")
        return None


async def get_yelp_reviews(yelp_id: str) -> list[dict]:
    """
    Get reviews for a business from Yelp.
    
    Note: Yelp API only returns up to 3 reviews per business.
    """
    api_key = getattr(settings, 'yelp_api_key', None)
    if not api_key:
        return []
    
    reviews_url = f"{YELP_BASE_URL}/businesses/{yelp_id}/reviews"
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    params = {
        "limit": 3,
        "sort_by": "yelp_sort"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(reviews_url, headers=headers, params=params, timeout=10.0)
            
            if response.status_code != 200:
                print(f"Yelp reviews error: {response.status_code}")
                return []
            
            data = response.json()
            reviews = data.get("reviews", [])
            
            return [
                {
                    "text": review.get("text", ""),
                    "rating": review.get("rating"),
                    "time_created": review.get("time_created"),
                    "user": review.get("user", {}).get("name", "Anonymous")
                }
                for review in reviews
            ]
    except Exception as e:
        print(f"Yelp reviews error: {e}")
        return []


async def get_yelp_data(name: str, location: str) -> dict:
    """
    Get full Yelp data for a restaurant including reviews.
    
    Returns combined business info and reviews.
    """
    business = await search_yelp_business(name, location)
    
    if not business:
        return {
            "found": False,
            "business": None,
            "reviews": []
        }
    
    reviews = await get_yelp_reviews(business["yelp_id"])
    
    return {
        "found": True,
        "business": business,
        "reviews": reviews
    }


def format_yelp_for_recommendations(yelp_data: dict) -> str:
    """
    Format Yelp data as context for AI recommendations.
    """
    if not yelp_data.get("found"):
        return ""
    
    parts = []
    business = yelp_data.get("business", {})
    
    if business:
        parts.append(f"Yelp Rating: {business.get('rating', 'N/A')}/5 ({business.get('review_count', 0)} reviews)")
        if business.get("price"):
            parts.append(f"Price Level: {business.get('price')}")
        if business.get("categories"):
            parts.append(f"Categories: {', '.join(business.get('categories', []))}")
    
    reviews = yelp_data.get("reviews", [])
    if reviews:
        parts.append("\nRecent Yelp Reviews:")
        for i, review in enumerate(reviews[:3], 1):
            rating = review.get("rating", "?")
            text = review.get("text", "")[:200]  # Truncate long reviews
            parts.append(f"  {i}. ({rating}/5) \"{text}...\"")
    
    return "\n".join(parts)