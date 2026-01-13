"""
Menu discovery service using Claude with web search.
Replaces manual HTML scraping with AI-powered web search.
"""

import json
from anthropic import Anthropic
from app.core.config import get_settings

settings = get_settings()


async def get_menu_with_web_search(
    restaurant_name: str,
    location: str = "",
    cuisine_type: str = ""
) -> list[dict]:
    """
    Use Claude with web search to find menu items for a restaurant.
    
    This is more reliable than scraping because:
    - Works with JS-heavy sites (searches indexed content)
    - Aggregates info from multiple sources
    - Handles various menu formats automatically
    
    Returns list of menu items with name, description, price, category.
    """
    if not settings.anthropic_api_key:
        return []
    
    # Build search context
    search_query = f"{restaurant_name}"
    if location:
        search_query += f" {location}"
    
    prompt = f"""Find the menu for this restaurant and extract all the dishes:

Restaurant: {restaurant_name}
{f'Location: {location}' if location else ''}
{f'Cuisine Type: {cuisine_type}' if cuisine_type else ''}

Please search for this restaurant's menu and provide a comprehensive list of their dishes.

Return the menu items as a JSON array. Each item should have:
- "name": dish name
- "description": brief description (null if not found)
- "price": price as a number without $ sign (null if not found)
- "category": category like "Appetizers", "Entrees", "Pasta", "Desserts", etc.

Try to find as many menu items as possible from their full menu.
If you find prices, include them. If not, that's okay.

Return ONLY the JSON array, no other text or markdown formatting."""

    try:
        client = Anthropic(api_key=settings.anthropic_api_key)
        
        # Use web search tool
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            tools=[{
                "type": "web_search_20250305",
                "name": "web_search"
            }],
            messages=[{"role": "user", "content": prompt}]
        )
        
        # Extract text response (Claude may return multiple content blocks)
        response_text = ""
        for block in message.content:
            if hasattr(block, 'text'):
                response_text += block.text
        
        response_text = response_text.strip()
        
        # Clean up response if wrapped in markdown
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]
        
        response_text = response_text.strip()
        
        menu_items = json.loads(response_text)
        
        if isinstance(menu_items, list):
            print(f"Found {len(menu_items)} menu items via web search")
            return menu_items
        return []
        
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        print(f"Response was: {response_text[:500]}")
        return []
    except Exception as e:
        print(f"Web search menu error: {e}")
        return []


async def scrape_restaurant_menu(
    website_url: str | None,
    restaurant_name: str,
    location: str = ""
) -> list[dict]:
    """
    Get menu items for a restaurant using web search.
    
    Args:
        website_url: Ignored (kept for backwards compatibility)
        restaurant_name: Name of the restaurant
        location: Optional location to narrow search
    
    Returns list of menu items with name, description, price, category.
    """
    # Use web search instead of direct scraping
    return await get_menu_with_web_search(restaurant_name, location)


# Keep the old functions as fallbacks if needed
async def fetch_website_content(url: str) -> str | None:
    """Fetch HTML content from a URL - legacy fallback."""
    try:
        import httpx
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        async with httpx.AsyncClient(follow_redirects=True, timeout=15.0) as client:
            response = await client.get(url, headers=headers)
            if response.status_code == 200:
                return response.text
    except Exception as e:
        print(f"Error fetching {url}: {e}")
    return None