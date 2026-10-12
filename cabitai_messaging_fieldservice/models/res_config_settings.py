# Copyright 2026 CabitAI
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    cabitai_fsm_account_id = fields.Many2one(
        related="company_id.cabitai_fsm_account_id", readonly=False
    )
    cabitai_fsm_lang = fields.Selection(
        related="company_id.cabitai_fsm_lang", readonly=False
    )
    cabitai_fsm_reminder = fields.Boolean(
        related="company_id.cabitai_fsm_reminder", readonly=False
    )
    cabitai_fsm_reminder_hours = fields.Integer(
        related="company_id.cabitai_fsm_reminder_hours", readonly=False
    )
    cabitai_fsm_completion = fields.Boolean(
        related="company_id.cabitai_fsm_completion", readonly=False
    )
    cabitai_fsm_confirm_stage_id = fields.Many2one(
        related="company_id.cabitai_fsm_confirm_stage_id", readonly=False
    )
    cabitai_fsm_cancel_mode = fields.Selection(
        related="company_id.cabitai_fsm_cancel_mode", readonly=False
    )
    cabitai_fsm_activity_user_id = fields.Many2one(
        related="company_id.cabitai_fsm_activity_user_id", readonly=False
    )
    cabitai_fsm_reminder_status = fields.Selection(
        related="company_id.cabitai_fsm_reminder_template_id.meta_status",
        string="Reminder Template Status",
    )
    cabitai_fsm_completion_status = fields.Selection(
        related="company_id.cabitai_fsm_completion_template_id.meta_status",
        string="Completion Template Status",
    )

    def action_cabitai_fsm_setup_templates(self):
        self.ensure_one()
        # Save the choices first: the button may be pressed before "Save".
        self.execute()
        self.company_id._cabitai_fsm_setup_templates()
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "type": "success",
                "message": self.env._(
                    "Templates submitted to Meta. Nothing is sent until Meta "
                    "approves them; the status updates by itself."
                ),
                "next": {"type": "ir.actions.client", "tag": "soft_reload"},
            },
        }
