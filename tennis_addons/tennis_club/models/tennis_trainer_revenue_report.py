# -*- coding: utf-8 -*-
"""Tennis Trainer Revenue Report."""

from odoo import api, fields, models
from odoo.exceptions import UserError
from datetime import datetime
from dateutil.relativedelta import relativedelta


class TennisTrainerRevenueReport(models.Model):
    """Trainer Revenue Report Model."""
    
    _name = "tennis.trainer.revenue.report"
    _description = "Tennis Trainer Revenue Report"
    
    @api.model
    def _get_trainer_domain(self):
        """Get domain for trainer selection based on user role."""
        user = self.env.user
        
        # Director sees all trainers
        if user.has_group("tennis_club.group_tennis_director"):
            return [("is_trainer", "=", True)]
        
        # Manager sees only trainers from their centers
        if user.has_group("tennis_club.group_tennis_manager"):
            employee = self.env["hr.employee"].search([("user_id", "=", user.id)], limit=1)
            if employee:
                centers = self.env["tennis.center"].search([("manager_id", "=", employee.id)])
                return [("is_trainer", "=", True), ("center_id", "in", centers.ids)]
        
        # Default: no trainers
        return [("id", "=", False)]
    
    date_from = fields.Date(
        string="Date From",
        required=True,
        default=lambda self: fields.Date.today().replace(day=1),
        help="Start date for revenue calculation (default: first day of current month)",
    )
    
    date_to = fields.Date(
        string="Date To",
        required=True,
        default=fields.Date.today,
        help="End date for revenue calculation (default: today)",
    )
    
    trainer_id = fields.Many2one(
        comodel_name="hr.employee",
        string="Trainer",
        domain=lambda self: self._get_trainer_domain(),
        help="Leave empty to show all trainers",
    )
    
    line_ids = fields.One2many(
        comodel_name="tennis.trainer.revenue.report.line",
        inverse_name="report_id",
        string="Revenue Lines",
    )
    
    total_sessions = fields.Integer(
        string="Total Sessions",
        compute="_compute_totals",
    )
    
    total_cost = fields.Monetary(
        string="Total Cost",
        currency_field="currency_id",
        compute="_compute_totals",
    )
    
    total_revenue_sum = fields.Monetary(
        string="Total Revenue",
        currency_field="currency_id",
        compute="_compute_totals",
    )
    
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
    )
    
    def _compute_totals(self):
        """Compute totals from lines."""
        for record in self:
            record.total_sessions = sum(record.line_ids.mapped("session_count"))
            record.total_cost = sum(record.line_ids.mapped("total_trainer_cost"))
            record.total_revenue_sum = sum(record.line_ids.mapped("total_revenue"))
    
    def action_print_report(self):
        """Print revenue report as PDF."""
        self.ensure_one()
        report = self.env["ir.actions.report"].search([
            ("model", "=", "tennis.trainer.revenue.report"),
            ("report_type", "=", "qweb-pdf")
        ], limit=1)
        if not report:
            raise UserError("Report not found!")
        return report.report_action(self)
    
    def action_generate_report(self):
        """Generate revenue report for selected period."""
        self.ensure_one()
        
        # Clear existing lines
        self.line_ids.unlink()
        
        # Build domain
        domain = [
            ("date", ">=", self.date_from),
            ("date", "<=", self.date_to),
            ("status", "=", "completed"),
        ]
        
        # Filter by manager's center
        user = self.env.user
        if user.has_group("tennis_club.group_tennis_manager"):
            employee = self.env["hr.employee"].search([("user_id", "=", user.id)], limit=1)
            if employee and employee.center_id:
                domain.append(("center_id", "=", employee.center_id.id))
        
        
        if self.trainer_id:
            domain.append(("trainer_id", "=", self.trainer_id.id))
        
        # Get sessions
        sessions = self.env["tennis.training.session"].search(domain)
        
        # Group by trainer
        trainer_data = {}
        for session in sessions:
            trainer = session.trainer_id
            if trainer not in trainer_data:
                trainer_data[trainer] = {
                    "sessions": 0,
                    "total_revenue": 0.0,
                    "total_trainer_cost": 0.0,
                }
            
            trainer_data[trainer]["sessions"] += 1
            trainer_data[trainer]["total_revenue"] += session.revenue
            trainer_data[trainer]["total_trainer_cost"] += session.trainer_cost
        
        # Create report lines
        for trainer, data in trainer_data.items():
            self.env["tennis.trainer.revenue.report.line"].create({
                "report_id": self.id,
                "trainer_id": trainer.id,
                "session_count": data["sessions"],
                "total_revenue": data["total_revenue"],
                "total_trainer_cost": data["total_trainer_cost"],
            })
        
        # Return action to stay on the same form (NOT close it!)
        return {
            "type": "ir.actions.act_window",
            "res_model": "tennis.trainer.revenue.report",
            "view_mode": "form",
            "res_id": self.id,
            "target": "current",
        }


class TennisTrainerRevenueReportLine(models.Model):
    """Line for Trainer Revenue Report."""
    
    _name = "tennis.trainer.revenue.report.line"
    _description = "Tennis Trainer Revenue Report Line"
    _order = "total_revenue desc"
    
    report_id = fields.Many2one(
        comodel_name="tennis.trainer.revenue.report",
        string="Report",
        required=True,
        ondelete="cascade",
    )
    
    trainer_id = fields.Many2one(
        comodel_name="hr.employee",
        string="Trainer",
        domain="[('is_trainer', '=', True)]",
        required=True,
    )
    
    session_count = fields.Integer(
        string="Sessions",
        help="Number of completed sessions",
    )
    
    total_trainer_cost = fields.Monetary(
        string="Total Trainer Cost",
        currency_field="currency_id",
        help="Total amount paid to trainer",
    )
    
    total_revenue = fields.Monetary(
        string="Total Revenue (Profit)",
        currency_field="currency_id",
        help="Total profit from trainer's sessions",
    )
    
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
        required=True,
    )
