"""
Database setup script for SaladBot POC.
Creates the menu_items table and seeds it with data from JSON file.
"""

import os
import json
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
JSON_FILE_PATH = "גיליון מוצרים ל-AI ChatBot.json"


def get_supabase_client() -> Client:
    """Initialize and return Supabase client."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in .env file")

    return create_client(SUPABASE_URL, SUPABASE_KEY)


def create_menu_items_table(supabase: Client):
    """
    Create the menu_items table.

    Note: This uses Supabase's SQL editor or should be run via Supabase dashboard.
    The Python client doesn't directly create tables, so this SQL should be executed
    in the Supabase SQL Editor.
    """
    sql = """
    CREATE TABLE IF NOT EXISTS menu_items (
        id SERIAL PRIMARY KEY,
        category TEXT NOT NULL,
        name TEXT NOT NULL,
        description TEXT,
        price_per_100g DECIMAL(10, 2),
        price_per_unit DECIMAL(10, 2),
        package_type TEXT,
        allergens_contains TEXT,
        allergens_traces TEXT,
        availability_days TEXT,
        is_vegan BOOLEAN DEFAULT FALSE,
        is_gluten_free BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );

    -- Create index for text search
    CREATE INDEX IF NOT EXISTS idx_menu_items_name ON menu_items(name);
    CREATE INDEX IF NOT EXISTS idx_menu_items_category ON menu_items(category);
    """

    print("=" * 60)
    print("TABLE CREATION SQL")
    print("=" * 60)
    print("Please run the following SQL in your Supabase SQL Editor:")
    print()
    print(sql)
    print()
    print("=" * 60)

    return sql


def parse_allergens(allergen_text):
    """Parse allergen text and extract clean allergen list."""
    if not allergen_text or allergen_text.strip() == "":
        return None

    # Remove prefix text like "מידע על אלרגנים: מכיל:"
    if "מכיל:" in allergen_text:
        allergen_text = allergen_text.split("מכיל:")[-1]

    # Clean and return
    cleaned = allergen_text.strip()
    return cleaned if cleaned else None


def parse_traces(traces_text):
    """Parse traces text and extract clean allergen traces list."""
    if not traces_text or traces_text.strip() == "":
        return None

    # Remove prefix text
    if "עלול להכיל" in traces_text:
        # Extract just the allergens part
        allergen_text = traces_text.replace("מיוצר בסביבה שאינה סטרילית מאלרגנים ועלול להכיל עקבות של", "")
        allergen_text = allergen_text.strip()
        return allergen_text if allergen_text else None

    return traces_text.strip() if traces_text.strip() else None


def determine_vegan(ingredients, allergens_contains):
    """Determine if item is vegan based on ingredients and allergens."""
    # Common non-vegan indicators in Hebrew
    non_vegan_keywords = ["בשר", "ביצ", "חלב", "דבש", "דגים", "עוף", "בקר"]

    text_to_check = f"{ingredients} {allergens_contains or ''}".lower()

    for keyword in non_vegan_keywords:
        if keyword in text_to_check:
            return False

    return True


def determine_gluten_free(allergens_contains):
    """Determine if item is gluten-free."""
    if not allergens_contains:
        return True

    gluten_keywords = ["גלוטן", "gluten", "קמח", "לחם", "פסטה"]
    allergens_lower = allergens_contains.lower()

    for keyword in gluten_keywords:
        if keyword in allergens_lower:
            return False

    return True


def load_menu_from_json(json_path):
    """Load menu items from JSON file and convert to database format."""
    print(f"📂 Loading menu data from {json_path}...")

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # The JSON has a key "גיליון1" containing the array
    raw_items = data.get("גיליון1", [])

    menu_items = []
    for item in raw_items:
        # Parse allergens
        allergens_contains = parse_allergens(item.get("אלרגנים", ""))
        allergens_traces = parse_traces(item.get("עלול להכיל", ""))

        # Determine dietary flags
        ingredients = item.get("רכיבים", "")
        is_vegan = determine_vegan(ingredients, allergens_contains)
        is_gluten_free = determine_gluten_free(allergens_contains)

        # Handle both pricing models
        price_per_100g = item.get("מחיר ל-100 גרם")
        price_per_unit = item.get("מחיר ליחידה")
        package_type = item.get("סוג אריזה / משקל באריזה", "")

        # Convert to float or None
        price_per_100g = float(price_per_100g) if price_per_100g else None
        price_per_unit = float(price_per_unit) if price_per_unit else None

        # Handle package_type (could be string, int, or None)
        if package_type:
            package_type = str(package_type).strip()
        else:
            package_type = None

        menu_item = {
            "category": item.get("קטגוריה", "").strip(),
            "name": item.get("שם מוצר", "").strip(),
            "description": ingredients.strip(),
            "price_per_100g": price_per_100g,
            "price_per_unit": price_per_unit,
            "package_type": package_type if package_type else None,
            "allergens_contains": allergens_contains,
            "allergens_traces": allergens_traces,
            "availability_days": item.get("זמינות במהלך השבוע", "").strip(),
            "is_vegan": is_vegan,
            "is_gluten_free": is_gluten_free
        }

        menu_items.append(menu_item)

    print(f"✅ Loaded {len(menu_items)} items from JSON")
    return menu_items


def seed_menu_items(supabase: Client):
    """
    Seed the database with menu items from JSON file.
    """
    try:
        # Load items from JSON
        menu_items = load_menu_from_json(JSON_FILE_PATH)

        if not menu_items:
            print("⚠️  No items found in JSON file")
            return

        # Insert in batches of 100 to avoid timeout
        batch_size = 100
        total_inserted = 0

        print(f"\n📥 Inserting {len(menu_items)} items into database...")

        for i in range(0, len(menu_items), batch_size):
            batch = menu_items[i:i + batch_size]
            response = supabase.table("menu_items").insert(batch).execute()
            total_inserted += len(batch)
            print(f"   Inserted batch {i//batch_size + 1}: {total_inserted}/{len(menu_items)} items")

        print(f"\n✅ Successfully seeded database with {total_inserted} menu items!")

        # Show sample items
        print("\n📊 Sample items:")
        for idx, item in enumerate(menu_items[:5], 1):
            print(f"{idx}. {item['name']} ({item['category']})")
            if item['price_per_100g']:
                print(f"   Price: {item['price_per_100g']} ₪ ל-100 גרם")
            if item['price_per_unit']:
                print(f"   Price: {item['price_per_unit']} ₪ ליחידה")
            if item['package_type']:
                print(f"   Package: {item['package_type']}")
            print(f"   Vegan: {item['is_vegan']}, Gluten-Free: {item['is_gluten_free']}")
            if item['allergens_contains']:
                print(f"   Contains: {item['allergens_contains']}")
            if item['allergens_traces']:
                print(f"   May contain traces: {item['allergens_traces']}")
            print()

        if len(menu_items) > 5:
            print(f"... and {len(menu_items) - 5} more items")

        return total_inserted

    except FileNotFoundError:
        print(f"❌ Error: JSON file not found at {JSON_FILE_PATH}")
        print("   Make sure the file is in the root directory of the project")
        raise
    except Exception as e:
        print(f"❌ Error seeding database: {e}")
        raise


def main():
    """Main execution function."""
    print("🚀 SaladBot Database Setup")
    print()

    # Initialize Supabase client
    try:
        supabase = get_supabase_client()
        print("✅ Connected to Supabase")
        print()
    except ValueError as e:
        print(f"❌ {e}")
        return

    # Display table creation SQL
    create_menu_items_table(supabase)

    # Ask user if they want to proceed with seeding
    print()
    response = input("Have you created the table? Proceed with seeding data? (y/n): ")

    if response.lower() == 'y':
        print()
        seed_menu_items(supabase)
        print("✅ Database setup complete!")
    else:
        print("⏸️  Seeding skipped. Run this script again after creating the table.")


if __name__ == "__main__":
    main()
