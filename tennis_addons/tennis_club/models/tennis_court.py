# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class TennisCourt(models.Model):
    """Tennis Court model."""
    
    _name = "tennis.court"
    _description = "Tennis Court"
    _order = "center_id, name"

    name = fields.Char(
        string="Court Name",
        required=True,
        help="Court name or number"
    )
    
    code = fields.Char(
        string="Code",
        required=True,
        help="Unique code for the court"
    )
    
    center_id = fields.Many2one(
        comodel_name="tennis.center",
        string="Center",
        required=True,
        ondelete="cascade",
        help="Tennis center where this court is located"
    )
    
    surface_type = fields.Selection(
        selection=[
            ('hard', 'Hard Court'),
            ('clay', 'Clay Court'),
            ('grass', 'Grass Court'),
            ('carpet', 'Carpet'),
        ],
        string="Surface Type",
        default='hard',
        required=True,
        help="Type of court surface"
    )
    
    court_type = fields.Selection(
        selection=[
            ('indoor', 'Indoor'),
            ('outdoor', 'Outdoor'),
        ],
        string="Court Type",
        default='outdoor',
        required=True,
        help="Indoor or outdoor court"
    )
    
    has_lighting = fields.Boolean(
        string="Has Lighting",
        default=True,
        help="Court has lighting for evening play"
    )
    
    active = fields.Boolean(
        string="Active",
        default=True,
        help="Court is active and available for booking"
    )
    
    notes = fields.Text(
        string="Notes",
        help="Additional information about the court"
    )
    
    _sql_constraints = [
        ('code_unique', 'UNIQUE(code)', 'Court code must be unique!'),
    ]
    
    @api.constrains('name', 'center_id')
    def _check_name_center_unique(self):
        """Ensure court name is unique within a center"""
        for record in self:
            existing = self.search([
                ('name', '=', record.name),
                ('center_id', '=', record.center_id.id),
                ('id', '!=', record.id)
            ])
            if existing:
                raise ValidationError(
                    f'Court "{record.name}" already exists in {record.center_id.name}!'
                )
