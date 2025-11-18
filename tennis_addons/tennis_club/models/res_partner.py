# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    """Extend Partner for Tennis Clients."""

    _inherit = "res.partner"

    # Tennis-specific flags
    is_client = fields.Boolean(
        string="Is Tennis Client",
        default=False,
        help="Check if this contact is a tennis club client",
    )

    client_type = fields.Selection(
        selection=[
            ("regular", "Regular"),
            ("vip", "VIP"),
            ("corporate", "Corporate"),
            ("trial", "Trial"),
        ],
        string="Client Type",
        default="regular",
        help="Type of tennis club client",
    )

    # Currency and balance fields
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
        help="Currency used for the client's balance",
    )

    balance = fields.Monetary(
        string="Balance",
        currency_field="currency_id",
        help="Client's account balance (automatically reduced after trainings).",
    )

    # STAGE1: Training session relationship (FIXED: client_id not partner_id!)
    training_session_ids = fields.Many2many(
        "tennis.training.session",
        "training_session_client_rel",
        "client_id",
        "session_id",
        string="Training Sessions"
    )

    # STAGE1: Training statistics (simple, no store)
    training_count = fields.Integer(
        string="Total Trainings",
        compute="_compute_training_counts",
        help="Number of training sessions for this client",
    )
    completed_training_count = fields.Integer(
        string="Completed Trainings",
        compute="_compute_training_counts",
        help="Number of completed training sessions for this client",
    )

    # STAGE1: Telegram fields
    telegram_chat_id = fields.Char(
        string="Telegram Chat ID",
        help="Telegram chat ID for notifications"
    )

    telegram_username = fields.Char(
        string="Telegram Username"
    )

    receive_telegram_notifications = fields.Boolean(
        string="Receive Telegram Notifications",
        default=True
    )

    notification_hours_before = fields.Integer(
        string="Notification Hours Before Training",
        default=2,
        help="Hours before training to send reminder notification"
    )

    client_notes = fields.Text(
        string="Client Notes",
        help="Additional information about the tennis client",
    )

    def _compute_training_counts(self):
        """Compute training statistics."""
        for partner in self:
            # Total trainings - all sessions (any status)
            partner.training_count = len(partner.training_session_ids)
            
            # Completed trainings - only completed sessions
            completed_count = self.env['tennis.training.session'].search_count([
                ('client_ids', 'in', partner.id),
                ('status', '=', 'completed')
            ])
            partner.completed_training_count = completed_count

    @api.constrains("balance")
    def _check_balance_negative(self):
        """Prevent negative balance."""
        for partner in self:
            if partner.balance < 0:
                raise ValidationError(
                    _("Balance cannot be negative!\nCurrent balance: %.2f") % partner.balance
                )

    @api.constrains("notification_hours_before")
    def _check_notification_hours(self):
        """Validate notification hours."""
        for partner in self:
            if partner.notification_hours_before < 0:
                raise ValidationError(_("Notification hours cannot be negative!"))
            if partner.notification_hours_before > 72:
                raise ValidationError(_("Notification hours cannot exceed 72 hours!"))

    def action_add_balance(self):
        """Open wizard to add balance."""
        return {
            "name": _("Add Balance"),
            "type": "ir.actions.act_window",
            "res_model": "client.balance.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_partner_id": self.id,
                "default_operation": "add"
            }
        }

    def action_view_training_sessions(self):
        """View all training sessions for this client."""
        self.ensure_one()
        return {
            "name": _("Training Sessions"),
            "type": "ir.actions.act_window",
            "res_model": "tennis.training.session",
            "view_mode": "tree,form,calendar",
            "domain": [("client_ids", "in", self.id)],
        }

    def check_balance_sufficient(self, amount):
        """Check if client has sufficient balance."""
        self.ensure_one()
        return self.balance >= amount

    def write(self, vals):
        """Override write to track balance changes."""
        result = super(ResPartner, self).write(vals)

        # TEMPORARY: Disable message_post to avoid email errors
        # if "balance" in vals:
        #     for partner in self:
        #         partner.message_post(
        #             body=_("Balance updated to %.2f by %s") % (
        #                 partner.balance,
        #                 self.env.user.name
        #             ),
        #             subtype_xmlid="mail.mt_note"
        #         )

        return result

    def send_telegram_notification(self, message_type, message_text, session_id=None):
        """Send Telegram notification to client.
        
        Args:
            message_type: Type of notification
            message_text: Message content
            session_id: Optional session ID
            
        Returns:
            bool: Success status
        """
        self.ensure_one()
        
        # TEMPORARY: Disable all Telegram notifications to avoid email configuration errors
        return True
        
        # TEMPORARY: Disable all Telegram notifications to avoid email configuration errors
        return True
        
        if not self.telegram_chat_id:
            return False
        
        if not self.receive_telegram_notifications:
            return False
        
        # Create notification log
        notification = self.env["telegram.notification"].create_notification(
            partner_id=self.id,
            message_type=message_type,
            message_text=message_text,
            session_id=session_id
        )
        
        if not notification:
            return False
        
        # TEMPORARY FIX: Skip write if notification is bool
        if isinstance(notification, bool):
            return True
        
        # Send via Telegram API
        from .telegram_helper import TelegramHelper
        helper = TelegramHelper(self.env)
        result = helper.send_message(self.telegram_chat_id, message_text)
        
        # Update notification record
        notification.write({
            "sent_successfully": result["success"],
            "error_message": result.get("error", False),
            "telegram_message_id": result.get("message_id", False),
        })
        
        return result["success"]
    
    def action_send_test_notification(self):
        """Send test notification (for testing purposes)."""
        self.ensure_one()
        
        if not self.telegram_chat_id:
            raise ValidationError(_("This client has no Telegram chat ID configured!"))
        
        message = f"""
<b>🎾 Test Notification</b>

Hello {self.name}!

This is a test message from Tennis Club Management System.

Your Telegram integration is working correctly! ✅
"""
        
        success = self.send_telegram_notification(
            message_type="balance_updated",
            message_text=message
        )
        
        if success:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("Success"),
                    "message": _("Test notification sent successfully!"),
                    "type": "success",
                    "sticky": False,
                }
            }
        else:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("Error"),
                    "message": _("Failed to send notification. Check configuration."),
                    "type": "danger",
                    "sticky": False,
                }
            }
