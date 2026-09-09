from odoo import api, fields, models

CALL_STATUS = [
    ("connected", "Connected"),
    ("voicemail", "Voice mail"),
]

DISPOSITION = [
    ("not_interested", "Not interested"),
    ("right_person_absent", "Right person not in the office"),
    ("callback_requested", "Request to call back"),
]


class CrmCallOutcome(models.Model):
    _name = "crm.call.outcome"
    _description = "Call Outcome"
    _order = "call_date desc, id desc"
    _rec_name = "lead_id"

    lead_id = fields.Many2one(
        "crm.lead", string="Lead/Opportunity", required=True,
        ondelete="cascade", index=True,
    )
    partner_id = fields.Many2one(
        "res.partner", string="Customer",
        related="lead_id.partner_id", store=True, index=True,
    )
    team_id = fields.Many2one(
        "crm.team", string="Sales Team",
        related="lead_id.team_id", store=True, index=True,
    )
    company_id = fields.Many2one(
        "res.company", string="Company",
        related="lead_id.company_id", store=True, index=True,
    )
    stage_id = fields.Many2one(
        "crm.stage", string="Stage at call",
        related="lead_id.stage_id", store=True,
    )
    user_id = fields.Many2one(
        "res.users", string="Caller", required=True, index=True,
        default=lambda self: self.env.user,
    )
    call_date = fields.Datetime(
        string="Call Date", required=True, index=True,
        default=fields.Datetime.now,
    )
    call_status = fields.Selection(CALL_STATUS, string="Call status", required=True)
    disposition = fields.Selection(DISPOSITION, string="Outcome")
    feedback = fields.Text(string="Feedback")

    # Constant 1: gives a clean "Calls" sum measure in pivot/graph views.
    call_count = fields.Integer(string="Calls", default=1, readonly=True)

    def _compute_display_name(self):
        for rec in self:
            date = fields.Datetime.to_string(rec.call_date) or ""
            rec.display_name = f"{rec.lead_id.display_name} · {date[:16]}"
