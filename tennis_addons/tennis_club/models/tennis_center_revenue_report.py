"""Tennis Center Revenue Report."""

from odoo import api, fields, models
from datetime import datetime
from dateutil.relativedelta import relativedelta


class TennisCenterRevenueReport(models.Model):
    """Wizard for Center Revenue Report."""
    
    _name = "tennis.center.revenue.report"
    _description = "Tennis Center Revenue Report"
    
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
    
    center_id = fields.Many2one(
        comodel_name="tennis.center",
        string="Center",
        help="Leave empty to show all centers",
    )
    
    line_ids = fields.One2many(
        comodel_name="tennis.center.revenue.report.line",
        inverse_name="report_id",
        string="Revenue Lines",
    )

    total_sessions = fields.Integer(
        string="Total Sessions",
        compute="_compute_totals",
    )

    total_cost = fields.Float(
        string="Total Cost",
        compute="_compute_totals",
    )

    total_revenue_sum = fields.Float(
        string="Total Revenue",
        compute="_compute_totals",
    )

    
    def _compute_totals(self):
        for record in self:
            record.total_sessions = sum(record.line_ids.mapped("session_count"))
            record.total_cost = sum(record.line_ids.mapped("total_center_cost"))
            record.total_revenue_sum = sum(record.line_ids.mapped("total_revenue"))

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
        
        if self.center_id:
            domain.append(("center_id", "=", self.center_id.id))
        
        # Get sessions
        sessions = self.env["tennis.training.session"].search(domain)
        
        # Group by center
        center_data = {}
        for session in sessions:
            center = session.center_id
            if center not in center_data:
                center_data[center] = {
                    "sessions": 0,
                    "total_revenue": 0.0,
                    "total_center_cost": 0.0,
                }
            
            center_data[center]["sessions"] += 1
            center_data[center]["total_revenue"] += session.revenue
            center_data[center]["total_center_cost"] += session.price
        
        # Create report lines
        for center, data in center_data.items():
            self.env["tennis.center.revenue.report.line"].create({
                "report_id": self.id,
                "center_id": center.id,
                "session_count": data["sessions"],
                "total_revenue": data["total_revenue"],
                "total_center_cost": data["total_center_cost"],
            })
        
        # Return action to show results
        return {
            "type": "ir.actions.act_window",
            "res_model": "tennis.center.revenue.report",
            "view_mode": "form",
            "res_id": self.id,
            "target": "new",
        }


class TennisCenterRevenueReportLine(models.Model):
    """Line for Center Revenue Report."""
    
    _name = "tennis.center.revenue.report.line"
    _description = "Tennis Center Revenue Report Line"
    _order = "total_revenue desc"
    
    report_id = fields.Many2one(
        comodel_name="tennis.center.revenue.report",
        string="Report",
        required=True,
        ondelete="cascade",
    )
    
    center_id = fields.Many2one(
        comodel_name="tennis.center",
        string="Center",
        required=True,
    )
    
    session_count = fields.Integer(
        string="Sessions",
        help="Number of completed sessions",
    )
    
    total_revenue = fields.Monetary(
        string="Total Revenue (Profit)",
        help="Total profit from all sessions",
    )
    
    total_center_cost = fields.Monetary(
        string="Total Center Cost",
        help="Total cost paid to center",
    )
    
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
    )

