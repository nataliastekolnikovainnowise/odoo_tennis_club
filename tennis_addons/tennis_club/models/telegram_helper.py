# -*- coding: utf-8 -*-
"""Telegram Helper - utilities for sending messages."""

import requests
import logging
from odoo import _

_logger = logging.getLogger(__name__)


class TelegramHelper:
    """Helper class for Telegram API interactions."""
    
    def __init__(self, env):
        """Initialize with Odoo environment."""
        self.env = env
        # Get bot token from system parameters
        self.bot_token = env["ir.config_parameter"].sudo().get_param("tennis_club.telegram_bot_token")
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
    
    def send_message(self, chat_id, text, parse_mode="HTML"):
        """Send message to Telegram chat.
        
        Args:
            chat_id: Telegram chat ID
            text: Message text
            parse_mode: Format (HTML or Markdown)
            
        Returns:
            dict with success status and message_id or error
        """
        if not self.bot_token:
            _logger.error("Telegram bot token not configured!")
            return {"success": False, "error": "Bot token not configured"}
        
        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            result = response.json()
            
            if result.get("ok"):
                return {
                    "success": True,
                    "message_id": result["result"]["message_id"]
                }
            else:
                _logger.error(f"Telegram API error: {result}")
                return {
                    "success": False,
                    "error": result.get("description", "Unknown error")
                }
        except Exception as e:
            _logger.error(f"Exception sending Telegram message: {e}")
            return {"success": False, "error": str(e)}
    
    def format_booking_confirmation(self, session):
        """Format booking confirmation message."""
        message = f"""
<b>🎾 Training Booking Confirmed</b>

<b>Session:</b> {session.name}
<b>Date:</b> {session.date.strftime('%d.%m.%Y')}
<b>Time:</b> {session.time_from.strftime('%H:%M')} - {session.time_to.strftime('%H:%M')}
<b>Duration:</b> {session.duration} hours

<b>Location:</b>
📍 {session.center_id.name}
🎾 Court: {session.court_id.name}

<b>Trainer:</b> {session.trainer_id.name}
<b>Training Type:</b> {session.training_type_id.name}

See you on the court! 💪
"""
        return message.strip()
    
    def format_reminder(self, session, hours_before):
        """Format reminder message."""
        message = f"""
<b>⏰ Training Reminder</b>

Your training starts in <b>{hours_before} hours</b>!

<b>Date:</b> {session.date.strftime('%d.%m.%Y')}
<b>Time:</b> {session.time_from.strftime('%H:%M')} - {session.time_to.strftime('%H:%M')}

<b>Location:</b> {session.center_id.name}, Court {session.court_id.name}
<b>Trainer:</b> {session.trainer_id.name}

Don't forget your racket! 🎾
"""
        return message.strip()
    
    def format_balance_info(self, partner):
        """Format balance information message."""
        message = f"""
<b>💰 Your Balance</b>

<b>Current Balance:</b> ${partner.balance:.2f}

<b>Training Statistics:</b>
- Total trainings: {partner.training_count}
- Completed: {partner.completed_training_count}

Contact your manager to top up your balance.
"""
        return message.strip()
    
    def format_upcoming_trainings(self, sessions):
        """Format upcoming trainings list."""
        if not sessions:
            return "<b>📅 Upcoming Trainings</b>\n\nYou have no upcoming trainings scheduled."
        
        message = "<b>📅 Your Upcoming Trainings</b>\n\n"
        
        for session in sessions:
            message += f"""
<b>{session.date.strftime('%d.%m.%Y')} {session.time_from.strftime('%H:%M')}</b>
📍 {session.center_id.name}, Court {session.court_id.name}
👨‍🏫 {session.trainer_id.name}
⏱ {session.duration}h - {session.training_type_id.name}

"""
        
        return message.strip()
    
    def format_cancellation(self, session):
        """Format cancellation message."""
        message = f"""
<b>❌ Training Cancelled</b>

The following training has been cancelled:

<b>Date:</b> {session.date.strftime('%d.%m.%Y')}
<b>Time:</b> {session.time_from.strftime('%H:%M')} - {session.time_to.strftime('%H:%M')}
<b>Location:</b> {session.center_id.name}, Court {session.court_id.name}

Your balance has been refunded if payment was made.
"""
        return message.strip()
