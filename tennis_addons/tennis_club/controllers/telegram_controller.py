# -*- coding: utf-8 -*-
"""Telegram Webhook Controller."""

from odoo import http
from odoo.http import request
import logging
import json

_logger = logging.getLogger(__name__)


class TelegramController(http.Controller):
    """Controller for Telegram bot webhook."""
    
    @http.route('/telegram/webhook', type='json', auth='public', methods=['POST'], csrf=False)
    def telegram_webhook(self, **kwargs):
        """Handle incoming Telegram updates.
        
        This endpoint receives updates from Telegram Bot API.
        The actual bot logic is handled by external Python bot script.
        This is just for receiving webhooks if needed.
        """
        try:
            data = request.jsonrequest
            _logger.info(f"Received Telegram webhook: {data}")
            
            return {"status": "ok"}
        except Exception as e:
            _logger.error(f"Error processing Telegram webhook: {e}")
            return {"status": "error", "message": str(e)}
    
    @http.route('/telegram/balance/<int:partner_id>', type='json', auth='user', methods=['GET'])
    def get_balance(self, partner_id, **kwargs):
        """Get client balance via API.
        
        Args:
            partner_id: res.partner ID
            
        Returns:
            dict with balance information
        """
        try:
            partner = request.env['res.partner'].browse(partner_id)
            
            if not partner.exists():
                return {"error": "Partner not found"}
            
            if not partner.is_client:
                return {"error": "Not a client"}
            
            return {
                "partner_id": partner.id,
                "name": partner.name,
                "balance": partner.balance,
                "currency": partner.currency_id.name,
                "training_count": partner.training_count,
                "completed_training_count": partner.completed_training_count,
            }
        except Exception as e:
            _logger.error(f"Error getting balance: {e}")
            return {"error": str(e)}
    
    @http.route('/telegram/trainings/<int:partner_id>', type='json', auth='user', methods=['GET'])
    def get_trainings(self, partner_id, **kwargs):
        """Get upcoming trainings for client.
        
        Args:
            partner_id: res.partner ID
            
        Returns:
            list of upcoming training sessions
        """
        try:
            partner = request.env['res.partner'].browse(partner_id)
            
            if not partner.exists():
                return {"error": "Partner not found"}
            
            # Get upcoming trainings
            from datetime import datetime
            today = datetime.today().date()
            
            sessions = request.env['tennis.training.session'].search([
                ('client_ids', 'in', partner.id),
                ('date', '>=', today),
                ('status', 'in', ['confirmed', 'draft', 'pending_approval']),
            ], order='date asc, time_from asc', limit=10)
            
            trainings = []
            for session in sessions:
                trainings.append({
                    "id": session.id,
                    "name": session.name,
                    "date": session.date.strftime('%Y-%m-%d'),
                    "time_from": session.time_from.strftime('%H:%M'),
                    "time_to": session.time_to.strftime('%H:%M'),
                    "center": session.center_id.name,
                    "court": session.court_id.name,
                    "trainer": session.trainer_id.name,
                    "training_type": session.training_type_id.name,
                    "status": session.status,
                })
            
            return {
                "partner_id": partner.id,
                "name": partner.name,
                "trainings": trainings,
            }
        except Exception as e:
            _logger.error(f"Error getting trainings: {e}")
            return {"error": str(e)}
