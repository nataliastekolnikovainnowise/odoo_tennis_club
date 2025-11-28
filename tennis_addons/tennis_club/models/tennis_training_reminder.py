# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)


class TennisTrainingReminder(models.Model):
    _name = 'tennis.training.reminder'
    _description = 'Training Session Reminder'
    _order = 'reminder_time desc'

    session_id = fields.Many2one(
        'tennis.training.session',
        string='Training Session',
        required=True,
        ondelete='cascade',
    )
    
    client_id = fields.Many2one(
        'res.partner',
        string='Client',
        required=True,
    )
    
    reminder_time = fields.Datetime(
        string='Reminder Time',
        required=True,
        help='When to send the reminder',
    )
    
    sent = fields.Boolean(
        string='Sent',
        default=False,
    )
    
    sent_date = fields.Datetime(
        string='Sent Date',
        readonly=True,
    )
    
    error_message = fields.Text(
        string='Error Message',
        readonly=True,
    )

    @api.model
    def _cron_send_pending_reminders(self):
        """Cron job method to send pending reminders"""
        _logger.info("=== Starting reminder cron job ===")
        
        now = fields.Datetime.now()
        pending_reminders = self.search([
            ('sent', '=', False),
            ('reminder_time', '<=', now),
        ])
        
        _logger.info(f"Found {len(pending_reminders)} pending reminders")
        
        for reminder in pending_reminders:
            try:
                self._send_reminder(reminder)
            except Exception as e:
                _logger.error(f"Failed to send reminder {reminder.id}: {str(e)}")
                reminder.write({'error_message': str(e)})
        
        _logger.info("=== Reminder cron job completed ===")
    
    def _send_reminder(self, reminder):
        """Send a single reminder via Telegram"""
        session = reminder.session_id
        client = reminder.client_id
        
        if not client.telegram_chat_id:
            _logger.warning(f"Client {client.name} has no telegram_chat_id")
            return
        
        message = (
            f"🔔 <b>Training Reminder!</b>\n\n"
            f"📅 Date: {session.time_from.strftime('%d.%m.%Y')}\n"
            f"⏰ Time: {session.time_from.strftime('%H:%M')} - "
            f"{session.time_to.strftime('%H:%M')}\n"
            f"🎾 Type: {session.training_type_id.name}\n"
            f"👨‍🏫 Trainer: {session.trainer_id.name}\n"
            f"🏢 Center: {session.center_id.name}\n"
            f"🎯 Court: {session.court_id.name}\n\n"
            f"{int(session.reminder_hours * 60)} minutes until training starts!\n"
            f"Don't forget to prepare! 💪"
        )
        
        success = client.send_telegram_notification(
            message_type='booking_reminder',
            message_text=message,
            session_id=session.id
        )
        
        if success:
            reminder.write({
                'sent': True,
                'sent_date': fields.Datetime.now(),
            })
            _logger.info(f"Reminder sent to {client.name} for session {session.name}")
        else:
            raise Exception("Failed to send telegram notification")


class TennisTrainingSession(models.Model):
    _inherit = 'tennis.training.session'

    reminder_ids = fields.One2many(
        'tennis.training.reminder',
        'session_id',
        string='Reminders',
    )
    
    reminder_hours = fields.Float(
        string='Reminder Hours Before',
        default=0.083,
        help='Send reminder N hours before training starts',
    )

    def _create_reminders(self):
        """Create reminder records for all clients"""
        self.ensure_one()
        
        if self.status != 'confirmed':
            return
        
        self.reminder_ids.unlink()
        
        reminder_time = self.time_from - timedelta(hours=self.reminder_hours)
        
        if reminder_time <= fields.Datetime.now():
            _logger.info(f"Reminder time is in past for {self.name}")
            return
        
        for client in self.client_ids:
            if client.telegram_chat_id:
                self.env['tennis.training.reminder'].sudo().create({
                    'session_id': self.id,
                    'client_id': client.id,
                    'reminder_time': reminder_time,
                })

    def write(self, vals):
        res = super().write(vals)
        
        if any(key in vals for key in ['time_from', 'client_ids', 'status', 'reminder_hours']):
            for session in self:
                if session.status == 'confirmed':
                    session.sudo()._create_reminders()
        
        return res

    @api.model_create_multi
    def create(self, vals_list):
        sessions = super().create(vals_list)
        
        for session in sessions:
            if session.status == 'confirmed':
                session._create_reminders()
        
        return sessions
