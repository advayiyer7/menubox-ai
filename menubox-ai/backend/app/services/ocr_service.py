"""
OCR Service - Extract menu items from images using Claude Vision API.
"""

import json
import base64
from anthropic import Anthropic
from app.core.config import get_settings

settings = get_settings()


async def extract_menu_from_image(
    image_data: bytes,
    content_type: str = "image/jpeg"
) -> dict:
    """
    Extract menu items from an uploaded menu image using Claude Vision.
    
    Args:
        image_data: Raw bytes of the image
        content_type: MIME type (image/jpeg, image/png, image/webp, image/gif)
    
    Returns:
        dict with:
            - restaurant_name: Detected or "Uploaded Menu"
            - menu_items: List of extracted dishes
    """
    if not settings.anthropic_api_key:
        raise ValueError("Anthropic API key not configured")
    
    # Convert image to base64
    image_base64 = base64.standard_b64encode(image_data).decode("utf-8")
    
    # Map content type to Claude's expected format
    media_type_map = {
        "image/jpeg": "image/jpeg",
        "image/jpg": "image/jpeg",
        "image/png": "image/png",
        "image/webp": "image/webp",
        "image/gif": "image/gif"
    }
    media_type = media_type_map.get(content_type, "image/jpeg")
    
    prompt = """Analyze this menu image and extract all the dishes/items you can see.

For each item, extract:
- "name": The dish name exactly as shown
- "description": Description if visible (null if not shown)
- "price": Price as a number without currency symbol (null if not visible)
- "category": The section/category it's under (e.g., "Appetizers", "Mains", "Desserts", "Drinks") - infer from context if not explicit

Also try to identify the restaurant name if visible on the menu.

Return your response as a JSON object with:
{
    "restaurant_name": "Name if visible, otherwise null",
    "menu_items": [
        {"name": "...", "description": "...", "price": ..., "category": "..."},
        ...
    ]
}

Extract as many items as you can clearly read. If text is blurry or unclear, skip that item.
Return ONLY the JSON object, no other text or markdown formatting."""

    try:
        client = Anthropic(api_key=settings.anthropic_api_key)
        
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": image_base64
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ]
        )
        
        response_text = message.content[0].text.strip()
        
        # Clean up response if wrapped in markdown
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]
        
        response_text = response_text.strip()
        
        result = json.loads(response_text)
        
        # Ensure structure is correct
        if not isinstance(result, dict):
            result = {"restaurant_name": None, "menu_items": []}
        
        if "menu_items" not in result:
            result["menu_items"] = []
        
        if "restaurant_name" not in result:
            result["restaurant_name"] = None
            
        print(f"OCR extracted {len(result['menu_items'])} menu items")
        
        return result
        
    except json.JSONDecodeError as e:
        print(f"OCR JSON parsing error: {e}")
        print(f"Response was: {response_text[:500] if response_text else 'empty'}")
        return {"restaurant_name": None, "menu_items": []}
    except Exception as e:
        print(f"OCR extraction error: {e}")
        import traceback
        traceback.print_exc()
        raise


async def extract_menu_from_multiple_images(
    images: list[tuple[bytes, str]]
) -> dict:
    """
    Extract menu items from multiple images and combine results.
    
    Args:
        images: List of (image_data, content_type) tuples
    
    Returns:
        Combined dict with restaurant_name and all menu_items
    """
    all_items = []
    restaurant_name = None
    
    for image_data, content_type in images:
        result = await extract_menu_from_image(image_data, content_type)
        
        if result.get("restaurant_name") and not restaurant_name:
            restaurant_name = result["restaurant_name"]
        
        all_items.extend(result.get("menu_items", []))
    
    # Deduplicate by name (case-insensitive)
    seen_names = set()
    unique_items = []
    for item in all_items:
        name_lower = item.get("name", "").lower()
        if name_lower and name_lower not in seen_names:
            seen_names.add(name_lower)
            unique_items.append(item)
    
    return {
        "restaurant_name": restaurant_name,
        "menu_items": unique_items
    }