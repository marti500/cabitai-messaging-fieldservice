# Copyright 2026 CabitAI
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""19.0.1.1.0 replaces the example automation rules by built-in reminders and
buttons; the old rules (no-update data) are removed. In SQL: this module no longer
depends on base_automation, so its model may not be loaded yet."""

OLD = (
    "automation_visit_reminder",
    "automation_order_completed",
    "action_visit_reminder",
    "action_order_completed",
)


def migrate(cr, version):
    cr.execute(
        """
        SELECT model, res_id FROM ir_model_data
         WHERE module = 'cabitai_messaging_fieldservice' AND name IN %s
        """,
        [OLD],
    )
    rows = cr.fetchall()
    rules = tuple(res_id for model, res_id in rows if model == "base.automation")
    actions = tuple(res_id for model, res_id in rows if model == "ir.actions.server")
    if actions:
        cr.execute("DELETE FROM ir_act_server WHERE id IN %s", [actions])
    if rules:
        cr.execute("DELETE FROM base_automation WHERE id IN %s", [rules])
    cr.execute(
        """
        DELETE FROM ir_model_data
         WHERE module = 'cabitai_messaging_fieldservice' AND name IN %s
        """,
        [OLD],
    )
