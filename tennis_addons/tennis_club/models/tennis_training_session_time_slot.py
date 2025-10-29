# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError

class TennisTrainingSessionTimeSlot(models.Model):
    """Time slots for recurring training sessions."""
    
    _name = "tennis.training.session.time.slot"
    _description = "Training Session Time Slot"
    _order = "time_from"
    
    session_id = fields.Many2one(
        "tennis.training.session",
        string="Training Session",
        required=True,
        ondelete="cascade"
    )
    
    time_from = fields.Datetime(
        string="Start Time",
        required=True,
        help="Start time for this slot"
    )
    
    time_to = fields.Datetime(
        string="End Time",
        required=True,
        help="End time for this slot"
    )
    
    duration = fields.Float(
        string="Duration (hours)",
        compute="_compute_duration",
        store=True
    )
    
    @api.depends("time_from", "time_to")
    def _compute_duration(self):
        """Calculate duration in hours."""
        for slot in self:
            if slot.time_from and slot.time_to:
                delta = slot.time_to - slot.time_from
                slot.duration = delta.total_seconds() / 3600.0
            else:
                slot.duration = 0.0
    
    @api.constrains("time_from", "time_to")
    def _check_times(self):
        """Validate time slot times."""
        for slot in self:
            if slot.time_to <= slot.time_from:
                raise ValidationError("End time must be after start time!")
