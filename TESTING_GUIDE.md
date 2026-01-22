# Database Testing Guide

## Step 1: Install Dependencies

First, make sure you're in your virtual environment and install the required packages:

```bash
# Activate virtual environment (if not already activated)
source venv/bin/activate

# Install dependencies (python>=3.8 line has been removed from requirements.txt)
pip install -r requirements.txt
```

**Note**: The `python>=3.8` line has been removed from requirements.txt as it's not a pip package.

## Step 2: Run the Test Script

Run the comprehensive test script to verify everything works:

```bash
python3 test_database_setup.py
```

This script will:
1. ✅ Test all imports
2. ✅ Initialize the database and create all tables
3. ✅ Test all CRUD operations (Create, Read, Update, Delete)
4. ✅ Test relationships and cascade deletes

## Step 3: Manual Testing (Optional)

You can also test manually:

### Initialize Database
```bash
python3 -m src.database.init_db
```

### Run Example Usage
```bash
python3 -m src.database.example_usage
```

### Run Unit Tests (if pytest is installed)
```bash
pytest tests/test_database.py -v
```

## Expected Output

When running `test_database_setup.py`, you should see:

```
============================================================
MediAnalyze Pro - Database Module Test Suite
============================================================
============================================================
TEST 1: Testing Imports
============================================================
✅ All imports successful!

============================================================
TEST 2: Database Initialization
============================================================
Initializing database...
✅ Database initialized successfully!

Created tables: 6
  ✅ biomedical_signals
  ✅ correlation_results
  ✅ health_metrics
  ✅ medical_images
  ✅ patients
  ✅ spectrum_analysis

✅ All expected tables created!

============================================================
TEST 3: CRUD Operations
============================================================
1. Testing patient insertion...
   ✅ Patient created with ID: 1
2. Testing patient retrieval...
   ✅ Patient retrieved: Test Patient
... (more tests)

🎉 ALL TESTS PASSED! Database module is working correctly.
```

## Troubleshooting

### Import Errors
- Make sure you're in the project root directory
- Verify virtual environment is activated
- Check that all dependencies are installed

### Database Errors
- Check that the `data/` directory exists and is writable
- Verify SQLite is working: `python3 -c "import sqlite3; print('OK')"`

### Path Issues
- Make sure you're running from the project root: `/Users/dev/Desktop/MediAnalyze Pro`

## Database Location

The database file will be created at:
```
data/medanalyze.db
```

You can verify it exists after running the initialization.
