"""
Data Ingestion Package for Meal Planning Platform

This package contains all recipe data ingestion modules for fetching
and normalizing recipe data from various external sources.

Available ingesters:
- TheMealDBIngester: Free recipe data from TheMealDB API
- (Future) SpoonacularIngester: Premium recipe data from Spoonacular API
- (Future) CustomIngester: For manual recipe data
"""

from .base_ingester import BaseIngester
from .themealdb_ingester import TheMealDBIngester, run_themealdb_ingestion

__all__ = [
    "BaseIngester",
    "TheMealDBIngester", 
    "run_themealdb_ingestion"
]

__version__ = "0.1.0"