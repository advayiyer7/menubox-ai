"""
Review analyzer service - uses Claude to extract dish mentions and sentiment from reviews.
"""

import json
from anthropic import Anthropic
from app.core.config import get_settings

settings = get_settings()


async def analyze_reviews_for_dishes(
    reviews: list[dict],
    menu_items: list[str]
) -> dict[str, dict]:
    """
    Analyze reviews to find mentions of specific dishes and their sentiment.
    
    Args:
        reviews: List of review dicts with 'text' and 'rating' keys
        menu_items: List of menu item names to look for
    
    Returns:
        Dict mapping dish names to {mentions: int, sentiment: str, quotes: []}
    """
    if not reviews or not menu_items or not settings.anthropic_api_key:
        return {}
    
    # Format reviews
    reviews_text = "\n\n".join([
        f"Review (Rating: {r.get('rating', 'N/A')}/5):\n{r.get('text', '')}"
        for r in reviews[:10]  # Limit to 10 most recent reviews
    ])
    
    menu_list = "\n".join([f"- {item}" for item in menu_items])
    
    prompt = f"""Analyze these restaurant reviews and identify mentions of specific menu items.

MENU ITEMS TO LOOK FOR:
{menu_list}

REVIEWS:
{reviews_text}

For each menu item that is mentioned (or clearly referenced) in the reviews, provide:
- "mentions": number of times mentioned/referenced
- "sentiment": "positive", "negative", or "mixed"
- "quotes": 1-2 short relevant quotes from reviews (max 100 chars each)

Return as JSON object where keys are the exact menu item names.
Only include items that are actually mentioned in reviews.
If no items are mentioned, return empty object {{}}.

Return ONLY the JSON object, no other text."""

    try:
        client = Anthropic(api_key=settings.anthropic_api_key)
        
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )
        
        response_text = message.content[0].text.strip()
        
        # Clean up response
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        response_text = response_text.strip()
        
        dish_analysis = json.loads(response_text)
        return dish_analysis if isinstance(dish_analysis, dict) else {}
        
    except Exception as e:
        print(f"Review analysis error: {e}")
        return {}


async def get_popular_dishes_from_reviews(reviews: list[dict]) -> list[dict]:
    """
    Extract popular dishes mentioned in reviews even without a menu.
    
    Returns list of {name, mentions, sentiment} for dishes found in reviews.
    """
    if not reviews or not settings.anthropic_api_key:
        return []
    
    reviews_text = "\n\n".join([
        f"Review (Rating: {r.get('rating', 'N/A')}/5):\n{r.get('text', '')}"
        for r in reviews[:10]
    ])
    
    prompt = f"""Analyze these restaurant reviews and identify specific dishes/menu items that customers mention.

REVIEWS:
{reviews_text}

Extract all specific food items mentioned and provide:
- "name": the dish name as mentioned
- "mentions": estimated number of mentions
- "sentiment": "positive", "negative", or "mixed" based on context
- "description": brief description if inferable from reviews

Return as JSON array sorted by number of mentions (most mentioned first).
Only include actual dishes, not generic terms like "food" or "everything".

Return ONLY the JSON array, no other text."""

    try:
        client = Anthropic(api_key=settings.anthropic_api_key)
        
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )
        
        response_text = message.content[0].text.strip()
        
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        response_text = response_text.strip()
        
        dishes = json.loads(response_text)
        return dishes if isinstance(dishes, list) else []
        
    except Exception as e:
        print(f"Popular dishes extraction error: {e}")
        return []