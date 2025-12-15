"""Generate SQL UPDATE statements for package_type column"""

import json
import os

def generate_sql():
    """Generate SQL UPDATE statements from JSON"""

    json_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'גיליון מוצרים ל-AI ChatBot.json')

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    items = data['גיליון1']

    sql_statements = []

    for item in items:
        name = item.get('שם מוצר')
        package_type = item.get('סוג אריזה / משקל באריזה')

        if not name or not package_type:
            continue

        # Convert to string and append "גרם" for numbers
        if isinstance(package_type, (int, float)):
            package_type = f"{int(package_type)} גרם"
        else:
            package_type = str(package_type)

        # Escape single quotes in SQL
        name_escaped = name.replace("'", "''")
        package_type_escaped = package_type.replace("'", "''")

        # Generate UPDATE statement
        sql = f"UPDATE menu_items SET package_type = '{package_type_escaped}' WHERE name = '{name_escaped}';"
        sql_statements.append(sql)

    # Write to file
    output_path = os.path.join(os.path.dirname(__file__), 'update_package_type.sql')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("-- SQL statements to update package_type column\n")
        f.write("-- Run this in Supabase SQL Editor\n\n")
        f.write('\n'.join(sql_statements))

    print(f"Generated {len(sql_statements)} SQL statements")
    print(f"Saved to: {output_path}")

    # Also print first 10 for verification
    print("\nFirst 10 statements:")
    for sql in sql_statements[:10]:
        print(sql)

if __name__ == "__main__":
    generate_sql()
