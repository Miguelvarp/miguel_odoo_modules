# POS Margin Pricelists

Adds a checkbox, **"Only for products available in POS"**, to Pricelist
Rules. When ticked, a cost-based (or any) Formula rule only applies to
products that have **Available in POS** ticked on the product itself -
everything else falls through to the next matching rule, or the plain
sales price.

## Why

Odoo's pricelist rule "Apply On" only supports *All Products / Product
Category / Product / Product Variant* - there's no way to condition a
rule on an arbitrary checkbox like "Available in POS". This module adds
that missing condition, so a POS margin rule (e.g. "sale price = cost +
40%") can be scoped to `3_global` ("All Products") and still only ever
touch products actually sold through POS, without needing a dedicated
product category as a proxy.

## What it adds

**1 new field on `product.pricelist.item`**: `pos_products_only`
(boolean). Shown on the Pricelist Rule form, next to the other
Formula-only fields (only visible when Computation = Formula).

**Server-side logic**: overrides `_is_applicable_for()` on
`product.pricelist.item` - if the rule has `pos_products_only` ticked, it
also requires `product.product_tmpl_id.available_in_pos` (or
`product.available_in_pos` if given a template directly) to be `True`
before the rule is considered a match for that product.

This does not change matching for rules that leave the checkbox
unticked - existing pricelists behave exactly as before.

## Setup

1. Settings → Sales → Pricing → enable **Advanced price rules
   (discounts, formulas)** if not already on.
2. Create/edit a Pricelist Rule, set Computation = **Formula**, Based on
   = **Cost**, fill in the Discount/margin - then tick **Only for
   products available in POS**.
3. Assign that pricelist to the relevant POS config (Point of Sale →
   Settings → that POS → Pricelists). Products without **Available in
   POS** ticked keep their normal sales price even if this same
   pricelist is ever applied elsewhere.

## Testing locally

Docker stack in `../../odoo-dev` (Odoo 17, http://localhost:8069) mounts
this folder. Start it, then install **POS Margin Pricelists** from Apps
(Point of Sale and the Advanced Pricelists setting must be enabled
first).

After edits:
- **Python only**: `dev_mode = reload` restarts Odoo automatically - just
  refresh.
- **View/field changes**: `..\..\odoo-dev\update-module.ps1 -Module pos_margin`,
  then `docker compose restart odoo` (Windows bind-mount caveat, same as
  the other modules here).

## Deploying to production (Odoo.sh)

Contains Python, so *Apps → Import Module* will reject it. Hand the
module folder to whoever manages the Odoo.sh git repo to push via a
dev/staging branch, same as the other custom modules here.
