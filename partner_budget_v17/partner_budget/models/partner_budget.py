from odoo import api, fields, models


class PartnerBudget(models.Model):
    _name = "partner.budget"
    _description = "Partner Budget Target"
    _order = "year desc, company_id"

    partner_id = fields.Many2one(
        "res.partner", string="Customer", required=True,
        ondelete="cascade", index=True,
    )
    company_id = fields.Many2one(
        "res.company", string="Company", required=True,
        default=lambda self: self.env.company,
    )
    year = fields.Selection(
        selection="_selection_year", string="Year", required=True,
        default=lambda self: str(fields.Date.context_today(self).year),
    )
    currency_id = fields.Many2one(
        "res.currency", string="Currency",
        related="company_id.currency_id", store=True, readonly=True,
    )
    budget_amount = fields.Monetary(
        string="Budget", required=True, currency_field="currency_id",
        help="Enter as untaxed (net) revenue, to match Invoiced below.",
    )
    invoiced_amount = fields.Monetary(
        string="Invoiced", currency_field="currency_id", readonly=True, copy=False,
        help="Untaxed amount posted on customer invoices for this customer/company/"
             "year. Set when the line is created; click Refresh to recheck later.",
    )
    budget_achieved_pct = fields.Float(string="Reached", readonly=True, copy=False)
    remaining_amount = fields.Monetary(
        string="Remaining", currency_field="currency_id", readonly=True, copy=False,
    )
    notes = fields.Text(string="Notes")

    _sql_constraints = [
        (
            "partner_company_year_uniq",
            "unique(partner_id, company_id, year)",
            "There is already a budget line for this customer, company and year.",
        ),
    ]

    def _selection_year(self):
        current = fields.Date.context_today(self).year
        return [(str(y), str(y)) for y in range(current - 5, current + 4)]

    def _compute_display_name(self):
        for rec in self:
            rec.display_name = f"{rec.partner_id.display_name} · {rec.company_id.name} · {rec.year}"

    def _get_invoiced_amount(self):
        self.ensure_one()
        year = int(self.year)
        moves = self.env["account.move"].search([
            ("partner_id", "child_of", self.partner_id.id),
            ("move_type", "in", ["out_invoice", "out_refund"]),
            ("state", "=", "posted"),
            ("company_id", "=", self.company_id.id),
            ("invoice_date", ">=", f"{year}-01-01"),
            ("invoice_date", "<=", f"{year}-12-31"),
        ])
        return sum(moves.mapped("amount_untaxed_signed"))

    def action_refresh_invoiced(self):
        for line in self:
            invoiced = line._get_invoiced_amount()
            line.invoiced_amount = invoiced
            line.budget_achieved_pct = (
                invoiced / line.budget_amount if line.budget_amount else 0.0
            )
            line.remaining_amount = line.budget_amount - invoiced

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records.action_refresh_invoiced()
        return records
