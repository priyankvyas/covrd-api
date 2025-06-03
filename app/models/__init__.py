"""
Models package for the Meal Planning Platform

This package contains all SQLAlchemy models for the application.
Import models here to ensure they're registered with SQLAlchemy Base.
"""

from .recipe import Recipe

# Make models available at package level
__all__ = [
    "Recipe",
]

# This ensures all models are imported when the package is imported
# which is required for SQLAlchemy to create the tables properly