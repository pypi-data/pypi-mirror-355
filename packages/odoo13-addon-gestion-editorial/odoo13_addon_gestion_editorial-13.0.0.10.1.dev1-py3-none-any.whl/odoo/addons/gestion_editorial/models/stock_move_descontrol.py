from odoo import models, fields, api, _


class EditorialStockMove(models.Model):
    """ Extend stock.move template for editorial management """

    _description = "Editorial Stock Move"
    _inherit = 'stock.move'

    product_barcode = fields.Char(
        string='Código de barras / ISBN',
        related='product_id.barcode',
        readonly=True
    )

    pricelist_id = fields.Many2one(
        'product.pricelist',
        string='Tarifa',
        related='picking_id.pricelist_id',
        readonly=True
    )


class EditorialStockMoveLine(models.Model):
    """ Extend stock.move.line for editorial management """

    _description = "Editorial Stock Move Line"
    _inherit = 'stock.move.line'

    product_barcode = fields.Char(
        string='Código de barras / ISBN',
        related='product_id.barcode', readonly=True
    )

    pricelist_id = fields.Many2one(
        'product.pricelist',
        string='Tarifa',
        related='picking_id.pricelist_id',
        readonly=True
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('location_id') in self.env.ref("stock.stock_location_stock").get_all_child_locations():
                vals['qty_done'] = vals.get('product_uom_qty')
        return super(EditorialStockMoveLine, self).create(vals_list)
