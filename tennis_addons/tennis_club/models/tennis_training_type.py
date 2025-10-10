# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class TennisTrainingType(models.Model):
    """Training type definition (Individual, Split, Group)."""
    
    _name = "tennis.training.type"
    _description = "Training Type"
    _order = "sequence, name"

    # Basic Information
    name = fields.Char(
        string="Name",
        required=True,
        translate=True,
        help="Training type name"
    )
    code = fields.Char(
        string="Code",
        required=True,
        help="Unique code (individual, split, group)"
    )
    
    # Client Limits
    min_clients = fields.Integer(
        string="Min Clients",
        required=True,
        default=1,
        help="Minimum number of clients required"
    )
    max_clients = fields.Integer(
        string="Max Clients",
        required=True,
        default=1,
        help="Maximum number of clients allowed"
    )
    
    # Additional Info
    description = fields.Text(
        string="Description",
        translate=True,
        help="Training type description"
    )
    color = fields.Integer(
        string="Color",
        help="Color for calendar view"
    )
    sequence = fields.Integer(
        string="Sequence",
        default=10,
        help="Order of display"
    )
    active = fields.Boolean(
        string="Active",
        default=True
    )
    
    # SQL Constraints
    _sql_constraints = [
        (
            "code_unique",
            "UNIQUE(code)",
            "Training type code must be unique!"
        ),
    ]

    @api.constrains("min_clients", "max_clients")
    def _check_clients_count(self):
        """Validate client count limits are logical."""
        for record in self:
            if record.min_clients <= 0:
                raise ValidationError(
                    "Minimum clients must be greater than 0!"
                )
            if record.max_clients < record.min_clients:
                raise ValidationError(
                    "Maximum clients cannot be less than minimum clients!"
                )
