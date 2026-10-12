# Copyright 2026 CabitAI
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "CabitAI Business Messaging - Field Service",
    "summary": "WhatsApp appointment reminders with Confirm, Change and Cancel "
    "buttons for field service orders",
    "version": "19.0.1.1.0",
    "category": "Field Service",
    "author": "CabitAI",
    "website": "https://cabitai.com",
    "license": "AGPL-3",
    "depends": ["cabitai_messaging", "fieldservice"],
    "data": [
        "data/ir_actions_server.xml",
        "data/ir_cron.xml",
        "views/fsm_order_views.xml",
        "views/res_config_settings_views.xml",
    ],
    "images": ["static/description/banner.png"],
    "installable": True,
    "auto_install": False,
}
