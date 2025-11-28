#!/usr/bin/env python3
"""
Tennis Club Telegram Bot
Handles user commands: /start, /balance, /trainings, /help
"""

import logging
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Настройки
BOT_TOKEN = "8249291715:AAHiYML9snDm8ixwbARqVtzqhN46Q1aT6VQ"
ODOO_URL = "http://localhost:8018"
ODOO_DB = "tennis_club_db"

# Логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    message = f"""
<b>Welcome!</b>
Your Chat ID: <code>{chat_id}</code>
Username: @{user.username if user.username else 'N/A'}

Contact your manager to link your account.
"""
    
    await update.message.reply_text(message, parse_mode='HTML')


async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /balance command."""
    chat_id = str(update.effective_chat.id)
    
    try:
        # Поиск клиента по telegram_chat_id через xmlrpc
        import xmlrpc.client
        
        common = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/common')
        uid = common.authenticate(ODOO_DB, 'admin', 'admin', {})
        
        if not uid:
            await update.message.reply_text("Authentication failed!")
            return
        
        models = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/object')
        
        # Найти клиента
        partner_ids = models.execute_kw(
            ODOO_DB, uid, 'admin',
            'res.partner', 'search',
            [[('telegram_chat_id', '=', chat_id)]]
        )
        
        if not partner_ids:
            await update.message.reply_text("You are not registered! Contact your manager.")
            return
        
        # Получить данные
        partner = models.execute_kw(
            ODOO_DB, uid, 'admin',
            'res.partner', 'read',
            [partner_ids[0]],
            {'fields': ['name', 'balance', 'training_count', 'completed_training_count']}
        )[0]
        
        message = f"""
<b>Your Balance</b>
<b>Name:</b> {partner['name']}
<b>Balance:</b> ${partner['balance']:.2f}
<b>Total trainings:</b> {partner['training_count']}
<b>Completed:</b> {partner['completed_training_count']}
"""
        
        await update.message.reply_text(message, parse_mode='HTML')
        
    except Exception as e:
        logger.error(f"Error in /balance: {e}")
        await update.message.reply_text(f"Error: {str(e)}")


async def trainings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /trainings command."""
    chat_id = str(update.effective_chat.id)
    
    try:
        import xmlrpc.client
        from datetime import datetime
        
        common = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/common')
        uid = common.authenticate(ODOO_DB, 'admin', 'admin', {})
        
        if not uid:
            await update.message.reply_text("Authentication failed!")
            return
        
        models = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/object')
        
        # Найти клиента
        partner_ids = models.execute_kw(
            ODOO_DB, uid, 'admin',
            'res.partner', 'search',
            [[('telegram_chat_id', '=', chat_id)]]
        )
        
        if not partner_ids:
            await update.message.reply_text("Tennis Club Bot: You are not registered! Contact your manager.")
            return
        
        partner_id = partner_ids[0]
        
        # Найти грядущие тренировки
        today = datetime.now().strftime('%Y-%m-%d')
        
        session_ids = models.execute_kw(
            ODOO_DB, uid, 'admin',
            'tennis.training.session', 'search',
            [[
                ('client_ids', 'in', partner_id),
                ('date', '>=', today),
                ('status', 'in', ['confirmed', 'draft'])
            ]],
            {'order': 'date asc, time_from asc', 'limit': 10}
        )
        
        if not session_ids:
            await update.message.reply_text("<b>No upcoming trainings</b>", parse_mode='HTML')
            return
        
        # Получить детали
        sessions = models.execute_kw(
            ODOO_DB, uid, 'admin',
            'tennis.training.session', 'read',
            [session_ids],
            {'fields': ['name', 'date', 'time_from', 'time_to', 'center_id', 'court_id', 'trainer_id', 'training_type_id', 'status']}
        )
        
        message = "<b>🎾 Your Upcoming Trainings</b>\n\n"
        
        for s in sessions:
            # Форматируем время
            time_from = datetime.fromisoformat(s['time_from']).strftime('%H:%M')
            time_to = datetime.fromisoformat(s['time_to']).strftime('%H:%M')
            date_str = datetime.fromisoformat(s['date']).strftime('%d.%m.%Y')
            
            message += f"""
<b>{s['name']}</b>
📅 {date_str} {time_from}-{time_to}
📍 {s['center_id'][1]}
🎾 {s['court_id'][1]}
👤 {s['trainer_id'][1]}
🏸 {s['training_type_id'][1]}
---
"""
        
        await update.message.reply_text(message, parse_mode='HTML')
        
    except Exception as e:
        logger.error(f"Error in /trainings: {e}")
        await update.message.reply_text(f"Error: {str(e)}")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command."""
    message = """
<b>Tennis Club Bot</b>
/start - Start
/balance - Balance
/trainings - Trainings
/help - Help
"""
    await update.message.reply_text(message, parse_mode='HTML')


def main():
    """Start the bot."""
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("balance", balance))
    application.add_handler(CommandHandler("trainings", trainings))
    application.add_handler(CommandHandler("help", help_command))
    
    logger.info("Bot started!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
