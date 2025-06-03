from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Float, JSON
from sqlalchemy.sql import func
from app.core.database import Base


class Recipe(Base):
    __tablename__ = "recipes"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Basic recipe information
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    instructions = Column(Text, nullable=False)
    
    # Timing and serving information
    prep_time_minutes = Column(Integer)
    cook_time_minutes = Column(Integer)
    total_time_minutes = Column(Integer)  # Computed or provided
    servings = Column(Integer, default=4)
    difficulty = Column(Integer, default=1)  # 1-5 scale (1=very easy, 5=expert)
    
    # Categorization
    cuisine_type = Column(String(100), index=True)  # e.g., "Italian", "Mexican"
    meal_type = Column(String(100), index=True)     # e.g., "breakfast", "dinner"
    course_type = Column(String(100))               # e.g., "appetizer", "main", "dessert"
    
    # Dietary restriction flags (your core innovation)
    is_vegetarian = Column(Boolean, default=False, index=True)
    is_vegan = Column(Boolean, default=False, index=True)
    is_gluten_free = Column(Boolean, default=False, index=True)
    is_dairy_free = Column(Boolean, default=False, index=True)
    is_nut_free = Column(Boolean, default=False, index=True)
    is_low_carb = Column(Boolean, default=False, index=True)
    is_keto = Column(Boolean, default=False, index=True)
    is_paleo = Column(Boolean, default=False, index=True)
    
    # Nutritional information (optional, can be populated later)
    calories_per_serving = Column(Integer)
    protein_grams = Column(Float)
    carbs_grams = Column(Float)
    fat_grams = Column(Float)
    fiber_grams = Column(Float)
    sugar_grams = Column(Float)
    sodium_mg = Column(Float)
    
    # External data
    external_id = Column(String(100))      # ID from source API
    external_source = Column(String(50))   # e.g., "themealdb", "spoonacular"
    image_url = Column(String(500))
    video_url = Column(String(500))
    source_url = Column(String(500))       # Original recipe URL
    
    # Ingredients (simplified for now - we'll expand this later)
    ingredients_json = Column(JSON)        # Store ingredients as JSON for now
    
    # Recipe tags and metadata
    tags = Column(JSON)                    # e.g., ["quick", "one-pot", "spicy"]
    equipment_needed = Column(JSON)        # e.g., ["oven", "blender"]
    
    # AI and recommendation fields (for future use)
    popularity_score = Column(Float, default=0.0)  # User rating/popularity
    complexity_score = Column(Float, default=0.0)  # Calculated complexity
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<Recipe(id={self.id}, name='{self.name}', cuisine='{self.cuisine_type}')>"
    
    @property
    def dietary_flags(self):
        """Return a list of dietary restrictions this recipe meets"""
        flags = []
        if self.is_vegetarian:
            flags.append("vegetarian")
        if self.is_vegan:
            flags.append("vegan")
        if self.is_gluten_free:
            flags.append("gluten_free")
        if self.is_dairy_free:
            flags.append("dairy_free")
        if self.is_nut_free:
            flags.append("nut_free")
        if self.is_low_carb:
            flags.append("low_carb")
        if self.is_keto:
            flags.append("keto")
        if self.is_paleo:
            flags.append("paleo")
        return flags
    
    def meets_dietary_restrictions(self, required_restrictions):
        """Check if recipe meets all required dietary restrictions"""
        recipe_flags = set(self.dietary_flags)
        required_flags = set(required_restrictions)
        return required_flags.issubset(recipe_flags)