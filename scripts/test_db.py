"""Quick test script to verify database data"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

# Get first 5
first_5 = supabase.table('menu_items').select('*').order('id').limit(5).execute()

# Get last 5
last_5 = supabase.table('menu_items').select('*').order('id', desc=True).limit(5).execute()

print('\n=== FIRST 5 ITEMS ===')
for item in first_5.data:
    print(f"{item['id']}. {item['name']} ({item['category']}) - {item['price_per_100g']} ₪")

print('\n=== LAST 5 ITEMS ===')
for item in reversed(last_5.data):
    print(f"{item['id']}. {item['name']} ({item['category']}) - {item['price_per_unit']} ₪")
