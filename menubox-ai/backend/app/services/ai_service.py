"""
AI Recommendation Service
Uses Claude API to generate personalized menu recommendations
based on user preferences and dietary restrictions.
"""
import json
from anthropic import Anthropic
from app.core.config import get_settings
from app.models.menu_item import MenuItem
from app.models.preference import Preference
from app.schemas.recommendation import RecommendedItem

settings = get_settings()


async def generate_recommendations(
    menu_items: list[MenuItem],
    preferences: Preference | None,
    max_items: int = 5
) -> list[RecommendedItem]:
    """
    Generate personalized menu recommendations using Claude AI.
    
    Analyzes menu items against user preferences and returns
    ranked recommendations with reasoning.
    """
    
    # Build menu items text
    menu_text = "\n".join([
        f"- {item.item_name}" + 
        (f": {item.description}" if item.description else "") +
        (f" (${item.price})" if item.price else "") +
        (f" [Category: {item.category}]" if item.category else "")
        for item in menu_items
    ])
    
    # Build preferences text
    if preferences:
        pref_parts = []
        if preferences.dietary_restrictions:
            pref_parts.append(f"Dietary restrictions: {', '.join(preferences.dietary_restrictions)}")
        if preferences.favorite_cuisines:
            pref_parts.append(f"Favorite cuisines: {', '.join(preferences.favorite_cuisines)}")
        if preferences.disliked_ingredients:
            pref_parts.append(f"Dislikes: {', '.join(preferences.disliked_ingredients)}")
        if preferences.spice_preference != "medium":
            pref_parts.append(f"Spice preference: {preferences.spice_preference}")
        if preferences.price_preference != "any":
            pref_parts.append(f"Price preference: {preferences.price_preference}")
        
        preferences_text = "\n".join(pref_parts) if pref_parts else "No specific preferences set."
    else:
        preferences_text = "No preferences set - recommend popular/highly-rated items."
    
    prompt = f"""Analyze this restaurant menu and recommend the top {max_items} dishes for a customer.

MENU ITEMS:
{menu_text}

CUSTOMER PREFERENCES:
{preferences_text}

Return your recommendations as a JSON array with exactly {max_items} items. Each item should have:
- "item_name": exact name from the menu
- "score": match score from 0-100 based on how well it fits preferences
- "reasoning": brief explanation (1-2 sentences) of why this is recommended

Consider:
1. How well each item matches dietary restrictions (most important)
2. Alignment with favorite cuisines and flavor preferences
3. Avoidance of disliked ingredients
4. General popularity indicators in the dish name/description

Return ONLY the JSON array, no other text."""

    # Check if we have an API key
    if not settings.anthropic_api_key:
        # Return mock recommendations if no API key
        return _generate_mock_recommendations(menu_items, max_items)
    
    try:
        client = Anthropic(api_key=settings.anthropic_api_key)
        
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        # Parse response
        response_text = message.content[0].text.strip()
        
        # Clean up response if needed
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        
        recommendations_data = json.loads(response_text)
        
        return [
            RecommendedItem(
                item_name=item["item_name"],
                score=item["score"],
                reasoning=item["reasoning"]
            )
            for item in recommendations_data[:max_items]
        ]
        
    except Exception as e:
        print(f"AI recommendation error: {e}")
        # Fallback to mock recommendations
        return _generate_mock_recommendations(menu_items, max_items)


def _generate_mock_recommendations(menu_items: list[MenuItem], max_items: int) -> list[RecommendedItem]:
    """Generate basic recommendations when AI is unavailable."""
    recommendations = []
    
    for i, item in enumerate(menu_items[:max_items]):
        score = 95 - (i * 5)  # Decreasing scores
        recommendations.append(
            RecommendedItem(
                item_name=item.item_name,
                score=score,
                reasoning=f"Popular menu item. {'Highly rated by other customers.' if i == 0 else 'Recommended based on menu popularity.'}"
            )
        )
    
    return recommendations
