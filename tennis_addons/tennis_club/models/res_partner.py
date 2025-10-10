# -*- coding: utf-8 -*-
from odoo import fields, models


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

    client_notes = fields.Text(
        string="Client Notes",
        help="Additional information about the tennis client",
    )

    training_count = fields.Integer(
        string="Trainings",
        compute="_compute_training_count",
        help="Number of training sessions for this client",
    )

    def _compute_training_count(self):
        """Compute number of trainings (will be implemented with training sessions)."""
        for client in self:
            client.training_count = 0
