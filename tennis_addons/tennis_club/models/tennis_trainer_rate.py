# -*- coding: utf-8 -*-

from odoo import fields, models


class TennisTrainerRate(models.Model):
    """Trainer hourly rates by training type."""
    
    _name = "tennis.trainer.rate"
    _description = "Trainer Rate by Training Type"

    trainer_id = fields.Many2one(
        comodel_name="hr.employee",
        string="Trainer",
        required=True,
        domain="[('is_trainer', '=', True)]",
        ondelete="cascade"
    )
    
    training_type_id = fields.Many2one(
        comodel_name="tennis.training.type",
        string="Training Type",
        required=True,
        ondelete="cascade"
    )
    
    hourly_rate = fields.Monetary(
        string="Hourly Rate",
        currency_field="currency_id",
        required=True,
        help="Trainer's rate per hour for this training type"
    )
    
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id
    )
    
    _sql_constraints = [
        (
            "unique_trainer_training_type",
            "UNIQUE(trainer_id, training_type_id)",
            "Rate for this training type already exists for this trainer!"
        ),
    ]
