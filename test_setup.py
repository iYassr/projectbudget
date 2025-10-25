#!/usr/bin/env python3
"""
Test Setup - Verify that the expense tracker is properly configured
"""
import os
import sys
from pathlib import Path


def check_python_version():
    """Check Python version"""
    print("Checking Python version...", end=" ")
    if sys.version_info < (3, 8):
        print("✗ FAIL")
        print(f"  Python 3.8+ required, found {sys.version}")
        return False
    print(f"✓ OK ({sys.version.split()[0]})")
    return True


def check_dependencies():
    """Check if required packages are installed"""
    print("\nChecking dependencies...")

    required_packages = [
        'pandas',
        'plotly',
        'streamlit',
        'openpyxl',
        'anthropic',
        'dotenv'
    ]

    all_ok = True
    for package in required_packages:
        print(f"  {package}...", end=" ")
        try:
            __import__(package.replace('-', '_'))
            print("✓")
        except ImportError:
            print("✗ MISSING")
            all_ok = False

    return all_ok


def check_directories():
    """Check if required directories exist"""
    print("\nChecking directories...")

    required_dirs = ['src', 'data', 'config', 'reports']

    all_ok = True
    for dir_name in required_dirs:
        print(f"  {dir_name}/...", end=" ")
        if os.path.isdir(dir_name):
            print("✓")
        else:
            print("✗ MISSING")
            all_ok = False

    return all_ok


def check_config_files():
    """Check if configuration files exist"""
    print("\nChecking configuration files...")

    files = {
        'config/categories.json': 'Categories configuration',
        '.env.example': 'Environment template',
        'requirements.txt': 'Python dependencies'
    }

    all_ok = True
    for file_path, description in files.items():
        print(f"  {file_path}...", end=" ")
        if os.path.isfile(file_path):
            print("✓")
        else:
            print(f"✗ MISSING ({description})")
            all_ok = False

    return all_ok


def check_env_file():
    """Check .env file"""
    print("\nChecking environment configuration...")

    print("  .env file...", end=" ")
    if os.path.isfile('.env'):
        print("✓")

        # Check for API key
        print("  ANTHROPIC_API_KEY...", end=" ")
        from dotenv import load_dotenv
        load_dotenv()

        api_key = os.getenv('ANTHROPIC_API_KEY')
        if api_key and api_key != 'your_anthropic_api_key_here':
            print("✓ (configured)")
        else:
            print("⚠ (not configured - AI categorization will be disabled)")

        return True
    else:
        print("⚠ MISSING (copy from .env.example)")
        return False


def check_messages_db():
    """Check if Messages database is accessible"""
    print("\nChecking Messages database access...")

    messages_db = os.path.expanduser("~/Library/Messages/chat.db")
    print(f"  {messages_db}...", end=" ")

    if os.path.isfile(messages_db):
        # Try to read it
        try:
            import sqlite3
            conn = sqlite3.connect(f"file:{messages_db}?mode=ro", uri=True)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM message LIMIT 1")
            cursor.fetchone()
            conn.close()
            print("✓ (accessible)")
            return True
        except Exception as e:
            print(f"✗ PERMISSION DENIED")
            print("\n  ⚠️  You need to grant Full Disk Access to Terminal:")
            print("     System Preferences → Security & Privacy → Privacy → Full Disk Access")
            return False
    else:
        print("✗ NOT FOUND")
        print("\n  ⚠️  This might not be a Mac, or Messages is not synced")
        return False


def test_expense_parser():
    """Test the expense parser with sample data"""
    print("\nTesting expense parser...")

    try:
        from src.expense_parser import ExpenseParser

        parser = ExpenseParser()

        test_messages = [
            "You spent Rs 150.50 at STARBUCKS",
            "Card used for $25.00 at Uber",
            "Invalid message without expense"
        ]

        parsed_count = 0
        for msg in test_messages:
            result = parser.parse_message(msg)
            if result:
                parsed_count += 1

        print(f"  Parsed {parsed_count}/{len(test_messages)} test messages...", end=" ")
        if parsed_count >= 2:
            print("✓")
            return True
        else:
            print("✗ FAIL")
            return False

    except Exception as e:
        print(f"✗ ERROR: {e}")
        return False


def test_database():
    """Test database operations"""
    print("\nTesting database...")

    try:
        from src.database import ExpenseDatabase
        from datetime import datetime

        # Use a test database
        test_db_path = "data/test_setup.db"

        db = ExpenseDatabase(test_db_path)

        # Test adding expense
        expense = {
            'date': datetime.now(),
            'amount': 10.00,
            'merchant': 'Test Merchant',
            'category': 'Test'
        }

        expense_id = db.add_expense(expense)

        # Test retrieving
        expenses = db.get_expenses()

        # Clean up
        os.remove(test_db_path)

        print("  Database operations...", end=" ")
        if expense_id > 0 and len(expenses) > 0:
            print("✓")
            return True
        else:
            print("✗ FAIL")
            return False

    except Exception as e:
        print(f"✗ ERROR: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 70)
    print("Expense Tracker - Setup Verification")
    print("=" * 70)

    results = []

    results.append(("Python version", check_python_version()))
    results.append(("Dependencies", check_dependencies()))
    results.append(("Directories", check_directories()))
    results.append(("Config files", check_config_files()))
    results.append(("Environment", check_env_file()))
    results.append(("Messages DB", check_messages_db()))
    results.append(("Expense parser", test_expense_parser()))
    results.append(("Database", test_database()))

    print("\n" + "=" * 70)
    print("Summary")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {name:.<50} {status}")

    print("=" * 70)
    print(f"Result: {passed}/{total} checks passed")

    if passed == total:
        print("\n✓ All checks passed! Your setup is ready to use.")
        print("\nNext steps:")
        print("  1. Activate virtual environment: source venv/bin/activate")
        print("  2. Process messages: python src/main.py process --this-month")
        print("  3. Launch dashboard: streamlit run src/dashboard.py")
        return 0
    else:
        print(f"\n⚠ {total - passed} check(s) failed. Please review the errors above.")
        print("\nCommon solutions:")
        print("  - Missing dependencies: pip install -r requirements.txt")
        print("  - Missing .env: cp .env.example .env")
        print("  - Messages DB access: Grant Full Disk Access (see README)")
        return 1


if __name__ == '__main__':
    sys.exit(main())
