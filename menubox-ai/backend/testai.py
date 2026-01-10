"""
Test script for MenuBox AI recommendation system.
Run from backend directory with: python test_ai_recommendations.py
"""

import sys
sys.path.insert(0, '.')

from uuid import uuid4
from app.core.database import SessionLocal, engine
from app.core.config import get_settings
from app.models.restaurant import Restaurant
from app.models.menu_item import MenuItem
from app.models.preference import Preference
from app.models.user import User
from app.services.ai_service import generate_recommendations
import asyncio

settings = get_settings()

def check_api_key():
    """Check if Anthropic API key is configured."""
    if settings.anthropic_api_key:
        # Show first/last few chars for verification
        key = settings.anthropic_api_key
        masked = f"{key[:10]}...{key[-4:]}" if len(key) > 14 else "***"
        print(f"✅ API Key configured: {masked}")
        return True
    else:
        print("❌ API Key NOT configured")
        print("   Make sure ANTHROPIC_API_KEY is set in backend/.env")
        return False

def create_test_data(db):
    """Create test restaurant with menu items."""
    
    # Check if test restaurant already exists
    existing = db.query(Restaurant).filter(Restaurant.name == "Test Italian Bistro").first()
    if existing:
        print(f"✅ Test restaurant already exists: {existing.id}")
        return existing
    
    # Create test restaurant
    restaurant = Restaurant(
        id=uuid4(),
        name="Test Italian Bistro",
        location ="123 Test Street",
        cuisine_type="Italian",
        price_range="$$"
    )
    db.add(restaurant)
    db.flush()
    
    # Create menu items
    menu_items_data = [
        {"item_name": "Margherita Pizza", "description": "Fresh tomatoes, mozzarella, basil", "price": 14.99, "category": "Pizza"},
        {"item_name": "Spicy Arrabbiata Pasta", "description": "Penne with spicy tomato sauce, garlic, chili flakes", "price": 13.99, "category": "Pasta"},
        {"item_name": "Grilled Salmon", "description": "Atlantic salmon with lemon butter, seasonal vegetables", "price": 24.99, "category": "Seafood"},
        {"item_name": "Caesar Salad", "description": "Romaine, parmesan, croutons, house caesar dressing", "price": 10.99, "category": "Salads"},
        {"item_name": "Chicken Parmesan", "description": "Breaded chicken breast, marinara, melted mozzarella", "price": 18.99, "category": "Entrees"},
        {"item_name": "Tiramisu", "description": "Classic Italian dessert with espresso and mascarpone", "price": 8.99, "category": "Desserts"},
        {"item_name": "Vegetable Risotto", "description": "Creamy arborio rice with seasonal vegetables, parmesan", "price": 16.99, "category": "Vegetarian"},
        {"item_name": "Beef Carpaccio", "description": "Thinly sliced raw beef, arugula, capers, olive oil", "price": 15.99, "category": "Appetizers"},
    ]
    
    for item_data in menu_items_data:
        menu_item = MenuItem(
            id=uuid4(),
            restaurant_id=restaurant.id,
            **item_data
        )
        db.add(menu_item)
    
    db.commit()
    print(f"✅ Created test restaurant: {restaurant.id}")
    print(f"   Added {len(menu_items_data)} menu items")
    
    return restaurant

def create_test_preferences():
    """Create mock preferences for testing."""
    class MockPreference:
        dietary_restrictions = ["vegetarian"]
        favorite_cuisines = ["Italian", "Mediterranean"]
        disliked_ingredients = ["anchovies", "olives"]
        spice_preference = "mild"
        price_preference = "moderate"
    
    return MockPreference()

async def test_recommendations(db, restaurant):
    """Test the AI recommendation service directly."""
    print("\n" + "="*50)
    print("Testing AI Recommendation Service")
    print("="*50)
    
    # Get menu items
    menu_items = db.query(MenuItem).filter(MenuItem.restaurant_id == restaurant.id).all()
    print(f"\n📋 Menu items loaded: {len(menu_items)}")
    for item in menu_items:
        print(f"   - {item.item_name} (${item.price})")
    
    # Create test preferences
    preferences = create_test_preferences()
    print(f"\n👤 Test preferences:")
    print(f"   Dietary: {preferences.dietary_restrictions}")
    print(f"   Cuisines: {preferences.favorite_cuisines}")
    print(f"   Dislikes: {preferences.disliked_ingredients}")
    print(f"   Spice: {preferences.spice_preference}")
    
    # Generate recommendations
    print("\n🤖 Calling Claude AI...")
    print("-"*50)
    
    try:
        recommendations = await generate_recommendations(
            menu_items=menu_items,
            preferences=preferences,
            max_items=5
        )
        
        print("\n✅ Recommendations received!")
        print("-"*50)
        for i, rec in enumerate(recommendations, 1):
            print(f"\n{i}. {rec.item_name}")
            print(f"   Score: {rec.score}/100")
            print(f"   Reason: {rec.reasoning}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("="*50)
    print("MenuBox AI - Recommendation Test")
    print("="*50)
    
    # Check API key
    print("\n1. Checking API Key...")
    has_key = check_api_key()
    
    if not has_key:
        print("\n⚠️  Will use mock recommendations (no AI)")
    
    # Create test data
    print("\n2. Setting up test data...")
    db = SessionLocal()
    try:
        restaurant = create_test_data(db)
        
        # Test recommendations
        print("\n3. Testing recommendations...")
        asyncio.run(test_recommendations(db, restaurant))
        
        # Print restaurant ID for API testing
        print("\n" + "="*50)
        print("📝 For API Testing:")
        print("="*50)
        print(f"\nRestaurant ID: {restaurant.id}")
        print("\nUse this in your API request:")
        print(f'''
curl -X POST "http://localhost:8000/api/recommendations/generate" \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -d '{{"restaurant_id": "{restaurant.id}", "max_items": 5}}'
''')
        
    finally:
        db.close()

if __name__ == "__main__":
    main()
