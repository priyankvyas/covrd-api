"""
Meal Planner API - Main FastAPI Application

This is the main entry point for the Meal Planning Platform API.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional

# Import our database and models
from app.core.database import get_db, create_tables
from app.models import Recipe

# Create tables on startup (for development)
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database tables on app startup"""
    create_tables()
    yield    

# Create FastAPI app
app = FastAPI(
    title="Meal Planner API",
    description="AI-Enhanced Meal Planning Platform with smart dietary restriction handling",
    version="0.1.0",
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc",  # ReDoc
    lifespan=lifespan
)

# Add CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/")
async def root():
    """Root endpoint for health checks"""
    return {
        "message": "Meal Planner API is running!",
        "version": "0.1.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "meal-planner-api"}

# Dietary restriction endpoint (showcasing your core innovation)
@app.get("/recipes/dietary/{restrictions}")
async def get_recipes_by_dietary_restrictions(
    restrictions: str,
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """
    Get recipes that meet specific dietary restrictions
    
    This demonstrates your symbolic constraint system ensuring 100% compliance.
    
    Usage: /recipes/dietary/vegetarian,gluten_free
    Available restrictions: vegetarian, vegan, gluten_free, dairy_free, nut_free, low_carb, keto, paleo
    """
    
    # Parse restrictions
    restriction_list = [r.strip() for r in restrictions.split(",")]
    
    # Validate restrictions
    valid_restrictions = {
        "vegetarian", "vegan", "gluten_free", "dairy_free", 
        "nut_free", "low_carb", "keto", "paleo"
    }
    
    invalid_restrictions = set(restriction_list) - valid_restrictions
    if invalid_restrictions:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid restrictions: {list(invalid_restrictions)}. Valid options: {list(valid_restrictions)}"
        )
    
    # Build query with symbolic constraints
    query = db.query(Recipe)
    
    for restriction in restriction_list:
        if restriction == "vegetarian":
            query = query.filter(Recipe.is_vegetarian == True)
        elif restriction == "vegan":
            query = query.filter(Recipe.is_vegan == True)
        elif restriction == "gluten_free":
            query = query.filter(Recipe.is_gluten_free == True)
        elif restriction == "dairy_free":
            query = query.filter(Recipe.is_dairy_free == True)
        elif restriction == "nut_free":
            query = query.filter(Recipe.is_nut_free == True)
        elif restriction == "low_carb":
            query = query.filter(Recipe.is_low_carb == True)
        elif restriction == "keto":
            query = query.filter(Recipe.is_keto == True)
        elif restriction == "paleo":
            query = query.filter(Recipe.is_paleo == True)
    
    recipes = query.limit(limit).all()
    
    return {
        "requested_restrictions": restriction_list,
        "found_recipes": len(recipes),
        "recipes": [
            {
                "id": recipe.id,
                "name": recipe.name,
                "cuisine_type": recipe.cuisine_type,
                "meal_type": recipe.meal_type,
                "dietary_flags": recipe.dietary_flags,
                "meets_requirements": recipe.meets_dietary_restrictions(restriction_list)
            }
            for recipe in recipes
        ]
    }

@app.get("/recipes/search")
async def search_recipes(
    q: str = Query(..., description="Search query for recipe names and descriptions"),
    db: Session = Depends(get_db)
):
    """Search recipes by name or description"""
    
    recipes = db.query(Recipe).filter(
        Recipe.name.ilike(f"%{q}%") | Recipe.description.ilike(f"%{q}%")
    ).limit(20).all()
    
    return [
        {
            "id": recipe.id,
            "name": recipe.name,
            "description": recipe.description,
            "cuisine_type": recipe.cuisine_type,
            "dietary_flags": recipe.dietary_flags,
            "prep_time_minutes": recipe.prep_time_minutes,
            "difficulty": recipe.difficulty
        }
        for recipe in recipes
    ]

# Recipe endpoints
@app.get("/recipes", response_model=List[dict])
async def get_recipes(
    skip: int = Query(0, ge=0, description="Number of recipes to skip"),
    limit: int = Query(10, ge=1, le=100, description="Number of recipes to return"),
    cuisine: Optional[str] = Query(None, description="Filter by cuisine type"),
    meal_type: Optional[str] = Query(None, description="Filter by meal type"),
    vegetarian: Optional[bool] = Query(None, description="Filter vegetarian recipes"),
    vegan: Optional[bool] = Query(None, description="Filter vegan recipes"),
    gluten_free: Optional[bool] = Query(None, description="Filter gluten-free recipes"),
    db: Session = Depends(get_db)
):
    """
    Get recipes with optional filtering
    
    This endpoint demonstrates your core innovation of reliable dietary restriction filtering.
    """
    
    # Start with base query
    query = db.query(Recipe)
    
    # Apply filters
    if cuisine:
        query = query.filter(Recipe.cuisine_type.ilike(f"%{cuisine}%"))
    
    if meal_type:
        query = query.filter(Recipe.meal_type.ilike(f"%{meal_type}%"))
    
    # Dietary restriction filters (your symbolic constraint system)
    if vegetarian is True:
        query = query.filter(Recipe.is_vegetarian == True)
    
    if vegan is True:
        query = query.filter(Recipe.is_vegan == True)
    
    if gluten_free is True:
        query = query.filter(Recipe.is_gluten_free == True)
    
    # Execute query with pagination
    recipes = query.offset(skip).limit(limit).all()
    
    # Convert to dictionaries for response
    return [
        {
            "id": recipe.id,
            "name": recipe.name,
            "description": recipe.description,
            "prep_time_minutes": recipe.prep_time_minutes,
            "cook_time_minutes": recipe.cook_time_minutes,
            "total_time_minutes": recipe.total_time_minutes,
            "servings": recipe.servings,
            "difficulty": recipe.difficulty,
            "cuisine_type": recipe.cuisine_type,
            "meal_type": recipe.meal_type,
            "course_type": recipe.course_type,
            "dietary_flags": recipe.dietary_flags,
            "calories_per_serving": recipe.calories_per_serving,
            "image_url": recipe.image_url,
            "tags": recipe.tags,
            "created_at": recipe.created_at
        }
        for recipe in recipes
    ]

@app.get("/recipes/{recipe_id}")
async def get_recipe(recipe_id: int, db: Session = Depends(get_db)):
    """Get a specific recipe by ID with full details"""
    
    recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
    
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    return {
        "id": recipe.id,
        "name": recipe.name,
        "description": recipe.description,
        "instructions": recipe.instructions,
        "prep_time_minutes": recipe.prep_time_minutes,
        "cook_time_minutes": recipe.cook_time_minutes,
        "total_time_minutes": recipe.total_time_minutes,
        "servings": recipe.servings,
        "difficulty": recipe.difficulty,
        "cuisine_type": recipe.cuisine_type,
        "meal_type": recipe.meal_type,
        "course_type": recipe.course_type,
        "dietary_flags": recipe.dietary_flags,
        "ingredients": recipe.ingredients_json,
        "equipment_needed": recipe.equipment_needed,
        "calories_per_serving": recipe.calories_per_serving,
        "protein_grams": recipe.protein_grams,
        "carbs_grams": recipe.carbs_grams,
        "fat_grams": recipe.fat_grams,
        "image_url": recipe.image_url,
        "video_url": recipe.video_url,
        "source_url": recipe.source_url,
        "tags": recipe.tags,
        "popularity_score": recipe.popularity_score,
        "external_source": recipe.external_source,
        "created_at": recipe.created_at,
        "updated_at": recipe.updated_at
    }

@app.get("/stats")
async def get_stats(db: Session = Depends(get_db)):
    """Get database statistics"""
    
    total_recipes = db.query(Recipe).count()
    
    # Count by cuisine
    cuisines = db.query(Recipe.cuisine_type).distinct().all()
    cuisine_counts = {}
    for (cuisine,) in cuisines:
        if cuisine:
            count = db.query(Recipe).filter(Recipe.cuisine_type == cuisine).count()
            cuisine_counts[cuisine] = count
    
    # Count dietary restrictions
    vegetarian_count = db.query(Recipe).filter(Recipe.is_vegetarian == True).count()
    vegan_count = db.query(Recipe).filter(Recipe.is_vegan == True).count()
    gluten_free_count = db.query(Recipe).filter(Recipe.is_gluten_free == True).count()
    
    return {
        "total_recipes": total_recipes,
        "cuisines": cuisine_counts,
        "dietary_stats": {
            "vegetarian": vegetarian_count,
            "vegan": vegan_count,
            "gluten_free": gluten_free_count
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)