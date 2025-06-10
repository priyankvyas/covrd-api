#!/usr/bin/env python3
"""
Fix Dietary Flags Script

This script re-analyzes existing recipes and corrects dietary restriction flags
using the improved detection logic. This is crucial for maintaining the accuracy
of your symbolic constraint system.

Usage:
    python scripts/fix_dietary_flags.py                    # Fix all recipes
    python scripts/fix_dietary_flags.py --dry-run          # Preview changes
    python scripts/fix_dietary_flags.py --recipe-id 123    # Fix specific recipe
    python scripts/fix_dietary_flags.py --vegan-only       # Fix only vegan misclassifications
"""

import sys
import os
import argparse
import logging
from datetime import datetime
from typing import List, Dict, Any

# Add the parent directory to Python path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import get_db_session
from app.models import Recipe

class DietaryFlagFixer:
    """Fix dietary flags for existing recipes"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"ingester.flag_fixer")
        self.fixes_made = {
            "vegetarian": {"fixed": 0, "examples": []},
            "vegan": {"fixed": 0, "examples": []},
            "gluten_free": {"fixed": 0, "examples": []},
            "dairy_free": {"fixed": 0, "examples": []},
            "nut_free": {"fixed": 0, "examples": []},
            # Add the more complex flag support later
        }
    
    def detect_dietary_restrictions(self, ingredients: List[Dict[str, Any]]) -> Dict[str, bool]:
        """
        Detect dietary restrictions based on ingredients
        This is part of your core innovation - reliable dietary restriction detection
        """
        
        # Convert ingredients to lowercase text for analysis
        ingredient_text = " ".join([
            ingredient.get("name", "").lower() 
            for ingredient in ingredients
        ])
        
        # Define restriction keywords (comprehensive meat list)
        meat_keywords = [
            # Common meats
            "beef", "chicken", "pork", "lamb", "turkey", "duck", "goose", "rabbit",
            "venison", "veal", "mutton", "goat", "meat", "steak", "ground beef",
            
            # Cuts and specific parts
            "oxtail", "ribs", "brisket", "chuck", "sirloin", "tenderloin", "flank",
            "drumstick", "thigh", "breast", "wing", "leg", "shoulder", "loin",
            
            # Processed meats
            "bacon", "ham", "sausage", "salami", "pepperoni", "prosciutto", 
            "pancetta", "chorizo", "pastrami", "corned beef", "hot dog", "bratwurst",
            "mortadella", "capicola", "bresaola", "kielbasa",
            
            # Seafood and fish
            "fish", "salmon", "tuna", "cod", "halibut", "tilapia", "sea bass", "trout",
            "mackerel", "sardine", "anchovy", "herring", "sole", "flounder", "snapper",
            "shrimp", "crab", "lobster", "scallop", "mussel", "clam", "oyster",
            "squid", "octopus", "calamari", "prawns", "crawfish", "crayfish",
            
            # Poultry variations
            "chicken breast", "chicken thigh", "chicken wing", "whole chicken",
            "turkey breast", "ground turkey", "duck breast", "duck leg",
            
            # Game and organ meats
            "liver", "kidney", "heart", "tongue", "brain", "sweetbread", "tripe",
            "blood sausage", "boudin", "haggis",
            
            # Stock and broth
            "chicken stock", "beef stock", "bone broth", "chicken broth", "beef broth",
            "demi-glace", "meat stock", "fish stock", "seafood stock"
        ]
        
        dairy_keywords = [
            # Basic dairy
            "milk", "cheese", "butter", "cream", "yogurt", "yoghurt", 
            
            # Milk varieties
            "whole milk", "skim milk", "2% milk", "1% milk", "buttermilk",
            "goat milk", "sheep milk", "buffalo milk", "condensed milk", 
            "evaporated milk", "powdered milk", "dry milk", "milk powder",
            
            # Cheese varieties
            "cheddar", "mozzarella", "parmesan", "parmigiano", "pecorino",
            "ricotta", "cottage cheese", "cream cheese", "feta", "goat cheese",
            "blue cheese", "brie", "camembert", "swiss", "gruyere", "gouda",
            "provolone", "manchego", "asiago", "gorgonzola", "roquefort",
            "mascarpone", "boursin", "queso", "paneer", "halloumi",
            
            # Cream varieties
            "heavy cream", "whipping cream", "light cream", "half and half",
            "sour cream", "crème fraîche", "whipped cream", "clotted cream",
            "double cream", "single cream",
            
            # Yogurt varieties
            "greek yogurt", "plain yogurt", "vanilla yogurt", "frozen yogurt",
            "kefir", "labneh", "skyr",
            
            # Butter varieties
            "salted butter", "unsalted butter", "clarified butter", "ghee",
            "cultured butter", "butter substitute",
            
            # Ice cream and frozen
            "ice cream", "gelato", "sorbet", "frozen custard", "sherbet",
            "milkshake", "milk shake",
            
            # Dairy-based ingredients
            "casein", "whey", "lactose", "milk solids", "milk protein",
            "sodium caseinate", "calcium caseinate", "lactalbumin",
            "lactoglobulin", "milk fat", "butterfat",
            
            # Sauces and preparations
            "white sauce", "béchamel", "alfredo", "carbonara sauce",
            "cheese sauce", "cream sauce", "ranch dressing", "caesar dressing"
        ]
        
        gluten_keywords = [
            # Wheat varieties
            "flour", "wheat", "wheat flour", "all-purpose flour", "bread flour",
            "cake flour", "pastry flour", "self-rising flour", "whole wheat",
            "durum wheat", "semolina", "bulgur", "wheat bran", "wheat germ",
            "spelt", "kamut", "einkorn", "emmer", "farro",
            
            # Other gluten grains
            "barley", "rye", "triticale", "malt", "malted barley", "malt extract",
            "malt syrup", "malt vinegar", "malted milk", "beer", "ale", "lager",
            
            # Bread products
            "bread", "white bread", "whole grain bread", "sourdough", "bagel",
            "english muffin", "baguette", "ciabatta", "focaccia", "pita",
            "naan", "tortilla", "wrap", "roll", "bun", "croissant", "brioche",
            "breadcrumbs", "bread crumbs", "panko", "croutons",
            
            # Pasta and noodles
            "pasta", "spaghetti", "linguine", "fettuccine", "penne", "rigatoni",
            "macaroni", "fusilli", "farfalle", "ravioli", "tortellini", "gnocchi",
            "lasagna", "noodles", "egg noodles", "ramen", "udon", "soba",
            "couscous", "orzo",
            
            # Baked goods
            "cake", "cookies", "crackers", "muffins", "donuts", "doughnuts",
            "pastry", "pie crust", "pizza dough", "biscuits", "scones",
            "pretzels", "wafers",
            
            # Cereals and grains
            "cereal", "granola", "muesli", "oats", "oatmeal", "rolled oats",
            "steel cut oats", "barley", "wheat berries",
            
            # Hidden gluten sources
            "soy sauce", "tamari", "teriyaki", "hoisin sauce", "oyster sauce",
            "worcestershire", "miso", "seitan", "vital wheat gluten",
            "modified food starch", "hydrolyzed wheat protein",
            "textured vegetable protein", "tvp",
            
            # Processed foods (often contain gluten)
            "breading", "battered", "tempura", "flour tortilla", "graham crackers",
            "matzo", "communion wafer"
        ]
        
        nut_keywords = [
            # Tree nuts
            "almond", "almonds", "brazil nut", "brazil nuts", "cashew", "cashews",
            "hazelnut", "hazelnuts", "macadamia", "macadamias", "pecan", "pecans",
            "pine nut", "pine nuts", "pistachio", "pistachios", "walnut", "walnuts",
            "chestnut", "chestnuts", "beech nut", "beech nuts", "hickory nut",
            "black walnut", "english walnut",
            
            # Peanuts (technically legumes but often grouped with nuts)
            "peanut", "peanuts", "groundnut", "groundnuts", "monkey nut",
            
            # Nut butters
            "almond butter", "peanut butter", "cashew butter", "hazelnut butter",
            "walnut butter", "pecan butter", "pistachio butter", "tahini",
            "sunflower seed butter", "sunbutter",
            
            # Nut oils
            "almond oil", "walnut oil", "hazelnut oil", "peanut oil",
            "groundnut oil", "argan oil",
            
            # Nut flours and meals
            "almond flour", "almond meal", "hazelnut flour", "walnut flour",
            "pecan flour", "chestnut flour", "coconut flour",
            
            # Nut milks
            "almond milk", "cashew milk", "hazelnut milk", "walnut milk",
            "macadamia milk", "pecan milk", "pistachio milk",
            
            # Coconut (technically a fruit but often restricted with nuts)
            "coconut", "coconut oil", "coconut milk", "coconut cream",
            "coconut flour", "desiccated coconut", "coconut flakes",
            "coconut butter", "coconut meat",
            
            # Seeds often grouped with nuts
            "sesame", "sesame seeds", "sesame oil", "sunflower seeds",
            "pumpkin seeds", "poppy seeds", "chia seeds", "flax seeds",
            "hemp seeds",
            
            # Nut-based products
            "marzipan", "nougat", "praline", "gianduja", "nutella",
            "amaretto", "frangelico", "orgeat",
            
            # Hidden nut ingredients
            "natural flavoring", "artificial flavoring", "nut extract",
            "almond extract", "vanilla extract"  # Some vanilla extracts contain nuts
        ]
        
        # Detect restrictions (absence of problematic ingredients)
        has_meat = any(keyword in ingredient_text for keyword in meat_keywords)
        has_dairy = any(keyword in ingredient_text for keyword in dairy_keywords)
        has_gluten = any(keyword in ingredient_text for keyword in gluten_keywords)
        has_nuts = any(keyword in ingredient_text for keyword in nut_keywords)
        
        return {
            "is_vegetarian": not has_meat,
            "is_vegan": not has_meat and not has_dairy,
            "is_gluten_free": not has_gluten,
            "is_dairy_free": not has_dairy,
            "is_nut_free": not has_nuts,
            # More complex restrictions would need nutritional data
            "is_low_carb": False,  # Can't determine without nutritional info
            "is_keto": False,      # Can't determine without nutritional info
            "is_paleo": not has_dairy and not has_gluten  # Simplified paleo check
        }
    
    def analyze_single_recipe(self, recipe: Recipe) -> Dict[str, Any]:
        """Analyze a single recipe and return corrected dietary flags"""
        
        if not recipe.ingredients_json:
            return {}
        
        # Use the improved dietary detection from base ingester
        corrected_flags = self.detect_dietary_restrictions(recipe.ingredients_json)
        
        # Compare with current flags
        changes = {}
        current_flags = {
            "is_vegetarian": recipe.is_vegetarian,
            "is_vegan": recipe.is_vegan,
            "is_gluten_free": recipe.is_gluten_free,
            "is_dairy_free": recipe.is_dairy_free,
            "is_nut_free": recipe.is_nut_free,
            # Add more complex flag support later
        }
        
        for flag_name, new_value in corrected_flags.items():
            current_value = current_flags.get(flag_name)
            if current_value != new_value:
                changes[flag_name] = {
                    "old": current_value,
                    "new": new_value
                }
        
        return changes
    
    def find_problematic_recipes(self, restriction_type: str = None) -> List[Recipe]:
        """Find recipes that might have incorrect dietary flags"""
        
        db = get_db_session()
        try:
            query = db.query(Recipe).filter(Recipe.ingredients_json.isnot(None))
            
            if restriction_type == "vegan":
                # Find recipes marked as vegan that might contain meat/dairy
                query = query.filter(Recipe.is_vegan == True)
            elif restriction_type == "vegetarian":
                # Find recipes marked as vegetarian that might contain meat
                query = query.filter(Recipe.is_vegetarian == True)
            elif restriction_type == "gluten_free":
                # Find recipes marked as gluten-free that might contain gluten-containing products
                query = query.filter(Recipe.is_gluten_free == True)
            elif restriction_type == "dairy_free":
                # Find recipes marked as dairy-free that might contain milk products
                query = query.filter(Recipe.is_dairy_free == True)
            elif restriction_type == "nut_free":
                # Find recipes marked as nut-free that might contain nuts
                query = query.filter(Recipe.is_nut_free == True)
            # Add more complex flag support later
            
            return query.all()
        finally:
            db.close()
    
    def fix_recipe_flags(self, recipe: Recipe, dry_run: bool = False) -> Dict[str, Any]:
        """Fix dietary flags for a specific recipe"""
        
        changes = self.analyze_single_recipe(recipe)
        
        if not changes:
            return {}
        
        # Log the changes
        ingredient_text = ", ".join([
            ing.get("name", "") for ing in recipe.ingredients_json[:5]
        ])
        if len(recipe.ingredients_json) > 5:
            ingredient_text += f" (and {len(recipe.ingredients_json) - 5} more)"
        
        self.logger.info(f"🔍 Recipe: {recipe.name}")
        self.logger.info(f"   Ingredients: {ingredient_text}")
        
        for flag_name, change in changes.items():
            flag_display = flag_name.replace("is_", "").replace("_", " ").title()
            old_status = "✅" if change["old"] else "❌"
            new_status = "✅" if change["new"] else "❌"
            
            self.logger.info(f"   {flag_display}: {old_status} → {new_status}")
            
            # Track statistics
            restriction_key = flag_name.replace("is_", "")
            if restriction_key in self.fixes_made:
                self.fixes_made[restriction_key]["fixed"] += 1
                if len(self.fixes_made[restriction_key]["examples"]) < 3:
                    self.fixes_made[restriction_key]["examples"].append({
                        "name": recipe.name,
                        "old": change["old"],
                        "new": change["new"]
                    })
        
        if not dry_run:
            # Apply the changes to database
            db = get_db_session()
            try:
                db_recipe = db.query(Recipe).filter(Recipe.id == recipe.id).first()
                
                for flag_name, change in changes.items():
                    setattr(db_recipe, flag_name, change["new"])
                
                db_recipe.updated_at = datetime.now()
                db.commit()
                
                self.logger.info(f"✅ Updated recipe ID {recipe.id}")
                
            except Exception as e:
                db.rollback()
                self.logger.error(f"❌ Error updating recipe {recipe.id}: {e}")
                raise
            finally:
                db.close()
        
        return changes
    
    def run_analysis(self, recipe_id: int = None, restriction_type: str = None, dry_run: bool = False):
        """Run the dietary flag fixing process"""
        
        self.logger.info("🔍 Starting dietary flag analysis...")
        
        if recipe_id:
            # Fix specific recipe
            db = get_db_session()
            try:
                recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
                if not recipe:
                    self.logger.error(f"Recipe with ID {recipe_id} not found")
                    return
                
                recipes_to_check = [recipe]
            finally:
                db.close()
        else:
            # Find all problematic recipes
            recipes_to_check = self.find_problematic_recipes(restriction_type)
        
        self.logger.info(f"📊 Analyzing {len(recipes_to_check)} recipes...")
        
        total_recipes_changed = 0
        
        for i, recipe in enumerate(recipes_to_check, 1):
            self.logger.info(f"\n🔄 Checking {i}/{len(recipes_to_check)}: {recipe.name}")
            
            try:
                changes = self.fix_recipe_flags(recipe, dry_run)
                
                if changes:
                    total_recipes_changed += 1
                    if dry_run:
                        self.logger.info("   [DRY RUN] - Would apply changes")
                else:
                    self.logger.info("   ✅ No changes needed")
                    
            except Exception as e:
                self.logger.error(f"   ❌ Error processing recipe: {e}")
                continue
        
        # Print summary
        self.print_fix_summary(total_recipes_changed, len(recipes_to_check), dry_run)
    
    def print_fix_summary(self, recipes_changed: int, total_analyzed: int, dry_run: bool):
        """Print summary of fixes made"""
        
        mode = "DRY RUN - NO CHANGES SAVED" if dry_run else "CHANGES APPLIED TO DATABASE"
        
        print("\n" + "="*60)
        print(f"🛠️  DIETARY FLAG FIX SUMMARY - {mode}")
        print("="*60)
        print(f"📊 Total Recipes Analyzed: {total_analyzed}")
        print(f"🔧 Recipes Needing Changes: {recipes_changed}")
        print(f"✅ Success Rate: {((total_analyzed - recipes_changed) / max(total_analyzed, 1)) * 100:.1f}% were already correct")
        
        if recipes_changed > 0:
            print(f"\n📝 Changes by Restriction Type:")
            for restriction, data in self.fixes_made.items():
                if data["fixed"] > 0:
                    print(f"   • {restriction.replace('_', ' ').title()}: {data['fixed']} recipes fixed")
                    
                    # Show examples
                    for example in data["examples"]:
                        old_status = "✅" if example["old"] else "❌"
                        new_status = "✅" if example["new"] else "❌"
                        print(f"     - {example['name']}: {old_status} → {new_status}")
        
        print("="*60)
        
        if dry_run and recipes_changed > 0:
            print("💡 To apply these fixes, run without --dry-run flag")
        elif recipes_changed > 0:
            print("🎉 All dietary flags have been corrected!")
            print("💡 Your symbolic constraint system is now more accurate!")


def main():
    """Main function"""
    
    parser = argparse.ArgumentParser(description="Fix dietary restriction flags for existing recipes")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without saving")
    parser.add_argument("--recipe-id", type=int, help="Fix specific recipe by ID")
    parser.add_argument("--vegan-only", action="store_true", help="Only check recipes marked as vegan")
    parser.add_argument("--vegetarian-only", action="store_true", help="Only check recipes marked as vegetarian")
    
    args = parser.parse_args()
    
    print("🛠️  DIETARY FLAG FIXER")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Determine restriction type filter
    restriction_type = None
    if args.vegan_only:
        restriction_type = "vegan"
    elif args.vegetarian_only:
        restriction_type = "vegetarian"
    
    try:
        fixer = DietaryFlagFixer()
        fixer.run_analysis(
            recipe_id=args.recipe_id,
            restriction_type=restriction_type,
            dry_run=args.dry_run
        )
        
        if not args.dry_run:
            print("\n💡 Next steps:")
            print("   • Test your API: curl 'http://localhost:8000/recipes/dietary/vegan'")
            print("   • Check results: python scripts/check_ingestion.py --test-filters")
        
    except Exception as e:
        print(f"❌ Error during dietary flag fixing: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()