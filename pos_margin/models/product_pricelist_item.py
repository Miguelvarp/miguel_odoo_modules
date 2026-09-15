from odoo import fields, models


class ProductPricelistItem(models.Model):
    _inherit = "product.pricelist.item"

    pos_products_only = fields.Boolean(
        string="Only for products available in POS",
        help="Limit this rule to products flagged 'Available in POS'. "
        "Products not sold through POS fall through to the next matching "
        "rule (or the sales price) instead of getting this one applied.",
    )

    def _is_applicable_for(self, product, qty_in_product_uom):
        res = super()._is_applicable_for(product, qty_in_product_uom)
        if res and self.pos_products_only:
            template = (
                product
                if product._name == "product.template"
                else product.product_tmpl_id
            )
            return template.available_in_pos
        return res
