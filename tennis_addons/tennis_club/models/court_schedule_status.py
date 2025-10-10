# -*- coding: utf-8 -*-
"""Court Schedule Status Model - like crm.stage."""

from odoo import models, fields, api


class CourtScheduleStatus(models.Model):
    """Status model for court schedule (like CRM stages)."""
    
    _name = "court.schedule.status"
    _description = "Court Schedule Status"
    _order = "sequence, id"
    
    name = fields.Char(
        string="Status Name",
        required=True,
        translate=True,
    )
    
    sequence = fields.Integer(
        string="Sequence",
        default=10,
        help="Used to order statuses",
    )
    
    fold = fields.Boolean(
        string="Folded in Kanban",
        default=False,
        help="This status is folded in the kanban view",
    )
    
    description = fields.Text(
        string="Description",
        help="Description of this status",
    )
    
    active = fields.Boolean(
        string="Active",
        default=True,
    )
