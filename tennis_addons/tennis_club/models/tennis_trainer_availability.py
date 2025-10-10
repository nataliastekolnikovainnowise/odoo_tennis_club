# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class TennisTrainerAvailability(models.Model):
    """Trainer Availability Schedule."""
    
    _name = "tennis.trainer.availability"
    _description = "Trainer Availability"
    _order = "trainer_id, date, time_from"

    trainer_id = fields.Many2one(
        comodel_name="hr.employee",
        string="Trainer",
        required=True,
        domain="[('is_trainer', '=', True)]",
        ondelete="cascade",
        help="Tennis trainer"
    )
    
    date = fields.Date(
        string="Date",
        required=True,
        help="Date of availability"
    )
    
    time_from = fields.Datetime(
        string="From",
        required=True,
        help="Start time"
    )
    
    time_to = fields.Datetime(
        string="To",
        required=True,
        help="End time"
    )
    
    is_available = fields.Boolean(
        string="Available",
        default=True,
        help="Trainer is available during this time"
    )
    
    notes = fields.Text(
        string="Notes",
        help="Additional notes about availability"
    )
    
    _sql_constraints = [
        (
            "check_time_order",
            "CHECK(time_to > time_from)",
            "End time must be after start time!"
        ),
    ]
    
    @api.constrains("time_from", "time_to", "date")
    def _check_times(self):
        """Validate that times are on the same date."""
        for record in self:
            if record.time_from.date() != record.date:
                raise ValidationError("Start time must be on the selected date!")
            if record.time_to.date() != record.date:
                raise ValidationError("End time must be on the selected date!")
            if record.time_from >= record.time_to:
                raise ValidationError("End time must be after start time!")
    
    @api.constrains("trainer_id", "date", "time_from", "time_to")
    def _check_overlap(self):
        """Check for overlapping availability records."""
        for record in self:
            overlapping = self.search([
                ("trainer_id", "=", record.trainer_id.id),
                ("date", "=", record.date),
                ("id", "!=", record.id),
                "|",
                "&", ("time_from", "<=", record.time_from), ("time_to", ">", record.time_from),
                "&", ("time_from", "<", record.time_to), ("time_to", ">=", record.time_to),
            ])
            if overlapping:
                raise ValidationError(
                    f"Overlapping availability found for {record.trainer_id.name} on {record.date}!"
                )
    
    def name_get(self):
        """Custom display name."""
        result = []
        for record in self:
            status = "Available" if record.is_available else "Unavailable"
            name = f"{record.trainer_id.name} - {record.date} ({record.time_from.strftime('%H:%M')}-{record.time_to.strftime('%H:%M')}): {status}"
            result.append((record.id, name))
        return result
