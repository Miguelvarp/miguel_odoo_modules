from odoo import api, fields, models
from odoo.exceptions import ValidationError


class PartnerBudget(models.Model):
    _name = "partner.budget"
    _description = "Partner Budget Target"
    _order = "year desc, company_id"

    partner_id = fields.Many2one(
        "res.partner", string="Customer", required=True,
        ondelete="cascade", index=True,
    )
    company_id = fields.Many2one(
        "res.company", string="Company",
        default=lambda self: self.env.company,
        help="Leave blank for a single Odoo-wide target for this customer, "
             "not tied to one company: Confirmed Orders/Invoiced then roll "
             "up every company's activity, converted to EUR.",
    )
    year = fields.Selection(
        selection="_selection_year", string="Year", required=True,
        default=lambda self: str(fields.Date.context_today(self).year),
    )
    currency_id = fields.Many2one(
        "res.currency", string="Currency",
        compute="_compute_currency_id", store=True, readonly=True,
    )
    budget_amount = fields.Monetary(
        string="Budget", required=True, currency_field="currency_id",
        help="Enter as untaxed (net) revenue, to match Invoiced below.",
    )
    confirmed_orders_amount = fields.Monetary(
        string="Confirmed Orders", currency_field="currency_id", readonly=True, copy=False,
        help="Untaxed value of confirmed sales orders placed during this year "
             "(regardless of invoicing status yet), converted to company currency. "
             "Set when the line is created; click Refresh to recheck later.",
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

    # EUR-converted mirrors of the amounts above, so the Budget by Year /
    # Company list can always be read in one currency regardless of which
    # company's row it is. The native-currency fields above stay the source
    # of truth (budget_amount is still what gets entered per company).
    eur_currency_id = fields.Many2one(
        "res.currency", string="EUR", compute="_compute_eur_currency_id",
    )
    budget_amount_eur = fields.Monetary(
        string="Budget (EUR)", currency_field="eur_currency_id",
        compute="_compute_eur_amounts", inverse="_inverse_budget_amount_eur",
        help="Budget converted to EUR at today's spot rate. Editing this "
             "converts back and updates the native-currency Budget.",
    )
    confirmed_orders_amount_eur = fields.Monetary(
        string="Confirmed Orders (EUR)", currency_field="eur_currency_id",
        compute="_compute_eur_amounts",
    )
    invoiced_amount_eur = fields.Monetary(
        string="Invoiced (EUR)", currency_field="eur_currency_id",
        compute="_compute_eur_amounts",
    )
    remaining_amount_eur = fields.Monetary(
        string="Remaining (EUR)", currency_field="eur_currency_id",
        compute="_compute_eur_amounts",
    )

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

    @api.constrains("partner_id", "company_id", "year")
    def _check_unique_all_companies_line(self):
        # The SQL unique constraint above doesn't catch this: Postgres treats
        # every NULL company_id as distinct, so it would happily allow several
        # "all companies" (blank company_id) lines for the same customer/year.
        for rec in self:
            if rec.company_id:
                continue
            duplicate = self.search([
                ("id", "!=", rec.id),
                ("partner_id", "=", rec.partner_id.id),
                ("company_id", "=", False),
                ("year", "=", rec.year),
            ], limit=1)
            if duplicate:
                raise ValidationError(
                    "There is already an all-companies budget line for this "
                    "customer and year."
                )

    @api.depends("company_id", "company_id.currency_id")
    def _compute_currency_id(self):
        eur = self.env.ref("base.EUR")
        for rec in self:
            rec.currency_id = rec.company_id.currency_id or eur

    def _compute_eur_currency_id(self):
        eur = self.env.ref("base.EUR")
        for rec in self:
            rec.eur_currency_id = eur

    @api.depends(
        "budget_amount", "confirmed_orders_amount", "invoiced_amount",
        "remaining_amount", "currency_id", "company_id",
    )
    def _compute_eur_amounts(self):
        eur = self.env.ref("base.EUR")
        today = fields.Date.context_today(self)
        for rec in self:
            rec.budget_amount_eur = rec.currency_id._convert(
                rec.budget_amount, eur, rec.company_id, today,
            )
            rec.confirmed_orders_amount_eur = rec.currency_id._convert(
                rec.confirmed_orders_amount, eur, rec.company_id, today,
            )
            rec.invoiced_amount_eur = rec.currency_id._convert(
                rec.invoiced_amount, eur, rec.company_id, today,
            )
            rec.remaining_amount_eur = rec.currency_id._convert(
                rec.remaining_amount, eur, rec.company_id, today,
            )

    def _inverse_budget_amount_eur(self):
        eur = self.env.ref("base.EUR")
        today = fields.Date.context_today(self)
        for rec in self:
            rec.budget_amount = eur._convert(
                rec.budget_amount_eur, rec.currency_id, rec.company_id, today,
            )

    def _compute_display_name(self):
        for rec in self:
            company_label = rec.company_id.name or "All Companies"
            rec.display_name = f"{rec.partner_id.display_name} · {company_label} · {rec.year}"

    def _get_invoiced_amount(self):
        self.ensure_one()
        year = int(self.year)
        # Roll up to the ultimate parent company, so invoices posted against
        # any individual contact under it still count.
        commercial = self.partner_id.commercial_partner_id
        domain = [
            ("partner_id", "child_of", commercial.id),
            ("move_type", "in", ["out_invoice", "out_refund"]),
            ("state", "=", "posted"),
            ("invoice_date", ">=", f"{year}-01-01"),
            ("invoice_date", "<=", f"{year}-12-31"),
        ]
        # Blank company_id means "all companies" - don't scope to just one.
        if self.company_id:
            domain.append(("company_id", "=", self.company_id.id))
        moves = self.env["account.move"].search(domain)
        today = fields.Date.context_today(self)
        # amount_untaxed_signed is expressed in each move's own company
        # currency, so it needs converting when rolling up across companies
        # that don't all share the line's currency (a no-op when they do).
        return sum(
            move.company_id.currency_id._convert(
                move.amount_untaxed_signed, self.currency_id, move.company_id, today,
            )
            for move in moves
        )

    def _get_confirmed_orders_amount(self):
        self.ensure_one()
        year = int(self.year)
        commercial = self.partner_id.commercial_partner_id
        domain = [
            ("partner_id", "child_of", commercial.id),
            ("state", "=", "sale"),
            ("date_order", ">=", f"{year}-01-01"),
            ("date_order", "<", f"{year + 1}-01-01"),
        ]
        if self.company_id:
            domain.append(("company_id", "=", self.company_id.id))
        orders = self.env["sale.order"].search(domain)
        today = fields.Date.context_today(self)
        return sum(
            order.currency_id._convert(
                order.amount_untaxed, self.currency_id, order.company_id, today,
            )
            for order in orders
        )

    def action_refresh(self):
        for line in self:
            invoiced = line._get_invoiced_amount()
            line.invoiced_amount = invoiced
            line.confirmed_orders_amount = line._get_confirmed_orders_amount()
            line.budget_achieved_pct = (
                invoiced / line.budget_amount if line.budget_amount else 0.0
            )
            line.remaining_amount = line.budget_amount - invoiced

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records.action_refresh()
        return records
