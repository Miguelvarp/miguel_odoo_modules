# Arplama Batch Payment Bank Export (V19)

V19 port of `../modules V17/arplama_batch_payment_export`. Identical models
and logic — this module has no views, so none of the usual v18+ arch changes
(`<tree>` → `<list>`) apply. Only `__manifest__.py` `"version"` changed.

See `../modules V17/arplama_batch_payment_export/README.md` for the full
write-up: what triggers the export, the file format, and the known
assumptions (payment order number, Priority, the 35-char beneficiary name
split) that still need verifying against a live bank upload.

## Testing locally

`../../odoo-dev/docker-compose.v19.yml` runs Odoo 19 on
**http://localhost:8169** and mounts this folder. Same caveat as V17: this
depends on `account_batch_payment`, which is **Enterprise-only** and not
part of the Community image — installing this module here will fail on that
missing dependency unless Enterprise addons are also mounted into the stack.

```
cd ../../odoo-dev
docker compose -f docker-compose.v19.yml up -d
```

Re-apply after edits:

```
docker compose -f docker-compose.v19.yml exec -u odoo odoo \
  odoo -c /etc/odoo/odoo.conf -d <db> -u arplama_batch_payment_export --stop-after-init
docker compose -f docker-compose.v19.yml restart odoo
```

## Deploying to production (Odoo.sh)

Contains Python, so *Apps → Import Module* will reject it. Hand the module
folder (or its `.zip`) to whoever manages the Odoo.sh git repo to push via a
dev/staging branch, then merge to production — only once Arplama's
production Odoo is actually on 19; until then, deploy the V17 copy.
