# Monthly Expense Tracker

A Python-based system to extract, analyze, and visualize expenses from iPhone SMS messages.

## Features

- 🏦 Extract expense data from iPhone Messages database or TXT exports
- 🤖 AI-powered expense categorization (OpenAI/Anthropic)
- 📊 Interactive Streamlit dashboard with 25+ visualizations
- 💰 Multi-currency support (SAR, USD, EUR, GBP, INR)
- 🇸🇦 Saudi-specific categories (Zakat, Charity, Padel, etc.)
- 📱 Smart SMS parsing with Arabic support
- 🐳 **Docker support for easy deployment**
- 🎯 Budget tracking and spending insights
- 📤 Export to Excel, CSV, and Google Sheets
- 🔄 Automated monthly reports

## Quick Start (Docker) 🐳

**Fastest way to get started:**

```bash
# 1. Clone repository
git clone <your-repo>
cd projectbudget

# 2. Copy environment file
cp .env.example .env

# 3. Start dashboard
docker-compose up dashboard
```

Dashboard available at **http://localhost:8501**

See [DOCKER.md](DOCKER.md) for complete Docker documentation.

---

## Setup (Traditional)

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
├── reports/                  # Generated reports
├── Dockerfile                # Docker image configuration
├── docker-compose.yml        # Docker orchestration
└── docker-entrypoint.sh      # Docker startup script
```

## 📚 Documentation

- **[DOCKER.md](DOCKER.md)** - Complete Docker setup and deployment guide
- **[USAGE.md](USAGE.md)** - Detailed usage instructions
- **[QUICKSTART.md](QUICKSTART.md)** - Quick start guide
- **[RECATEGORIZATION_GUIDE.md](RECATEGORIZATION_GUIDE.md)** - Guide to categorizing merchants
- **[DASHBOARD_FEATURES.md](DASHBOARD_FEATURES.md)** - Dashboard features overview
- **[SENDER_FILTERING.md](SENDER_FILTERING.md)** - SMS sender filtering guide

## 🐳 Docker vs Traditional Setup

| Feature | Docker | Traditional |
|---------|--------|------------|
| **Setup Time** | 2 minutes | 10-15 minutes |
| **Dependencies** | Auto-installed | Manual pip install |
| **Portability** | ✅ Works anywhere | ❌ Python env required |
| **Isolation** | ✅ Containerized | ❌ System-wide |
| **Updates** | Easy rebuild | Manual dependency updates |
| **Production Ready** | ✅ Yes | Requires extra config |
| **Development** | ✅ Hot reload | ✅ Direct access |

**Recommendation:** Use Docker for deployment, Traditional for development.

## 🚀 Common Tasks

### Docker Commands
```bash
# Start dashboard
docker-compose up dashboard

# Extract expenses from TXT
docker-compose run --rm dashboard extract /app/data/messages.txt

# Recategorize with AI
docker-compose run --rm dashboard recategorize --use-ai --apply

# Backup database
docker-compose run --rm dashboard backup

# Interactive shell
docker-compose run --rm dashboard bash
```

### Traditional Commands
```bash
# Start dashboard
streamlit run src/dashboard.py

# Extract from TXT export
python extract_from_txt_export.py messages.txt

# Recategorize
python recategorize_others.py --apply

# Run tests
python -m pytest tests/
```

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with Docker: `docker-compose up --build`
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

- Built with Streamlit, Plotly, and SQLite
- AI categorization powered by OpenAI and Anthropic
- Saudi-specific features for local market needs
