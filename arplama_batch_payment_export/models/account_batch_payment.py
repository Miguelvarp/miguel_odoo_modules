import base64
import io
import logging

from odoo import models

_logger = logging.getLogger(__name__)

# Not documented by the bank; inferred from a rejected upload where a
# 45-character beneficiary name failed and a split name succeeded.
# Long names are wrapped onto "Beneficiary Name 1" rather than truncated.
BENEFICIARY_NAME_LIMIT = 35

FILE_COLUMNS = [
    "Payer IBAN",
    "Beneficiary IBAN",
    "Amount",
    "Currency",
    "Beneficiary Name",
    "Beneficiary Name 1",
    "Description",
    "Payment order number",
    "Beneficiary Identification Number Treasury Payment",
    "Payment evidence number Treasury Payment",
    "Fees (SHA/BEN/OUR)",
    "Priority (STANDARD/URGENT)",
]


class AccountBatchPayment(models.Model):
    _inherit = "account.batch.payment"

    def write(self, vals):
        to_generate = self.env["account.batch.payment"]
        if vals.get("state") == "sent":
            to_generate = self.filtered(lambda b: b.state != "sent")

        res = super().write(vals)

        for batch in to_generate:
            if batch.batch_type == "outbound" and batch.payment_method_code == "manual":
                try:
                    batch._generate_bank_import_file()
                except Exception:
                    _logger.exception(
                        "Failed to auto-generate bank import file for batch payment %s",
                        batch.name,
                    )
        return res

    def _generate_bank_import_file(self):
        self.ensure_one()
        try:
            import xlsxwriter
        except ImportError:
            _logger.warning(
                "xlsxwriter not available; skipping bank import file for %s",
                self.name,
            )
            return

        payer_iban = (self.journal_id.bank_acc_number or "").replace(" ", "")
        warnings = []

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {"in_memory": True})
        sheet = workbook.add_worksheet("Sheet1")
        for col, header in enumerate(FILE_COLUMNS):
            sheet.write(0, col, header)

        payments = self.payment_ids.sorted("name")
        for row, payment in enumerate(payments, start=1):
            bank = payment.partner_bank_id
            ben_iban = (bank.acc_number or "").replace(" ", "") if bank else ""
            if not ben_iban:
                warnings.append(
                    f"{payment.name} ({payment.partner_id.name}): no beneficiary "
                    "bank account on file — IBAN left blank."
                )

            name, name1 = self._split_beneficiary_name(payment.partner_id.name or "")
            description = payment.ref or f"Payment {payment.name}"

            sheet.write_row(row, 0, [
                payer_iban,
                ben_iban,
                payment.amount,
                payment.currency_id.name,
                name,
                name1,
                description,
                row,
                "",
                "",
                "SHA",
                "STANDARD",
            ])

        workbook.close()
        output.seek(0)
        file_data = base64.b64encode(output.read())

        parts = (self.name or "").split("/")
        short_ref = "-".join(parts[-2:]) if len(parts) >= 2 else (self.name or "batch")
        filename = f"BOUT-{short_ref}.xlsx"  # kept under 30 chars

        self.env["ir.attachment"].create({
            "name": filename,
            "type": "binary",
            "res_model": self._name,
            "res_id": self.id,
            "mimetype": (
                "application/vnd.openxmlformats-officedocument"
                ".spreadsheetml.sheet"
            ),
            "datas": file_data,
        })

        note = f"Bank import file <b>{filename}</b> auto-generated ({len(payments)} payment(s))."
        if warnings:
            note += "<br/>Check before uploading:<ul>" + "".join(
                f"<li>{w}</li>" for w in warnings
            ) + "</ul>"
        self.message_post(body=note)

    @staticmethod
    def _split_beneficiary_name(name, limit=BENEFICIARY_NAME_LIMIT):
        name = (name or "").strip()
        if len(name) <= limit:
            return name, ""

        line1, line2 = "", ""
        for word in name.split(" "):
            candidate = f"{line1} {word}".strip()
            if len(candidate) <= limit:
                line1 = candidate
            else:
                line2 = f"{line2} {word}".strip()
        if not line1 and line2:
            # A single word alone exceeded the limit (pathological input) -
            # keep the primary field populated rather than leaving it blank.
            line1, line2 = line2, ""
        return line1[:limit], line2[:limit]
