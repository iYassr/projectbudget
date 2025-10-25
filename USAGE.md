# Expense Tracker - Usage Guide

## Quick Start

### 1. Setup

```bash
# Run setup script
./setup.sh

# Activate virtual environment
source venv/bin/activate

# Edit .env and add your Anthropic API key (optional)
nano .env
```

### 2. Grant Permissions (Mac Only)

For SMS extraction to work, you need to grant Full Disk Access:

1. Open **System Preferences** → **Security & Privacy** → **Privacy**
2. Select **Full Disk Access** from the left sidebar
3. Click the lock icon and authenticate
4. Add your Terminal app or IDE to the list
5. Restart Terminal/IDE

## Basic Usage

### Process SMS Messages

Extract and process expenses from iPhone messages:

```bash
# Process current month
python src/main.py process --this-month

# Process last month
python src/main.py process --last-month

# Process specific date range
python src/main.py process --start-date 2025-01-01 --end-date 2025-01-31

# Process and generate review
python src/main.py process --this-month --review
```

### Generate Monthly Review

```bash
# Review current month
python src/main.py review --this-month

# Review specific month
python src/main.py review --year 2025 --month 1
```

### Export Data

```bash
# Export current month (all formats)
python src/main.py export --this-month

# Export specific format
python src/main.py export --year 2025 --month 1 --format excel

# Available formats: csv, excel, json, report, all
```

### Launch Dashboard

```bash
streamlit run src/dashboard.py
```

This will open an interactive web dashboard at http://localhost:8501

## Advanced Usage

### Individual Modules

#### Extract SMS Only

```bash
python src/sms_extractor.py --start-date 2025-01-01 --end-date 2025-01-31 --output data/messages.csv
```

#### Test Expense Parser

```bash
python src/expense_parser.py
```

#### Test Categorization

```bash
python src/categorizer.py
```

#### Generate Analysis Report

```bash
python src/analyzer.py
```

### API Usage

You can also use the modules programmatically:

```python
from src.database import ExpenseDatabase
from src.analyzer import ExpenseAnalyzer
from src.exporter import ExpenseExporter

# Initialize
db = ExpenseDatabase("data/expenses.db")
analyzer = ExpenseAnalyzer(db)

# Get monthly summary
summary = analyzer.get_monthly_summary(2025, 1)
print(f"Total spent: ${summary['total_amount']}")

# Export
exporter = ExpenseExporter(db)
exporter.export_to_excel("reports/january.xlsx", "2025-01-01", "2025-01-31")
```

## Configuration

### Categories

Edit `config/categories.json` to customize expense categories:

```json
{
  "categories": [
    "Food & Dining",
    "Transportation",
    "Shopping",
    ...
  ],
  "merchant_keywords": {
    "Food & Dining": ["restaurant", "cafe", "pizza", ...]
  }
}
```

### AI Categorization

To enable AI-powered categorization:

1. Get an Anthropic API key from https://console.anthropic.com/
2. Add to `.env`:
   ```
   ANTHROPIC_API_KEY=your_key_here
   ```
3. AI will automatically be used for categorization

Without AI, the system uses rule-based categorization with keywords.

## Automation

### Monthly Cron Job

Add to your crontab to run automatically each month:

```bash
# Edit crontab
crontab -e

# Add this line (runs on 1st of each month at 9 AM)
0 9 1 * * cd /path/to/projectbudget && source venv/bin/activate && python src/main.py process --last-month --review
```

### Launchd (Mac)

Create `~/Library/LaunchAgents/com.expensetracker.monthly.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.expensetracker.monthly</string>
    <key>ProgramArguments</key>
    <array>
        <string>/path/to/projectbudget/venv/bin/python</string>
        <string>/path/to/projectbudget/src/main.py</string>
        <string>process</string>
        <string>--last-month</string>
        <string>--review</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Day</key>
        <integer>1</integer>
        <key>Hour</key>
        <integer>9</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
</dict>
</plist>
```

Load it:
```bash
launchctl load ~/Library/LaunchAgents/com.expensetracker.monthly.plist
```

## Troubleshooting

### "Messages database not found"

- Make sure you're on a Mac with Messages synced from iPhone
- Grant Full Disk Access to Terminal (see Setup section)
- Check if database exists: `ls ~/Library/Messages/chat.db`

### "No messages found"

- Check date range is correct
- Verify iPhone messages are synced to Mac (Settings → Messages → Enable Messages in iCloud)
- Try expanding the date range

### Parsing issues

- The parser works best with English bank SMS messages
- Add custom parsing patterns in `src/expense_parser.py` for your specific bank format
- Check `data/raw_messages.csv` to see what messages were extracted

### AI categorization not working

- Verify `ANTHROPIC_API_KEY` is set in `.env`
- Check your API key is valid and has credits
- System will fall back to rule-based categorization if AI fails

## Data Storage

All data is stored locally:

- **Database**: `data/expenses.db` (SQLite)
- **Reports**: `reports/` directory
- **Raw messages**: `data/raw_messages.csv`

No data is sent to external services except:
- Anthropic API (if AI categorization is enabled)
- Google Sheets API (if you configure Google Sheets export)

## Privacy & Security

- All processing happens locally on your Mac
- SMS data never leaves your machine (except for optional AI categorization)
- Database is not encrypted by default - use FileVault for disk encryption
- Keep your `.env` file secure (contains API keys)
- Add `.env` to `.gitignore` (already done)

## Tips

1. **First time setup**: Run on a small date range first to test
2. **Review before processing**: Check `data/raw_messages.csv` to see what messages were extracted
3. **Manual corrections**: Use the database directly or export to Excel to make corrections
4. **Learning**: The system learns merchant→category mappings over time
5. **Backup**: Regularly backup `data/expenses.db`
