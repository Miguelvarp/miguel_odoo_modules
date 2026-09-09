{
    "name": "CRM Call Outcome",
    "summary": "Popup to log a call outcome (status + disposition + feedback) on leads/opportunities",
    "version": "17.0.2.1.1",
    "category": "Sales/CRM",
    "author": "Miguel Vanduffel",
    "maintainer": "Miguel Vanduffel",
    "company": "Arplama",
    "license": "LGPL-3",
    "depends": ["crm"],
    "data": [
        "security/ir.model.access.csv",
        "security/crm_call_outcome_rules.xml",
        "wizard/call_outcome_wizard_views.xml",
        "views/crm_call_outcome_views.xml",
        "views/crm_lead_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "crm_call_outcome/static/src/call_outcome.css",
            # Option B (custom phone-icon widget) is shipped but disabled by
            # default. To enable it, uncomment the two lines below and follow
            # README.md.
            # "crm_call_outcome/static/src/phone_outcome_field.js",
            # "crm_call_outcome/static/src/phone_outcome_field.xml",
        ],
    },
    "installable": True,
    "application": False,
    "auto_install": False,
}
