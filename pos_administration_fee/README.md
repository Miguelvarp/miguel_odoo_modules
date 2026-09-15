# POS Administration Fee

Automatically adds an "Administration Fee" line to a POS order whenever its
total falls below a configurable threshold, and removes/adjusts it live as
the order changes - no cashier action needed.

## What it adds

**3 new fields on `pos.config`** (per Point of Sale, not global):

- **Administration Fee** (toggle) - `administration_fee_enabled`
- **Administration Fee Threshold** - `administration_fee_threshold`
  (default 10.0). Orders with a tax-included total below this amount get
  the fee line added automatically; it's removed again once the total is
  back at or above this amount.
- **Administration Fee Amount** - `administration_fee_amount` (default 2.0).
  The fee line's amount.
- **Administration Fee Product** - `administration_fee_product_id`. The
  product used for the fee line - create a regular product for this (e.g.
  "Administration Fee"), tick **Available in POS** on it, and set whatever
  tax you want charged on the fee itself. Consider leaving it out of any
  POS category so it doesn't also show up as a tile cashiers can tap.

All four are configurable in **Point of Sale → Configuration → Settings**,
same place as the built-in Tips setting (right below it) - per-POS, exactly
like Tips.

**POS frontend behavior**: the fee line is kept in sync live, the same way
the built-in tip line works, on every order-changing action - adding or
removing a product, changing quantity, price, or discount on any line. It's
excluded from its own threshold calculation (the fee doesn't count toward
triggering itself), and self-heals if the configured amount changes
mid-order.

## Setup

1. Create a product for the fee (**Point of Sale → Products → Products**),
   tick **Available in POS**, set a name (e.g. "Administration Fee") and
   whatever tax applies.
2. **Point of Sale → Configuration → Settings**, pick the POS at the top,
   find **Administration Fee** (below Tips), enable it, and fill in the
   threshold, amount, and the product from step 1.
3. Open a POS session and test: ring up an order under the threshold - the
   fee line should appear automatically; add another item to cross the
   threshold - it should disappear.

## Testing locally

Docker stack in `../../odoo-dev` (Odoo 17, http://localhost:8069) mounts
this folder. Start it, install **Point of Sale**, then install
**POS Administration Fee** from Apps.

This module ships only JS (POS frontend) + view/field changes, no server
Python logic beyond plain fields, so after edits:

- **JS changes**: hard-refresh the POS UI tab (`Ctrl+Shift+R`) - POS assets
  are a separate bundle from the backend and don't hot-reload with
  `dev_mode = reload`.
- **View/field changes**: `..\..\odoo-dev\update-module.ps1 -Module pos_administration_fee`,
  then restart (`docker compose restart odoo`) per the same Windows
  bind-mount caveat noted in the other modules' READMEs.

## Deploying to production (Odoo.sh)

Contains Python (however minimal), so *Apps → Import Module* will reject
it. Hand the module folder (or zip) to whoever manages the Odoo.sh git
repo to push via a dev/staging branch, same as the other custom modules
here.
