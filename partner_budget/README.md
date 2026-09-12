# Partner Budget Tracking

V19 port of `../modules V17/partner_budget`. Same models and logic; only the
view arch tags differ (`<tree>` → `<list>`, `view_mode` strings `tree` → `list`),
per the house convention documented in `../README.md`.

See `../modules V17/partner_budget/README.md` for the full design writeup
(what each field means, where budgets are entered, KPI definitions).

## Testing locally

`../../odoo-dev/docker-compose.v19.yml` runs Odoo 19 on http://localhost:8169
and mounts this folder. Install **Sales** + **CRM**, then **Partner Budget
Tracking**. Re-apply after edits:

```
docker compose -f docker-compose.v19.yml exec -u odoo odoo \
  odoo -c /etc/odoo/odoo.conf -d <db> -u partner_budget --stop-after-init
docker compose -f docker-compose.v19.yml restart odoo
```
