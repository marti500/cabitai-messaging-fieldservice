============================================
CabitAI Business Messaging - Field Service
============================================

Appointment messages for OCA Field Service orders, on top of CabitAI Business
Messaging. Turnkey: choose the account in the settings and tick what you want; no
automation rule to write.

- A reminder before each visit (24 hours by default) with **Confirm**, **Change** and
  **Cancel** buttons. Confirm marks the order (and can move it to a stage), Change
  creates an activity to agree a new time, Cancel cancels the order or creates an
  activity.
- A thank-you message when the order is completed.
- The module writes the templates (Spanish or English) and submits them to Meta;
  nothing is sent before Meta approves them.
- The customer's answer is shown on the order (waiting, confirmed, wants to change,
  wants to cancel).
- Messages go to the location's primary contact, or to the location itself.
- A "Send WhatsApp" button on the order form for any other template.

This module is not affiliated with, endorsed or sponsored by Meta or WhatsApp.

**Table of contents**

.. contents::
   :local:

Configuration
=============

In Field Service, Configuration, Settings, section WhatsApp:

#. Choose the WhatsApp account and the language of the templates.
#. Tick the reminder (and its hours before the visit) and/or the completion message.
#. Choose what happens when the customer answers: the stage when they confirm
   (optional), whether Cancel cancels the order or creates an activity, and who gets
   the activities.
#. Click **Submit templates to Meta**. The status of each template is shown next to
   it; reminders start as soon as Meta approves them.

Usage
=====

Nothing to do day to day: every hour, upcoming orders inside the reminder window get
their reminder once. Moving an order to another date resets its reminder. The
"Customer Confirmation" column of the orders list shows the answers; activities appear
for the changes and cancellations to handle. The customer's answer opens the 24-hour
window, so the conversation can continue from Discuss if installed.

Other messages can be sent with the "Send WhatsApp" button on the order, and your own
automation rules can still use the "Send WhatsApp Message" server action.

Changelog
=========

19.0.1.1.0 (2026-10-12)
-----------------------

Turnkey appointments: settings section, templates written and submitted by the
module, reminders with Confirm, Change and Cancel buttons, completion message, customer
confirmation on the order. The example automation rules are removed and the module no
longer depends on Automation Rules.

19.0.1.0.0 (2026-10-12)
-----------------------

First release: default recipient for field service orders, send button and example
automation rules.

Support
=======

Contact CabitAI through https://cabitai.com.

Credits
=======

Authors
-------

* CabitAI

Contributors
------------

* CabitAI (https://cabitai.com)
