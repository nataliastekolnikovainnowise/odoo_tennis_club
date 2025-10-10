# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import ValidationError, UserError


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
        domain="[('is_trainer', '=', True), ('center_id', '=', center_id)]",
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
    
    _sql_constraints = [
        (
            "check_time_order",
            "CHECK(time_to > time_from)",
            "End time must be after start time!"
        ),
    ]
    
    @api.model
    def create(self, vals):
        """Generate sequence number and check if created by trainer."""
        if vals.get("name", "New") == "New":
            vals["name"] = self.env["ir.sequence"].next_by_code("tennis.training.session") or "New"
        
        # Check if current user is a trainer
        current_employee = self.env["hr.employee"].search([
            ("user_id", "=", self.env.uid)
        ], limit=1)
        
        if current_employee and current_employee.is_trainer:
            vals["created_by_trainer"] = True
            vals["needs_approval"] = True
            vals["status"] = "pending_approval"
        
        return super().create(vals)
    
    def write(self, vals):
        """Check if modifications by trainer need approval and handle status changes."""
        # If trainer is modifying important fields, require approval
        important_fields = ["date", "time_from", "time_to", "court_id", "client_ids", "training_type_id"]
        
        current_employee = self.env["hr.employee"].search([
            ("user_id", "=", self.env.uid)
        ], limit=1)
        
        if current_employee and current_employee.is_trainer:
            if any(field in vals for field in important_fields):
                for record in self:
                    if record.status in ["confirmed", "completed"]:
                        vals["needs_approval"] = True
                        vals["status"] = "pending_approval"
        
        # Check if status is changing to confirmed
        if "status" in vals and vals["status"] == "confirmed":
            for record in self:
                if not record.balance_deducted:
                    # This will trigger the balance check and deduction
                    record._check_and_deduct_balance()
        
        return super().write(vals)
    
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
                # Получаем ставку тренера для этого типа тренировки
                trainer_rate = self.env["tennis.trainer.rate"].search([
                    ("trainer_id", "=", session.trainer_id.id),
                    ("training_type_id", "=", session.training_type_id.id)
                ], limit=1)
                
                # Получаем цену в центре для этого типа
                center_price = self.env["tennis.center.price"].search([
                    ("center_id", "=", session.center_id.id),
                    ("training_type_id", "=", session.training_type_id.id)
                ], limit=1)
                
                if trainer_rate and center_price:
                    # Стоимость тренера = ставка * продолжительность
                    session.trainer_cost = trainer_rate.hourly_rate * session.duration
                    # Цена клиента = цена центра * продолжительность
                    session.price = center_price.price * session.duration
                    # Прибыль = цена - стоимость тренера
                    session.revenue = session.price - session.trainer_cost
                else:
                    session.trainer_cost = 0.0
                    session.price = 0.0
                    session.revenue = 0.0
            else:
                session.trainer_cost = 0.0
                session.price = 0.0
                session.revenue = 0.0
    
    @api.constrains("time_from", "time_to", "date")
    def _check_times(self):
        """Validate times are on the same date."""
        for session in self:
            if session.time_from.date() != session.date:
                raise ValidationError("Start time must be on the selected date!")
            if session.time_to.date() != session.date:
                raise ValidationError("End time must be on the selected date!")
            if session.time_from >= session.time_to:
                raise ValidationError("End time must be after start time!")
    
    @api.constrains("trainer_id", "center_id")
    def _check_trainer_center(self):
        """Validate trainer belongs to the same center as the session."""
        for session in self:
            if session.trainer_id and session.center_id:
                if session.trainer_id.center_id != session.center_id:
                    raise ValidationError(
                        f"Trainer {session.trainer_id.name} is not assigned to {session.center_id.name}!"
                    )
    
    @api.constrains("client_ids", "training_type_id")
    def _check_client_count(self):
        """Validate number of clients matches training type."""
        for session in self:
            client_count = len(session.client_ids)
            if session.training_type_id and client_count > 0:
                if client_count < session.training_type_id.min_clients:
                    raise ValidationError(
                        f"Minimum {session.training_type_id.min_clients} clients required for {session.training_type_id.name}!"
                    )
                if client_count > session.training_type_id.max_clients:
                    raise ValidationError(
                        f"Maximum {session.training_type_id.max_clients} clients allowed for {session.training_type_id.name}!"
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
                        f"Court {session.court_id.name} is already booked at this time!"
                    )
    
    @api.constrains("time_from", "time_to", "court_id", "center_id")
    def _check_working_hours(self):
        """Validate session is within court working hours."""
        for session in self:
            if session.time_from and session.time_to and session.center_id:
                # Get day of week (0=Monday, 6=Sunday)
                day_of_week = str(session.date.weekday())
                
                working_hours = self.env["tennis.center.working.hours"].search([
                    ("center_id", "=", session.center_id.id),
                    ("day_of_week", "=", day_of_week),
                    ("is_closed", "=", False)
                ], limit=1)
                
                if not working_hours:
                    raise ValidationError(
                        f"Center {session.center_id.name} is not open on {session.date.strftime('%A')}!"
                    )
                
                # Convert datetime to float hours for comparison
                session_start = session.time_from.hour + session.time_from.minute / 60.0
                session_end = session.time_to.hour + session.time_to.minute / 60.0
                
                if session_start < working_hours.time_from or session_end > working_hours.time_to:
                    # Format hours for error message
                    start_h = int(working_hours.time_from)
                    start_m = int((working_hours.time_from % 1) * 60)
                    end_h = int(working_hours.time_to)
                    end_m = int((working_hours.time_to % 1) * 60)
                    raise ValidationError(
                        f"Session must be within working hours: {start_h:02d}:{start_m:02d} - {end_h:02d}:{end_m:02d}"
                    )    
    def _check_client_balance(self):
        """Check if all clients have sufficient balance."""
        self.ensure_one()
        
        if not self.client_ids:
            raise UserError("Cannot confirm session without clients!")
        
        insufficient_clients = []
        price_per_client = self.price / len(self.client_ids) if self.client_ids else 0
        
        for client in self.client_ids:
            if client.balance < price_per_client:
                insufficient_clients.append(
                    f"{client.name} (Balance: ${client.balance:.2f}, Required: ${price_per_client:.2f})"
                )
        
        if insufficient_clients:
            raise UserError(
                "Insufficient balance for clients:\n" + "\n".join(insufficient_clients)
            )
    
    def _deduct_client_balance(self):
        """Deduct session price from client balances."""
        self.ensure_one()
        
        if self.balance_deducted:
            return  # Already deducted
        
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
            return  # Already deducted
        
        if not self.client_ids:
            raise UserError("Cannot process session without clients!")
        
        # Check balance
        insufficient_clients = []
        price_per_client = self.price / len(self.client_ids) if self.client_ids else 0
        
        for client in self.client_ids:
            if client.balance < price_per_client:
                insufficient_clients.append(
                    f"{client.name} (Balance: ${client.balance:.2f}, Required: ${price_per_client:.2f})"
                )
        
        if insufficient_clients:
            raise UserError(
                "Insufficient balance for clients:\n" + "\n".join(insufficient_clients)
            )
        
        # Deduct balance
        for client in self.client_ids:
            client.balance -= price_per_client
        
        self.balance_deducted = True
        self.payment_status = "paid"
        self.status = "completed"
    
    def action_confirm(self):
        """Confirm session."""
        for session in self:
            if session.needs_approval:
                raise UserError("This session requires manager approval first!")
            
            # Check client balances
            session._check_client_balance()
            
            session.status = "confirmed"
        
        return True
    
    def action_approve(self):
        """Approve session (Manager only)."""
        # Check if current user is a manager
        current_employee = self.env["hr.employee"].search([
            ("user_id", "=", self.env.uid)
        ], limit=1)
        
        # TODO: Add proper manager check when security groups are implemented
        # For now, assume any non-trainer can approve
        
        for session in self:
            session.write({
                "needs_approval": False,
                "approved_by": current_employee.id if current_employee else False,
                "approval_date": fields.Datetime.now(),
                "status": "confirmed"
            })
            
            # Check client balances after approval
            session._check_client_balance()
        
        return True
    
    def action_complete(self):
        """Complete session and deduct balance."""
        for session in self:
            if session.status != "confirmed":
                raise UserError("Only confirmed sessions can be completed!")
            
            # Deduct client balance
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
                raise UserError("Cannot reset session where balance was already deducted!")
            
            session.write({
                "status": "draft",
                "needs_approval": False,
                "approved_by": False,
                "approval_date": False,
            })
        
        return True
