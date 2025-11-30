# Tennis Club Management System

A comprehensive tennis club management system built on Odoo 18, designed to manage multiple tennis centers, courts, trainers, training sessions, and client bookings with integrated Telegram notifications.

## Overview

This production-ready application handles the complete lifecycle of tennis training management, from court scheduling to financial reporting, with a strong emphasis on user experience through Telegram integration and automated workflows.

**Version:** 18.0.1.0.0
**Author:** Natalia Stekolnikova
**License:** LGPL-3
**Category:** Sports

## Key Features

### 🎾 Multi-Center Management
- Manage multiple tennis centers with individual configurations
- Center-specific pricing and working hours
- Court management with surface types (hard, clay, grass, carpet)
- Indoor/outdoor court designation with lighting options

### 📅 Training Session Management
- Create individual, split, or group training sessions
- Automatic session numbering (TS-XXXX format)
- Court availability validation
- Recurring sessions (daily/weekly/monthly patterns)
- Approval workflow for trainer-created sessions
- Status tracking: draft → pending_approval → confirmed → completed/cancelled

### 👥 User Management
- **Trainers**: Hourly rate configuration, availability tracking, revenue statistics
- **Clients**: Balance management, training history, type classification (regular/VIP/corporate/trial)
- **Role-based access control**: User, Trainer, Manager, Director

### 💰 Financial System
- Automatic revenue calculation: `Revenue = Price - Trainer Cost`
- Client balance management with auto-deduction
- Comprehensive reports:
  - Trainer Revenue Report
  - Center Revenue Report
  - Top Statistics (most profitable trainer, popular training type, active client)

### 📱 Telegram Bot Integration
- **Automated Notifications:**
  - Booking confirmations
  - Training reminders (configurable hours before session)
  - Balance updates
  - Low balance alerts
- **Self-Service Commands:**
  - `/start` - Register and link Telegram account
  - `/balance` - Check current balance
  - `/trainings` - View upcoming sessions
  - `/help` - Get help information

### 🔒 Security & Access Control
- 4-level hierarchical user groups
- 57 granular access rules
- Record-level security (trainers see only their center)
- Approval workflow with audit trail

## Project Structure

```
tennis_project/
├── config/
│   └── odoo.conf                    # Main Odoo configuration
├── data/                            # Odoo data directory
├── logs/                            # Application logs
├── backups/                         # Database backups
├── tennis_addons/
│   ├── tennis_club/                 # Main custom addon
│   │   ├── models/                  # 19 Python models
│   │   ├── views/                   # XML views and menus
│   │   ├── security/                # Access control and rules
│   │   ├── data/                    # Initial data and sequences
│   │   ├── wizards/                 # Wizard models
│   │   ├── reports/                 # QWeb report templates
│   │   └── __manifest__.py          # Module manifest
│   └── oca_queue/                   # OCA Queue Job modules
├── start_tennis.sh                  # Launch utility script
├── tennis_telegram_bot.py           # Standalone Telegram bot
└── README.md                        # This file
```

## Installation

### Prerequisites

- Python 3.10+
- PostgreSQL 12+
- Odoo 18
- Telegram Bot Token (for notifications)

### Steps

1. **Clone the repository:**
   ```bash
   cd /home/vboxuser/tennis_project
   ```

2. **Install Odoo 18:**
   Follow the official Odoo installation guide for your platform.

3. **Install Python dependencies:**
   ```bash
   pip install python-telegram-bot requests
   ```

4. **Configure Odoo:**
   Edit `config/odoo.conf` to match your environment:
   ```ini
   [options]
   addons_path = /usr/lib/python3/dist-packages/odoo/addons,/home/vboxuser/tennis_project/tennis_addons
   http_port = 8018
   db_host = localhost
   db_port = 5432
   db_user = odoo
   db_password = odoo
   ```

5. **Start Odoo and install the module:**
   ```bash
   ./start_tennis.sh
   # Select option 1 to start Odoo
   # Then select option 3 to install tennis_club module
   ```

6. **Configure Telegram Bot:**
   - Create a bot via [@BotFather](https://t.me/botfather)
   - In Odoo, go to Settings → Technical → Parameters → System Parameters
   - Add key: `telegram.bot_token` with your bot token value

7. **Start the Telegram bot (optional):**
   ```bash
   python3 tennis_telegram_bot.py
   ```

## Configuration

### Initial Setup

1. **Create Tennis Centers:**
   - Navigate to: Tennis Club → Configuration → Centers
   - Add centers with name, code, manager, contact info, and address

2. **Configure Working Hours:**
   - Navigate to: Tennis Club → Courts → Working Hours
   - Set operating hours for each day of the week per center

3. **Add Courts:**
   - Navigate to: Tennis Club → Courts → Courts
   - Create courts with surface type and indoor/outdoor designation

4. **Define Pricing:**
   - **Trainer Rates:** Tennis Club → Configuration → Trainer Rates
   - **Client Prices:** Tennis Club → Configuration → Center Prices

5. **Set Up Training Types:**
   Default types are loaded automatically:
   - Individual (1 client, 1 trainer)
   - Split (2 clients, 1 trainer)
   - Group (3-5 clients, 1 trainer)

6. **Create Users:**
   - Trainers: Mark employees as trainers and assign to centers
   - Clients: Create partners and mark as clients
   - Assign appropriate security groups

## Usage

### For Managers/Directors

**Creating a Training Session:**
1. Navigate to: Tennis Club → Training → Training Sessions
2. Click "Create"
3. Fill in: Date, Time, Center, Court, Trainer, Clients, Training Type
4. The system will automatically:
   - Calculate price and trainer cost
   - Validate court availability
   - Check working hours compliance
   - Generate session number

**Managing Recurring Sessions:**
1. Create a session as above
2. Enable "Recurring" option
3. Configure: Recurrence pattern, Skip weekends, End date
4. System generates all sessions automatically

**Approving Sessions:**
1. Navigate to pending sessions (filter by status)
2. Review session details
3. Click "Approve" or "Reject"
4. System automatically deducts client balance on approval

**Viewing Reports:**
1. Navigate to: Tennis Club → Reports
2. Select report type and date range
3. Generate PDF or view on screen

### For Trainers

**Creating Sessions:**
1. Follow same steps as managers
2. Sessions are created in "Pending Approval" status
3. Wait for manager approval before session is confirmed

**Checking Schedule:**
1. Use calendar view to see your sessions
2. Filter by your name to see only your trainings

### For Clients (via Telegram)

**Linking Account:**
1. Find the bot in Telegram
2. Send `/start` command
3. Follow prompts to link your account

**Checking Balance:**
```
/balance
```

**Viewing Upcoming Trainings:**
```
/trainings
```

**Getting Help:**
```
/help
```

## Data Models

### Core Models (19 total)

| Model | Description |
|-------|-------------|
| `tennis.center` | Tennis facilities/locations |
| `tennis.court` | Individual courts |
| `tennis.training.session` | Training bookings (central model) |
| `tennis.training.type` | Training types configuration |
| `tennis.trainer.rate` | Hourly rates per trainer |
| `tennis.center.price` | Client prices per center |
| `tennis.center.working.hours` | Operating hours per day |
| `court.schedule` | Court booking schedule |
| `court.schedule.status` | Schedule status definitions |
| `tennis.trainer.availability` | Trainer availability tracking |
| `telegram.notification` | Telegram notification log |
| `hr.employee` (extended) | Trainer management |
| `res.partner` (extended) | Client management |

## User Roles & Permissions

### 1. Tennis Club User
- Basic access to view sessions
- Limited editing capabilities

### 2. Trainer
- Create training sessions (requires approval)
- View own sessions and center data
- Cannot approve own changes
- Cannot access financial reports

### 3. Manager
- Approve training sessions
- Manage assigned center(s)
- Access center revenue reports
- Full CRUD on center resources

### 4. Director
- Full system access
- View all centers and reports
- System configuration
- User management

## Utilities

### start_tennis.sh Script

Management utility with options:

```bash
./start_tennis.sh

1. Start Odoo (normal mode)
2. Start Odoo (DEV mode)
3. Install tennis_club module
4. Update tennis_club module
5. Stop Odoo
6. Create new database
7. List all databases
8. Drop database
```

### Telegram Bot Script

Standalone bot for client self-service:

```bash
python3 tennis_telegram_bot.py
```

Connects to Odoo via XML-RPC and provides client interface.

## Technical Details

### Technology Stack
- **Backend:** Odoo 18 (Python 3.10+)
- **Database:** PostgreSQL 12+
- **Integration:** Telegram Bot API
- **Queue:** OCA Queue Job framework
- **Dependencies:** hr, contacts, calendar, mail

### Key Design Patterns
- **Computed Fields:** Performance-optimized revenue calculations
- **Constraint Validation:** SQL + Python-level business rules
- **Multi-tenancy:** Record-level security via access rules
- **Workflow Management:** Status-based session lifecycle
- **Inheritance:** Extends hr.employee and res.partner models

### Financial Calculation Logic

```python
# Per training session
price = center_price × duration × client_count
trainer_cost = trainer_rate × duration
revenue = price - trainer_cost

# Balance deduction
client_balance -= price / client_count  # Split among clients
```

### Notification System

Two-stage notification process:
1. Create `telegram.notification` record
2. Send via Telegram API using TelegramHelper
3. Update record with success/failure status
4. Prevents duplicate notifications

## API & Integration

### Telegram Webhook Endpoint

```
POST /telegram/webhook
```

Receives updates from Telegram Bot API and processes commands.

### XML-RPC Interface

External applications can connect using Odoo's XML-RPC:

```python
import xmlrpc.client

url = 'http://localhost:8018'
db = 'tennis_db'
username = 'admin'
password = 'admin'

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})

models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
# Execute methods...
```

## Development

### Code Quality Standards
- Comprehensive docstrings for all methods
- Type hints in function signatures
- Extensive logging using `_logger`
- Error handling with ValidationError, UserError, AccessError
- Multi-language support with `translate=True`

### Running in Development Mode

```bash
./start_tennis.sh
# Select option 2 for DEV mode
```

Benefits:
- Auto-reload on code changes
- Enhanced logging
- Debug mode enabled

### Updating the Module

After code changes:

```bash
./start_tennis.sh
# Select option 4 to update tennis_club module
```

Or via Odoo UI:
1. Enable Developer Mode
2. Apps → tennis_club
3. Click "Upgrade"

## Troubleshooting

### Common Issues

**1. Module not loading:**
- Check `addons_path` in odoo.conf
- Verify file permissions
- Check logs in `logs/` directory

**2. Telegram notifications not sending:**
- Verify bot token in System Parameters
- Check `telegram.notification` records for errors
- Ensure internet connectivity
- Review Telegram API rate limits

**3. Permission errors:**
- Verify user is in correct security group
- Check record rules in Security → Record Rules
- Review access rights in ir.model.access.csv

**4. Balance not deducting:**
- Check session status (must be "confirmed")
- Verify `balance_deducted` flag is False
- Check client has sufficient balance
- Review error logs

**5. Court conflicts:**
- Check court schedule for overlapping bookings
- Verify working hours configuration
- Review validation constraints

## Logging

Logs are stored in `/home/vboxuser/tennis_project/logs/`

View recent errors:
```bash
tail -f logs/odoo.log | grep ERROR
```

## Backup & Restore

### Database Backup

```bash
pg_dump tennis_db > backups/tennis_db_$(date +%Y%m%d).sql
```

### Restore Database

```bash
psql -d tennis_db < backups/tennis_db_20250130.sql
```

## Contributing

### Branch Naming Convention
- Feature: `TENNIS-XXX_description`
- Bugfix: `FIX-XXX_description`
- Improvement: `IMP-XXX_description`

### Commit Message Format
```
[TAG] module: TICKET-ID Description

- Detail 1
- Detail 2
```

Tags: `[ADD]`, `[FIX]`, `[IMP]`, `[REF]`, `[REM]`

## Support

For issues and questions:
- Check logs in `logs/` directory
- Review Odoo documentation: https://www.odoo.com/documentation/18.0/
- OCA Queue Job: https://github.com/OCA/queue

## License

LGPL-3 - See LICENSE file for details

## Credits

**Author:** Natalia Stekolnikova
**Built with:** Odoo 18
**Telegram Integration:** python-telegram-bot library
**Queue System:** OCA Queue Job framework

---

**Version:** 18.0.1.0.0
**Last Updated:** 2025-01-30
**Status:** Production Ready
