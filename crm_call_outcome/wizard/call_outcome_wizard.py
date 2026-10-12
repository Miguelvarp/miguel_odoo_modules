from dateutil.relativedelta import relativedelta
from markupsafe import Markup

from odoo import _, fields, models

from ..models.crm_call_outcome import CALL_STATUS, DISPOSITION


class CrmCallOutcomeWizard(models.TransientModel):
    _name = "crm.call.outcome.wizard"
    _description = "Log Call Outcome"

    lead_id = fields.Many2one(
        "crm.lead", string="Lead/Opportunity", required=True, ondelete="cascade"
    )
    phone = fields.Char(related="lead_id.phone", string="Phone", readonly=True)
    partner_name = fields.Char(
        related="lead_id.partner_id.name", string="Contact", readonly=True
    )

    call_status = fields.Selection(
        CALL_STATUS, string="Call status", required=True, default="connected"
    )
    disposition = fields.Selection(DISPOSITION, string="Outcome")
    feedback = fields.Text(string="Feedback")

    callback_date = fields.Date(
        string="Call back on",
        default=lambda self: fields.Date.context_today(self) + relativedelta(days=1),
    )

    def _label(self, field_name, value):
        """Translated label for a selection value."""
        if not value:
            return ""
        return dict(self._fields[field_name]._description_selection(self.env)).get(
            value, value
        )

    def _summary_body(self):
        body = Markup("<p><strong>&#128222; Call outcome</strong></p><ul>")
        body += Markup("<li><strong>Status:</strong> %s</li>") % self._label(
            "call_status", self.call_status
        )
        if self.disposition:
            body += Markup("<li><strong>Outcome:</strong> %s</li>") % self._label(
                "disposition", self.disposition
            )
        body += Markup("</ul>")
        if self.feedback:
            # Markup(...) % value escapes the interpolated value.
            body += Markup("<p><strong>Feedback:</strong><br/>%s</p>") % self.feedback
        return body

    def action_log_call(self):
        self.ensure_one()
        body = self._summary_body()

        # B - keep every call as its own record for reporting.
        self.env["crm.call.outcome"].create(
            {
                "lead_id": self.lead_id.id,
                "user_id": self.env.user.id,
                "call_status": self.call_status,
                "disposition": self.disposition,
                "feedback": self.feedback,
            }
        )

        # Log the call as a completed "Call" activity (shows in the chatter).
        call_type = self.env.ref(
            "mail.mail_activity_data_call", raise_if_not_found=False
        )
        if call_type:
            activity = self.lead_id.activity_schedule(
                act_type_xmlid="mail.mail_activity_data_call",
                summary=self._label("call_status", self.call_status),
                user_id=self.env.user.id,
            )
            # Pass the summary only as feedback; setting it as the activity
            # `note` too makes Odoo echo it a second time ("Original note:").
            activity.action_feedback(feedback=body)
        else:
            self.lead_id.message_post(body=body, subject=_("Call outcome"))

        # A - "Request to call back" leaves an open follow-up Call activity.
        if self.disposition == "callback_requested" and self.callback_date:
            self.lead_id.activity_schedule(
                act_type_xmlid="mail.mail_activity_data_call",
                date_deadline=self.callback_date,
                summary=_("Call back"),
                note=self.feedback or "",
                user_id=self.env.user.id,
            )

        return {"type": "ir.actions.act_window_close"}
