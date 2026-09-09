from odoo import fields, models


class CrmLead(models.Model):
    _inherit = "crm.lead"

    call_outcome_ids = fields.One2many(
        "crm.call.outcome", "lead_id", string="Call Outcomes",
    )
    call_outcome_count = fields.Integer(
        string="Calls Logged", compute="_compute_call_outcome_count",
    )

    def _compute_call_outcome_count(self):
        data = self.env["crm.call.outcome"]._read_group(
            [("lead_id", "in", self.ids)], groupby=["lead_id"], aggregates=["__count"],
        )
        mapped = {lead.id: count for lead, count in data}
        for lead in self:
            lead.call_outcome_count = mapped.get(lead.id, 0)

    def action_view_call_outcomes(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Call Outcomes",
            "res_model": "crm.call.outcome",
            "view_mode": "tree,form,pivot,graph",
            "domain": [("lead_id", "=", self.id)],
            "context": {"default_lead_id": self.id, "search_default_lead_id": self.id},
        }
