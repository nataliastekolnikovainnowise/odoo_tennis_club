# -*- coding: utf-8 -*-
"""Tennis Court Schedule Model."""

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta


class CourtSchedule(models.Model):
    """Court Schedule - manages time slots for all courts."""
    
    _name = "court.schedule"
    _description = "Tennis Court Schedule"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "date desc, time_from desc"
    _rec_name = "display_name"
    
    # Core fields
    court_id = fields.Many2one(
        comodel_name="tennis.court",
        string="Court",
        required=True,
        ondelete="cascade",
        index=True,
    )
    
    center_id = fields.Many2one(
        comodel_name="tennis.center",
        string="Sports Center",
        related="court_id.center_id",
        store=True,
        index=True,
    )
    
    date = fields.Date(
        string="Date",
        required=True,
        index=True,
    )
    
    time_from = fields.Datetime(
        string="Start Time",
        required=True,
        index=True,
    )
    
    time_to = fields.Datetime(
        string="End Time",
        required=True,
    )
    
    # Relationships
    session_id = fields.Many2one(
        comodel_name="tennis.training.session",
        string="Training Session",
        ondelete="cascade",
        help="Linked training session (if booked)",
    )
    
    # Status
    status_id = fields.Many2one(
        comodel_name="court.schedule.status",
        string="Status",
        required=True,
        index=True,
        default=lambda self: self.env.ref('tennis_club.status_available', raise_if_not_found=False),
    )
    
    is_recurring = fields.Boolean(
        string="Is Recurring",
        default=False,
        help="Part of recurring schedule",
    )
    
    # Additional info
    notes = fields.Text(
        string="Notes",
        help="Additional notes (e.g., maintenance reason)",
    )
    
    blocked_reason = fields.Char(
        string="Block Reason",
        help="Reason for blocking this slot",
    )
    
    # Computed fields
    display_name = fields.Char(
        string="Display Name",
        compute="_compute_display_name",
        store=True,
    )
    
    duration = fields.Float(
        string="Duration (hours)",
        compute="_compute_duration",
        store=True,
    )
    
    trainer_id = fields.Many2one(
        comodel_name="hr.employee",
        string="Trainer",
        related="session_id.trainer_id",
        store=True,
    )
    
    # Constraints
    _sql_constraints = [
        (
            "check_time_order",
            "CHECK(time_to > time_from)",
            "End time must be after start time!",
        ),
    ]
    
    @api.depends("court_id", "date", "time_from", "time_to", "status_id")
    def _compute_display_name(self):
        """Compute display name."""
        for record in self:
            if record.court_id and record.date:
                time_str = ""
                if record.time_from:
                    time_str = record.time_from.strftime("%H:%M")
                    if record.time_to:
                        time_str += f"-{record.time_to.strftime('%H:%M')}"
                
                # Status icon
                status_icon = ""
                if record.status_id:
                    status_map = {
                        "Available": "🟢",
                        "Booked": "🔴",
                        "Blocked": "⚫",
                    }
                    status_icon = status_map.get(record.status_id.name, "")
                
                record.display_name = (
                    f"{status_icon} {record.court_id.name} - "
                    f"{record.date} {time_str}"
                )
            else:
                record.display_name = "New Schedule Slot"
    
    @api.depends("time_from", "time_to")
    def _compute_duration(self):
        """Compute duration in hours."""
        for record in self:
            if record.time_from and record.time_to:
                delta = record.time_to - record.time_from
                record.duration = delta.total_seconds() / 3600.0
            else:
                record.duration = 0.0
    
    @api.constrains("court_id", "date", "time_from", "time_to")
    def _check_no_overlap(self):
        """Ensure no overlapping slots for the same court."""
        for record in self:
            # Get available status
            available_status = self.env.ref('tennis_club.status_available', raise_if_not_found=False)
            
            overlapping = self.search([
                ("id", "!=", record.id),
                ("court_id", "=", record.court_id.id),
                ("date", "=", record.date),
                ("time_from", "<", record.time_to),
                ("time_to", ">", record.time_from),
                ("status_id", "!=", available_status.id if available_status else False),
            ])
            
            if overlapping:
                raise ValidationError(
                    f"Time slot overlaps with existing schedule:\n"
                    f"{overlapping[0].display_name}"
                )
    
    @api.constrains("time_from", "time_to", "court_id")
    def _check_working_hours(self):
        """Ensure slot is within court working hours."""
        for record in self:
            if not record.court_id or not record.time_from:
                continue
            
            center = record.court_id.center_id
            if not center:
                continue
            
            # Get working hours for this day
            weekday = record.date.weekday()
            working_hours = self.env["tennis.center.working.hours"].search([
                ("center_id", "=", center.id),
                ("day_of_week", "=", str(weekday)),
            ], limit=1)
            
            if not working_hours:
                continue
            
            # Check if slot is within working hours
            slot_time_from = record.time_from.time()
            slot_time_to = record.time_to.time()
            
            # Определяем правильные имена полей и типы
            hour_from_value = None
            hour_to_value = None
            
            # Пробуем разные варианты имен полей
            for attr_name in ['hour_from_time', 'hour_from', 'time_from']:
                if hasattr(working_hours, attr_name):
                    hour_from_value = getattr(working_hours, attr_name)
                    if hour_from_value:
                        break
            
            for attr_name in ['hour_to_time', 'hour_to', 'time_to']:
                if hasattr(working_hours, attr_name):
                    hour_to_value = getattr(working_hours, attr_name)
                    if hour_to_value:
                        break
            
            if not hour_from_value or not hour_to_value:
                # Если нет времени в working hours - пропускаем проверку
                continue
            
            # Конвертировать Float в time если нужно
            if isinstance(hour_from_value, float):
                # Float часы (например 9.5 = 09:30)
                hours = int(hour_from_value)
                minutes = int((hour_from_value - hours) * 60)
                hour_from = datetime.strptime(f"{hours:02d}:{minutes:02d}", "%H:%M").time()
            else:
                hour_from = hour_from_value
            
            if isinstance(hour_to_value, float):
                hours = int(hour_to_value)
                minutes = int((hour_to_value - hours) * 60)
                hour_to = datetime.strptime(f"{hours:02d}:{minutes:02d}", "%H:%M").time()
            else:
                hour_to = hour_to_value
            
            # Проверка
            if (slot_time_from < hour_from or slot_time_to > hour_to):
                raise ValidationError(
                    f"Schedule slot must be within working hours:\n"
                    f"{hour_from.strftime('%H:%M')} - {hour_to.strftime('%H:%M')}"
                )
    
    def action_block_slot(self):
        """Block this time slot."""
        self.ensure_one()
        booked_status = self.env.ref('tennis_club.status_booked', raise_if_not_found=False)
        blocked_status = self.env.ref('tennis_club.status_blocked', raise_if_not_found=False)
        
        if self.status_id == booked_status and self.session_id:
            raise ValidationError(
                "Cannot block a slot with an active training session!"
            )
        self.status_id = blocked_status
    
    def action_unblock_slot(self):
        """Unblock this time slot."""
        self.ensure_one()
        available_status = self.env.ref('tennis_club.status_available', raise_if_not_found=False)
        
        self.status_id = available_status
        self.blocked_reason = False
        self.notes = False
    
    @api.model
    def get_available_slots(self, court_id, date, duration=1.0):
        """Get list of available time slots for a court on a date.
        
        Args:
            court_id: ID of the court
            date: Date to check (datetime.date or string)
            duration: Duration in hours (default: 1.0)
            
        Returns:
            List of dicts with available time slots
        """
        court = self.env["tennis.court"].browse(court_id)
        if not court.exists():
            return []
        
        if isinstance(date, str):
            date = fields.Date.from_string(date)
        
        weekday = date.weekday()
        working_hours = self.env["tennis.center.working.hours"].search([
            ("center_id", "=", court.center_id.id),
            ("day_of_week", "=", str(weekday)),
        ], limit=1)
        
        if not working_hours:
            return []
        
        # Определяем правильные имена полей
        hour_from_value = None
        hour_to_value = None
        
        for attr_name in ['hour_from_time', 'hour_from', 'time_from']:
            if hasattr(working_hours, attr_name):
                hour_from_value = getattr(working_hours, attr_name)
                if hour_from_value:
                    break
        
        for attr_name in ['hour_to_time', 'hour_to', 'time_to']:
            if hasattr(working_hours, attr_name):
                hour_to_value = getattr(working_hours, attr_name)
                if hour_to_value:
                    break
        
        if not hour_from_value or not hour_to_value:
            return []
        
        # Конвертировать Float в time если нужно
        if isinstance(hour_from_value, float):
            hours = int(hour_from_value)
            minutes = int((hour_from_value - hours) * 60)
            hour_from = datetime.strptime(f"{hours:02d}:{minutes:02d}", "%H:%M").time()
        else:
            hour_from = hour_from_value
        
        if isinstance(hour_to_value, float):
            hours = int(hour_to_value)
            minutes = int((hour_to_value - hours) * 60)
            hour_to = datetime.strptime(f"{hours:02d}:{minutes:02d}", "%H:%M").time()
        else:
            hour_to = hour_to_value
        
        # Get available status
        available_status = self.env.ref('tennis_club.status_available', raise_if_not_found=False)
        
        # Get occupied slots
        occupied_slots = self.search([
            ("court_id", "=", court_id),
            ("date", "=", date),
            ("status_id", "!=", available_status.id if available_status else False),
        ])
        
        available = []
        
        start_time = datetime.combine(date, hour_from)
        end_time = datetime.combine(date, hour_to)
        
        current = start_time
        while current + timedelta(hours=duration) <= end_time:
            slot_end = current + timedelta(hours=duration)
            
            # Check if slot is free
            is_free = True
            for occupied in occupied_slots:
                if (current < occupied.time_to and slot_end > occupied.time_from):
                    is_free = False
                    break
            
            if is_free:
                available.append({
                    "time_from": current,
                    "time_to": slot_end,
                    "display": f"{current.strftime('%H:%M')} - {slot_end.strftime('%H:%M')}",
                })
            
            current += timedelta(hours=1)
        
        return available
