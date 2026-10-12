# WhatsApp appointment reminders for OCA Field Service (Odoo 19)

Free add-on for **[CabitAI Business Messaging](https://apps.odoo.com/apps/modules/19.0/cabitai_messaging)**
that sends WhatsApp appointment reminders for **OCA Field Service** orders, with
**Confirm**, **Change** and **Cancel** buttons that update the order by themselves.

> Not affiliated with, endorsed or sponsored by Meta Platforms, Inc. or WhatsApp LLC.

## What it does

- **Reminder before each visit** (24 hours by default, configurable), sent once per
  order from an hourly job; orders created at the last minute are reminded too, and
  moving an order to another date sends a new reminder.
- **Buttons the customer taps on WhatsApp:**

  | Button  | Effect on the order                                                        |
  | ------- | -------------------------------------------------------------------------- |
  | Confirm | Marked "Confirmed by the customer", optionally moved to a chosen stage     |
  | Change  | Marked "Customer wants to change" + an activity to agree a new time         |
  | Cancel  | Order cancelled, or an activity created (your choice)                      |

- **Thank-you message** when the order is completed.
- **Turnkey:** the module writes the WhatsApp templates (Spanish or English) and
  submits them to Meta; nothing is sent before Meta approves them.
- **Customer Confirmation** column on the orders list, and a **Send WhatsApp** button on
  the order form.
- Messages go to the location's primary contact, or to the location itself; they greet
  the customer by name and show date, time (in the customer's time zone) and address.

## Requirements

- Odoo **19.0** (Community or Enterprise).
- **CabitAI Business Messaging** 19.0, available on
  [Odoo Apps](https://apps.odoo.com/apps/modules/19.0/cabitai_messaging), connected to
  your WhatsApp Business Account.
- **OCA Field Service** 19.0 (`fieldservice`), from
  [github.com/OCA/field-service](https://github.com/OCA/field-service/tree/19.0).

## Installation

1. Put the folder `cabitai_messaging_fieldservice` of this repository in an addons path
   of your Odoo server, next to `fieldservice` and `cabitai_messaging`
   (e.g. `git clone https://github.com/marti500/cabitai-messaging-fieldservice.git`
   and add the clone to `addons_path`).
2. Restart Odoo, update the Apps list and install **CabitAI Business Messaging - Field
   Service** (or tick *Field Service Appointments* in Business Messaging,
   Configuration, Settings).

## Configuration

Field Service, Configuration, Settings, section **WhatsApp**:

1. Choose the WhatsApp account and the language of the templates.
2. Tick the reminder (and the hours before the visit) and/or the completion message.
3. Choose what happens when the customer answers: stage when confirmed (optional),
   whether Cancel cancels the order or creates an activity, and who gets the
   activities.
4. Save and click **Submit templates to Meta**. The status of each template is shown
   next to it; reminders start as soon as Meta approves them.

## How it works

- Settings are stored per company. "Submit templates to Meta" creates two templates
  on the chosen account (reminder with three quick-reply buttons, completion), maps
  their variables to order fields and links each button to one of the module's server
  actions, then submits them through the core's template editor.
- An hourly scheduled action finds open orders whose start is inside the reminder
  window and not yet reminded, queues the reminder with the core (consent, opt-out and
  test mode rules apply) and records the time on the order.
- When the customer taps a button, the core matches the tap to the original message and
  runs the linked action on the order: `_cabitai_customer_confirm`, `_change` or
  `_cancel` on `fsm.order`.
- Completing an order (any path that sets the Completed stage) queues the completion
  message.

## License and support

AGPL-3.0 (see [LICENSE](LICENSE)), as OCA Field Service. Developed by
[CabitAI](https://cabitai.com); support through <https://cabitai.com>.
