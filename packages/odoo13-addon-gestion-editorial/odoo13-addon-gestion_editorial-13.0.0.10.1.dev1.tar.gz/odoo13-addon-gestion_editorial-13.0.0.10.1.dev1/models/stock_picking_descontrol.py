from odoo import models, fields, api, _
from odoo.exceptions import UserError

class EditorialPicking(models.Model):
    """ Extend stock.picking template for editorial management """

    _description = "Editorial Stock Picking"
    _inherit = 'stock.picking'  # odoo/addons/stock/models/stock_picking.py

    pricelist_id = fields.Many2one(
        'product.pricelist',
        string='Tarifa',
        related='sale_id.pricelist_id',
        readonly=True
    )

    @api.depends(
            'state',
            'move_lines',
            'move_lines.state',
            'move_lines.package_level_id',
            'move_lines.move_line_ids.package_level_id'
        )
    def _compute_move_without_package(self):
        for picking in self:
            for move in self.move_lines:
                for ml in move.move_line_ids:
                    # If owner_id is equal we don't need to change anything so we don't call write method
                    if ml.owner_id != self.partner_id:
                        ml.owner_id = self.partner_id
            picking.move_ids_without_package = picking._get_move_ids_without_package()

    # DDAA: Derechos de autoría
    # Cuando se valida un stock.picking, se comprueba que la localización de
    # destino o origen (devoluciones) sea Partner Locations Customers para actualizar 
    # el albarán de autoría. Se revisa también que la tarifa de la venta genere DDAA
    def generate_picking_ddaa(self):
        if self.env.company.module_editorial_ddaa and \
            (not self.sale_id or self.sale_id.pricelist_id.genera_ddaa) and \
            self.env.ref("stock.stock_location_customers").id in \
                (self.location_dest_id.id, self.location_id.id):
            # Para las líneas que contengan un libro que tenga derechos de
            # autoría. Busca una purchase order a ese autor con la línea con
            # el derecho de autoría, si no, créala
            book_lines = self.move_line_ids_without_package.filtered(
                lambda line: self.env.company.is_category_genera_ddaa_or_child(
                    line.product_id.categ_id
                )
            )
            if book_lines:
                for book_line in book_lines:
                    if self.location_dest_id.id == self.env.ref("stock.stock_location_customers").id:
                        ddaa_qty = book_line.qty_done
                    else:
                        ddaa_qty = 0 - book_line.qty_done  # For refunds the qty_done is negative

                    book_line.product_id.product_tmpl_id.generate_ddaa(ddaa_qty)

    def check_ddaa_and_books_authors(self):
        for product in self.move_ids_without_package:
            if not product.product_tmpl_id.genera_ddaa:
                raise UserError(_(f"El libro {product.name} no genera DDAA y por lo tanto no puede ser transferido de esta forma."))
            product_authors = product.product_tmpl_id.authorship_ids.mapped('author_id')
            if self.partner_id not in product_authors:
                raise UserError(_(f"El libro {product.name} no corresponde con el autor de esta transferencia."))

    def update_ddaa_order_authorship_lines(self):
        domain = [
                ('partner_id', '=', self.partner_id.id),
                ('state', '=', 'draft'),
                ('is_ddaa_order', '=', True)
            ]
        authorship_purchase_order = self.env['purchase.order'].search(domain, order='date_order desc', limit=1)
        if not authorship_purchase_order:
            raise UserError(_(f"No se encuentra el albarán de DDAA para el autor {self.partner_id.name}."))
        
        for line in self.move_ids_without_package:
            if line.product_id.product_tmpl_id.genera_ddaa:
                authorship_purchase_order.update_ddaa_order_book_line(line.product_id.product_tmpl_id, 'update_qty', line.quantity_done, self.name)

    def button_validate(self):
        if self.picking_type_id.id == self.env.ref("gestion_editorial.stock_picking_type_entrega_autoria").id:
            self.check_ddaa_and_books_authors()
            self.update_ddaa_order_authorship_lines()
        self.generate_picking_ddaa()
        return super(EditorialPicking, self).button_validate()
    
    def action_assign(self):
        if self.picking_type_id.id == self.env.ref("gestion_editorial.stock_picking_type_entrega_autoria").id:
            self.check_ddaa_and_books_authors()
        return super(EditorialPicking, self).action_assign()

    def action_confirm(self):
        if self.picking_type_id.id == self.env.ref("gestion_editorial.stock_picking_type_entrega_autoria").id:
            self.check_ddaa_and_books_authors()
        return super(EditorialPicking, self).action_confirm()


class EditorialStockImmediateTransfer(models.TransientModel):

    """ Extend stock.immediate.transfer for editorial management """

    _description = "Editorial Stock Immediate Transfer"
    # odoo/addons/stock/models/stock_immediate_transfer.py
    _inherit = 'stock.immediate.transfer'

    def process(self):
        pick_to_backorder = self.env['stock.picking']
        pick_to_do = self.env['stock.picking']
        for picking in self.pick_ids:
            # If still in draft => confirm and assign
            if picking.state == 'draft':
                picking.action_confirm()
                if picking.state != 'assigned':
                    picking.action_assign()
                    if picking.state != 'assigned':
                        raise UserError(_("Could not reserve all requested products. Please use the \'Mark as Todo\' button to handle the reservation manually."))

            for move in picking.move_lines.filtered(lambda m: m.state not in ['done', 'cancel']):
                for move_line in move.move_line_ids:
                    move_line.qty_done = move_line.product_uom_qty
            if picking._check_backorder():
                pick_to_backorder |= picking
                continue
            pick_to_do |= picking

        # Process every picking that do not require a backorder,
        # then return a single backorder wizard for every other ones.
        if pick_to_do:
            pick_to_do.generate_picking_ddaa()
            pick_to_do.action_done()
        if pick_to_backorder:
            return pick_to_backorder.action_generate_backorder_wizard()
        return False
