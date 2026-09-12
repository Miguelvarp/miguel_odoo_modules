# Partner Budget Tracking

Per-customer yearly budget vs. what's actually happening in Odoo — invoiced,
pipeline, and backlog still to invoice. No manual reporting needed: everything
except the budget figure itself is computed from existing Odoo data
(`account.move`, `crm.lead`, `sale.order`).

## What it adds

**New model `partner.budget`** — one row per (customer, company, year): a
`budget_amount` plus a per-row Invoiced / Reached % / Remaining, auto-filled
when the row is created and re-checkable any time with the **Refresh** button.

**On the Customer form** (`res.partner`):

- A **Budget** tab:
  - This Year: Budget, Invoiced, Budget Reached (%), Budget Remaining
  - Pipeline & Backlog: Pipeline (Expected), Pipeline (Weighted by
    probability), Backlog to Invoice
  - An editable list of budget lines — add a row per company/year here.
    **This is where you input the budget**, one customer at a time.
- 3 smart buttons in the header (Invoiced / Pipeline / Backlog) that jump
  to the underlying invoices / opportunities / sales orders.

**Sales → Partner Budgets** — a read-only, sortable, summable list across
every customer with the same KPI columns, for a portfolio-level view.

**Sales → Budget Lines** — the raw `partner.budget` records, one row per
customer/company/year. Supports normal create/edit **and Odoo's built-in
Import**: use *Favorites → Import records* to bulk-load budgets for every
customer in one file. Odoo's Import wizard can generate a blank template
with the right columns (Customer, Company, Year, Budget) — match "Customer"
either by exact name or, more reliably for a bulk file, by internal ID
(`partner_id/id` / the customer's database id) or External ID if you have
one. Existing (customer, company, year) rows are protected by a unique
constraint, so re-importing the same file is safe (it'll error per-row on
duplicates rather than double them) — use *Update* mode in the Import wizard
if you're re-importing to change amounts.

## Definitions — everything below is untaxed / excludes VAT

- **Invoiced (This Year)**: posted customer invoices minus credit notes
  (`amount_untaxed_signed`), current calendar year, current company. This
  Odoo field is already expressed in the **company's own currency**
  (converted at the invoice's date rate) regardless of what currency the
  invoice was raised in — nothing extra needed here.
- **Pipeline (Expected)** / **Pipeline (Weighted)**: open opportunities
  (`probability < 100` — excludes both lost and already-won) linked
  *directly* to the customer record, summed on `expected_revenue` /
  `expected_revenue × probability`. **Stored + auto-recomputed**: installing
  or upgrading this module backfills it for every existing opportunity, and
  editing an opportunity's expected revenue or probability updates it
  immediately — not just for newly created opportunities. Note: because a
  stored field can't safely depend on which company happens to be active
  when it's viewed, this one is **not company-scoped** and does **not** roll
  up child contacts the way Invoiced/Backlog do (see below).
- **Backlog to Invoice**: confirmed sales orders (`state = sale`), summed on
  the line-level `untaxed_amount_to_invoice`. That field is in the *order's
  own currency*, not the company's, so each line is explicitly converted to
  the company currency at today's rate before summing (`Currency._convert`).
- Invoiced/Backlog/the This-Year summary are scoped to **the active company**
  and match the customer *and its child contacts* (`child_of`), so they roll
  up correctly whether invoices/opportunities sit on the company record or
  on a contact under it.

## Testing locally

Docker stack in `../../odoo-dev` (Odoo 17, http://localhost:8069) mounts this
folder. Start it, install **Sales** and **CRM** if not already installed,
then install **Partner Budget Tracking** from Apps.

After Python edits, re-apply with
`../../odoo-dev/update-module.ps1 -Module partner_budget` **and then restart**
(`docker compose restart odoo`) — on Windows, bind-mount file changes don't
reliably trigger `dev_mode`'s auto-restart, so the running server can keep
serving stale code after an `-u` upgrade until it's restarted manually.

## Deploying to production (Odoo.sh)

Contains Python, so *Apps → Import Module* will reject it. Hand the module
folder (or zip) to whoever manages the Odoo.sh git repo to push via a
dev/staging branch.
