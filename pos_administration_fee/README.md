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

## What changed vs. the V17 version

Odoo 18/19 rewrote the POS frontend data model. This isn't the usual
`<tree>` → `<list>` / `view_mode` swap the other V19 modules in this repo
needed - the classes this module patches don't exist anymore, so the JS
(`static/src/js/models.js`) is a real rewrite, not a port:

- `Order`/`Orderline` (from `@point_of_sale/app/store/models`) → separate
  `PosOrder` (`@point_of_sale/app/models/pos_order`) and `PosOrderline`
  (`@point_of_sale/app/models/pos_order_line`) classes, using a generic
  relational ORM (`related_models`) instead of plain JS objects.
- Method names went camelCase: `get_orderlines()` → `getOrderlines()`,
  `get_product()` → `getProduct()`, `set_quantity()` → `setQuantity()`, etc.
  `get_price_with_tax()` became the `priceIncl` getter.
- `Order.add_product()` no longer exists - adding a line is now
  orchestrated by the `PosStore` service's `addLineToCurrentOrder()`
  (configurators, combos, lot tracking, scales). The fee line doesn't need
  any of that, so it's created directly via the same low-level factory core
  itself uses internally (`this.models["pos.order.line"].create(...)`),
  which conveniently also means it can never recurse back into the patched
  `addLineToCurrentOrder` hook.
- `pos.config` Many2one fields (e.g. the fee product) now resolve directly
  to the related record client-side - no more manual
  `pos.db.get_product_by_id(config.field[0])` lookup.

Python/XML (`pos_config.py`, `res_config_settings.py`,
`res_config_settings_views.xml`) are unchanged from V17 beyond the manifest
version bump - the settings-screen `<setting>` pattern this module hooks
into (right after the built-in Tips block) is untouched by the frontend
rewrite.

## Testing locally

Separate Docker stack - `../../odoo-dev/docker-compose.v19.yml` runs Odoo 19
+ PostgreSQL 16 on **http://localhost:8169** and mounts this folder.

```
cd ../../odoo-dev
docker compose -f docker-compose.v19.yml up -d
```

Install **Point of Sale**, then install **POS Administration Fee** from
Apps. This module ships only JS (POS frontend) + view/field changes, no
server Python logic beyond plain fields, so after edits:

- **JS changes**: hard-refresh the POS UI tab (`Ctrl+Shift+R`) - POS assets
  are a separate bundle from the backend and don't hot-reload.
- **View/field changes**: upgrade the module, then
  `docker compose -f docker-compose.v19.yml restart odoo` - the running
  server's module registry doesn't pick up a fresh install/upgrade run
  through a separate one-off process until restarted.

## Deploying to production (Odoo.sh)

Contains Python (however minimal), so *Apps → Import Module* will reject
it. Hand the module folder (or zip) to whoever manages the Odoo.sh git
repo to push via a dev/staging branch, same as the other custom modules
here.

Production is currently on **Odoo 17** - this V19 folder is ready for
whenever that upgrade happens, per this repo's convention (keep the older
`modules Vxx` folder live until the newer one is actually in production).
