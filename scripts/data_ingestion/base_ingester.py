"""
Base ingester class for recipe data sources

This module provides the base functionality for ingesting recipe data
from various external sources into our standardized Recipe model.
"""

import sys
import os
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime

# Add the parent directory to Python path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.core.database import get_db_session
from app.models import Recipe

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class BaseIngester(ABC):
    """Base class for all recipe data ingesters"""
    
    def __init__(self, source_name: str):
        self.source_name = source_name
        self.logger = logging.getLogger(f"ingester.{source_name}")
        self.stats = {
            "total_fetched": 0,
            "total_processed": 0,
            "total_saved": 0,
            "total_skipped": 0,
            "total_errors": 0,
            "start_time": None,
            "end_time": None
        }
    
    @abstractmethod
    async def fetch_recipes(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Fetch raw recipe data from the external source"""
        pass
    
    @abstractmethod
    def normalize_recipe(self, raw_recipe: Dict[str, Any]) -> Dict[str, Any]:
        """Convert raw recipe data to our Recipe model format"""
        pass
    
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
        
        # Define restriction keywords
        meat_keywords = [
            "beef", "chicken", "pork", "lamb", "turkey", "duck", "fish", "salmon", 
            "tuna", "shrimp", "crab", "lobster", "bacon", "ham", "sausage", "meat",
            "anchovy", "prosciutto", "pancetta", "chorizo", "pepperoni"
        ]
        
        dairy_keywords = [
            "milk", "cheese", "butter", "cream", "yogurt", "sour cream", "cheddar",
            "mozzarella", "parmesan", "ricotta", "cottage cheese", "whipped cream",
            "heavy cream", "half and half", "buttermilk"
        ]
        
        gluten_keywords = [
            "flour", "wheat", "bread", "pasta", "spaghetti", "noodles", "barley",
            "rye", "oats", "breadcrumbs", "soy sauce", "beer", "malt"
        ]
        
        nut_keywords = [
            "peanut", "almond", "walnut", "pecan", "cashew", "pistachio", 
            "hazelnut", "macadamia", "pine nut", "brazil nut"
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
    
    def estimate_cooking_times(self, instructions: str, num_ingredients: int) -> Dict[str, int]:
        """Estimate prep and cook times based on instructions and complexity"""
        
        instruction_text = instructions.lower()
        
        # Base times
        prep_time = max(5, num_ingredients * 2)  # 2 minutes per ingredient minimum
        cook_time = 15  # Default cook time
        
        # Adjust based on cooking methods mentioned
        if any(word in instruction_text for word in ["bake", "roast", "oven"]):
            cook_time += 20
        
        if any(word in instruction_text for word in ["simmer", "slow", "braise"]):
            cook_time += 30
        
        if any(word in instruction_text for word in ["marinate", "chill", "refrigerate"]):
            prep_time += 30
        
        if any(word in instruction_text for word in ["quick", "fast", "minutes"]):
            cook_time = max(10, cook_time - 10)
            prep_time = max(5, prep_time - 5)
        
        # Look for time mentions in instructions
        import re
        time_matches = re.findall(r'(\d+)\s*(minute|hour)', instruction_text)
        if time_matches:
            total_mentioned_time = sum(
                int(num) * (60 if unit.startswith('hour') else 1) 
                for num, unit in time_matches
            )
            cook_time = max(cook_time, total_mentioned_time)
        
        return {
            "prep_time_minutes": min(prep_time, 60),  # Cap at 60 minutes
            "cook_time_minutes": min(cook_time, 180), # Cap at 3 hours
            "total_time_minutes": min(prep_time + cook_time, 240)
        }
    
    def estimate_difficulty(self, instructions: str, num_ingredients: int, techniques: List[str] = None) -> int:
        """Estimate recipe difficulty from 1-5"""
        
        instruction_text = instructions.lower()
        difficulty = 1
        
        # Base difficulty on ingredient count
        if num_ingredients > 15:
            difficulty += 1
        elif num_ingredients > 10:
            difficulty += 0.5
        
        # Adjust for complex techniques
        complex_techniques = [
            "fold", "whip", "emulsify", "temper", "reduce", "deglaze", 
            "julienne", "brunoise", "chiffonade", "sous vide"
        ]
        
        if any(technique in instruction_text for technique in complex_techniques):
            difficulty += 1
        
        # Multiple cooking methods
        cooking_methods = ["bake", "fry", "sauté", "braise", "roast", "grill", "steam"]
        method_count = sum(1 for method in cooking_methods if method in instruction_text)
        if method_count > 2:
            difficulty += 0.5
        
        # Long instructions suggest complexity
        if len(instructions) > 1000:
            difficulty += 0.5
        
        return min(int(difficulty + 0.5), 5)  # Round and cap at 5
    
    def save_recipe(self, recipe_data: Dict[str, Any]) -> bool:
        """Save a normalized recipe to the database"""
        
        db = get_db_session()
        try:
            # Check if recipe already exists (by external_id and source)
            existing = db.query(Recipe).filter(
                Recipe.external_id == recipe_data.get("external_id"),
                Recipe.external_source == recipe_data.get("external_source")
            ).first()
            
            if existing:
                self.logger.info(f"Recipe '{recipe_data['name']}' already exists, skipping")
                self.stats["total_skipped"] += 1
                return False
            
            # Create new recipe
            recipe = Recipe(**recipe_data)
            db.add(recipe)
            db.commit()
            
            self.logger.info(f"✅ Saved recipe: {recipe_data['name']}")
            self.stats["total_saved"] += 1
            return True
            
        except Exception as e:
            db.rollback()
            self.logger.error(f"❌ Error saving recipe '{recipe_data.get('name', 'Unknown')}': {e}")
            self.stats["total_errors"] += 1
            return False
        finally:
            db.close()
    
    async def run_ingestion(self, limit: Optional[int] = None, dry_run: bool = False):
        """Run the complete ingestion process"""
        
        self.logger.info(f"🚀 Starting {self.source_name} ingestion...")
        self.stats["start_time"] = datetime.now()
        
        try:
            # Fetch raw recipes
            self.logger.info("📥 Fetching recipes from API...")
            raw_recipes = await self.fetch_recipes(limit)
            self.stats["total_fetched"] = len(raw_recipes)
            self.logger.info(f"📊 Fetched {len(raw_recipes)} recipes")
            
            if not raw_recipes:
                self.logger.warning("No recipes fetched!")
                return
            
            # Process each recipe
            for i, raw_recipe in enumerate(raw_recipes, 1):
                try:
                    self.logger.info(f"🔄 Processing recipe {i}/{len(raw_recipes)}: {raw_recipe.get('name', 'Unknown')}")
                    
                    # Normalize the recipe
                    normalized_recipe = self.normalize_recipe(raw_recipe)
                    self.stats["total_processed"] += 1
                    
                    if dry_run:
                        self.logger.info(f"🔍 [DRY RUN] Would save: {normalized_recipe['name']}")
                        continue
                    
                    # Save to database
                    self.save_recipe(normalized_recipe)
                    
                except Exception as e:
                    self.logger.error(f"❌ Error processing recipe {i}: {e}")
                    self.stats["total_errors"] += 1
                    continue
            
        except Exception as e:
            self.logger.error(f"💥 Fatal error during ingestion: {e}")
            raise
        
        finally:
            self.stats["end_time"] = datetime.now()
            self.print_summary()
    
    def print_summary(self):
        """Print ingestion summary statistics"""
        
        duration = None
        if self.stats["start_time"] and self.stats["end_time"]:
            duration = self.stats["end_time"] - self.stats["start_time"]
        
        print("\n" + "="*50)
        print(f"📊 {self.source_name.upper()} INGESTION SUMMARY")
        print("="*50)
        print(f"📥 Total Fetched:  {self.stats['total_fetched']}")
        print(f"🔄 Total Processed: {self.stats['total_processed']}")
        print(f"✅ Total Saved:    {self.stats['total_saved']}")
        print(f"⏭️  Total Skipped:  {self.stats['total_skipped']}")
        print(f"❌ Total Errors:   {self.stats['total_errors']}")
        
        if duration:
            print(f"⏱️  Duration:       {duration}")
        
        success_rate = (self.stats['total_saved'] / max(self.stats['total_fetched'], 1)) * 100
        print(f"📈 Success Rate:   {success_rate:.1f}%")
        print("="*50)