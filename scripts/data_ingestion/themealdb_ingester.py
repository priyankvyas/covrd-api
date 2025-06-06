"""
TheMealDB Recipe Ingester

This module handles fetching and normalizing recipe data from TheMealDB API.
TheMealDB provides free access to recipe data without requiring an API key.
"""

import aiohttp
import asyncio
from typing import Dict, List, Optional, Any
from .base_ingester import BaseIngester


class TheMealDBIngester(BaseIngester):
    """Ingester for TheMealDB API"""
    
    BASE_URL = "https://www.themealdb.com/api/json/v1/1"
    
    def __init__(self):
        super().__init__("themealdb")
        self.session = None
    
    async def _get_session(self):
        """Get or create aiohttp session"""
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def _close_session(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def _fetch_json(self, url: str) -> Dict[str, Any]:
        """Fetch JSON data from URL with error handling"""
        session = await self._get_session()
        
        try:
            async with session.get(url) as response:
                response.raise_for_status()
                data = await response.json()
                return data
        except Exception as e:
            self.logger.error(f"Error fetching {url}: {e}")
            raise
    
    async def fetch_recipes_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Fetch all recipes from a specific category"""
        
        # First, get all meal IDs in the category
        category_url = f"{self.BASE_URL}/filter.php?c={category}"
        self.logger.info(f"Fetching meals in category: {category}")
        
        try:
            category_data = await self._fetch_json(category_url)
            meals = category_data.get("meals", [])
            
            if not meals:
                self.logger.warning(f"No meals found in category: {category}")
                return []
            
            self.logger.info(f"Found {len(meals)} meals in category {category}")
            
            # Fetch detailed recipe for each meal
            detailed_recipes = []
            for meal in meals:
                meal_id = meal["idMeal"]
                detail_url = f"{self.BASE_URL}/lookup.php?i={meal_id}"
                
                try:
                    detail_data = await self._fetch_json(detail_url)
                    meal_details = detail_data.get("meals", [])
                    
                    if meal_details:
                        detailed_recipes.append(meal_details[0])
                        self.logger.debug(f"Fetched details for: {meal_details[0]['strMeal']}")
                    
                    # Add small delay to be respectful to the API
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    self.logger.error(f"Error fetching meal details for ID {meal_id}: {e}")
                    continue
            
            return detailed_recipes
            
        except Exception as e:
            self.logger.error(f"Error fetching category {category}: {e}")
            return []
    
    async def fetch_random_recipes(self, count: int) -> List[Dict[str, Any]]:
        """Fetch random recipes from TheMealDB"""
        
        recipes = []
        self.logger.info(f"Fetching {count} random recipes...")
        
        for i in range(count):
            try:
                random_url = f"{self.BASE_URL}/random.php"
                data = await self._fetch_json(random_url)
                meals = data.get("meals", [])
                
                if meals:
                    recipes.append(meals[0])
                    self.logger.debug(f"Fetched random recipe {i+1}/{count}: {meals[0]['strMeal']}")
                
                # Small delay to be respectful
                await asyncio.sleep(0.1)
                
            except Exception as e:
                self.logger.error(f"Error fetching random recipe {i+1}: {e}")
                continue
        
        return recipes
    
    async def fetch_recipes(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Fetch recipes from TheMealDB using multiple strategies"""
        
        all_recipes = []
        
        try:
            # Strategy 1: Fetch popular categories
            categories = [
                "Chicken", "Beef", "Pork", "Seafood", "Vegetarian", 
                "Pasta", "Side", "Dessert", "Breakfast"
            ]
            
            for category in categories:
                if limit and len(all_recipes) >= limit:
                    break
                
                category_recipes = await self.fetch_recipes_by_category(category)
                all_recipes.extend(category_recipes)
                
                self.logger.info(f"Total recipes so far: {len(all_recipes)}")
            
            # Strategy 2: If we need more recipes, get random ones
            if limit and len(all_recipes) < limit:
                remaining = limit - len(all_recipes)
                random_recipes = await self.fetch_random_recipes(min(remaining, 50))
                all_recipes.extend(random_recipes)
            
            # Remove duplicates based on meal ID
            seen_ids = set()
            unique_recipes = []
            for recipe in all_recipes:
                meal_id = recipe.get("idMeal")
                if meal_id not in seen_ids:
                    seen_ids.add(meal_id)
                    unique_recipes.append(recipe)
            
            # Apply limit if specified
            if limit:
                unique_recipes = unique_recipes[:limit]
            
            self.logger.info(f"Returning {len(unique_recipes)} unique recipes")
            return unique_recipes
            
        finally:
            await self._close_session()
    
    def _extract_ingredients(self, raw_recipe: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract ingredients from TheMealDB format"""
        
        ingredients = []
        
        # TheMealDB stores ingredients as strIngredient1, strIngredient2, etc.
        for i in range(1, 21):  # They go up to 20
            ingredient_key = f"strIngredient{i}"
            measure_key = f"strMeasure{i}"
            
            ingredient_name = raw_recipe.get(ingredient_key, "").strip()
            ingredient_measure = raw_recipe.get(measure_key, "").strip()
            
            if ingredient_name:  # Only add if ingredient name exists
                ingredients.append({
                    "name": ingredient_name,
                    "amount": ingredient_measure or "to taste"
                })
        
        return ingredients
    
    def _clean_instructions(self, instructions: str) -> str:
        """Clean and format instructions text"""
        if not instructions:
            return ""
        
        # Replace \\r\\n with actual line breaks
        instructions = instructions.replace("\\r\\n", "\n")
        instructions = instructions.replace("\\n", "\n")
        
        # Split into steps and clean
        steps = [step.strip() for step in instructions.split("\n") if step.strip()]
        
        # Number the steps if they aren't already
        numbered_steps = []
        for i, step in enumerate(steps, 1):
            if not step.startswith(str(i)):
                step = f"{i}. {step}"
            numbered_steps.append(step)
        
        return "\n".join(numbered_steps)
    
    def _determine_meal_type(self, category: str, tags: str = "") -> str:
        """Determine meal type from category and tags"""
        
        category = category.lower() if category else ""
        tags = tags.lower() if tags else ""
        
        if any(word in category for word in ["breakfast", "brunch"]):
            return "breakfast"
        elif any(word in category for word in ["lunch", "light"]):
            return "lunch"
        elif any(word in category for word in ["dinner", "main"]):
            return "dinner"
        elif any(word in category for word in ["dessert", "sweet"]):
            return "dessert"
        elif any(word in category for word in ["side", "appetizer", "starter"]):
            return "appetizer"
        elif any(word in tags for word in ["breakfast", "morning"]):
            return "breakfast"
        elif any(word in tags for word in ["dessert", "sweet", "cake"]):
            return "dessert"
        else:
            return "dinner"  # Default to dinner
    
    def normalize_recipe(self, raw_recipe: Dict[str, Any]) -> Dict[str, Any]:
        """Convert TheMealDB recipe to our Recipe model format"""
        
        # Extract basic information
        name = raw_recipe.get("strMeal", "Unknown Recipe")
        instructions = self._clean_instructions(raw_recipe.get("strInstructions", ""))
        ingredients = self._extract_ingredients(raw_recipe)
        
        # Extract categorization
        category = raw_recipe.get("strCategory", "")
        cuisine = raw_recipe.get("strArea", "")
        tags = raw_recipe.get("strTags", "")
        meal_type = self._determine_meal_type(category, tags)
        
        # Process tags
        tag_list = []
        if tags:
            tag_list = [tag.strip().lower() for tag in tags.split(",") if tag.strip()]
        if category:
            tag_list.append(category.lower())
        
        # Detect dietary restrictions using our base method
        dietary_flags = self.detect_dietary_restrictions(ingredients)
        
        # Estimate times and difficulty
        time_estimates = self.estimate_cooking_times(instructions, len(ingredients))
        difficulty = self.estimate_difficulty(instructions, len(ingredients))
        
        # Create normalized recipe data
        normalized = {
            # Basic info
            "name": name,
            "description": f"A delicious {cuisine} {category.lower()} recipe" if cuisine and category else None,
            "instructions": instructions,
            
            # Timing
            "prep_time_minutes": time_estimates["prep_time_minutes"],
            "cook_time_minutes": time_estimates["cook_time_minutes"],
            "total_time_minutes": time_estimates["total_time_minutes"],
            "servings": 4,  # TheMealDB doesn't provide this, use default
            "difficulty": difficulty,
            
            # Categorization
            "cuisine_type": cuisine or None,
            "meal_type": meal_type,
            "course_type": "main" if meal_type in ["breakfast", "lunch", "dinner"] else meal_type,
            
            # Dietary flags (your core innovation!)
            **dietary_flags,
            
            # Ingredients and metadata
            "ingredients_json": ingredients,
            "tags": tag_list,
            
            # External source tracking
            "external_id": raw_recipe.get("idMeal"),
            "external_source": "themealdb",
            "image_url": raw_recipe.get("strMealThumb"),
            "video_url": raw_recipe.get("strYoutube"),
            "source_url": raw_recipe.get("strSource"),
            
            # Initialize AI fields
            "popularity_score": 0.0,
            "complexity_score": float(difficulty) / 5.0,
        }
        
        return normalized


# Convenience function for easy usage
async def run_themealdb_ingestion(limit: int = 100, dry_run: bool = False):
    """Run TheMealDB ingestion with specified parameters"""
    
    ingester = TheMealDBIngester()
    await ingester.run_ingestion(limit=limit, dry_run=dry_run)


if __name__ == "__main__":
    # For testing the ingester directly
    import argparse
    
    parser = argparse.ArgumentParser(description="TheMealDB Recipe Ingester")
    parser.add_argument("--limit", type=int, default=100, help="Maximum number of recipes to fetch")
    parser.add_argument("--dry-run", action="store_true", help="Don't save to database, just test processing")
    
    args = parser.parse_args()
    
    # Run ingestion
    asyncio.run(run_themealdb_ingestion(limit=args.limit, dry_run=args.dry_run))