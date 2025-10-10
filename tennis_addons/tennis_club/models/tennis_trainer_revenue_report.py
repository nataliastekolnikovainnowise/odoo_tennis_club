"""Tennis Trainer Revenue Report."""

from odoo import api, fields, models
from datetime import datetime
from dateutil.relativedelta import relativedelta


class TennisTrainerRevenueReport(models.TransientModel):
    """Wizard for Trainer Revenue Report."""
    
    _name = "tennis.trainer.revenue.report"
    _description = "Tennis Trainer Revenue Report"
    
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
        domain="[('is_trainer', '=', True)]",
        help="Leave empty to show all trainers",
    )
    
    line_ids = fields.One2many(
        comodel_name="tennis.trainer.revenue.report.line",
        inverse_name="report_id",
        string="Revenue Lines",
    )
    
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
        
        # Return action to show results
        return {
            "type": "ir.actions.act_window",
            "res_model": "tennis.trainer.revenue.report",
            "view_mode": "form",
            "res_id": self.id,
            "target": "new",
        }


class TennisTrainerRevenueReportLine(models.TransientModel):
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
        required=True,
    )
    
    session_count = fields.Integer(
        string="Sessions",
        help="Number of completed sessions",
    )
    
    total_revenue = fields.Monetary(
        string="Total Revenue (Profit)",
        currency_field="currency_id",
        help="Total profit from all sessions",
    )
    
    total_trainer_cost = fields.Monetary(
        string="Total Trainer Cost",
        currency_field="currency_id",
        help="Total cost paid to trainer",
    )
    
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
    )
