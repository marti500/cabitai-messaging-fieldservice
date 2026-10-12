# Copyright 2026 CabitAI
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, models

# The person to notify at the service location; the location itself (it inherits
# a contact) is the fallback when no contact person is set or has a phone.
FSM_RECIPIENT_PATH = "location_id.contact_id"


class CabitaiMessagingTemplate(models.Model):
    _inherit = "cabitai.messaging.template"

    @api.depends("model_id")
    def _compute_recipient_path(self):
        res = super()._compute_recipient_path()
        for template in self.filtered(lambda t: t.model_id.model == "fsm.order"):
            template.recipient_path = FSM_RECIPIENT_PATH
        return res

    def _get_recipient(self, record):
        partner, phone = super()._get_recipient(record)
        if (
            phone
            or record._name != "fsm.order"
            or self.recipient_path != FSM_RECIPIENT_PATH
        ):
            return partner, phone
        location = record.location_id.partner_id
        if not location.phone:
            return partner, phone
        country = location.country_id or record.env.company.country_id
        return location, location._phone_format(number=location.phone, country=country)
