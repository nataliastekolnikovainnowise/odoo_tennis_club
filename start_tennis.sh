#!/bin/bash

# ============================================
# Tennis Club Odoo 18 Launcher
# ============================================

RED="\033[0;31m"
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
BLUE="\033[0;34m"
NC="\033[0m"

PROJECT_DIR="$HOME/tennis_project"
CONFIG="$PROJECT_DIR/config/odoo.conf"
ODOO_BIN="$HOME/Git/odoo/odoo-bin"

clear
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  🎾 TENNIS CLUB ODOO 18 🎾${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

if [ ! -f "$ODOO_BIN" ]; then
    echo -e "${RED}❌ Error: odoo-bin not found at $ODOO_BIN${NC}"
    exit 1
fi

if [ ! -f "$CONFIG" ]; then
    echo -e "${RED}❌ Error: Config not found at $CONFIG${NC}"
    exit 1
fi

echo -e "${BLUE}📁 Project:${NC} $PROJECT_DIR"
echo -e "${BLUE}⚙️  Config:${NC} $CONFIG"
echo -e "${BLUE}🔧 Odoo:${NC} Version 18"
echo -e "${BLUE}💾 DB User:${NC} admin"
echo -e "${BLUE}🌐 Access:${NC} http://localhost:8018"
echo ""

DB_NAME="${1:-tennis_club_db}"
echo -e "${BLUE}💾 Database:${NC} $DB_NAME"
echo ""

PORT=8018
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Warning: Port $PORT is already in use!${NC}"
    ps aux | grep "[o]doo-bin" | head -3
    echo ""
    read -p "Stop other Odoo and continue? (y/n): " choice
    if [ "$choice" == "y" ]; then
        pkill -f odoo-bin
        sleep 2
    else
        exit 1
    fi
fi

echo -e "${YELLOW}Select action:${NC}"
echo "1) 🚀 Start Odoo (normal)"
echo "2) 🔧 Start Odoo (DEV mode)"
echo "3) 📦 Install tennis_club module"
echo "4) 🔄 Update tennis_club module"
echo "5) 🛑 Stop Odoo"
echo "6) 🗄️  Create new database"
echo "7) 📋 List all databases"
echo "8) 🗑️  Drop database"
echo "9) ❌ Exit"
echo ""
read -p "Choice [1-9]: " choice

case $choice in
    1)
        echo ""
        echo -e "${GREEN}🚀 Starting Odoo 18...${NC}"
        echo -e "${YELLOW}   URL: http://localhost:8018${NC}"
        echo -e "${YELLOW}   Database: $DB_NAME${NC}"
        echo ""
        $ODOO_BIN -c $CONFIG -d $DB_NAME
        ;;
    2)
        echo ""
        echo -e "${GREEN}🔧 Starting Odoo 18 DEV mode...${NC}"
        echo -e "${YELLOW}   URL: http://localhost:8018${NC}"
        echo -e "${YELLOW}   Database: $DB_NAME${NC}"
        echo -e "${YELLOW}   Auto-reload: ON${NC}"
        echo ""
        $ODOO_BIN -c $CONFIG -d $DB_NAME --dev=all
        ;;
    3)
        echo ""
        echo -e "${GREEN}📦 Installing tennis_club module...${NC}"
        echo -e "${YELLOW}   Database: $DB_NAME${NC}"
        $ODOO_BIN -c $CONFIG -d $DB_NAME -i tennis_club --stop-after-init
        echo ""
        echo -e "${GREEN}✅ Installation complete!${NC}"
        echo -e "${YELLOW}   Now run option 1 or 2 to start Odoo${NC}"
        ;;
    4)
        echo ""
        echo -e "${GREEN}🔄 Updating tennis_club module...${NC}"
        echo -e "${YELLOW}   Database: $DB_NAME${NC}"
        $ODOO_BIN -c $CONFIG -d $DB_NAME -u tennis_club --stop-after-init
        echo ""
        echo -e "${GREEN}✅ Update complete!${NC}"
        ;;
    5)
        echo ""
        echo -e "${YELLOW}🛑 Stopping all Odoo processes...${NC}"
        pkill -f odoo-bin
        echo -e "${GREEN}✅ Done!${NC}"
        ;;
    6)
        echo ""
        read -p "Enter database name (default: tennis_club_db): " NEW_DB
        NEW_DB="${NEW_DB:-tennis_club_db}"
        echo -e "${GREEN}🗄️  Creating database: $NEW_DB...${NC}"
        $ODOO_BIN -c $CONFIG -d $NEW_DB -i base --stop-after-init
        echo ""
        echo -e "${GREEN}✅ Database '$NEW_DB' created!${NC}"
        echo -e "${YELLOW}   To use it, run: ./start_tennis.sh $NEW_DB${NC}"
        ;;
    7)
        echo ""
        echo -e "${YELLOW}📋 PostgreSQL databases:${NC}"
        sudo -u postgres psql -c "\l" | grep -E "(Name|tennis|admin)" | head -20
        echo ""
        ;;
    8)
        echo ""
        echo -e "${RED}⚠️  WARNING: This will DELETE the database!${NC}"
        read -p "Enter database name to drop: " DROP_DB
        if [ -z "$DROP_DB" ]; then
            echo -e "${RED}❌ No database name provided${NC}"
            exit 1
        fi
        echo ""
        read -p "Are you sure you want to drop '$DROP_DB'? (yes/no): " confirm
        if [ "$confirm" == "yes" ]; then
            sudo -u postgres dropdb "$DROP_DB"
            echo -e "${GREEN}✅ Database '$DROP_DB' dropped${NC}"
        else
            echo -e "${YELLOW}Cancelled${NC}"
        fi
        ;;
    9)
        echo ""
        echo -e "${GREEN}👋 Goodbye!${NC}"
        exit 0
        ;;
    *)
        echo ""
        echo -e "${RED}❌ Invalid choice${NC}"
        exit 1
        ;;
esac
