from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    # Open Orders / Invoiceable are new stored (non-compute) fields, so
    # existing budget lines would show 0 until someone clicked Refresh.
    env = api.Environment(cr, SUPERUSER_ID, {})
    env["partner.budget"].with_context(active_test=False).search([]).action_refresh()
