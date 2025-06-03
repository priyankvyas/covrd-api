#!/usr/bin/env python3
"""
Database initialization script for Meal Planning Platform

This script creates the database tables and optionally adds sample data.
Run this script to set up your database for the first time.

Usage:
    python scripts/init_db.py              # Create tables only
    python scripts/init_db.py --sample     # Create tables and add sample data
    python scripts/init_db.py --reset      # Drop existing tables and recreate
"""

import sys
import os
import argparse
from datetime import datetime

# Add the parent directory to Python path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import engine, create_tables, drop_tables, get_db_session
from app.models import Recipe


def create_sample_recipes():
    """Create sample recipes for testing and development"""
    
    sample_recipes = [
        {
            "name": "Classic Spaghetti Carbonara",
            "description": "A traditional Italian pasta dish with eggs, cheese, and pancetta",
            "instructions": """1. Cook spaghetti in salted water until al dente
2. While pasta cooks, whisk eggs with grated Parmesan
3. Cook pancetta until crispy
4. Drain pasta, reserving pasta water
5. Quickly mix hot pasta with egg mixture, adding pasta water as needed
6. Add pancetta and black pepper
7. Serve immediately with extra Parmesan""",
            "prep_time_minutes": 10,
            "cook_time_minutes": 15,
            "total_time_minutes": 25,
            "servings": 4,
            "difficulty": 2,
            "cuisine_type": "Italian",
            "meal_type": "dinner",
            "course_type": "main",
            "is_vegetarian": False,
            "is_gluten_free": False,
            "calories_per_serving": 520,
            "ingredients_json": [
                {"name": "spaghetti", "amount": "400g"},
                {"name": "eggs", "amount": "3 large"},
                {"name": "parmesan cheese", "amount": "100g, grated"},
                {"name": "pancetta", "amount": "150g, diced"},
                {"name": "black pepper", "amount": "to taste"}
            ],
            "tags": ["italian", "pasta", "quick", "traditional"],
            "equipment_needed": ["large pot", "whisk", "frying pan"]
        },
        {
            "name": "Buddha Bowl with Quinoa",
            "description": "A nutritious bowl with quinoa, roasted vegetables, and tahini dressing",
            "instructions": """1. Cook quinoa according to package instructions
2. Roast sweet potatoes and broccoli at 400°F for 25 minutes
3. Massage kale with lemon juice and olive oil
4. Prepare tahini dressing by whisking tahini, lemon juice, water, and garlic
5. Assemble bowl with quinoa, roasted vegetables, kale, and avocado
6. Drizzle with tahini dressing and sprinkle with pumpkin seeds""",
            "prep_time_minutes": 20,
            "cook_time_minutes": 30,
            "total_time_minutes": 50,
            "servings": 2,
            "difficulty": 1,
            "cuisine_type": "Mediterranean",
            "meal_type": "lunch",
            "course_type": "main",
            "is_vegetarian": True,
            "is_vegan": True,
            "is_gluten_free": True,
            "is_dairy_free": True,
            "calories_per_serving": 420,
            "ingredients_json": [
                {"name": "quinoa", "amount": "1 cup"},
                {"name": "sweet potato", "amount": "1 large, cubed"},
                {"name": "broccoli", "amount": "1 head, cut into florets"},
                {"name": "kale", "amount": "2 cups, chopped"},
                {"name": "avocado", "amount": "1, sliced"},
                {"name": "tahini", "amount": "3 tbsp"},
                {"name": "lemon juice", "amount": "2 tbsp"},
                {"name": "pumpkin seeds", "amount": "2 tbsp"}
            ],
            "tags": ["healthy", "vegan", "gluten-free", "bowl", "vegetarian"],
            "equipment_needed": ["baking sheet", "saucepan", "whisk"]
        },
        {
            "name": "Chicken Tikka Masala",
            "description": "Creamy tomato-based curry with tender chicken pieces",
            "instructions": """1. Marinate chicken in yogurt and spices for 30 minutes
2. Cook chicken in a hot pan until browned, set aside
3. Sauté onions, garlic, and ginger until fragrant
4. Add spices and tomato paste, cook for 1 minute
5. Add crushed tomatoes and simmer for 10 minutes
6. Stir in cream and return chicken to pan
7. Simmer until chicken is cooked through
8. Serve with rice and naan""",
            "prep_time_minutes": 45,
            "cook_time_minutes": 30,
            "total_time_minutes": 75,
            "servings": 4,
            "difficulty": 3,
            "cuisine_type": "Indian",
            "meal_type": "dinner",
            "course_type": "main",
            "is_vegetarian": False,
            "is_gluten_free": True,
            "calories_per_serving": 380,
            "ingredients_json": [
                {"name": "chicken breast", "amount": "500g, cubed"},
                {"name": "yogurt", "amount": "1/2 cup"},
                {"name": "onion", "amount": "1 large, diced"},
                {"name": "garlic", "amount": "4 cloves, minced"},
                {"name": "ginger", "amount": "1 tbsp, grated"},
                {"name": "crushed tomatoes", "amount": "400g can"},
                {"name": "heavy cream", "amount": "1/2 cup"},
                {"name": "garam masala", "amount": "2 tsp"},
                {"name": "cumin", "amount": "1 tsp"},
                {"name": "paprika", "amount": "1 tsp"}
            ],
            "tags": ["indian", "curry", "spicy", "protein"],
            "equipment_needed": ["large pan", "mixing bowl"]
        }
    ]
    
    # Create database session
    db = get_db_session()
    
    try:
        # Add sample recipes to database
        for recipe_data in sample_recipes:
            recipe = Recipe(**recipe_data)
            db.add(recipe)
        
        # Commit all recipes
        db.commit()
        print(f"✅ Added {len(sample_recipes)} sample recipes to database")
        
        # Print what we added
        for recipe_data in sample_recipes:
            print(f"   - {recipe_data['name']} ({recipe_data['cuisine_type']})")
            
    except Exception as e:
        db.rollback()
        print(f"❌ Error adding sample recipes: {e}")
        raise
    finally:
        db.close()


def main():
    """Main function to initialize the database"""
    
    parser = argparse.ArgumentParser(description="Initialize the meal planner database")
    parser.add_argument("--sample", action="store_true", help="Add sample recipes")
    parser.add_argument("--reset", action="store_true", help="Drop and recreate all tables")
    
    args = parser.parse_args()
    
    print("🚀 Initializing Meal Planner Database...")
    print(f"Database URL: {engine.url}")
    
    try:
        if args.reset:
            print("⚠️  Dropping existing tables...")
            drop_tables()
            print("✅ Tables dropped")
        
        print("📝 Creating database tables...")
        create_tables()
        print("✅ Database tables created successfully")
        
        if args.sample:
            print("🍳 Adding sample recipes...")
            create_sample_recipes()
        
        print("\n🎉 Database initialization complete!")
        print("\nNext steps:")
        print("1. Start your FastAPI server: uvicorn app.main:app --reload")
        print("2. Check your database was created properly")
        if not args.sample:
            print("3. Run with --sample flag to add test recipes")
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()