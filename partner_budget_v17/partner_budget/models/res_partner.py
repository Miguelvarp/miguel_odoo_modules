from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    budget_ids = fields.One2many(
        "partner.budget", "partner_id", string="Budgets",
    )
    # Direct link only (no child-contact roll-up): needed so Odoo can trigger
    # an automatic recompute of the stored pipeline fields below whenever an
    # opportunity's expected_revenue/probability changes.
    opportunity_ids = fields.One2many(
        "crm.lead", "partner_id", string="Opportunities",
    )

    company_currency_id = fields.Many2one(
        "res.currency", compute="_compute_budget_kpis",
    )
    budget_amount = fields.Monetary(
        string="Budget (This Year)", compute="_compute_budget_kpis",
        currency_field="company_currency_id",
    )
    invoiced_amount = fields.Monetary(
        string="Invoiced (This Year)", compute="_compute_budget_kpis",
        currency_field="company_currency_id",
        help="Untaxed amount posted on customer invoices this calendar year, "
             "current company.",
    )
    budget_achieved_pct = fields.Float(
        string="Budget Reached", compute="_compute_budget_kpis",
    )
    budget_remaining = fields.Monetary(
        string="Budget Remaining", compute="_compute_budget_kpis",
        currency_field="company_currency_id",
    )
    invoice_backlog_amount = fields.Monetary(
        string="Backlog to Invoice", compute="_compute_budget_kpis",
        currency_field="company_currency_id",
        help="Untaxed amount on confirmed sales orders not yet invoiced, "
             "current company.",
    )

    # Stored + api.depends (unlike the fields above) so that: (1) installing/
    # upgrading this module backfills every existing opportunity automatically,
    # and (2) editing expected_revenue/probability on any opportunity recomputes
    # this straight away, instead of only picking up newly created ones.
    pipeline_expected_revenue = fields.Monetary(
        string="Pipeline (Expected)", compute="_compute_pipeline", store=True,
        currency_field="company_currency_id",
        help="Sum of expected revenue on open opportunities (not won, not lost) "
             "linked directly to this customer, across all companies.",
    )
    pipeline_weighted_revenue = fields.Monetary(
        string="Pipeline (Weighted)", compute="_compute_pipeline", store=True,
        currency_field="company_currency_id",
        help="Expected revenue weighted by each opportunity's probability.",
    )

    def _compute_budget_kpis(self):
        year = fields.Date.context_today(self).year
        company = self.env.company
        year_start, year_end = f"{year}-01-01", f"{year}-12-31"

        for partner in self:
            budget = self.env["partner.budget"].search([
                ("partner_id", "=", partner.id),
                ("company_id", "=", company.id),
                ("year", "=", str(year)),
            ], limit=1)

            moves = self.env["account.move"].search([
                ("partner_id", "child_of", partner.id),
                ("move_type", "in", ["out_invoice", "out_refund"]),
                ("state", "=", "posted"),
                ("company_id", "=", company.id),
                ("invoice_date", ">=", year_start),
                ("invoice_date", "<=", year_end),
            ])
            invoiced = sum(moves.mapped("amount_untaxed_signed"))

            orders = self.env["sale.order"].search([
                ("partner_id", "child_of", partner.id),
                ("state", "=", "sale"),
                ("company_id", "=", company.id),
            ])
            # Untaxed, to stay on the same basis as invoiced/budget above
            # (order.amount_to_invoice is tax-included). untaxed_amount_to_invoice
            # is in the order's OWN currency, not the company's, so each line
            # needs an explicit spot-rate conversion before summing.
            today = fields.Date.context_today(self)
            backlog = sum(
                line.currency_id._convert(
                    line.untaxed_amount_to_invoice, company.currency_id, company, today,
                )
                for line in orders.order_line
            )

            partner.company_currency_id = company.currency_id
            partner.budget_amount = budget.budget_amount
            partner.invoiced_amount = invoiced
            partner.budget_achieved_pct = (
                invoiced / budget.budget_amount if budget.budget_amount else 0.0
            )
            partner.budget_remaining = budget.budget_amount - invoiced
            partner.invoice_backlog_amount = backlog

    @api.depends(
        "opportunity_ids",
        "opportunity_ids.active",
        "opportunity_ids.type",
        "opportunity_ids.expected_revenue",
        "opportunity_ids.probability",
    )
    def _compute_pipeline(self):
        for partner in self:
            leads = partner.opportunity_ids.filtered(
                lambda lead: lead.type == "opportunity" and lead.probability < 100
            )
            partner.pipeline_expected_revenue = sum(leads.mapped("expected_revenue"))
            partner.pipeline_weighted_revenue = sum(
                lead.expected_revenue * lead.probability / 100.0 for lead in leads
            )

    def action_view_partner_invoices(self):
        self.ensure_one()
        year = fields.Date.context_today(self).year
        return {
            "type": "ir.actions.act_window",
            "name": "Invoices",
            "res_model": "account.move",
            "view_mode": "tree,form",
            "domain": [
                ("partner_id", "child_of", self.id),
                ("move_type", "in", ["out_invoice", "out_refund"]),
                ("state", "=", "posted"),
                ("company_id", "=", self.env.company.id),
                ("invoice_date", ">=", f"{year}-01-01"),
                ("invoice_date", "<=", f"{year}-12-31"),
            ],
        }

    def action_view_partner_pipeline(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Pipeline",
            "res_model": "crm.lead",
            "view_mode": "tree,kanban,form",
            "domain": [
                ("partner_id", "=", self.id),
                ("type", "=", "opportunity"),
                ("probability", "<", 100),
            ],
        }

    def action_view_partner_backlog(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Backlog to Invoice",
            "res_model": "sale.order",
            "view_mode": "tree,form",
            "domain": [
                ("partner_id", "child_of", self.id),
                ("state", "=", "sale"),
                ("company_id", "=", self.env.company.id),
                ("invoice_status", "!=", "invoiced"),
            ],
        }
