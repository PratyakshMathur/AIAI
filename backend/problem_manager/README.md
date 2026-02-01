# Problem Manager - Setup Guide

## Quick Start

### 1. Initialize the Database

```bash
cd backend
python problem_manager/init_db.py
```

This creates `backend/problems.db` with the required schema.

### 2. Create Your First Problem

```bash
python problem_manager/manage_problems.py add-problem \
  --title "E-Commerce Sales Analysis" \
  --description "# E-Commerce Sales Analysis

Analyze quarterly sales data to identify trends and opportunities.

## Your Task
1. Explore customer purchase patterns
2. Identify top-performing products
3. Find seasonal trends
4. Recommend strategies to increase revenue

**Time Limit:** 45 minutes" \
  --difficulty medium
```

This will return a problem ID (e.g., `Created problem with ID: 1`)

### 3. Prepare Your Data (CSV Format)

Create CSV files with your sample data:

**customers.csv:**
```csv
customer_id,name,email,age,city,registration_date
1,Alice Johnson,alice@email.com,28,New York,2024-01-15
2,Bob Smith,bob@email.com,34,Los Angeles,2024-02-20
3,Carol White,carol@email.com,45,Chicago,2024-01-10
```

**orders.csv:**
```csv
order_id,customer_id,product_name,category,amount,order_date
1,1,Laptop,Electronics,1200.00,2024-03-01
2,1,Mouse,Electronics,25.00,2024-03-01
3,2,Desk Chair,Furniture,350.00,2024-03-15
```

### 4. Add Tables to Problem

```bash
python problem_manager/manage_problems.py add-table \
  --problem 1 \
  --csv customers.csv

python problem_manager/manage_problems.py add-table \
  --problem 1 \
  --csv orders.csv
```

### 5. Verify Your Problem

```bash
python problem_manager/manage_problems.py view-problem 1
```

Output:
```
================================================================================
Problem ID: 1
Title: E-Commerce Sales Analysis
Difficulty: medium
Created: 2024-02-01 12:00:00
================================================================================
Description:
# E-Commerce Sales Analysis
...

================================================================================
Tables:
  📊 customers (3 rows)
     Columns: customer_id (INTEGER), name (TEXT), email (TEXT), age (INTEGER), city (TEXT), registration_date (DATE)

  📊 orders (3 rows)
     Columns: order_id (INTEGER), customer_id (INTEGER), product_name (TEXT), category (TEXT), amount (REAL), order_date (DATE)
```

### 6. List All Problems

```bash
python problem_manager/manage_problems.py list-problems
```

### 7. Delete a Problem (if needed)

```bash
python problem_manager/manage_problems.py delete-problem 1
```

---

## Data Type Inference

The system automatically detects column types from your CSV:

| Pattern | Detected Type | Example |
|---------|---------------|---------|
| `123`, `-42` | INTEGER | customer_id, age |
| `3.14`, `99.99` | REAL | amount, price |
| `2024-01-15` | DATE | order_date, registration_date |
| Everything else | TEXT | name, email, city |

---

## Constraints

- **Max rows per table:** 10,000
- **Supported difficulties:** easy, medium, hard
- **Table naming:** Derived from CSV filename (e.g., `customers.csv` → `customers` table)
- **Column validation:** All rows must have same number of columns as header

---

## How It Works

### In the Database (problems.db):
- Tables stored as `customers_1`, `orders_1` (with problem_id suffix)

### What Candidates See:
```sql
SELECT * FROM customers;  -- No problem_id suffix!
```

### What Actually Runs:
```sql
SELECT * FROM customers_1;  -- Automatically aliased
```

This ensures:
✅ Clean SQL for candidates  
✅ Problem isolation  
✅ No data leakage between problems  

---

## Troubleshooting

### "Database not found"
Run `python problem_manager/init_db.py` first.

### "Problem ID not found"
Check available problems with `list-problems` command.

### "CSV file not found"
Use absolute path or relative to current directory:
```bash
python problem_manager/manage_problems.py add-table \
  --problem 1 \
  --csv /full/path/to/data.csv
```

### "Table already exists"
Each problem can only have one table with a given name. Delete and recreate the problem, or use a different table name.

---

## Example Workflow

```bash
# 1. Initialize
python problem_manager/init_db.py

# 2. Create problem
python problem_manager/manage_problems.py add-problem \
  --title "Customer Churn Analysis" \
  --description "Identify customers at risk of churning" \
  --difficulty hard

# 3. Add data tables
python problem_manager/manage_problems.py add-table --problem 1 --csv customers.csv
python problem_manager/manage_problems.py add-table --problem 1 --csv subscriptions.csv
python problem_manager/manage_problems.py add-table --problem 1 --csv usage_logs.csv

# 4. Verify
python problem_manager/manage_problems.py view-problem 1

# 5. Frontend will now show this problem in the dropdown!
```

---

## Frontend Integration

Once problems are added:
1. Restart backend server
2. Open frontend session setup
3. Problems appear in dropdown
4. Candidates select problem and start session
5. SQL queries automatically aliased to problem-specific tables

No code changes needed - it just works! 🎉
