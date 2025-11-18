# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ClientBalanceWizard(models.TransientModel):
    """Wizard for managing client balance."""
    
    _name = "client.balance.wizard"
    _description = "Client Balance Management"

    partner_id = fields.Many2one(
        "res.partner",
        string="Client",
        required=True,
        domain="[('is_client', '=', True)]",
        help="Client to manage balance for"
    )
    
    current_balance = fields.Monetary(
        string="Current Balance",
        related="partner_id.balance",
        readonly=True,
        currency_field="currency_id",
        help="Current client balance"
    )
    
    operation = fields.Selection(
        selection=[
            ("add", "Add to Balance"),
            ("set", "Set Balance"),
            ("deduct", "Deduct from Balance"),
        ],
        string="Operation",
        required=True,
        default="add",
        help="Type of balance operation"
    )
    
    amount = fields.Monetary(
        string="Amount",
        required=True,
        currency_field="currency_id",
        help="Amount to add/deduct/set"
    )
    
    new_balance = fields.Monetary(
        string="New Balance",
        compute="_compute_new_balance",
        currency_field="currency_id",
        help="Balance after operation"
    )
    
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        related="partner_id.currency_id",
        readonly=True
    )
    
    reason = fields.Text(
        string="Reason",
        help="Reason for balance change"
    )

    @api.depends("partner_id", "operation", "amount")
    def _compute_new_balance(self):
        """Compute new balance after operation."""
        for wizard in self:
            if wizard.partner_id and wizard.amount:
                if wizard.operation == "add":
                    wizard.new_balance = wizard.current_balance + wizard.amount
                elif wizard.operation == "deduct":
                    wizard.new_balance = wizard.current_balance - wizard.amount
                elif wizard.operation == "set":
                    wizard.new_balance = wizard.amount
                else:
                    wizard.new_balance = wizard.current_balance
            else:
                wizard.new_balance = wizard.current_balance

    @api.constrains("amount")
    def _check_amount(self):
        """Validate amount is positive."""
        for wizard in self:
            if wizard.amount <= 0:
                raise ValidationError(_("Amount must be greater than zero!"))

    @api.constrains("operation", "amount", "current_balance")
    def _check_deduct_amount(self):
        """Check that deduction doesn't result in negative balance."""
        for wizard in self:
            if wizard.operation == "deduct":
                if wizard.amount > wizard.current_balance:
                    raise ValidationError(
                        _("Cannot deduct %.2f from balance %.2f. Result would be negative!") 
                        % (wizard.amount, wizard.current_balance)
                    )

    def action_apply(self):
        """Apply balance change."""
        self.ensure_one()
        
        if not self.partner_id:
            raise ValidationError(_("Please select a client!"))
        
        # Calculate new balance
        if self.operation == "add":
            new_balance = self.current_balance + self.amount
            operation_text = _("Added %.2f to balance") % self.amount
        elif self.operation == "deduct":
            new_balance = self.current_balance - self.amount
            operation_text = _("Deducted %.2f from balance") % self.amount
        elif self.operation == "set":
            new_balance = self.amount
            operation_text = _("Set balance to %.2f") % self.amount
        else:
            return
        
        # Update balance
        self.partner_id.balance = new_balance
        
        # Log the change
        message = f"""
            <p><strong>{operation_text}</strong></p>
            <ul>
                <li>Previous Balance: {self.current_balance:.2f}</li>
                <li>New Balance: {new_balance:.2f}</li>
                <li>Changed by: {self.env.user.name}</li>
                {f'<li>Reason: {self.reason}</li>' if self.reason else ''}
            </ul>
        """
        
        self.partner_id.message_post(
            body=message,
            subject=_("Balance Updated"),
            subtype_xmlid="mail.mt_note"
        )
        
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Success"),
                "message": _("Balance updated successfully to %.2f") % new_balance,
                "type": "success",
                "sticky": False,
            }
        }
