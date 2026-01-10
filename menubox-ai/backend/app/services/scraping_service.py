"""
Web scraping service to extract menu data from restaurant websites.
Uses Claude to intelligently parse menu content from HTML.
"""

import httpx
import re
from bs4 import BeautifulSoup
from anthropic import Anthropic
from app.core.config import get_settings

settings = get_settings()


async def fetch_website_content(url: str) -> str | None:
    """Fetch HTML content from a URL."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        async with httpx.AsyncClient(follow_redirects=True, timeout=15.0) as client:
            response = await client.get(url, headers=headers)
            if response.status_code == 200:
                return response.text
    except Exception as e:
        print(f"Error fetching {url}: {e}")
    return None


def extract_text_from_html(html: str) -> str:
    """Extract readable text from HTML, focusing on menu-related content."""
    soup = BeautifulSoup(html, 'html.parser')
    
    # Remove script and style elements
    for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
        element.decompose()
    
    # Try to find menu-specific sections
    menu_keywords = ['menu', 'food', 'dishes', 'appetizer', 'entree', 'dessert', 'drink', 'beverage']
    menu_sections = []
    
    # Look for sections with menu-related class/id names
    for keyword in menu_keywords:
        elements = soup.find_all(class_=re.compile(keyword, re.I))
        elements += soup.find_all(id=re.compile(keyword, re.I))
        for el in elements:
            menu_sections.append(el.get_text(separator='\n', strip=True))
    
    if menu_sections:
        return '\n\n'.join(menu_sections)[:15000]  # Limit content size
    
    # Fallback: get all text
    text = soup.get_text(separator='\n', strip=True)
    
    # Clean up multiple newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text[:15000]  # Limit content size


async def find_menu_page(base_url: str) -> str | None:
    """Try to find the menu page URL from a restaurant website."""
    html = await fetch_website_content(base_url)
    if not html:
        return None
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Look for menu links
    menu_patterns = ['/menu', 'menu.html', 'menu.php', '/food', '/our-menu', '/dinner', '/lunch']
    
    for link in soup.find_all('a', href=True):
        href = link.get('href', '').lower()
        link_text = link.get_text().lower()
        
        if 'menu' in link_text or any(pattern in href for pattern in menu_patterns):
            full_url = href
            if href.startswith('/'):
                # Relative URL
                from urllib.parse import urljoin
                full_url = urljoin(base_url, href)
            elif not href.startswith('http'):
                full_url = f"{base_url.rstrip('/')}/{href}"
            
            return full_url
    
    return None


async def extract_menu_with_claude(website_content: str, restaurant_name: str) -> list[dict]:
    """
    Use Claude to intelligently extract menu items from website content.
    """
    if not settings.anthropic_api_key:
        return []
    
    prompt = f"""Analyze this restaurant website content and extract all menu items you can find.

Restaurant: {restaurant_name}

Website Content:
{website_content[:12000]}

Extract menu items and return as a JSON array. Each item should have:
- "name": dish name
- "description": brief description (if available, otherwise null)
- "price": price as a number (if available, otherwise null)
- "category": category like "Appetizers", "Entrees", "Desserts", etc. (if determinable)

Only include actual food/drink items, not section headers or other text.
If you cannot find any menu items, return an empty array [].

Return ONLY the JSON array, no other text."""

    try:
        client = Anthropic(api_key=settings.anthropic_api_key)
        
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}]
        )
        
        response_text = message.content[0].text.strip()
        
        # Clean up response
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        response_text = response_text.strip()
        
        import json
        menu_items = json.loads(response_text)
        
        return menu_items if isinstance(menu_items, list) else []
        
    except Exception as e:
        print(f"Claude menu extraction error: {e}")
        return []


async def scrape_restaurant_menu(website_url: str, restaurant_name: str) -> list[dict]:
    """
    Main function to scrape menu from a restaurant website.
    
    Returns list of menu items with name, description, price, category.
    """
    if not website_url:
        return []
    
    # Try to find dedicated menu page
    menu_url = await find_menu_page(website_url)
    target_url = menu_url or website_url
    
    print(f"Scraping menu from: {target_url}")
    
    # Fetch and parse content
    html = await fetch_website_content(target_url)
    if not html:
        return []
    
    text_content = extract_text_from_html(html)
    if len(text_content) < 100:
        return []
    
    # Use Claude to extract menu items
    menu_items = await extract_menu_with_claude(text_content, restaurant_name)
    
    return menu_items


async def search_google_for_menu(restaurant_name: str, location: str = "") -> list[dict]:
    """
    Search Google for menu information as a fallback.
    This is a placeholder - would need SerpAPI or similar for production.
    """
    # For now, return empty - this would need SerpAPI integration
    return []