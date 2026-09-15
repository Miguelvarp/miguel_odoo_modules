# Arplama Batch Payment Bank Export

Automatically builds a bank-import Excel file and attaches it to a payment
batch's chatter the moment the batch is validated (state changes to
**Sent**) — no manual "generate file, rename, re-upload" step.

## When it fires

Only for batches where:
- `batch_type == "outbound"` (payments going out), and
- `payment_method_code == "manual"` (i.e. Odoo has no native SEPA/XML file
  generation for this journal — `file_generation_enabled` is False). This is
  the case for the RON/Raiffeisen journal today; batches on a journal with
  native file generation are left alone.

Triggered from an override of `write()` — fires no matter which button or
wizard flips `state` to `sent`, not tied to a specific Odoo version's button
method name.

## What it produces

One `.xlsx` attachment per validated batch, named `BOUT-<year>-<seq>.xlsx`
(e.g. `BOUT-2026-0090.xlsx`, well under 30 characters), with one row per
payment in the batch:

| Column | Source |
|---|---|
| Payer IBAN | batch's journal bank account |
| Beneficiary IBAN | payment's `partner_bank_id` |
| Amount / Currency | payment |
| Beneficiary Name / Beneficiary Name 1 | partner name, wrapped onto a second field past 35 characters (see below) |
| Description | payment's `ref`, falling back to `Payment <name>` |
| Payment order number | plain sequential integer (1, 2, 3…) |
| Fees (SHA/BEN/OUR) | always `SHA` |
| Priority (STANDARD/URGENT) | always `STANDARD` |
| Beneficiary/Payment evidence number (Treasury) | left blank — only used for Romanian Treasury/public-institution payments |

A chatter note is posted alongside the attachment. If any payment has no
beneficiary bank account on file, it's called out there rather than
silently uploading a blank IBAN.

### Known assumptions — verify against the next live batch

These came from analysing real Raiffeisen Corporate Online rejection
reports (`*_REJECTED_PAYMENTS.xlsx`, not part of this repo) for
`BATCH/OUT/2026/0090`, not from official bank documentation:

- **Payment order number as plain integer** and **Priority = STANDARD**
  are both confirmed fixes — a prior upload using Odoo's payment name
  (`RO65R/2026/0705`) and no Priority was rejected outright; fixing both
  got 6 of 7 payments accepted.
- **35-character beneficiary name limit**, split onto `Beneficiary Name 1`
  rather than truncated, is inferred from the one payment that still
  failed (`"Beneficiary name is invalid"` on a 45-character name) — the
  bank never states an exact limit. **This split has not yet been tested
  against a live upload.**
- `Fees = SHA` is a precaution, not a confirmed requirement.

If the next auto-generated file still gets a rejection, check the
`Rejected Reason` column in the bank's own report and adjust
`BENEFICIARY_NAME_LIMIT` / the relevant field in
`models/account_batch_payment.py` accordingly.

## Testing locally

Docker stack in `../../odoo-dev` (Odoo 17 **Community**, http://localhost:8069).
`account_batch_payment` is a Community module, so this is testable there:

1. `docker compose up -d`, open the instance, install **Accounting**.
2. Enable batch payments (Accounting → Configuration → Settings →
   Customer/Vendor Payments → Batch Payments) and set a manual payment
   method + IBAN on a bank journal.
3. Apps → Update Apps List → install **Arplama Batch Payment Bank Export**.
4. Create a vendor payment (with the vendor's bank account set), add it to
   a new outbound batch payment, validate it → check the batch's chatter
   for the generated `.xlsx` attachment and the summary note.
5. After editing `account_batch_payment.py`:
   `..\..\odoo-dev\update-module.ps1 -Module arplama_batch_payment_export`,
   then `docker compose restart odoo`.

## Deploying to production (Odoo.sh)

Contains Python, so *Apps → Import Module* will reject it. Hand the module
folder to whoever manages the Odoo.sh git repo to push via a dev/staging
branch first, then merge to production, same as the other custom modules
here.
