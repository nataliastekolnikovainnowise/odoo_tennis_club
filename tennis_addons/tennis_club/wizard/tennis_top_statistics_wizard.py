# -*- coding: utf-8 -*-
"""Tennis Top Statistics Report."""

from odoo import api, fields, models


class TennisTopStatisticsReport(models.Model):
    """Report to show top statistics."""
    
    _name = "tennis.top.statistics.report"
    _description = "Tennis Top Statistics Report"
    
    date_from = fields.Date(
        string="Date From",
        required=True,
        default=lambda self: fields.Date.today().replace(day=1),
    )
    
    date_to = fields.Date(
        string="Date To",
        required=True,
        default=fields.Date.today,
    )
    
    # Results
    top_trainer_id = fields.Many2one(
        comodel_name="hr.employee",
        string="Most Profitable Trainer",
        compute="_compute_statistics",
        store=True,
    )
    
    top_trainer_revenue = fields.Monetary(
        string="Trainer Revenue",
        currency_field="currency_id",
        compute="_compute_statistics",
        store=True,
    )
    
    top_training_type_id = fields.Many2one(
        comodel_name="tennis.training.type",
        string="Most Popular Training Type",
        compute="_compute_statistics",
        store=True,
    )
    
    top_training_type_sessions = fields.Integer(
        string="Sessions Count",
        compute="_compute_statistics",
        store=True,
    )
    
    top_client_id = fields.Many2one(
        comodel_name="res.partner",
        string="Most Active Client",
        compute="_compute_statistics",
        store=True,
    )
    
    top_client_sessions = fields.Integer(
        string="Client Sessions",
        compute="_compute_statistics",
        store=True,
    )
    
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
    )
    
    @api.depends("date_from", "date_to")
    def _compute_statistics(self):
        """Compute top statistics."""
        for report in self:
            domain = [
                ("date", ">=", report.date_from),
                ("date", "<=", report.date_to),
                ("status", "=", "completed"),
            ]
            
            sessions = self.env["tennis.training.session"].search(domain)
            
            # Top Trainer (by revenue)
            trainer_revenue = {}
            for session in sessions:
                trainer = session.trainer_id
                if trainer not in trainer_revenue:
                    trainer_revenue[trainer] = 0.0
                trainer_revenue[trainer] += session.revenue
            
            if trainer_revenue:
                top_trainer = max(trainer_revenue, key=trainer_revenue.get)
                report.top_trainer_id = top_trainer
                report.top_trainer_revenue = trainer_revenue[top_trainer]
            else:
                report.top_trainer_id = False
                report.top_trainer_revenue = 0.0
            
            # Top Training Type (by session count)
            type_sessions = {}
            for session in sessions:
                training_type = session.training_type_id
                if training_type not in type_sessions:
                    type_sessions[training_type] = 0
                type_sessions[training_type] += 1
            
            if type_sessions:
                top_type = max(type_sessions, key=type_sessions.get)
                report.top_training_type_id = top_type
                report.top_training_type_sessions = type_sessions[top_type]
            else:
                report.top_training_type_id = False
                report.top_training_type_sessions = 0
            
            # Top Client (by session count)
            client_sessions = {}
            for session in sessions:
                for client in session.client_ids:
                    if client not in client_sessions:
                        client_sessions[client] = 0
                    client_sessions[client] += 1
            
            if client_sessions:
                top_client = max(client_sessions, key=client_sessions.get)
                report.top_client_id = top_client
                report.top_client_sessions = client_sessions[top_client]
            else:
                report.top_client_id = False
                report.top_client_sessions = 0
    
    def action_refresh(self):
        """Refresh statistics."""
        self._compute_statistics()
        return {
            "type": "ir.actions.act_window",
            "res_model": "tennis.top.statistics.report",
            "view_mode": "form",
            "res_id": self.id,
            "target": "current",
        }


    def action_generate_report(self):
        """Generate statistics report."""
        self.ensure_one()
        self._compute_statistics()
        return {
            "type": "ir.actions.act_window",
            "res_model": "tennis.top.statistics.report",
            "view_mode": "form",
            "res_id": self.id,
            "target": "current",
        }
