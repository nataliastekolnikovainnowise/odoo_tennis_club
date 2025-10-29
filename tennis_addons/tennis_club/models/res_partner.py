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
        compute="_compute_training_count",
        help="Number of training sessions for this client",
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

    def _compute_training_count(self):
        """Compute number of training sessions."""
        for partner in self:
            partner.training_count = len(partner.training_session_ids)

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

        if "balance" in vals:
            for partner in self:
                partner.message_post(
                    body=_("Balance updated to %.2f by %s") % (
                        partner.balance,
                        self.env.user.name
                    ),
                    subtype_xmlid="mail.mt_note"
                )

        return result
