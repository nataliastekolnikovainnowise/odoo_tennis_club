# -*- coding: utf-8 -*-
"""Telegram Notification Model."""
from odoo import api, fields, models
import logging

_logger = logging.getLogger(__name__)


class TelegramNotification(models.Model):
    """Log of Telegram notifications sent to clients."""
    
    _name = "telegram.notification"
    _description = "Telegram Notification Log"
    _order = "create_date desc"
    _rec_name = "message_type"
    
    partner_id = fields.Many2one(
        "res.partner",
        string="Client",
        required=True,
        ondelete="cascade",
        index=True,
        help="Client who received the notification"
    )
    
    telegram_chat_id = fields.Char(
        string="Telegram Chat ID",
        required=True,
        help="Telegram chat ID where message was sent"
    )
    
    message_type = fields.Selection(
        selection=[
            ("booking_confirmation", "Booking Confirmation"),
            ("booking_reminder", "Training Reminder"),
            ("booking_cancelled", "Booking Cancelled"),
            ("balance_low", "Low Balance Warning"),
            ("balance_updated", "Balance Updated"),
        ],
        string="Message Type",
        required=True,
        help="Type of notification sent"
    )
    
    session_id = fields.Many2one(
        "tennis.training.session",
        string="Training Session",
        ondelete="set null",
        help="Related training session (if applicable)"
    )
    
    message_text = fields.Text(
        string="Message Content",
        required=True,
        help="Content of the notification message"
    )
    
    sent_successfully = fields.Boolean(
        string="Sent Successfully",
        default=False,
        help="Whether the message was successfully delivered"
    )
    
    error_message = fields.Text(
        string="Error Message",
        help="Error details if sending failed"
    )
    
    sent_date = fields.Datetime(
        string="Sent Date",
        default=fields.Datetime.now,
        required=True,
        help="When the notification was sent"
    )
    
    @api.model
    def create_notification(self, partner_id, message_type, message_text, session_id=None):
        """Create notification record.
        
        Args:
            partner_id: res.partner ID
            message_type: Type of notification
            message_text: Message content
            session_id: Optional training session ID
            
        Returns:
            telegram.notification record
        """
        partner = self.env["res.partner"].browse(partner_id)
        
        if not partner.telegram_chat_id:
            _logger.warning(f"Partner {partner.name} has no telegram_chat_id")
            return False
        
        vals = {
            "partner_id": partner_id,
            "telegram_chat_id": partner.telegram_chat_id,
            "message_type": message_type,
            "message_text": message_text,
            "session_id": session_id,
            "sent_successfully": False,
        }
        return self.create(vals)
