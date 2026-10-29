from odoo import fields, models

from odoo.addons.product.report.product_label_report import _prepare_data


class ProductLabelLayout(models.TransientModel):
    _inherit = 'product.label.layout'

    # Adds "2 x 4 (A5)" to the Format dropdown of the Print Labels wizard.
    print_format = fields.Selection(
        selection_add=[('2x4', '2 x 4 (A5)')],
        ondelete={'2x4': 'set default'},
    )

    def _prepare_report_data(self):
        # The core method already maps any '<cols>x<rows>' format to the report
        # xmlid 'product.report_product_template_label_<cols>x<rows>[_noprice]'.
        # We only redirect '2x4' to OUR report action (defined in this module).
        xml_id, data = super()._prepare_report_data()
        if self.print_format == '2x4':
            xml_id = 'arplama_product_label_a5.report_product_template_label_2x4_noprice'
        return xml_id, data


class ReportProductLabel2x4(models.AbstractModel):
    # report_name is 'arplama_product_label_a5.report_producttemplatelabel2x4',
    # so the report model must be 'report.<report_name>'.
    _name = 'report.arplama_product_label_a5.report_producttemplatelabel2x4'
    _description = 'Product Label Report 2x4 (A5)'

    def _get_report_values(self, docids, data):
        # Reuse Odoo's own label data engine (quantity, page_numbers, pricelist, ...).
        return _prepare_data(self.env, docids, data)
