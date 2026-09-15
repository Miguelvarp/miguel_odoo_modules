# Partner Budget Tracking

Per-customer yearly budget vs. what's actually happening in Odoo — confirmed
orders, invoiced, and backlog still to invoice. No manual reporting needed:
everything except the budget figure itself is computed from existing Odoo
data (`account.move`, `crm.lead`, `sale.order`).

## What it adds

**New model `partner.budget`** — one row per (customer, company, year):
Budget, Confirmed Orders, Invoiced, Reached %, Remaining. Only `budget_amount`
is typed in; the rest is auto-filled when the row is created and re-checkable
any time with **Refresh** (per row, or **Refresh Selected** above the list to
recheck many rows — or every row matching your filter — in one click).

**Company is optional** — leave it blank for a single Odoo-wide target for
that customer/year, not tied to any one company. A blank-company line rolls
up Confirmed Orders and Invoiced across **every** company (still scoped to
the customer, via `commercial_partner_id`/`child_of` like every other line),
converting each company's own-currency amounts to EUR before summing — EUR
is also the fixed currency for entering and displaying the blank-company
line itself. A given customer/year can still have only one blank-company
line (enforced in Python, since a plain SQL unique constraint doesn't stop
several NULL `company_id` rows). The Customer form's "This Year" tab falls
back to a blank-company line when there's no line for the active company.

**On the Customer form** (`res.partner`):

- A **Budget** tab:
  - This Year: Budget, Confirmed Orders, Invoiced, Budget Reached (%),
    Budget Remaining
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

- **Rolled up to the ultimate parent company** (`commercial_partner_id`):
  Confirmed Orders, Invoiced and Backlog all match the customer *and every
  individual contact under it*, not just the exact contact record the order
  or invoice happens to be attached to or the budget line happens to be set
  on. Whichever contact a salesperson picked when creating the order still
  counts against the company's budget.
- **Confirmed Orders (of the budget year)**: the full untaxed value of
  confirmed sales orders (`state = sale`) whose order date falls in that
  year — regardless of whether they've been invoiced yet. A leading
  indicator alongside Invoiced (the lagging, "actually billed" figure).
  Converted to company currency (orders are in their own currency, not
  necessarily the company's).
- **Invoiced (of the budget year)**: posted customer invoices minus credit
  notes (`amount_untaxed_signed`), matching the line's own year. This Odoo
  field is already expressed in the **company's own currency** (converted
  at the invoice's date rate) regardless of what currency the invoice was
  raised in — nothing extra needed here.
- **Reached %** / **Remaining**: still Budget vs. Invoiced specifically (not
  Confirmed Orders) — unchanged definition, just now correctly rolled up.
- **Pipeline (Expected)** / **Pipeline (Weighted)**: open opportunities
  (`probability < 100` — excludes both lost and already-won) linked to the
  customer's ultimate parent company *or any direct contact under it*,
  summed on `expected_revenue` / `expected_revenue × probability`. **Stored +
  auto-recomputed**: installing or upgrading this module backfills it for
  every existing opportunity, and editing an opportunity's expected revenue
  or probability updates it immediately — not just for newly created
  opportunities. Opening either the parent's form or a child contact's form
  shows the same total. One difference from the rest of this module, for a
  reason that doesn't apply to it (a stored field can't safely depend on
  which company happens to be active when it's viewed): pipeline is **not
  company-scoped** — it aggregates across all companies. Flag if that
  becomes a problem in practice; fixing it adds real complexity (per-company
  stored fields, or giving up the auto-recompute).
- **Backlog to Invoice**: confirmed sales orders, summed on the line-level
  `untaxed_amount_to_invoice`, across **any** order year (unlike Confirmed
  Orders/Invoiced above, which are scoped to one specific budget year) — a
  standing "what's still owed" figure. That field is in the order's own
  currency, so each line is explicitly converted to company currency at
  today's rate before summing.
- Invoiced/Confirmed Orders/Backlog/the This-Year summary are all further
  scoped to **the active company** — except a blank-company budget line
  (see above), which is Odoo-wide by design.

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
