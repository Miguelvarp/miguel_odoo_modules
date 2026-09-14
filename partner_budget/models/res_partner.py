from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    budget_ids = fields.One2many(
        "partner.budget", "partner_id", string="Budgets",
    )
    # Direct link only. Used as the base relation for the pipeline depends
    # chain below (rollup to the commercial partner happens in the compute).
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
    confirmed_orders_amount = fields.Monetary(
        string="Confirmed Orders (This Year)", compute="_compute_budget_kpis",
        currency_field="company_currency_id",
        help="Untaxed value of confirmed sales orders placed this calendar year "
             "(regardless of invoicing status yet), current company.",
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
             "current company, any order year.",
    )

    # Stored + api.depends (unlike the fields above) so that: (1) installing/
    # upgrading this module backfills every existing opportunity automatically,
    # and (2) editing expected_revenue/probability on any opportunity recomputes
    # this straight away, instead of only picking up newly created ones.
    pipeline_expected_revenue = fields.Monetary(
        string="Pipeline (Expected)", compute="_compute_pipeline", store=True,
        currency_field="company_currency_id",
        help="Sum of expected revenue on open opportunities linked to this "
             "customer or any contact under it, across all companies.",
    )
    pipeline_weighted_revenue = fields.Monetary(
        string="Pipeline (Weighted)", compute="_compute_pipeline", store=True,
        currency_field="company_currency_id",
        help="Expected revenue weighted by each opportunity's probability.",
    )

    def _compute_budget_kpis(self):
        year = fields.Date.context_today(self).year
        company = self.env.company
        company_currency = company.currency_id
        year_start, year_end = f"{year}-01-01", f"{year}-12-31"
        next_year_start = f"{year + 1}-01-01"
        today = fields.Date.context_today(self)

        for partner in self:
            # Roll up to the ultimate parent company, so invoices/orders
            # posted against any individual contact under it still count.
            commercial = partner.commercial_partner_id

            budget = self.env["partner.budget"].search([
                ("partner_id", "=", partner.id),
                ("company_id", "=", company.id),
                ("year", "=", str(year)),
            ], limit=1)

            moves = self.env["account.move"].search([
                ("partner_id", "child_of", commercial.id),
                ("move_type", "in", ["out_invoice", "out_refund"]),
                ("state", "=", "posted"),
                ("company_id", "=", company.id),
                ("invoice_date", ">=", year_start),
                ("invoice_date", "<=", year_end),
            ])
            invoiced = sum(moves.mapped("amount_untaxed_signed"))

            confirmed_orders = self.env["sale.order"].search([
                ("partner_id", "child_of", commercial.id),
                ("state", "=", "sale"),
                ("company_id", "=", company.id),
            ])
            # Backlog: still to invoice on ANY confirmed order, any order year.
            # untaxed_amount_to_invoice is in the order's OWN currency, not the
            # company's, so each line needs an explicit spot-rate conversion.
            backlog = sum(
                line.currency_id._convert(
                    line.untaxed_amount_to_invoice, company_currency, company, today,
                )
                for line in confirmed_orders.order_line
            )

            year_orders = confirmed_orders.filtered(
                lambda o: o.date_order and year_start <= o.date_order.strftime("%Y-%m-%d") < next_year_start
            )
            confirmed_this_year = sum(
                order.currency_id._convert(
                    order.amount_untaxed, company_currency, company, today,
                )
                for order in year_orders
            )

            partner.company_currency_id = company_currency
            partner.budget_amount = budget.budget_amount
            partner.confirmed_orders_amount = confirmed_this_year
            partner.invoiced_amount = invoiced
            partner.budget_achieved_pct = (
                invoiced / budget.budget_amount if budget.budget_amount else 0.0
            )
            partner.budget_remaining = budget.budget_amount - invoiced
            partner.invoice_backlog_amount = backlog

    @api.depends(
        "commercial_partner_id",
        "commercial_partner_id.child_ids",
        "commercial_partner_id.opportunity_ids",
        "commercial_partner_id.opportunity_ids.active",
        "commercial_partner_id.opportunity_ids.type",
        "commercial_partner_id.opportunity_ids.expected_revenue",
        "commercial_partner_id.opportunity_ids.probability",
        "commercial_partner_id.child_ids.opportunity_ids",
        "commercial_partner_id.child_ids.opportunity_ids.active",
        "commercial_partner_id.child_ids.opportunity_ids.type",
        "commercial_partner_id.child_ids.opportunity_ids.expected_revenue",
        "commercial_partner_id.child_ids.opportunity_ids.probability",
    )
    def _compute_pipeline(self):
        for partner in self:
            # Always resolve to the ultimate parent company first, so a
            # child contact's form shows the same total as the parent's.
            commercial = partner.commercial_partner_id
            leads = commercial.opportunity_ids | commercial.child_ids.opportunity_ids
            leads = leads.filtered(
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
                ("partner_id", "child_of", self.commercial_partner_id.id),
                ("move_type", "in", ["out_invoice", "out_refund"]),
                ("state", "=", "posted"),
                ("company_id", "=", self.env.company.id),
                ("invoice_date", ">=", f"{year}-01-01"),
                ("invoice_date", "<=", f"{year}-12-31"),
            ],
        }

    def action_view_partner_pipeline(self):
        self.ensure_one()
        commercial = self.commercial_partner_id
        partner_ids = [commercial.id] + commercial.child_ids.ids
        return {
            "type": "ir.actions.act_window",
            "name": "Pipeline",
            "res_model": "crm.lead",
            "view_mode": "tree,kanban,form",
            "domain": [
                ("partner_id", "in", partner_ids),
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
                ("partner_id", "child_of", self.commercial_partner_id.id),
                ("state", "=", "sale"),
                ("company_id", "=", self.env.company.id),
                ("invoice_status", "!=", "invoiced"),
            ],
        }
