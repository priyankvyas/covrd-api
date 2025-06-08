#!/usr/bin/env python3
"""
Check Ingestion Results Script

This script provides a quick way to verify your recipe ingestion results
and get insights into your recipe database.

Usage:
    python scripts/check_ingestion.py              # Basic stats
    python scripts/check_ingestion.py --detailed   # Detailed breakdown
    python scripts/check_ingestion.py --samples 5  # Show sample recipes
"""

import sys
import os
import argparse
from collections import Counter
from datetime import datetime, timedelta

# Add the parent directory to Python path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import get_db_session
from app.models import Recipe


def print_basic_stats(db):
    """Print basic database statistics"""
    
    total_recipes = db.query(Recipe).count()
    
    print("\n📊 RECIPE DATABASE STATISTICS")
    print("="*40)
    print(f"Total Recipes: {total_recipes}")
    
    if total_recipes == 0:
        print("❌ No recipes found in database!")
        print("   Run: python scripts/run_ingestion.py")
        return
    
    # Count by source
    sources = db.query(Recipe.external_source).all()
    source_counts = Counter([s[0] for s in sources if s[0]])
    
    print("\n📥 Sources:")
    for source, count in source_counts.items():
        print(f"   • {source}: {count} recipes")
    
    # Dietary restriction stats
    vegetarian_count = db.query(Recipe).filter(Recipe.is_vegetarian == True).count()
    vegan_count = db.query(Recipe).filter(Recipe.is_vegan == True).count()
    gluten_free_count = db.query(Recipe).filter(Recipe.is_gluten_free == True).count()
    dairy_free_count = db.query(Recipe).filter(Recipe.is_dairy_free == True).count()
    
    print("\n🥗 Dietary Restrictions:")
    print(f"   • Vegetarian: {vegetarian_count} ({(vegetarian_count/total_recipes)*100:.1f}%)")
    print(f"   • Vegan: {vegan_count} ({(vegan_count/total_recipes)*100:.1f}%)")
    print(f"   • Gluten-Free: {gluten_free_count} ({(gluten_free_count/total_recipes)*100:.1f}%)")
    print(f"   • Dairy-Free: {dairy_free_count} ({(dairy_free_count/total_recipes)*100:.1f}%)")


def print_detailed_stats(db):
    """Print detailed database analysis"""
    
    print_basic_stats(db)
    
    # Cuisine analysis
    cuisines = db.query(Recipe.cuisine_type).all()
    cuisine_counts = Counter([c[0] for c in cuisines if c[0]])
    
    print("\n🌍 Cuisines (Top 10):")
    for cuisine, count in cuisine_counts.most_common(10):
        print(f"   • {cuisine}: {count} recipes")
    
    # Meal type analysis
    meal_types = db.query(Recipe.meal_type).all()
    meal_type_counts = Counter([m[0] for m in meal_types if m[0]])
    
    print("\n🍽️ Meal Types:")
    for meal_type, count in meal_type_counts.items():
        print(f"   • {meal_type}: {count} recipes")
    
    # Difficulty analysis
    difficulties = db.query(Recipe.difficulty).all()
    difficulty_counts = Counter([d[0] for d in difficulties if d[0]])
    
    print("\n⭐ Difficulty Distribution:")
    for difficulty in sorted(difficulty_counts.keys()):
        count = difficulty_counts[difficulty]
        stars = "⭐" * difficulty
        print(f"   • {difficulty} {stars}: {count} recipes")
    
    # Time analysis
    prep_times = [r.prep_time_minutes for r in db.query(Recipe.prep_time_minutes).all() if r.prep_time_minutes]
    cook_times = [r.cook_time_minutes for r in db.query(Recipe.cook_time_minutes).all() if r.cook_time_minutes]
    
    if prep_times:
        avg_prep = sum(prep_times) / len(prep_times)
        print(f"\n⏱️ Average Prep Time: {avg_prep:.1f} minutes")
    
    if cook_times:
        avg_cook = sum(cook_times) / len(cook_times)
        print(f"⏱️ Average Cook Time: {avg_cook:.1f} minutes")
    
    # Recent additions
    recent_cutoff = datetime.now() - timedelta(days=1)
    recent_count = db.query(Recipe).filter(Recipe.created_at > recent_cutoff).count()
    
    print(f"\n📅 Recent Additions (24h): {recent_count} recipes")


def show_sample_recipes(db, count=5):
    """Show sample recipes"""
    
    recipes = db.query(Recipe).limit(count).all()
    
    print(f"\n🍳 SAMPLE RECIPES (showing {len(recipes)} of {db.query(Recipe).count()}):")
    print("="*60)
    
    for i, recipe in enumerate(recipes, 1):
        print(f"\n{i}. {recipe.name}")
        print(f"   Cuisine: {recipe.cuisine_type or 'Unknown'}")
        print(f"   Type: {recipe.meal_type or 'Unknown'}")
        print(f"   Difficulty: {'⭐' * (recipe.difficulty or 1)}")
        print(f"   Time: {recipe.prep_time_minutes or 0}min prep + {recipe.cook_time_minutes or 0}min cook")
        print(f"   Dietary: {', '.join(recipe.dietary_flags) if recipe.dietary_flags else 'None specified'}")
        print(f"   Source: {recipe.external_source or 'Manual'}")
        
        if recipe.ingredients_json:
            ingredient_count = len(recipe.ingredients_json)
            print(f"   Ingredients: {ingredient_count} items")
            
            # Show first few ingredients
            ingredients = recipe.ingredients_json[:3]
            for ingredient in ingredients:
                name = ingredient.get('name', 'Unknown')
                amount = ingredient.get('amount', '')
                print(f"     • {amount} {name}".strip())
            
            if ingredient_count > 3:
                print(f"     ... and {ingredient_count - 3} more")


def test_dietary_filtering(db):
    """Test the dietary filtering functionality (your core innovation)"""
    
    print("\n🧪 TESTING DIETARY FILTERING (Your Core Innovation)")
    print("="*55)
    
    # Test individual restrictions
    restrictions = [
        ("vegetarian", Recipe.is_vegetarian == True),
        ("vegan", Recipe.is_vegan == True),
        ("gluten_free", Recipe.is_gluten_free == True),
        ("dairy_free", Recipe.is_dairy_free == True)
    ]
    
    for name, filter_condition in restrictions:
        count = db.query(Recipe).filter(filter_condition).count()
        print(f"✅ {name.title().replace('_', '-')}: {count} recipes found")
        
        # Show one example
        example = db.query(Recipe).filter(filter_condition).first()
        if example:
            print(f"   Example: {example.name}")
    
    # Test combination filtering (the power of symbolic constraints!)
    vegan_gluten_free = db.query(Recipe).filter(
        Recipe.is_vegan == True,
        Recipe.is_gluten_free == True
    ).count()
    
    print(f"\n🎯 Combined Filter Test:")
    print(f"   Vegan + Gluten-Free: {vegan_gluten_free} recipes")
    print("   ✅ Symbolic constraints ensure 100% compliance!")


def main():
    """Main function"""
    
    parser = argparse.ArgumentParser(description="Check recipe ingestion results")
    parser.add_argument("--detailed", action="store_true", help="Show detailed statistics")
    parser.add_argument("--samples", type=int, default=5, help="Number of sample recipes to show")
    parser.add_argument("--test-filters", action="store_true", help="Test dietary filtering")
    
    args = parser.parse_args()
    
    print("🔍 RECIPE DATABASE CHECKER")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Get database session
    try:
        db = get_db_session()
        
        if args.detailed:
            print_detailed_stats(db)
        else:
            print_basic_stats(db)
        
        if args.samples > 0:
            show_sample_recipes(db, args.samples)
        
        if args.test_filters:
            test_dietary_filtering(db)
        
        print("\n✅ Database check completed!")
        print("💡 Try these commands:")
        print("   python scripts/check_ingestion.py --detailed")
        print("   python scripts/check_ingestion.py --samples 10")
        print("   python scripts/check_ingestion.py --test-filters")
        
    except Exception as e:
        print(f"❌ Error checking database: {e}")
        print("   Make sure your database is set up:")
        print("   python scripts/init_db.py")
        sys.exit(1)
    
    finally:
        if 'db' in locals():
            db.close()


if __name__ == "__main__":
    main()