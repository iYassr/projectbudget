# Quick Start Guide

Get your expense tracker running in 5 minutes!

## Prerequisites

- **Mac computer** with Messages synced from iPhone
- **Python 3.8+** installed
- **SMS messages** from banks/payment services on your iPhone

## Installation

```bash
# 1. Navigate to project directory
cd projectbudget

# 2. Run setup
./setup.sh

# 3. Activate virtual environment
source venv/bin/activate

# 4. Verify setup
python test_setup.py
```

## Grant Permissions (Required for Mac)

1. Open **System Preferences**
2. Go to **Security & Privacy** → **Privacy** → **Full Disk Access**
3. Click the **+** button and add **Terminal** (or your IDE)
4. Restart Terminal

## First Run

### Option 1: Process This Month's Expenses

```bash
python src/main.py process --this-month --review
```

This will:
- Extract SMS messages from this month
- Parse expense data
- Categorize expenses
- Save to database
- Generate a monthly report
- Export to CSV, Excel, JSON, and text report

### Option 2: Launch Interactive Dashboard

```bash
streamlit run src/dashboard.py
```

Opens a web dashboard at http://localhost:8501 with:
- Interactive charts and graphs
- Category breakdown
- Top merchants
- Recent transactions
- Export functionality

## Configuration (Optional)

### Add AI Categorization

1. Get an Anthropic API key: https://console.anthropic.com/
2. Edit `.env`:
   ```bash
   nano .env
   ```
3. Add your key:
   ```
   ANTHROPIC_API_KEY=sk-ant-...
   ```

### Customize Categories

Edit `config/categories.json` to add/modify expense categories and keywords.

## Common Commands

```bash
# Process last month
python src/main.py process --last-month

# Process specific dates
python src/main.py process --start-date 2025-01-01 --end-date 2025-01-31

# Generate monthly review
python src/main.py review --this-month

# Export data
python src/main.py export --format excel

# Launch dashboard
streamlit run src/dashboard.py
```

## File Locations

- **Database**: `data/expenses.db`
- **Reports**: `reports/` directory
- **Configuration**: `config/categories.json`
- **Environment**: `.env`

## Troubleshooting

### "Messages database not found"
→ Grant Full Disk Access to Terminal (see above)

### "No messages found"
→ Ensure iPhone Messages are synced to Mac via iCloud

### "Module not found"
→ Activate virtual environment: `source venv/bin/activate`

### "Permission denied"
→ Make scripts executable: `chmod +x setup.sh test_setup.py`

## Next Steps

1. Review the generated reports in `reports/` directory
2. Explore the dashboard for interactive analysis
3. Set up monthly automation (see USAGE.md)
4. Customize categories for your spending patterns

## Need Help?

- Full documentation: `README.md`
- Detailed usage guide: `USAGE.md`
- Test your setup: `python test_setup.py`

---

**Privacy Note**: All data processing happens locally on your Mac. Your SMS messages and expense data never leave your computer (except for optional AI categorization via Anthropic API).
