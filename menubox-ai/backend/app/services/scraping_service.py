"""
Menu discovery service using Claude with web search.
Replaces manual HTML scraping with AI-powered web search.
"""

import json
import re
import asyncio
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
    
    Returns list of menu items with name, description, price, category.
    """
    if not settings.anthropic_api_key:
        return []
    
    prompt = f"""Search for the menu of {restaurant_name}{f' in {location}' if location else ''} and extract dishes.

IMPORTANT: You MUST respond with ONLY a JSON array. No explanations, no markdown, no text before or after.

If you find menu items, return them in this exact format:
[
  {{"name": "Dish Name", "description": "Brief description", "price": 15.99, "category": "Category"}},
  ...
]

If you cannot find specific menu items, still return your best guess based on what the restaurant serves:
[
  {{"name": "Popular Dish", "description": null, "price": null, "category": "Entrees"}},
  ...
]

Rules:
- Return ONLY the JSON array, nothing else
- No markdown code blocks
- No explanatory text
- price should be a number or null (no $ sign)
- Include at least 10-20 items if possible

START YOUR RESPONSE WITH [ AND END WITH ]"""

    try:
        client = Anthropic(api_key=settings.anthropic_api_key)
        
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            tools=[{
                "type": "web_search_20250305",
                "name": "web_search"
            }],
            messages=[{"role": "user", "content": prompt}]
        )
        
        # Debug output
        print(f"Response has {len(message.content)} content blocks")
        for i, block in enumerate(message.content):
            print(f"  Block {i}: type={type(block).__name__}")
        
        # Extract text from all blocks
        response_text = ""
        for block in message.content:
            if hasattr(block, 'text') and block.text is not None:
                response_text += block.text
        
        print(f"Extracted response text length: {len(response_text)}")
        
        if not response_text.strip():
            print("Empty response from Claude")
            return []
        
        response_text = response_text.strip()
        
        # Try multiple extraction methods
        menu_items = None
        
        # Method 1: Direct parse (if response is clean JSON)
        if response_text.startswith('['):
            try:
                menu_items = json.loads(response_text)
            except json.JSONDecodeError:
                pass
        
        # Method 2: Extract from markdown code block
        if menu_items is None and "```" in response_text:
            try:
                if "```json" in response_text:
                    json_str = response_text.split("```json")[1].split("```")[0]
                else:
                    json_str = response_text.split("```")[1].split("```")[0]
                menu_items = json.loads(json_str.strip())
            except (json.JSONDecodeError, IndexError):
                pass
        
        # Method 3: Regex to find JSON array anywhere in text
        if menu_items is None:
            # Find anything that looks like a JSON array
            json_match = re.search(r'\[\s*\{[^{}]*\}(?:\s*,\s*\{[^{}]*\})*\s*\]', response_text, re.DOTALL)
            if json_match:
                try:
                    menu_items = json.loads(json_match.group(0))
                except json.JSONDecodeError:
                    pass
        
        # Method 4: More aggressive - find [ and ] and try to parse between
        if menu_items is None:
            start_idx = response_text.find('[')
            end_idx = response_text.rfind(']')
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                try:
                    potential_json = response_text[start_idx:end_idx + 1]
                    menu_items = json.loads(potential_json)
                except json.JSONDecodeError:
                    pass
        
        if menu_items and isinstance(menu_items, list):
            print(f"Found {len(menu_items)} menu items via web search")
            return menu_items
        
        print(f"Could not parse JSON from response")
        print(f"Response preview: {response_text[:300]}...")
        return []
        
    except Exception as e:
        error_str = str(e)
        if "rate_limit" in error_str.lower() or "429" in error_str:
            print(f"Rate limit hit, waiting 30 seconds...")
            await asyncio.sleep(30)
            # Could retry here, but for now just return empty
            return []
        
        print(f"Web search menu error: {e}")
        import traceback
        traceback.print_exc()
        return []


async def scrape_restaurant_menu(
    website_url: str | None,
    restaurant_name: str,
    location: str = ""
) -> list[dict]:
    """
    Get menu items for a restaurant using web search.
    """
    return await get_menu_with_web_search(restaurant_name, location)


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