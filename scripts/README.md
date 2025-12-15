# Database Setup Instructions

## Prerequisites
1. Create a `.env` file in the root directory (copy from `.env.example`)
2. Fill in your Supabase credentials in `.env`
3. Make sure `גיליון מוצרים ל-AI ChatBot.json` is in the root directory

## Steps to Run

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Create the Database Table
The script will display SQL code. Copy and paste it into your Supabase SQL Editor:

1. Go to your Supabase dashboard
2. Click on "SQL Editor" in the left sidebar
3. Create a new query
4. Paste the SQL code from the script output
5. Click "Run"

### 3. Run the Setup Script
```bash
python scripts/setup_db.py
```

The script will:
1. Display the SQL to create the table (run this in Supabase first)
2. Ask if you're ready to seed the data
3. Load all items from the JSON file
4. Parse allergens and dietary flags automatically
5. Insert items in batches of 100
6. Show you a summary of inserted items

## What the Script Does

- **Parses allergens**: Extracts allergens from Hebrew text
- **Determines vegan status**: Checks ingredients for meat, eggs, dairy, etc.
- **Determines gluten-free status**: Checks allergens for gluten keywords
- **Batch inserts**: Inserts 100 items at a time to avoid timeouts
- **Error handling**: Clear error messages if something goes wrong

## Expected Output
```
🚀 SaladBot Database Setup

✅ Connected to Supabase

[SQL code displayed here - copy to Supabase]

Have you created the table? Proceed with seeding data? (y/n): y

📂 Loading menu data from גיליון מוצרים ל-AI ChatBot.json...
✅ Loaded 150 items from JSON

📥 Inserting 150 items into database...
   Inserted batch 1: 100/150 items
   Inserted batch 2: 150/150 items

✅ Successfully seeded database with 150 menu items!

📊 Sample items:
1. מוסקה חצילים ובשר (בשר)
   Price: 9.0 ₪ ל-100 גרם
   Vegan: False, Gluten-Free: False
   Contains: ביצים, גלוטן, סויה, סלרי
   May contain traces: גלוטן, אגוזים, ביצים, סויה, דגים, שומשום, חרדל וסלרי

... and 145 more items
```

---

## Testing Scripts

### Security Testing

**`test_security.py`** - Comprehensive security test suite

Tests SQL injection and prompt injection protections:
- ✅ SQL injection via parameterized queries (Supabase SDK)
- ✅ Prompt injection detection (21 attack patterns)
- ✅ Input sanitization (length limits, control chars)
- ✅ End-to-end integration tests

**Run:**
```powershell
python scripts/test_security.py
```

**Expected Output:**
```
✅ ALL SECURITY TESTS PASSED
```

See `docs/SECURITY.md` for detailed security documentation.

### Other Tests

- **`test_ai_core.py`** - AI core functionality tests
- **`test_agent.py`** - Agent behavior tests
- **`test_db.py`** - Database connection tests
- **`test_dish_repetition.py`** - Dish repetition prevention tests
- **`test_context_awareness.py`** - Context handling tests
