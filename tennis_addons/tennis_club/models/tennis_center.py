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
    

    # Revenue tracking
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
    )

    total_revenue = fields.Monetary(
        string="Total Revenue",
        compute="_compute_revenues",
        currency_field="currency_id",
        help="Total revenue from all trainers in this center",
    )

    current_month_revenue = fields.Monetary(
        string="Revenue (Current Month)",
        compute="_compute_revenues",
        currency_field="currency_id",
        help="Revenue for current month from all trainers",
    )

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
    
    def _compute_revenues(self):
        """Compute total and current month revenue for center."""
        from datetime import datetime
        for center in self:
            # Get all trainers in this center
            trainers = self.env["hr.employee"].search([
                ("is_trainer", "=", True),
                ("center_id", "=", center.id),
            ])
            
            # Total revenue
            total = 0.0
            current_month = 0.0
            
            # First day of current month
            today = datetime.today()
            first_day = today.replace(day=1)
            
            for trainer in trainers:
                # All completed sessions
                all_sessions = self.env["tennis.training.session"].search([
                    ("trainer_id", "=", trainer.id),
                    ("status", "=", "completed"),
                ])
                total += sum(all_sessions.mapped("revenue"))
                
                # Current month sessions
                month_sessions = self.env["tennis.training.session"].search([
                    ("trainer_id", "=", trainer.id),
                    ("status", "=", "completed"),
                    ("date", ">=", first_day.date()),
                    ("date", "<=", today.date()),
                ])
                current_month += sum(month_sessions.mapped("revenue"))
            
            center.total_revenue = total
            center.current_month_revenue = current_month

        """Validate phone format."""
        for center in self:
            if center.phone:
                phone_pattern = r'^\+?[0-9]{10,15}$'
                if not re.match(phone_pattern, center.phone):
                    raise ValidationError(
                        f"Invalid phone format: {center.phone}. Must be 10-15 digits."
                    )
