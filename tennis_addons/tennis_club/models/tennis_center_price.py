# -*- coding: utf-8 -*-

from odoo import fields, models


class TennisCenterPrice(models.Model):
    """Training prices by center and type."""
    
    _name = "tennis.center.price"
    _description = "Center Price by Training Type"

    center_id = fields.Many2one(
        comodel_name="tennis.center",
        string="Center",
        required=True,
        ondelete="cascade"
    )
    
    training_type_id = fields.Many2one(
        comodel_name="tennis.training.type",
        string="Training Type",
        required=True,
        ondelete="cascade"
    )
    
    price = fields.Monetary(
        string="Price",
        currency_field="currency_id",
        required=True,
        help="Price per hour for this training type"
    )
    
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id
    )
    
    _sql_constraints = [
        (
            "unique_center_training_type",
            "UNIQUE(center_id, training_type_id)",
            "Price for this training type already exists in this center!"
        ),
    ]
