#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Expense Tracker Docker Container ===${NC}"

# Initialize database if it doesn't exist
if [ ! -f "/app/data/expenses.db" ]; then
    echo -e "${YELLOW}Database not found. Initializing...${NC}"
    python3 -c "from src.database import ExpenseDatabase; ExpenseDatabase('data/expenses.db')"
    echo -e "${GREEN}Database initialized successfully${NC}"
fi

# Ensure directories exist
mkdir -p /app/data /app/reports /app/logs /app/backups

# Handle different commands
case "$1" in
    dashboard)
        echo -e "${GREEN}Starting Streamlit dashboard on port 8501...${NC}"
        exec streamlit run src/dashboard.py \
            --server.port=8501 \
            --server.address=0.0.0.0 \
            --server.headless=true \
            --browser.gatherUsageStats=false \
            --server.fileWatcherType=none
        ;;

    extract)
        echo -e "${GREEN}Running expense extraction...${NC}"
        if [ -z "$2" ]; then
            echo -e "${RED}Error: Please provide input file path${NC}"
            echo "Usage: docker compose run dashboard extract /path/to/messages.txt"
            exit 1
        fi
        exec python3 extract_from_txt_export.py "$2"
        ;;

    recategorize)
        echo -e "${GREEN}Recategorizing expenses...${NC}"
        exec python3 recategorize_others.py "$@"
        ;;

    scheduler)
        echo -e "${GREEN}Starting scheduler service...${NC}"
        # Run scheduled tasks in a loop
        while true; do
            # Run monthly processing on the 1st of each month at 9 AM
            current_day=$(date +%d)
            current_hour=$(date +%H)

            if [ "$current_day" = "01" ] && [ "$current_hour" = "09" ]; then
                echo -e "${GREEN}Running monthly processing...${NC}"
                python3 src/main.py process --last-month --review 2>&1 | tee -a /app/logs/scheduler.log
            fi

            # Check every hour
            sleep 3600
        done
        ;;

    backup)
        echo -e "${GREEN}Creating database backup...${NC}"
        timestamp=$(date +%Y%m%d_%H%M%S)
        backup_file="/app/backups/expenses_backup_${timestamp}.db"

        if [ -f "/app/data/expenses.db" ]; then
            cp /app/data/expenses.db "$backup_file"
            echo -e "${GREEN}Backup created: ${backup_file}${NC}"

            # Keep only last 30 backups
            cd /app/backups
            ls -t expenses_backup_*.db | tail -n +31 | xargs -r rm
            echo -e "${GREEN}Old backups cleaned up${NC}"
        else
            echo -e "${RED}No database found to backup${NC}"
            exit 1
        fi
        ;;

    test)
        echo -e "${GREEN}Running tests...${NC}"
        exec python3 -m pytest tests/ -v
        ;;

    bash|sh|shell)
        echo -e "${GREEN}Starting interactive bash shell...${NC}"
        exec /bin/bash
        ;;

    python)
        echo -e "${GREEN}Starting Python shell...${NC}"
        exec python3
        ;;

    help|--help|-h)
        echo -e "${GREEN}Expense Tracker Docker Commands:${NC}"
        echo ""
        echo "  dashboard         - Start Streamlit dashboard (default)"
        echo "  extract <file>    - Extract expenses from TXT file"
        echo "  recategorize      - Recategorize existing expenses"
        echo "  scheduler         - Run scheduled tasks"
        echo "  backup            - Create database backup"
        echo "  test              - Run test suite"
        echo "  bash|shell        - Open bash shell"
        echo "  python            - Open Python shell"
        echo "  help              - Show this help message"
        echo ""
        echo "Examples:"
        echo "  docker compose up dashboard"
        echo "  docker compose run dashboard extract /data/messages.txt"
        echo "  docker compose run dashboard recategorize --apply"
        echo "  docker compose run dashboard backup"
        echo "  docker compose run dashboard bash"
        ;;

    *)
        echo -e "${YELLOW}Unknown command: $1${NC}"
        echo "Run 'docker compose run dashboard help' for available commands"
        echo -e "${YELLOW}Starting dashboard by default...${NC}"
        exec streamlit run src/dashboard.py \
            --server.port=8501 \
            --server.address=0.0.0.0 \
            --server.headless=true \
            --browser.gatherUsageStats=false
        ;;
esac
