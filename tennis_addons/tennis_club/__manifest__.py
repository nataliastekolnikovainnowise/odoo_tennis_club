# -*- coding: utf-8 -*-
{
    "name": "Tennis Club Management",
    "version": "18.0.1.0.0",
    "category": "Sports",
    "summary": "Tennis club network management system",
    "description": """
        Tennis Club Management System:
        - Sports centers and courts management
        - Training schedule management
        - Trainers and clients management
        - Financial analytics
    """,
    "author": "Natalia Stekolnikova",
    "license": "LGPL-3",
    "depends": [
        "base",
        "hr",
        "contacts",
        "calendar",   
        "mail", 
    ],
    "data": [
        "security/tennis_club_groups.xml",
        "security/tennis_club_security.xml",
        "security/ir.model.access.csv",
        "security/tennis_club_rules.xml",
        "data/tennis_training_type_data.xml",
        "data/tennis_training_session_sequence.xml",
        "data/tennis_training_reminder_cron.xml",
        "data/court_schedule_status_data.xml",
        "data/telegram_reminders_cron.xml",
        # Views
        "data/tennis_center_revenue_menu.xml",
        "views/tennis_training_type_views.xml",
        "views/court_schedule_views.xml",
        "views/tennis_center_views.xml",
        "views/tennis_court_views.xml",
        "views/tennis_center_working_hours_views.xml",
        "views/hr_employee_views.xml",
        "views/tennis_trainer_availability_views.xml",
        "views/res_partner_views.xml",
        "views/tennis_trainer_rate_views.xml",
        "views/tennis_center_price_views.xml",
        "views/tennis_training_session_views.xml",
        "views/tennis_trainer_revenue_report_views.xml",
        "report/tennis_trainer_revenue_report_template.xml",
        "report/tennis_center_revenue_report_template.xml",
        "report/tennis_top_statistics_report_template.xml",
        "views/tennis_center_revenue_report_views.xml",
        "views/telegram_notification_views.xml",
        # Wizards
        "wizard/client_balance_wizard_views.xml",
        "wizard/tennis_top_statistics_wizard_views.xml",
        "views/tennis_menu.xml",
    ],
    "demo": [],
    "installable": True,
    "application": True,
    "auto_install": False,
}
