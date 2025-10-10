# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class TennisCenterWorkingHours(models.Model):
    """Tennis Center Working Hours model."""
    
    _name = "tennis.center.working.hours"
    _description = "Tennis Center Working Hours"
    _order = "center_id, day_of_week, time_from"

    center_id = fields.Many2one(
        comodel_name="tennis.center",
        string="Center",
        required=True,
        ondelete="cascade",
        help="Tennis center"
    )
    
    day_of_week = fields.Selection(
        selection=[
            ("0", "Monday"),
            ("1", "Tuesday"),
            ("2", "Wednesday"),
            ("3", "Thursday"),
            ("4", "Friday"),
            ("5", "Saturday"),
            ("6", "Sunday"),
        ],
        string="Day of Week",
        required=True,
        help="Day of the week"
    )
    
    time_from = fields.Float(
        string="From",
        required=True,
        help="Opening time in 24h format (e.g., 9.0 for 09:00, 9.5 for 09:30)"
    )
    
    time_to = fields.Float(
        string="To",
        required=True,
        help="Closing time in 24h format (e.g., 21.0 for 21:00, 18.5 for 18:30)"
    )
    
    is_closed = fields.Boolean(
        string="Closed",
        default=False,
        help="Check if center is closed on this day"
    )
    
    _sql_constraints = [
        (
            "check_hours_order",
            "CHECK(time_to > time_from)",
            "Closing time must be after opening time!"
        ),
        (
            "unique_center_day",
            "UNIQUE(center_id, day_of_week)",
            "Working hours already defined for this day!"
        ),
    ]
    
    @api.constrains("time_from", "time_to")
    def _check_hours_range(self):
        """Validate hours are within 0-24 range."""
        for record in self:
            if not (0 <= record.time_from < 24):
                raise ValidationError("Opening time must be between 0 and 24!")
            if not (0 < record.time_to <= 24):
                raise ValidationError("Closing time must be between 0 and 24!")
            if record.time_from >= record.time_to:
                raise ValidationError("Closing time must be after opening time!")
