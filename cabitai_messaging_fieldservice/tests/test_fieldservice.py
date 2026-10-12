# Copyright 2026 CabitAI
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from datetime import timedelta

from odoo import fields

from odoo.addons.cabitai_messaging.tests.common import MessagingCase, fake_response
from odoo.addons.cabitai_messaging.tests.test_webhook import inbound_payload


def created(template_id):
    return fake_response(
        200, {"id": template_id, "status": "PENDING", "category": "UTILITY"}
    )


class TestFieldService(MessagingCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env["res.lang"]._activate_lang("es_ES")
        cls.account_a.write({"require_opt_in": False, "test_mode": False})
        cls.contact = cls.env["res.partner"].create(
            {
                "name": "Test Site Contact",
                "phone": "+34600000002",
                "lang": "es_ES",
                "tz": "Europe/Madrid",
            }
        )
        site = cls.env["res.partner"].create(
            {"name": "Test Site", "phone": "+34600000003", "street": "Test Street 1"}
        )
        cls.location = cls.env["fsm.location"].create(
            {
                "name": "Test Site",
                "partner_id": site.id,
                "owner_id": site.id,
                "contact_id": cls.contact.id,
            }
        )
        cls.company = cls.env.company
        cls.company.write(
            {
                "cabitai_fsm_account_id": cls.account_a.id,
                "cabitai_fsm_lang": "es",
                "cabitai_fsm_reminder": True,
                "cabitai_fsm_completion": True,
            }
        )
        cls.Message = cls.env["cabitai.messaging.message"]

    def setup_templates(self, approve=True):
        with self.mock_meta(
            created("300000000000101"), created("300000000000102")
        ) as mock:
            self.company._cabitai_fsm_setup_templates()
        templates = (
            self.company.cabitai_fsm_reminder_template_id
            | self.company.cabitai_fsm_completion_template_id
        )
        if approve:
            templates.write({"meta_status": "approved"})
        return mock

    def order(self, hours=20, **values):
        start = fields.Datetime.now() + timedelta(hours=hours)
        return self.env["fsm.order"].create(
            {"location_id": self.location.id, "scheduled_date_start": start, **values}
        )

    def messages_for(self, orders):
        return self.Message.search(
            [("res_model", "=", "fsm.order"), ("res_id", "in", orders.ids)]
        )

    def tap(self, message, index, wamid):
        text = message.template_id.button_ids.filtered(
            lambda b: b.button_index == index
        ).text
        payload = inbound_payload(text, wamid, "34600000002")
        data = payload["entry"][0]["changes"][0]["value"]["messages"][0]
        data.pop("text")
        data.update(
            {
                "type": "button",
                "button": {"text": text, "payload": f"cabitai:{message.id}:{index}"},
            }
        )
        self.account_a._process_webhook(payload)

    # -- recipient ----------------------------------------------------------

    def test_default_recipient_path(self):
        template = self.env["cabitai.messaging.template"].create(
            {
                "account_id": self.account_a.id,
                "name": "manual_template",
                "lang_code": "es",
                "model_id": self.env["ir.model"]._get("fsm.order").id,
            }
        )
        self.assertEqual(template.recipient_path, "location_id.contact_id")
        order = self.order()
        self.assertEqual(template._get_recipient(order), (self.contact, "+34600000002"))
        self.assertEqual(order.cabitai_customer_name, "Test Site Contact")
        self.contact.phone = False
        self.location.contact_id = False
        self.assertEqual(order.cabitai_customer_name, "Test Site")
        self.location.contact_id = self.contact
        self.assertEqual(
            template._get_recipient(order),
            (self.location.partner_id, "+34600000003"),
        )

    # -- templates ----------------------------------------------------------

    def test_setup_writes_and_submits_the_templates(self):
        mock = self.setup_templates(approve=False)
        reminder = self.company.cabitai_fsm_reminder_template_id
        self.assertEqual(reminder.name, "fs_recordatorio_cita")
        self.assertEqual(reminder.meta_status, "pending")
        self.assertEqual(
            reminder.variable_ids.sorted("position").mapped("field_path"),
            [
                "cabitai_customer_name",
                "scheduled_date_start",
                "scheduled_date_start",
                "location_id.street",
            ],
        )
        ref = self.env.ref
        self.assertEqual(
            reminder.button_ids.mapped("action_id"),
            ref("cabitai_messaging_fieldservice.action_customer_confirm")
            | ref("cabitai_messaging_fieldservice.action_customer_change")
            | ref("cabitai_messaging_fieldservice.action_customer_cancel"),
        )
        sent = mock.call_args_list[0].kwargs["json"]
        self.assertEqual(
            [b["text"] for b in sent["components"][-1]["buttons"]],
            ["Confirmar", "Cambiar cita", "Cancelar"],
        )
        with self.mock_meta() as again:
            self.company._cabitai_fsm_setup_templates()
        self.assertFalse(again.called, "pending templates are not submitted twice")

    # -- reminders and completion -------------------------------------------

    def test_reminder_sent_once_inside_the_window(self):
        self.setup_templates()
        due = self.order(20)
        late = self.order(2)
        later = self.order(30)
        cancelled = self.order(10)
        cancelled.action_cancel()
        self.env["fsm.order"]._cabitai_cron_send_reminders()
        self.assertEqual(len(self.messages_for(due | late)), 2)
        self.assertFalse(self.messages_for(later | cancelled))
        self.assertEqual(due.cabitai_customer_state, "pending")
        self.env["fsm.order"]._cabitai_cron_send_reminders()
        self.assertEqual(len(self.messages_for(due | late)), 2, "never twice")
        # The message shows the visit time in the customer's time zone.
        local = fields.Datetime.context_timestamp(
            due.with_context(tz="Europe/Madrid"), due.scheduled_date_start
        )
        self.assertIn(local.strftime("%H:%M"), self.messages_for(due).body)

    def test_nothing_sent_before_approval(self):
        self.setup_templates(approve=False)
        order = self.order(20)
        self.env["fsm.order"]._cabitai_cron_send_reminders()
        order.action_complete()
        self.assertFalse(self.messages_for(order))

    def test_rescheduling_resets_the_reminder(self):
        self.setup_templates()
        order = self.order(20)
        self.env["fsm.order"]._cabitai_cron_send_reminders()
        order.scheduled_date_start = fields.Datetime.now() + timedelta(hours=10)
        self.assertFalse(order.cabitai_reminder_sent_at or order.cabitai_customer_state)
        self.env["fsm.order"]._cabitai_cron_send_reminders()
        self.assertEqual(len(self.messages_for(order)), 2)

    def test_completion_message(self):
        self.setup_templates()
        order = self.order(-1)
        order.action_complete()
        message = self.messages_for(order)
        self.assertEqual(message.template_id.name, "fs_servicio_completado")
        self.assertIn("Test Street 1", message.body)

    # -- buttons ------------------------------------------------------------

    def reminded(self):
        order = self.order(20)
        self.env["fsm.order"]._cabitai_cron_send_reminders()
        return order, self.messages_for(order)

    def test_confirm(self):
        self.setup_templates()
        stage = self.env["fsm.stage"].create(
            {"name": "Confirmed (test)", "stage_type": "order", "sequence": 20}
        )
        self.company.cabitai_fsm_confirm_stage_id = stage
        order, message = self.reminded()
        self.tap(message, 0, "wamid.TEST9201")
        self.assertEqual(order.cabitai_customer_state, "confirmed")
        self.assertEqual(order.stage_id, stage)

    def test_change_creates_an_activity(self):
        self.setup_templates()
        order, message = self.reminded()
        self.tap(message, 1, "wamid.TEST9202")
        self.assertEqual(order.cabitai_customer_state, "change")
        self.assertEqual(len(order.activity_ids), 1)

    def test_cancel(self):
        self.setup_templates()
        order, message = self.reminded()
        self.tap(message, 2, "wamid.TEST9203")
        self.assertEqual(order.cabitai_customer_state, "cancel")
        self.assertEqual(
            order.stage_id, self.env.ref("fieldservice.fsm_stage_cancelled")
        )
        self.company.cabitai_fsm_cancel_mode = "activity"
        other, message = self.reminded()
        self.tap(message, 2, "wamid.TEST9204")
        self.assertFalse(other.stage_id.is_closed)
        self.assertEqual(len(other.activity_ids), 1)
