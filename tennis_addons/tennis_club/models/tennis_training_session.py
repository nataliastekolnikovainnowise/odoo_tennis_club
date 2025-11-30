# -*- coding: utf-8 -*-

from odoo.tools.translate import _
from datetime import datetime, timedelta
from odoo import api, fields, models
from odoo.exceptions import ValidationError, UserError, AccessError
import logging

_logger = logging.getLogger(__name__)


class TennisTrainingSession(models.Model):
    """Tennis Training Session."""
    
    _name = "tennis.training.session"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Tennis Training Session"
    _order = "date desc, time_from desc"

    name = fields.Char(
        string="Reference",
        required=True,
        copy=False,
        readonly=True,
        default="New"
    )
    
    center_id = fields.Many2one(
        comodel_name="tennis.center",
        string="Center",
        required=True,
        default=lambda self: self._default_center_id(),
        help="Tennis center"
    )

    court_id = fields.Many2one(
        comodel_name="tennis.court",
        string="Court",
        required=True,
        domain="[('center_id', '=', center_id)]",
        help="Tennis court"
    )

    trainer_id = fields.Many2one(
        comodel_name="hr.employee",
        string="Trainer",
        required=True,
        default=lambda self: self._default_trainer_id(),
        domain="[('is_trainer', '=', True)]",
        help="Trainer (must be from same center)"
    )
    
    client_ids = fields.Many2many(
        comodel_name="res.partner",
        relation="training_session_client_rel",
        column1="session_id",
        column2="client_id",
        string="Clients",
        domain="[('is_client', '=', True)]",
        help="Training clients"
    )
    
    training_type_id = fields.Many2one(
        comodel_name="tennis.training.type",
        string="Training Type",
        required=True,
        help="Type of training"
    )
    
    date = fields.Date(
        string="Date",
        required=True,
        default=fields.Date.context_today,
        help="Training date"
    )
    
    time_from = fields.Datetime(
        string="Start Time",
        required=True,
        help="Training start time"
    )
    
    time_to = fields.Datetime(
        string="End Time",
        required=True,
        help="Training end time"
    )
    
    duration = fields.Float(
        string="Duration (hours)",
        compute="_compute_duration",
        store=True,
        help="Training duration in hours"
    )
    
    price = fields.Monetary(
        string="Price",
        currency_field="currency_id",
        compute="_compute_financial",
        store=True,
        help="Training price (charged to clients)"
    )
    
    trainer_cost = fields.Monetary(
        string="Trainer Cost",
        currency_field="currency_id",
        compute="_compute_financial",
        store=True,
        help="Cost paid to trainer"
    )
    
    revenue = fields.Monetary(
        string="Revenue (Profit)",
        currency_field="currency_id",
        compute="_compute_financial",
        store=True,
        help="Profit: price minus trainer cost"
    )
    
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id
    )
    
    status = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("pending_approval", "Pending Approval"),
            ("confirmed", "Confirmed"),
            ("completed", "Completed"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
        default="draft",
        required=True,
        tracking=True,
        help="Training session status"
    )
    
    payment_status = fields.Selection(
        selection=[
            ("unpaid", "Unpaid"),
            ("partial", "Partially Paid"),
            ("paid", "Paid"),
        ],
        string="Payment Status",
        default="unpaid",
        required=True,
        help="Payment status"
    )
    
    needs_approval = fields.Boolean(
        string="Needs Approval",
        default=False,
        help="Session needs manager approval"
    )
    
    approved_by = fields.Many2one(
        comodel_name="hr.employee",
        string="Approved By",
        help="Manager who approved this session",
        readonly=True
    )
    
    approval_date = fields.Datetime(
        string="Approval Date",
        readonly=True,
        help="Date when session was approved"
    )
    
    created_by_trainer = fields.Boolean(
        string="Created by Trainer",
        default=False,
        help="True if session was created by trainer (requires approval)"
    )
    
    is_current_user_trainer = fields.Boolean(
        string="Is Current User Trainer",
        compute="_compute_is_current_user_trainer",
        help="Check if current user is a trainer"
    )
    
    notes = fields.Text(
        string="Notes",
        help="Additional notes"
    )
    
    balance_deducted = fields.Boolean(
        string="Balance Deducted",
        default=False,
        readonly=True,
        help="Indicates if client balance has been deducted"
    )
    
    is_recurring = fields.Boolean(
        string="Recurring Session",
        default=False,
        help="Is this a recurring training session?"
    )

    recurrence_pattern = fields.Selection(
        selection=[
            ("daily", "Daily"),
            ("weekly", "Weekly"),
            ("monthly", "Monthly"),
        ],
        string="Recurrence Pattern",
        help="How often should this session repeat?"
    )

    recurrence_interval = fields.Integer(
        string="Repeat Every",
        default=1,
        help="Repeat every X days/weeks/months"
    )

    recurrence_days = fields.Selection(
        selection=[
            ("monday", "Monday"),
            ("tuesday", "Tuesday"),
            ("wednesday", "Wednesday"),
            ("thursday", "Thursday"),
            ("friday", "Friday"),
            ("saturday", "Saturday"),
            ("sunday", "Sunday"),
        ],
        string="Day of Week",
        help="For weekly recurrence - which day?"
    )

    recurrence_end_date = fields.Date(
        string="Recurrence End Date",
        help="Until when should sessions be created?"
    )

    skip_weekends = fields.Boolean(
        string="Skip Weekends",
        default=True,
        help="Skip Saturday and Sunday when generating recurring sessions"
    )

    time_slot_ids = fields.One2many(
        "tennis.training.session.time.slot",
        "session_id",
        string="Time Slots",
        help="Multiple time slots for recurring sessions"
    )

    parent_recurring_session_id = fields.Many2one(
        "tennis.training.session",
        string="Parent Recurring Session",
        help="Reference to parent recurring session"
    )

    _sql_constraints = [
        (
            "check_time_order",
            "CHECK(time_to > time_from)",
            "End time must be after start time!"
        ),
    ]
    
    @api.model
    def _default_center_id(self):
        """Default center to trainer's center if current user is trainer."""
        # Search without is_trainer in domain to avoid hr_employee_public issues
        employees = self.env["hr.employee"].with_context(active_test=False).search([
            ("user_id", "=", self.env.uid)
        ])

        for emp in employees:
            # Access is_trainer field directly on the main table
            if emp.sudo().is_trainer and emp.sudo().center_id:
                return emp.center_id.id

        return False

    @api.model
    def _default_trainer_id(self):
        """Default trainer to current user if they are a trainer."""
        # Search without is_trainer in domain to avoid hr_employee_public issues
        employees = self.env["hr.employee"].with_context(active_test=False).search([
            ("user_id", "=", self.env.uid)
        ])

        for emp in employees:
            # Access is_trainer field directly on the main table
            if emp.sudo().is_trainer:
                return emp.id

        return False

    def _domain_center_id(self):
        """Domain for center - trainers see only their center."""
        # Not used anymore - removed from field definition
        return []

    def _domain_trainer_id(self):
        """Domain for trainer - trainers see only themselves."""
        # Not used anymore - using static domain instead
        return [('is_trainer', '=', True)]

    @api.depends_context('uid')
    def _compute_is_current_user_trainer(self):
        """Check if current user is a trainer."""
        # Search without is_trainer in domain to avoid hr_employee_public issues
        employees = self.env["hr.employee"].with_context(active_test=False).search([
            ("user_id", "=", self.env.uid)
        ])

        is_trainer = False
        for emp in employees:
            if emp.sudo().is_trainer:
                is_trainer = True
                break

        for session in self:
            session.is_current_user_trainer = is_trainer
    
    @api.model
    def create(self, vals):
        """Generate sequence number and check if created by trainer."""
        if vals.get("name", "New") == "New":
            vals["name"] = self.env["ir.sequence"].next_by_code("tennis.training.session") or "New"

        # Search without is_trainer in domain to avoid hr_employee_public issues
        employees = self.env["hr.employee"].with_context(active_test=False).search([
            ("user_id", "=", self.env.uid)
        ])

        for emp in employees:
            if emp.sudo().is_trainer:
                vals["created_by_trainer"] = True
                vals["needs_approval"] = True
                vals["status"] = "pending_approval"
                if "trainer_id" not in vals:
                    vals["trainer_id"] = emp.id
                break

        return super().create(vals)
    
    def write(self, vals):
        """Check if modifications by trainer need approval."""
        import logging
        _logger = logging.getLogger(__name__)
        
        important_fields = ["date", "time_from", "time_to", "court_id", "client_ids", "training_type_id"]

        # Search without is_trainer in domain to avoid hr_employee_public issues
        employees = self.env["hr.employee"].with_context(active_test=False).search([
            ("user_id", "=", self.env.uid)
        ])

        is_trainer = any(emp.sudo().is_trainer for emp in employees)
        if is_trainer:
            if any(field in vals for field in important_fields):
                vals["needs_approval"] = True
                vals["status"] = "pending_approval"
        
        if "status" in vals and vals["status"] == "confirmed":
            for record in self:
                if not record.balance_deducted:
                    record._check_and_deduct_balance()
        
        # Save old state for notification logic
        old_clients_map = {}
        for record in self:
            old_clients_map[record.id] = record.client_ids.ids
        
        old_status_map = {record.id: record.status for record in self}
        
        # Perform the write
        result = super().write(vals)
        
        # Check if status changed to confirmed or clients were added
        status_changed_to_confirmed = "status" in vals and vals["status"] == "confirmed"
        clients_changed = "client_ids" in vals
        
        _logger.info(f"Write: status_changed={status_changed_to_confirmed}, clients_changed={clients_changed}")
        
        # Send notifications after write
        for record in self:
            if record.status == "confirmed":
                # If clients were added
                if clients_changed:
                    old_clients = old_clients_map.get(record.id, [])
                    new_clients = record.client_ids.ids
                    added_clients = list(set(new_clients) - set(old_clients))
                    
                    if added_clients:
                        record._send_booking_confirmation(added_clients)
                
                # If status changed to confirmed, notify all clients
                elif status_changed_to_confirmed and record.client_ids:
                    record._send_booking_confirmation(record.client_ids.ids)
        
        return result
    
    @api.depends("time_from", "time_to")
    def _compute_duration(self):
        """Compute training duration in hours."""
        for session in self:
            if session.time_from and session.time_to:
                delta = session.time_to - session.time_from
                session.duration = delta.total_seconds() / 3600
            else:
                session.duration = 0.0
    
    @api.depends("training_type_id", "trainer_id", "center_id", "duration")
    def _compute_financial(self):
        """Compute price, trainer cost and revenue."""
        for session in self:
            if session.training_type_id and session.trainer_id and session.center_id and session.duration > 0:
                trainer_rate = self.env["tennis.trainer.rate"].search([
                    ("trainer_id", "=", session.trainer_id.id),
                    ("training_type_id", "=", session.training_type_id.id)
                ], limit=1)
                
                center_price = self.env["tennis.center.price"].search([
                    ("center_id", "=", session.center_id.id),
                    ("training_type_id", "=", session.training_type_id.id)
                ], limit=1)
                
                if trainer_rate and center_price:
                    session.trainer_cost = trainer_rate.hourly_rate * session.duration
                    session.price = center_price.price * session.duration
                    session.revenue = session.price - session.trainer_cost
                else:
                    session.trainer_cost = 0.0
                    session.price = 0.0
                    session.revenue = 0.0
            else:
                session.trainer_cost = 0.0
                session.price = 0.0
                session.revenue = 0.0
            if session.trainer_id and session.center_id:
                if session.trainer_id.center_id != session.center_id:
                    raise ValidationError(
                        f"Trainer {session.trainer_id.name} is not assigned to {session.center_id.name}!"
                    )
            # Also validate court belongs to the same center
            if session.court_id and session.center_id:
                if session.court_id.center_id != session.center_id:
                    raise ValidationError(
                        f"Court {session.court_id.name} belongs to {session.court_id.center_id.name}, "
                        f"but session is assigned to {session.center_id.name}!"
                    )
    
    @api.constrains("client_ids", "training_type_id")
    def _check_client_count(self):
        """Validate number of clients matches training type."""
        for session in self:
            client_count = len(session.client_ids)
            if session.training_type_id and client_count > 0:
                if client_count < session.training_type_id.min_clients:
                    raise ValidationError(
                        f"Minimum {session.training_type_id.min_clients} clients required!"
                    )
                if client_count > session.training_type_id.max_clients:
                    raise ValidationError(
                        f"Maximum {session.training_type_id.max_clients} clients allowed!"
                    )
    
    @api.constrains("court_id", "date", "time_from", "time_to")
    def _check_court_availability(self):
        """Check court is not already booked."""
        for session in self:
            if session.status not in ["cancelled"]:
                overlapping = self.search([
                    ("court_id", "=", session.court_id.id),
                    ("date", "=", session.date),
                    ("status", "in", ["draft", "pending_approval", "confirmed", "completed"]),
                    ("id", "!=", session.id),
                    "|",
                    "&", ("time_from", "<=", session.time_from), ("time_to", ">", session.time_from),
                    "&", ("time_from", "<", session.time_to), ("time_to", ">=", session.time_to),
                ])
                if overlapping:
                    raise ValidationError(
                        f"Court {session.court_id.name} is already booked!"
                    )
    
    @api.constrains("time_from", "time_to", "court_id", "center_id")
    def _check_working_hours(self):
        """Validate session is within court working hours."""
        for session in self:
            if session.time_from and session.time_to and session.center_id:
                day_of_week = str(session.date.weekday())
                
                working_hours = self.env["tennis.center.working.hours"].search([
                    ("center_id", "=", session.center_id.id),
                    ("day_of_week", "=", day_of_week),
                    ("is_closed", "=", False)
                ], limit=1)
                
                if not working_hours:
                    raise ValidationError(
                        f"Center is not open on {session.date.strftime('%A')}!"
                    )
                
                session_start = session.time_from.hour + session.time_from.minute / 60.0
                session_end = session.time_to.hour + session.time_to.minute / 60.0
                
                if session_start < working_hours.time_from or session_end > working_hours.time_to:
                    start_h = int(working_hours.time_from)
                    start_m = int((working_hours.time_from % 1) * 60)
                    end_h = int(working_hours.time_to)
                    end_m = int((working_hours.time_to % 1) * 60)
                    raise ValidationError(
                        f"Session must be within {start_h:02d}:{start_m:02d} - {end_h:02d}:{end_m:02d}"
                    )

    @api.onchange("center_id", "trainer_id")
    def _onchange_auto_fill_trainer_fields(self):
        """Auto-fill center and trainer for trainers on form open."""
        # Search without is_trainer in domain to avoid hr_employee_public issues
        employees = self.env["hr.employee"].with_context(active_test=False).search([
            ("user_id", "=", self.env.uid)
        ])

        for emp in employees:
            if emp.sudo().is_trainer:
                if not self.center_id and emp.sudo().center_id:
                    self.center_id = emp.center_id
                if not self.trainer_id:
                    self.trainer_id = emp
                break
    
    @api.onchange("date")
    @api.onchange("center_id")
    def _onchange_center_clear_fields(self):
        """Clear court and trainer when center changes to prevent cross-center assignments."""
        # Only clear if center actually changed (not on initial load)
        if self._origin.center_id and self.center_id != self._origin.center_id:
            # Center changed - clear court and trainer to force re-selection
            self.court_id = False
            if not self.is_current_user_trainer:
                # Only clear trainer for non-trainers (directors/managers)
                self.trainer_id = False

    def _onchange_date_sync_times(self):
        """Sync date with times when date changes."""
        if self.date:
            if self.time_from:
                new_time_from = datetime.combine(self.date, self.time_from.time())
                self.time_from = new_time_from
            if self.time_to:
                new_time_to = datetime.combine(self.date, self.time_to.time())
                self.time_to = new_time_to

    def _check_client_balance(self):
        """Check if all clients have sufficient balance."""
        self.ensure_one()
        
        if not self.client_ids:
            raise UserError("Cannot confirm session without clients!")
        
        insufficient_clients = []
        price_per_client = self.price / len(self.client_ids)
        
        for client in self.client_ids:
            if client.balance < price_per_client:
                insufficient_clients.append(
                    f"{client.name} (Balance: ${client.balance:.2f}, Required: ${price_per_client:.2f})"
                )
        
        if insufficient_clients:
            raise UserError("Insufficient balance:\n" + "\n".join(insufficient_clients))
    
    def _deduct_client_balance(self):
        """Deduct session price from client balances."""
        self.ensure_one()
        
        if self.balance_deducted:
            return
        
        if not self.client_ids:
            return
        
        price_per_client = self.price / len(self.client_ids)
        
        for client in self.client_ids:
            client.balance -= price_per_client
        
        self.balance_deducted = True
        self.payment_status = "paid"
    
    def _check_and_deduct_balance(self):
        """Check balance and deduct if sufficient."""
        self.ensure_one()
        
        if self.balance_deducted:
            return
        
        if not self.client_ids:
            raise UserError("Cannot process without clients!")
        
        price_per_client = self.price / len(self.client_ids)
        
        insufficient_clients = []
        for client in self.client_ids:
            if client.balance < price_per_client:
                insufficient_clients.append(
                    f"{client.name} (${client.balance:.2f} < ${price_per_client:.2f})"
                )
        
        if insufficient_clients:
            raise UserError("Insufficient balance:\n" + "\n".join(insufficient_clients))
        
        for client in self.client_ids:
            client.balance -= price_per_client
        
        self.balance_deducted = True
        self.payment_status = "paid"
    
    def action_confirm(self):
        """Confirm session."""
        for session in self:
            if session.needs_approval:
                raise UserError("This session requires manager approval first!")
            
            session._check_client_balance()
            session.status = "confirmed"
        
        return True
    
    def action_approve(self):
        """Approve session (Manager/Director only)."""
        if not self.env.user.has_group('tennis_club.group_tennis_manager') and \
           not self.env.user.has_group('tennis_club.group_tennis_director'):
            raise AccessError(_("Only managers and directors can approve sessions!"))
        
        current_employee = self.env["hr.employee"].search([
            ("user_id", "=", self.env.uid)
        ], limit=1)
        
        for session in self:
            if session.status != 'pending_approval':
                raise UserError(_("Only pending sessions can be approved!"))
            
            session.write({
                "needs_approval": session.created_by_trainer,  # Keep approval requirement for trainer sessions
                "approved_by": current_employee.id if current_employee else False,
                "approval_date": fields.Datetime.now(),
                "status": "confirmed"
            })
            
            session._check_client_balance()
        
        return True
    
    def action_complete(self):
        """Complete session and deduct balance."""
        for session in self:
            if session.status != "confirmed":
                raise UserError("Only confirmed sessions can be completed!")
            
            session._deduct_client_balance()
            session.status = "completed"
        
        return True
    
    def action_cancel(self):
        """Cancel session."""
        for session in self:
            if session.status == "completed":
                raise UserError("Cannot cancel completed session!")
            
            session.status = "cancelled"
        
        return True
    
    def action_reset_to_draft(self):
        """Reset to draft."""
        for session in self:
            if session.balance_deducted:
                raise UserError("Cannot reset - balance already deducted!")
            
            session.write({
                "status": "draft",
                "needs_approval": session.created_by_trainer,  # Keep approval requirement for trainer sessions
                "approved_by": False,
                "approval_date": False,
            })
        
        return True

    def action_create_recurring_sessions(self):
        """Create recurring training sessions."""
        from dateutil.relativedelta import relativedelta
        
        self.ensure_one()
        
        if not self.is_recurring:
            raise UserError(_("This is not a recurring session!"))
        
        if not self.recurrence_end_date:
            raise UserError(_("Please specify end date!"))
        
        if self.recurrence_end_date <= self.date:
            raise UserError(_("End date must be after start date!"))
        
        time_slots = [{"time_from": self.time_from, "time_to": self.time_to}]
        created_sessions = self.env["tennis.training.session"]
        current_date = self.date
        sessions_count = 0
        skipped_count = 0
        max_sessions = 500
        
        while current_date <= self.recurrence_end_date and sessions_count < max_sessions:
            if self.skip_weekends and current_date.weekday() in [5, 6]:
                current_date = self._get_next_date(current_date)
                skipped_count += 1
                continue

            day_of_week = str(current_date.weekday())
            working_hours = self.env["tennis.center.working.hours"].search([
                ("center_id", "=", self.center_id.id),
                ("day_of_week", "=", day_of_week),
            ], limit=1)
            
            if working_hours and working_hours.is_closed:
                current_date = self._get_next_date(current_date)
                skipped_count += 1
                continue

            for slot_data in time_slots:
                slot_start = datetime.combine(current_date, slot_data["time_from"].time())
                slot_end = datetime.combine(current_date, slot_data["time_to"].time())
                
                conflicting = self.env["tennis.training.session"].search([
                    ("court_id", "=", self.court_id.id),
                    ("date", "=", current_date),
                    ("time_from", "<", slot_end),
                    ("time_to", ">", slot_start),
                    ("status", "!=", "cancelled"),
                ])
                
                if not conflicting:
                    vals = {
                        "center_id": self.center_id.id,
                        "court_id": self.court_id.id,
                        "trainer_id": self.trainer_id.id,
                        "training_type_id": self.training_type_id.id,
                        "date": current_date,
                        "time_from": slot_start,
                        "time_to": slot_end,
                        "client_ids": [(6, 0, self.client_ids.ids)],
                        "parent_recurring_session_id": self.id,
                        "status": "draft",
                        "notes": f"Generated from {self.name}",
                    }
                    
                    new_session = self.create(vals)
                    created_sessions |= new_session
                    sessions_count += 1
                else:
                    skipped_count += 1
            
            current_date = self._get_next_date(current_date)
        
        if sessions_count == 0:
            raise UserError(_("No sessions created - all slots occupied!"))
        
        created_sessions |= self
        message = _("Created %s sessions") % sessions_count
        if skipped_count > 0:
            message += _(" (%s skipped)") % skipped_count
        
        return {
            "type": "ir.actions.act_window",
            "name": _("Recurring Sessions (%s)") % sessions_count,
            "res_model": "tennis.training.session",
            "view_mode": "list,form,calendar",
            "domain": [("id", "in", created_sessions.ids)],
        }
    
    def _get_next_date(self, current_date):
        """Calculate next date based on pattern."""
        from dateutil.relativedelta import relativedelta
        
        if self.recurrence_pattern == "daily":
            return current_date + timedelta(days=self.recurrence_interval)
        elif self.recurrence_pattern == "weekly":
            return current_date + timedelta(weeks=self.recurrence_interval)
        elif self.recurrence_pattern == "monthly":
            return current_date + relativedelta(months=self.recurrence_interval)
        return current_date + timedelta(days=1)

    @api.model
    def _send_booking_confirmation(self, client_ids):
        """Send booking confirmation to specified clients.
        
        Args:
            client_ids: List of res.partner IDs
        """
        import logging
        _logger = logging.getLogger(__name__)
        
        _logger.info(f"_send_booking_confirmation called with clients: {client_ids}")
        
        from .telegram_helper import TelegramHelper
        helper = TelegramHelper(self.env)
        
        clients = self.env['res.partner'].browse(client_ids)
        
        for client in clients:
            if not client.telegram_chat_id or not client.receive_telegram_notifications:
                continue
            
            # Check if notification already sent
            existing = self.env['telegram.notification'].search([
                ('partner_id', '=', client.id),
                ('session_id', '=', self.id),
                ('message_type', '=', 'booking_confirmation'),
            ])
            
            if existing:
                _logger.info(f"Notification already sent to {client.name}")
                continue
            
            # Format and send
            message = helper.format_booking_confirmation(self)
            
            # Send notification
            success = client.send_telegram_notification(
                message_type="booking_confirmation",
                message_text=message,
                session_id=self.id
            )
            
            if success:
                _logger.info(f"Booking confirmation sent to {client.name}")
            else:
                _logger.error(f"Failed to send booking confirmation to {client.name}")
    
    def cron_send_training_reminders(self):
        """Cron: Send training reminders."""
        from .telegram_helper import TelegramHelper
        
        helper = TelegramHelper(self.env)
        now = datetime.now()
        tomorrow = now + timedelta(days=1)
        
        sessions = self.search([
            ('status', '=', 'confirmed'),
            ('time_from', '>=', now),
            ('time_from', '<=', tomorrow),
        ])
        
        reminders_sent = 0
        
        for session in sessions:
            time_until = session.time_from - now
            hours_until = time_until.total_seconds() / 3600
            
            for client in session.client_ids:
                if not client.telegram_chat_id or not client.receive_telegram_notifications:
                    continue
                
                if hours_until <= client.notification_hours_before:
                    existing = self.env['telegram.notification'].search([
                        ('partner_id', '=', client.id),
                        ('session_id', '=', session.id),
                        ('message_type', '=', 'booking_reminder'),
                    ])
                    
                    if not existing:
                        message = helper.format_reminder(session, client.notification_hours_before)
                        success = client.send_telegram_notification(
                            message_type="booking_reminder",
                            message_text=message,
                            session_id=session.id
                        )
                        
                        if success:
                            reminders_sent += 1
        
        _logger.info(f"Sent {reminders_sent} reminders")
        return True
