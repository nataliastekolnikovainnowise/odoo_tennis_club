# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import ValidationError
import re


class TennisCenter(models.Model):
    """Tennis Center Model."""
    
    _name = "tennis.center"
    _description = "Tennis Center"
    _order = "name"

    name = fields.Char(
        string="Name",
        required=True,
        help="Tennis center name"
    )
    
    code = fields.Char(
        string="Code",
        required=True,
        help="Unique center code"
    )
    
    manager_id = fields.Many2one(
        comodel_name="hr.employee",
        string="Manager",
        help="Center manager"
    )
    
    phone = fields.Char(
        string="Phone",
        help="Contact phone number"
    )
    
    email = fields.Char(
        string="Email",
        help="Contact email"
    )
    
    address = fields.Text(
        string="Address",
        help="Physical address"
    )
    
    notes = fields.Text(
        string="Notes",
        help="Additional notes"
    )
    
    working_hours_ids = fields.One2many(
        comodel_name="tennis.center.working.hours",
        inverse_name="center_id",
        string="Working Hours",
        help="Center working hours by day of week"
    )
    
    court_ids = fields.One2many(
        comodel_name="tennis.court",
        inverse_name="center_id",
        string="Courts",
        help="Tennis courts in this center"
    )
    
    courts_count = fields.Integer(
        string="Courts Count",
        compute="_compute_courts_count",
        store=True,
        help="Number of courts"
    )
    
    price_ids = fields.One2many(
        comodel_name="tennis.center.price",
        inverse_name="center_id",
        string="Prices",
        help="Training prices in this center"
    )
    
    _sql_constraints = [
        ("code_unique", "UNIQUE(code)", "Center code must be unique!"),
    ]
    
    @api.depends("court_ids")
    def _compute_courts_count(self):
        """Compute number of courts."""
        for center in self:
            center.courts_count = len(center.court_ids)
    
    @api.constrains("email")
    def _check_email(self):
        """Validate email format."""
        for center in self:
            if center.email:
                email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                if not re.match(email_pattern, center.email):
                    raise ValidationError(f"Invalid email format: {center.email}")
    
    @api.constrains("phone")
    def _check_phone(self):
        """Validate phone format."""
        for center in self:
            if center.phone:
                phone_pattern = r'^\+?[0-9]{10,15}$'
                if not re.match(phone_pattern, center.phone):
                    raise ValidationError(
                        f"Invalid phone format: {center.phone}. Must be 10-15 digits."
                    )
