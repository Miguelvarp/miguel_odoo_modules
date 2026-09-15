from odoo import fields, models


class PosConfig(models.Model):
    _inherit = "pos.config"

    administration_fee_enabled = fields.Boolean(
        string="Administration Fee",
        help="Automatically add an administration fee line to orders on "
             "this Point of Sale whose total falls below the threshold "
             "below.",
    )
    administration_fee_threshold = fields.Float(
        string="Administration Fee Threshold",
        default=10.0,
        help="Orders with a tax-included total below this amount "
             "automatically get the administration fee line added. The fee "
             "is removed again if the order total rises back to or above "
             "this amount.",
    )
    administration_fee_amount = fields.Float(
        string="Administration Fee Amount",
        default=2.0,
        help="Amount of the automatically-added administration fee line.",
    )
    administration_fee_product_id = fields.Many2one(
        "product.product",
        string="Administration Fee Product",
        domain=[("available_in_pos", "=", True)],
        help="Product used for the automatically-added administration fee "
             "line. Must be available in this Point of Sale (tick "
             "'Available in POS' on the product) so the register can load "
             "it. Consider leaving it out of any POS category so it "
             "doesn't show up as a regular tile.",
    )
