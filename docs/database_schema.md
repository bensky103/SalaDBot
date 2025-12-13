# Database Schema: `menu_items`

## Columns
- `id` (int, PK)
- `category` (text): **IN HEBREW** e.g., 'בשר', 'עוף', 'דגים', 'סלטים', 'קינוחים', 'מאפים', 'טבעוני'
- `name` (text): **IN HEBREW** - The dish name.
- `description` (text): **IN HEBREW** - Ingredients and info.
- `price_per_100g` (decimal): Price per 100 grams (nullable).
- `price_per_unit` (decimal): Price per unit/item (nullable).
- `package_type` (text): Package size/type info (nullable). Examples: '250 גרם', '1 ליטר', 'פשטידה אישית', 'אינגליש קייק'.
- `allergens_contains` (text): **IN HEBREW** - CSV string of definite allergens (e.g., 'גלוטן, ביצים, סויה').
- `allergens_traces` (text): **IN HEBREW** - CSV string of trace allergens (e.g., 'אגוזים, דגים, שומשום').
- `availability_days` (text): **IN HEBREW** e.g., 'ימים א - ה', 'ימים ד - ו'.
- `is_vegan` (bool)
- `is_gluten_free` (bool)

## CRITICAL: Hebrew Data
**ALL text values in the database are stored in HEBREW:**
- Categories: `בשר`, `עוף`, `דגים`, `סלטי דגים`, `דג מעושן`, `גבינות`, `ממרחים`, `מאפים`, `פשטידות`, `מרקים`, `טוגנים`, `חמוצים`, `תוספות`, `קינוחים`, `קרקרים`, `עוגיות`, `טבעוני`, `סלטים`, `ספיישל שישי`, `ספיישלים שישי`
- Allergens: `גלוטן`, `ביצים`, `אגוזים`, `סויה`, `שומשום`, `חלב`, `סלרי`, `דגים`, `חרדל`
- Availability format: `ימים [Hebrew day letters]` (e.g., `ימים ד - ו` = Wednesday to Friday)

## SQL Notes
- Text search should be case-insensitive (though Hebrew has no case).
- **When filtering by category, allergens, or other text fields, use HEBREW values.**
- We prefer ILIKE or vector search if simple matching fails, but start with deterministic SQL queries.
