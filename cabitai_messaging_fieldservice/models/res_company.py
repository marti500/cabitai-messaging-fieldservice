# Copyright 2026 CabitAI
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models
from odoo.exceptions import UserError

# Templates the module writes and submits for the customer. Variables:
# (position, field path, format, fallback, example).
TEMPLATES = {
    "es": {
        "reminder": {
            "name": "fs_recordatorio_cita",
            "body": "Hola {{1}}, te recordamos tu cita el {{2}} a las {{3}} en {{4}}. "
            "¿Nos la confirmas?",
            "variables": [
                (1, "cabitai_customer_name", "auto", "cliente", "Ana"),
                (2, "scheduled_date_start", "date", False, "14/10/2026"),
                (3, "scheduled_date_start", "time", False, "10:00"),
                (
                    4,
                    "location_id.street",
                    "auto",
                    "la dirección acordada",
                    "Calle Mayor 1",
                ),
            ],
            "buttons": [
                ("Confirmar", "action_customer_confirm"),
                ("Cambiar cita", "action_customer_change"),
                ("Cancelar", "action_customer_cancel"),
            ],
        },
        "completion": {
            "name": "fs_servicio_completado",
            "body": "Hola {{1}}, hemos completado el servicio en {{2}}. "
            "¡Gracias por confiar en nosotros!",
            "variables": [
                (1, "cabitai_customer_name", "auto", "cliente", "Ana"),
                (2, "location_id.street", "auto", "tu dirección", "Calle Mayor 1"),
            ],
            "buttons": [],
        },
    },
    "en": {
        "reminder": {
            "name": "fs_appointment_reminder",
            "body": "Hello {{1}}, this is a reminder of your appointment on {{2}} at "
            "{{3}}, at {{4}}. Can you confirm it?",
            "variables": [
                (1, "cabitai_customer_name", "auto", "customer", "Ann"),
                (2, "scheduled_date_start", "date", False, "10/14/2026"),
                (3, "scheduled_date_start", "time", False, "10:00 AM"),
                (
                    4,
                    "location_id.street",
                    "auto",
                    "the agreed address",
                    "1 Main Street",
                ),
            ],
            "buttons": [
                ("Confirm", "action_customer_confirm"),
                ("Change", "action_customer_change"),
                ("Cancel", "action_customer_cancel"),
            ],
        },
        "completion": {
            "name": "fs_service_completed",
            "body": "Hello {{1}}, we have completed the service at {{2}}. "
            "Thank you for your trust!",
            "variables": [
                (1, "cabitai_customer_name", "auto", "customer", "Ann"),
                (2, "location_id.street", "auto", "your address", "1 Main Street"),
            ],
            "buttons": [],
        },
    },
}


class ResCompany(models.Model):
    _inherit = "res.company"

    cabitai_fsm_account_id = fields.Many2one(
        "cabitai.messaging.account", string="WhatsApp Account for Field Service"
    )
    cabitai_fsm_lang = fields.Selection(
        [("es", "Spanish"), ("en", "English")],
        string="WhatsApp Template Language",
        default="es",
    )
    cabitai_fsm_reminder = fields.Boolean(string="WhatsApp Appointment Reminder")
    cabitai_fsm_reminder_hours = fields.Integer(
        string="Reminder Hours Before", default=24
    )
    cabitai_fsm_completion = fields.Boolean(string="WhatsApp Message on Completion")
    cabitai_fsm_confirm_stage_id = fields.Many2one(
        "fsm.stage",
        string="Stage When Confirmed",
        domain="[('stage_type', '=', 'order'), ('is_closed', '=', False)]",
    )
    cabitai_fsm_cancel_mode = fields.Selection(
        [
            ("cancel", "Cancel the order"),
            ("activity", "Create an activity"),
        ],
        string="When the Customer Cancels",
        default="cancel",
    )
    cabitai_fsm_activity_user_id = fields.Many2one(
        "res.users",
        string="Activities For",
        domain=[("share", "=", False)],
        help="Who gets the activities when a customer asks to change or cancel. "
        "Empty: whoever created the order.",
    )
    cabitai_fsm_reminder_template_id = fields.Many2one(
        "cabitai.messaging.template", string="Reminder Template", readonly=True
    )
    cabitai_fsm_completion_template_id = fields.Many2one(
        "cabitai.messaging.template", string="Completion Template", readonly=True
    )

    def _cabitai_fsm_setup_templates(self):
        """Write the reminder and completion templates (with their variables and
        buttons) on the chosen account, and submit the drafts to Meta."""
        self.ensure_one()
        account = self.cabitai_fsm_account_id
        if not account:
            raise UserError(self.env._("Choose the WhatsApp account first."))
        specs = TEMPLATES[self.cabitai_fsm_lang or "es"]
        for kind in ("reminder", "completion"):
            field = f"cabitai_fsm_{kind}_template_id"
            template = self[field]
            spec = specs[kind]
            if template.account_id != account or template.name != spec["name"]:
                template = self._cabitai_fsm_template(account, spec)
                self[field] = template
            if template.meta_status in ("draft", "rejected", "paused"):
                template._submit_to_meta()

    def _cabitai_fsm_template(self, account, spec):
        Template = self.env["cabitai.messaging.template"].with_context(
            active_test=False
        )
        lang = self.cabitai_fsm_lang or "es"
        template = Template.search(
            [
                ("account_id", "=", account.id),
                ("name", "=", spec["name"]),
                ("lang_code", "=", lang),
            ],
            limit=1,
        )
        if template:
            template.active = True
            return template
        template = Template.create(
            {
                "account_id": account.id,
                "name": spec["name"],
                "lang_code": lang,
                "category": "utility",
                "model_id": self.env["ir.model"]._get("fsm.order").id,
                "body_text": spec["body"],
                "button_ids": [
                    (0, 0, {"button_type": "quick_reply", "text": text, "sequence": n})
                    for n, (text, _action) in enumerate(spec["buttons"])
                ],
            }
        )
        variables = {v.position: v for v in template.variable_ids}
        for position, path, value_format, fallback, sample in spec["variables"]:
            variables[position].write(
                {
                    "field_path": path,
                    "value_format": value_format,
                    "fallback": fallback,
                    "sample": sample,
                }
            )
        for button, (_text, action) in zip(
            template.button_ids, spec["buttons"], strict=True
        ):
            button.action_id = self.env.ref(f"cabitai_messaging_fieldservice.{action}")
        return template
