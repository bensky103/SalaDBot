"""Update package_type column from JSON source"""

import json
import sys
import os
import io

# Fix encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.ai_core import supabase

def update_package_types():
    """Read JSON and update package_type in database"""

    # Load JSON data
    json_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'גיליון מוצרים ל-AI ChatBot.json')

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    items = data['גיליון1']

    update_count = 0
    skip_count = 0

    for item in items:
        name = item.get('שם מוצר')
        package_type = item.get('סוג אריזה / משקל באריזה')

        if not name:
            continue

        # Convert package_type to string and append "גרם" for numbers
        if package_type is not None:
            if isinstance(package_type, (int, float)):
                package_type = f"{int(package_type)} גרם"
            else:
                package_type = str(package_type)

        # Skip if no package_type data
        if not package_type:
            skip_count += 1
            continue

        # Find matching item in DB and update
        try:
            # Query by exact name match
            result = supabase.table('menu_items')\
                .select('id,name,package_type')\
                .eq('name', name)\
                .execute()

            if result.data:
                for db_item in result.data:
                    # Update package_type
                    supabase.table('menu_items')\
                        .update({'package_type': package_type})\
                        .eq('id', db_item['id'])\
                        .execute()

                    print(f"✓ Updated: {name} → {package_type}")
                    update_count += 1
            else:
                print(f"⚠ Not found in DB: {name}")

        except Exception as e:
            print(f"✗ Error updating {name}: {e}")

    print(f"\n{'='*60}")
    print(f"Summary:")
    print(f"  Updated: {update_count}")
    print(f"  Skipped (no package_type): {skip_count}")
    print(f"{'='*60}")

if __name__ == "__main__":
    update_package_types()
