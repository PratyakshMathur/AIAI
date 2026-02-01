# 🚀 Problem Setup Guide

Complete guide to adding interview problems and datasets to the system.

## Prerequisites

Make sure you have:
- Backend dependencies installed (`pip install -r backend/requirements.txt`)
- Database initialized (see Step 1)

---

## Step 1: Initialize the Problems Database

**Run this ONCE** before adding any problems:

```bash
cd /Users/pratyaksh/UTA/AI_Interview_v1
python backend/problem_manager/init_db.py
```

**Expected Output:**
```
✅ Created problems database: backend/problems.db
   - problems table
   - problem_tables table
   - table_data table
```

---

## Step 2: Create Your First Problem

### Basic Command:
```bash
python backend/problem_manager/manage_problems.py add-problem \
  --title "Your Problem Title" \
  --description "Your problem description (supports Markdown)" \
  --difficulty medium
```

### Example - E-Commerce Analysis:
```bash
python backend/problem_manager/manage_problems.py add-problem \
  --title "E-Commerce Sales Analysis" \
  --description "# Sales Analysis

Analyze Q4 2025 sales data for our e-commerce platform.

## Tasks:
1. Find total revenue by customer
2. Identify top 5 customers by order count
3. Calculate average order value

## Available Tables:
- \`customers\`: Customer information
- \`orders\`: Order transactions" \
  --difficulty medium
```

**Expected Output:**
```
✅ Created problem with ID: 1
   Title: E-Commerce Sales Analysis
   Difficulty: medium
```

**Note the Problem ID** - you'll need it in the next step!

---

## Step 3: Prepare Your CSV Data

Create CSV files for your tables. **Table names come from filenames**.

### Example: customers.csv
```csv
customer_id,name,email,city,signup_date
1,Alice Johnson,alice@example.com,New York,2024-01-15
2,Bob Smith,bob@example.com,Los Angeles,2024-02-20
3,Carol Davis,carol@example.com,Chicago,2024-03-10
4,David Wilson,david@example.com,Houston,2024-04-05
5,Eve Martinez,eve@example.com,Phoenix,2024-05-12
```

### Example: orders.csv
```csv
order_id,customer_id,order_date,amount,status
101,1,2025-10-01,150.50,completed
102,1,2025-11-15,200.00,completed
103,2,2025-10-05,75.25,completed
104,3,2025-11-20,350.00,completed
105,2,2025-12-01,125.75,completed
```

### Data Type Rules:
The system **automatically infers** column types:

| Pattern | Detected Type | Example |
|---------|---------------|---------|
| `123` or `-45` | INTEGER | `customer_id`, `order_id` |
| `123.45` or `-67.89` | REAL | `amount`, `price` |
| `2024-01-15` | DATE | `signup_date`, `order_date` |
| Anything else | TEXT | `name`, `email`, `status` |

---

## Step 4: Add Tables to Your Problem

### Basic Command:
```bash
python backend/problem_manager/manage_problems.py add-table \
  --problem <PROBLEM_ID> \
  --csv <PATH_TO_CSV>
```

### Example - Add customers table:
```bash
python backend/problem_manager/manage_problems.py add-table \
  --problem 1 \
  --csv customers.csv
```

**Expected Output:**
```
✅ Added table 'customers' to problem 1
   Rows: 5
   Columns: customer_id (INTEGER), name (TEXT), email (TEXT), city (TEXT), signup_date (DATE)
```

### Example - Add orders table:
```bash
python backend/problem_manager/manage_problems.py add-table \
  --problem 1 \
  --csv orders.csv
```

**Expected Output:**
```
✅ Added table 'orders' to problem 1
   Rows: 5
   Columns: order_id (INTEGER), customer_id (INTEGER), order_date (DATE), amount (REAL), status (TEXT)
```

---

## Step 5: Verify Your Problem

### View complete problem details:
```bash
python backend/problem_manager/manage_problems.py view-problem 1
```

**Expected Output:**
```
================================================================================
Problem ID: 1
Title: E-Commerce Sales Analysis
Difficulty: medium
Created: 2026-02-01 12:34:56
================================================================================

Description:
# Sales Analysis

Analyze Q4 2025 sales data for our e-commerce platform.
...

================================================================================
Tables:

  📊 customers (5 rows)
     Columns: customer_id (INTEGER), name (TEXT), email (TEXT), city (TEXT), signup_date (DATE)

  📊 orders (5 rows)
     Columns: order_id (INTEGER), customer_id (INTEGER), order_date (DATE), amount (REAL), status (TEXT)
```

### List all problems:
```bash
python backend/problem_manager/manage_problems.py list-problems
```

---

## Step 6: Start the System

Restart your backend to load the new problems:

```bash
./start.sh
```

Or manually:
```bash
cd backend
uvicorn main:app --reload --port 8000
```

---

## Step 7: Test in Frontend

1. Open the frontend: http://localhost:3000
2. Click **"New Session"**
3. You should see your problem in the dropdown:
   - **E-Commerce Sales Analysis** (Medium)
4. Select it and create a session
5. The problem description will appear
6. Test SQL queries:
   ```sql
   SELECT * FROM customers;
   SELECT * FROM orders WHERE amount > 100;
   ```

---

## 🎯 Complete Example Workflow

```bash
# 1. Initialize database (first time only)
python backend/problem_manager/init_db.py

# 2. Create problem
python backend/problem_manager/manage_problems.py add-problem \
  --title "Product Inventory Analysis" \
  --description "Analyze our product inventory and sales trends" \
  --difficulty easy

# Output: Created problem with ID: 2

# 3. Add tables
python backend/problem_manager/manage_problems.py add-table --problem 2 --csv products.csv
python backend/problem_manager/manage_problems.py add-table --problem 2 --csv inventory.csv

# 4. Verify
python backend/problem_manager/manage_problems.py view-problem 2

# 5. Restart backend
./start.sh
```

---

## 🔧 Advanced Usage

### Delete a Problem
```bash
python backend/problem_manager/manage_problems.py delete-problem 1
```
⚠️ This deletes the problem and ALL its tables!

### Multiple Problems
You can have unlimited problems. Candidates will select from dropdown.

### Update a Problem
Currently not supported. To update:
1. Delete the old problem
2. Create a new one with updated data

### Large Datasets
- Maximum: **10,000 rows per table**
- For larger datasets, sample the data first

---

## ❓ Troubleshooting

### "Database not found" Error
```
❌ Database not found. Run init_db.py first
```
**Solution:** Run `python backend/problem_manager/init_db.py`

### "Problem ID not found"
```
❌ Problem ID 5 not found
```
**Solution:** Run `python backend/problem_manager/manage_problems.py list-problems` to see valid IDs

### Table Already Exists
```
❌ Table 'customers' already exists for problem 1
```
**Solution:** Each problem can only have ONE table with each name. Delete the problem and recreate it, or use a different table name.

### CSV Parsing Errors
```
⚠️  Skipping malformed row: ['1', 'Alice']
```
**Solution:** Ensure all rows have the same number of columns as headers

### Frontend Not Showing Problems
**Solution:** 
1. Check backend is running: `curl http://localhost:8000/api/problems`
2. Check browser console for errors
3. Refresh the page
4. Verify database has problems: `python backend/problem_manager/manage_problems.py list-problems`

---

## 📝 Tips

✅ **DO:**
- Use descriptive problem titles
- Include task instructions in description (Markdown supported)
- Test SQL queries before deploying
- Keep table names simple (lowercase, no spaces)
- Use realistic sample data

❌ **DON'T:**
- Exceed 10,000 rows per table
- Use special characters in filenames (they become table names)
- Forget to restart backend after adding problems
- Delete CSV files before importing (they're needed during import)

---

## 🎨 Difficulty Levels

- **easy**: Basic SELECT queries, simple filters
- **medium**: JOINs, aggregations, GROUP BY
- **hard**: Subqueries, window functions, complex logic

---

## 🔐 Security Notes

Candidates can only run SELECT queries. The following are **blocked**:
- DROP, DELETE, UPDATE, INSERT
- ALTER, CREATE, TRUNCATE
- ATTACH, DETACH
- And more...

All queries are automatically limited to 5000 rows and timeout after 30 seconds.

---

## Need Help?

Check the detailed README:
```bash
cat backend/problem_manager/README.md
```

Or view CLI help:
```bash
python backend/problem_manager/manage_problems.py --help
```
