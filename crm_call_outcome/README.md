# CRM Call Outcome

Adds a popup on a **lead / opportunity** to log the result of a phone call:

- **Call status** (radio, required): Connected / Voice mail
- **Outcome** (radio): Not interested / Right person not in the office / Request to call back
- **Feedback** (free text)

On **Log call** the module:

1. stores a `crm.call.outcome` record (one row per call) for reporting;
2. logs a completed **Call** activity on the lead (visible in the chatter);
3. if the outcome is *Request to call back*, also schedules an **open** Call
   activity for the chosen date, so it lands in "My Activities".

It does not change any other field on the lead.

## Reporting

*CRM → Reporting → Call Outcomes* — pivot / graph / list of every logged call,
pre-grouped by caller for the current month. Filter by call status, outcome,
team, stage, week. Each lead/opportunity also shows a **Calls** stat button
linking to its own calls.

This is a standalone module: install it, and uninstall it cleanly if it causes
trouble (see "Uninstall" below).

## What it contains

| File | Purpose |
|---|---|
| `wizard/call_outcome_wizard.py` | `crm.call.outcome.wizard` – a `TransientModel` (no permanent table) |
| `wizard/call_outcome_wizard_views.xml` | the popup form + the window action |
| `views/crm_lead_views.xml` | inherits the CRM lead form, adds a "Log call" button next to Phone |
| `security/ir.model.access.csv` | access to the wizard for all internal users |
| `static/src/*` | **Option B** – optional custom phone-icon widget, disabled by default |

The window action is also registered as a **contextual action** ("Action" menu)
on `crm.lead`, so it works even if the form button is ever removed.

## Install

### Odoo.sh
1. Put this folder in your Odoo.sh addons repository (top level, folder name `crm_call_outcome`).
2. Commit & push to a **staging** branch → wait for the build.
3. On staging: *Apps* → update list → search "CRM Call Outcome" → **Install**.
4. Test on a lead, then merge the branch to **production**.

### Self-hosted
1. Copy the folder into a directory on your `addons_path`.
2. Restart Odoo, then:
   ```
   odoo -u crm_call_outcome -d <database>
   ```
   or *Apps* → update list → Install.

## Use

Open any lead or opportunity that has a phone number → click **Log call** next
to the Phone field → fill the popup → **Log call**. The result appears in the
chatter.

## Option B – click the phone icon instead of a button

Only relevant on **Odoo Enterprise** (Community has no call icon on the phone
field at all).

1. In `__manifest__.py`, uncomment the `assets` block.
2. Replace the button in `views/crm_lead_views.xml` with:
   ```xml
   <xpath expr="//field[@name='phone']" position="attributes">
       <attribute name="widget">phone_outcome</attribute>
   </xpath>
   ```
3. Upgrade the module.

The custom widget keeps the standard phone behaviour and adds one extra icon
that opens the same popup.

## Uninstall

*Apps* → CRM Call Outcome → **Uninstall**.

Removed on uninstall: the wizard, the `crm.call.outcome` model **and its rows**
(the table is dropped), the popup + reporting views, the menu, the inherited
form changes (buttons disappear), and the assets. Two extra fields added to
`crm.lead` (`call_outcome_ids`, `call_outcome_count`) are computed/one2many, so
nothing is left in the `crm_lead` table. **Chatter messages and completed
"Call" activities already logged stay** – they are `mail.message` records on
the leads, not owned by this module.

> If you want to keep the historical call rows before uninstalling, export
> *CRM → Reporting → Call Outcomes* to Excel first.

## Reporting outside Odoo (Supabase mirror)

To get call outcomes into the Supabase `odoo` mirror for dashboards, follow the
checklist in the repo `CLAUDE.md` ("Adding a new Odoo model to the Supabase
mirror") for model `crm.call.outcome`:
fields `lead_id, partner_id, team_id, company_id, stage_id, user_id, call_date,
call_status, disposition, feedback`. Reads/reporting then go through the mirror;
the popup keeps writing straight to Odoo.
