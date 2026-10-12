# Copyright 2026 CabitAI
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from datetime import timedelta

from odoo import api, fields, models


class FsmOrder(models.Model):
    _inherit = "fsm.order"

    cabitai_customer_state = fields.Selection(
        [
            ("pending", "Waiting for confirmation"),
            ("confirmed", "Confirmed by the customer"),
            ("change", "Customer wants to change"),
            ("cancel", "Customer wants to cancel"),
        ],
        string="Customer Confirmation",
        readonly=True,
        copy=False,
        tracking=True,
    )
    cabitai_reminder_sent_at = fields.Datetime(
        string="WhatsApp Reminder Sent", readonly=True, copy=False
    )
    cabitai_customer_name = fields.Char(
        string="Customer Name for Messages",
        compute="_compute_cabitai_customer_name",
        help="The location's primary contact, or the location itself.",
    )

    @api.depends("location_id.contact_id.name", "location_id.name")
    def _compute_cabitai_customer_name(self):
        for order in self:
            location = order.location_id
            order.cabitai_customer_name = location.contact_id.name or location.name

    def write(self, vals):
        completed = self.env.ref("fieldservice.fsm_stage_completed")
        completing = self.browse()
        if vals.get("stage_id") == completed.id:
            completing = self.filtered(lambda o: o.stage_id != completed)
        moved = self.browse()
        if "scheduled_date_start" in vals:
            new_start = fields.Datetime.to_datetime(vals["scheduled_date_start"])
            moved = self.filtered(lambda o: o.scheduled_date_start != new_start)
        res = super().write(vals)
        if moved:
            # A new date needs a new reminder and a new confirmation.
            moved.write(
                {"cabitai_reminder_sent_at": False, "cabitai_customer_state": False}
            )
        if completing:
            completing._cabitai_send_completion()
        return res

    # ------------------------------------------------------------------
    # Messages
    # ------------------------------------------------------------------

    @api.model
    def _cabitai_cron_send_reminders(self):
        """Remind every upcoming order once, as soon as it is inside the reminder
        window (orders created at the last minute are reminded too)."""
        now = fields.Datetime.now()
        companies = self.env["res.company"].search(
            [("cabitai_fsm_reminder", "=", True)]
        )
        for company in companies:
            template = company.cabitai_fsm_reminder_template_id
            if template.meta_status != "approved":
                continue
            limit = now + timedelta(hours=company.cabitai_fsm_reminder_hours or 24)
            orders = self.search(
                [
                    ("company_id", "=", company.id),
                    ("cabitai_reminder_sent_at", "=", False),
                    ("stage_id.is_closed", "=", False),
                    ("scheduled_date_start", ">", now),
                    ("scheduled_date_start", "<=", limit),
                ]
            )
            if orders:
                self.env["cabitai.messaging.message"]._enqueue(template, orders)
                orders.write(
                    {
                        "cabitai_reminder_sent_at": now,
                        "cabitai_customer_state": "pending",
                    }
                )

    def _cabitai_send_completion(self):
        for company in self.company_id:
            template = company.cabitai_fsm_completion_template_id
            if company.cabitai_fsm_completion and template.meta_status == "approved":
                orders = self.filtered(lambda o, c=company: o.company_id == c)
                self.env["cabitai.messaging.message"]._enqueue(template, orders)

    # ------------------------------------------------------------------
    # Buttons tapped by the customer (server actions of this module)
    # ------------------------------------------------------------------

    def _cabitai_customer_confirm(self):
        for order in self:
            values = {"cabitai_customer_state": "confirmed"}
            stage = order.company_id.cabitai_fsm_confirm_stage_id
            if stage and not order.stage_id.is_closed:
                values["stage_id"] = stage.id
            order.write(values)

    def _cabitai_customer_change(self):
        self.write({"cabitai_customer_state": "change"})
        self._cabitai_schedule_activity(
            self.env._("The customer asked on WhatsApp to change this appointment.")
        )

    def _cabitai_customer_cancel(self):
        self.write({"cabitai_customer_state": "cancel"})
        for order in self:
            if order.company_id.cabitai_fsm_cancel_mode == "activity" or (
                order.stage_id.is_closed
            ):
                order._cabitai_schedule_activity(
                    self.env._(
                        "The customer asked on WhatsApp to cancel this appointment."
                    )
                )
            else:
                order.action_cancel()

    def _cabitai_schedule_activity(self, summary):
        for order in self:
            user = order.company_id.cabitai_fsm_activity_user_id or order.create_uid
            order.activity_schedule(
                "mail.mail_activity_data_todo", summary=summary, user_id=user.id
            )
