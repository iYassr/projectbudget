# Monthly Expense Tracker

A Python-based system to extract, analyze, and visualize expenses from iPhone SMS messages.

## Features

- Extract expense data from iPhone Messages database on Mac
- Automatic parsing of bank/payment SMS messages
- AI-powered expense categorization
- Interactive dashboard with visualizations
- Export to Excel, CSV, and Google Sheets
- Monthly automated reports

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment variables in `.env`:
```
ANTHROPIC_API_KEY=your_api_key_here
GOOGLE_SHEETS_CREDENTIALS=path_to_credentials.json
```

3. Grant Full Disk Access to Terminal (for Messages database access):
   - System Preferences → Security & Privacy → Privacy → Full Disk Access
   - Add Terminal or your IDE

## Usage

### Extract SMS Messages
```bash
python src/sms_extractor.py --start-date 2025-01-01 --end-date 2025-01-31
```

### Run Analysis
```bash
python src/analyzer.py
```

### Launch Dashboard
```bash
streamlit run src/dashboard.py
```

## Project Structure

```
projectbudget/
├── src/
│   ├── sms_extractor.py      # Extract SMS from Messages database
│   ├── expense_parser.py     # Parse expense data from SMS
│   ├── categorizer.py        # AI-powered categorization
│   ├── database.py           # SQLite database operations
│   ├── analyzer.py           # Data analysis and insights
│   ├── dashboard.py          # Streamlit dashboard
│   └── exporter.py           # Export to various formats
├── data/
│   └── expenses.db           # SQLite database
├── config/
│   └── categories.json       # Expense categories configuration
└── reports/                  # Generated reports
```
