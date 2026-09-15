from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    pos_administration_fee_enabled = fields.Boolean(
        related="pos_config_id.administration_fee_enabled", readonly=False,
    )
    pos_administration_fee_threshold = fields.Float(
        related="pos_config_id.administration_fee_threshold", readonly=False,
    )
    pos_administration_fee_amount = fields.Float(
        related="pos_config_id.administration_fee_amount", readonly=False,
    )
    pos_administration_fee_product_id = fields.Many2one(
        related="pos_config_id.administration_fee_product_id", readonly=False,
    )
