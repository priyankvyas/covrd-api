#!/usr/bin/env python3
"""
Recipe Data Ingestion Script

This script orchestrates the ingestion of recipe data from various external sources
into the Meal Planning Platform database. It supports multiple data sources and
provides options for testing, limiting, and monitoring the ingestion process.

Usage Examples:
    python scripts/run_ingestion.py                           # Default: 100 recipes from TheMealDB
    python scripts/run_ingestion.py --source themealdb --limit 50    # 50 recipes from TheMealDB
    python scripts/run_ingestion.py --dry-run --limit 10      # Test with 10 recipes (no DB save)
    python scripts/run_ingestion.py --all-sources             # Run all available sources
"""

import sys
import os
import asyncio
import argparse
from datetime import datetime

# Add the parent directory to Python path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_ingestion import TheMealDBIngester


AVAILABLE_SOURCES = {
    "themealdb": {
        "class": TheMealDBIngester,
        "description": "Free recipe database with 1000+ recipes",
        "api_key_required": False,
        "default_limit": 100
    },
    # Future sources can be added here
    # "spoonacular": {
    #     "class": SpoonacularIngester,
    #     "description": "Premium recipe API with nutrition data",
    #     "api_key_required": True,
    #     "default_limit": 50
    # }
}


def print_banner():
    """Print a nice banner for the ingestion script"""
    print("\n" + "="*60)
    print("🍳 MEAL PLANNER RECIPE INGESTION SYSTEM")
    print("="*60)
    print("AI-Enhanced Meal Planning Platform - Data Pipeline")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)


def print_available_sources():
    """Print information about available data sources"""
    print("\n📊 AVAILABLE DATA SOURCES:")
    print("-" * 40)
    
    for source_name, info in AVAILABLE_SOURCES.items():
        status = "✅ Ready" if not info["api_key_required"] else "🔑 API Key Required"
        print(f"• {source_name.upper()}")
        print(f"  Description: {info['description']}")
        print(f"  Status: {status}")
        print(f"  Default Limit: {info['default_limit']} recipes")
        print()


async def run_source_ingestion(source_name: str, limit: int, dry_run: bool = False):
    """Run ingestion for a specific source"""
    
    if source_name not in AVAILABLE_SOURCES:
        raise ValueError(f"Unknown source: {source_name}")
    
    source_info = AVAILABLE_SOURCES[source_name]
    ingester_class = source_info["class"]
    
    print(f"\n🚀 Starting {source_name.upper()} ingestion...")
    print(f"   Target: {limit} recipes")
    print(f"   Mode: {'DRY RUN (no database saves)' if dry_run else 'LIVE (saving to database)'}")
    
    # Create and run ingester
    ingester = ingester_class()
    await ingester.run_ingestion(limit=limit, dry_run=dry_run)
    
    return ingester.stats


async def run_all_sources(limit_per_source: int, dry_run: bool = False):
    """Run ingestion for all available sources"""
    
    print(f"\n🌟 Running ingestion for ALL sources...")
    print(f"   Limit per source: {limit_per_source} recipes")
    
    total_stats = {
        "total_fetched": 0,
        "total_saved": 0,
        "total_errors": 0,
        "sources_completed": 0
    }
    
    for source_name in AVAILABLE_SOURCES.keys():
        try:
            print(f"\n{'='*20} {source_name.upper()} {'='*20}")
            stats = await run_source_ingestion(source_name, limit_per_source, dry_run)
            
            # Aggregate stats
            total_stats["total_fetched"] += stats["total_fetched"]
            total_stats["total_saved"] += stats["total_saved"]
            total_stats["total_errors"] += stats["total_errors"]
            total_stats["sources_completed"] += 1
            
        except Exception as e:
            print(f"❌ Error with source {source_name}: {e}")
            total_stats["total_errors"] += 1
    
    # Print overall summary
    print("\n" + "="*60)
    print("🎯 OVERALL INGESTION SUMMARY")
    print("="*60)
    print(f"Sources Completed: {total_stats['sources_completed']}/{len(AVAILABLE_SOURCES)}")
    print(f"Total Recipes Fetched: {total_stats['total_fetched']}")
    print(f"Total Recipes Saved: {total_stats['total_saved']}")
    print(f"Total Errors: {total_stats['total_errors']}")
    
    if total_stats["total_fetched"] > 0:
        success_rate = (total_stats["total_saved"] / total_stats["total_fetched"]) * 100
        print(f"Overall Success Rate: {success_rate:.1f}%")
    
    print("="*60)


def validate_database_connection():
    """Check if database is accessible before starting ingestion"""
    try:
        from app.core.database import get_db_session
        from app.models import Recipe
        
        db = get_db_session()
        # Try a simple query
        count = db.query(Recipe).count()
        db.close()
        
        print(f"✅ Database connection verified ({count} existing recipes)")
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("   Make sure to run 'python scripts/init_db.py' first!")
        return False


async def main():
    """Main function to handle command line arguments and orchestrate ingestion"""
    
    parser = argparse.ArgumentParser(
        description="Recipe Data Ingestion for Meal Planning Platform",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                    # 100 recipes from TheMealDB
  %(prog)s --source themealdb --limit 50     # 50 recipes from TheMealDB  
  %(prog)s --dry-run --limit 10              # Test with 10 recipes
  %(prog)s --all-sources --limit 25          # 25 recipes from each source
  %(prog)s --list-sources                    # Show available sources
        """
    )
    
    # Add arguments
    parser.add_argument(
        "--source", 
        choices=list(AVAILABLE_SOURCES.keys()),
        default="themealdb",
        help="Data source to use for ingestion"
    )
    
    parser.add_argument(
        "--limit", 
        type=int, 
        help="Maximum number of recipes to fetch (default varies by source)"
    )
    
    parser.add_argument(
        "--dry-run", 
        action="store_true", 
        help="Test ingestion without saving to database"
    )
    
    parser.add_argument(
        "--all-sources", 
        action="store_true", 
        help="Run ingestion for all available sources"
    )
    
    parser.add_argument(
        "--list-sources", 
        action="store_true", 
        help="List all available data sources and exit"
    )
    
    args = parser.parse_args()
    
    # Print banner
    print_banner()
    
    # Handle list sources
    if args.list_sources:
        print_available_sources()
        return
    
    # Validate database connection (unless dry run)
    if not args.dry_run:
        if not validate_database_connection():
            sys.exit(1)
    
    # Determine limit
    if args.limit is None:
        if args.all_sources:
            limit = 50  # Conservative limit when running all sources
        else:
            limit = AVAILABLE_SOURCES[args.source]["default_limit"]
    else:
        limit = args.limit
    
    try:
        # Run ingestion
        if args.all_sources:
            await run_all_sources(limit, args.dry_run)
        else:
            await run_source_ingestion(args.source, limit, args.dry_run)
        
        # Final message
        print(f"\n🎉 Ingestion completed successfully!")
        if not args.dry_run:
            print("💡 Next steps:")
            print("   • Start your API: uvicorn app.main:app --reload")
            print("   • Check your recipes: http://localhost:8000/recipes")
            print("   • View stats: http://localhost:8000/stats")

    except Exception as e:
        print(f"\n💥 Ingestion failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Run the main function
    asyncio.run(main())