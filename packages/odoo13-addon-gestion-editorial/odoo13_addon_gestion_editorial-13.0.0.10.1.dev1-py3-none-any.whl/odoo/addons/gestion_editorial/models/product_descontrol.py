from odoo import models, fields, api, exceptions


class EditorialProducts(models.Model):
    """ Extend product product for editorial management """

    _description = "Editorial Core Products"
    _inherit = 'product.product'

    on_hand_qty = fields.Float(compute='_compute_on_hand_qty', string='En almacén')
    liquidated_qty = fields.Float(compute='_compute_liquidated_sales_qty', string='Ventas liquidadas')
    liquidated_purchases_qty = fields.Float(compute='_compute_liquidated_purchases_qty', string='Compras liquidadas')
    owned_qty = fields.Float(compute='_compute_owned_qty', string='Existencias totales')
    in_distribution_qty = fields.Float(compute='_compute_in_distribution_qty', string='En distribución')
    purchase_deposit_qty = fields.Float(compute='_compute_purchase_deposit_qty', string='Depósito de compra')
    received_qty = fields.Float(compute='_compute_received_qty', string='Recibidos')

    def get_liquidated_sales_qty(self):
        return (
            self.get_product_quantity_in_location(
                self.env.ref("stock.stock_location_customers")
            ) - self.get_sales_to_author_qty()
        )

    def get_product_quantity_in_location(self, location):
        location_ids = location.get_all_child_locations()

        quants = self.env['stock.quant'].search([
            ('product_id', '=', self.id),
            ('location_id', 'in', location_ids)
        ])

        quantity = sum(quant.quantity for quant in quants)
        return quantity

    def get_received_qty(self):
        domain = [
            ('state', 'in', ['purchase', 'done']),
            ('product_id', '=', self.id)
        ]
        purchase_order_lines = self.env['purchase.order.line'].search(domain)
        return sum(purchase_order_lines.mapped('qty_received'))

    def get_liquidated_purchases_qty(self):
        domain = [
            ('state', 'in', ['purchase', 'done']),
            ('product_id', '=', self.id)
        ]
        purchase_order_lines = self.env['purchase.order.line'].search(domain)
        return sum(purchase_order_lines.mapped('liquidated_qty'))
    
    def get_liquidated_sales_qty_per_partner(self, partner_id):
        liquidated_sale_lines = self.env['stock.move.line'].search([
            ('owner_id', '=', partner_id),
            ('state', '=', 'done'),
            ('location_dest_id', '=', self.env.ref("stock.stock_location_customers").id),
            ('product_id', '=', self.id)
        ])
        liquidated_sales_qty = sum(line.qty_done for line in liquidated_sale_lines)

        returned_sale_lines = self.env['stock.move.line'].search([
            ('owner_id', '=', partner_id),
            ('state', '=', 'done'),
            ('location_id', '=', self.env.ref("stock.stock_location_customers").id),
            ('product_id', '=', self.id)
        ])
        returned_sales_qty = sum(line.qty_done for line in returned_sale_lines)
        return liquidated_sales_qty - returned_sales_qty

    def get_sales_to_author_qty(self):
        # Get sale orders with author pricelist
        sale_order_lines = self.env['sale.order.line'].search([
            ('product_id', '=', self.id),
            ('order_id.pricelist_id', '=',
             self.env.company.sales_to_author_pricelist.id)
        ])
        sale_orders = sale_order_lines.mapped('order_id')

        # Get stock moves related to these orders
        stock_moves = self.env['stock.move'].search([
            ('picking_id.sale_id', 'in', sale_orders.ids),
            ('state', '=', 'done'),
            ('product_id', '=', self.id)
        ])

        stock_moves_sales = stock_moves.filtered(
            lambda m: m.picking_code == 'outgoing'
        )
        stock_moves_refunds = stock_moves.filtered(
            lambda m:
            m.picking_code == 'incoming'
            and m.origin_returned_move_id
        )

        total_quantity = (
            sum(move.product_uom_qty for move in stock_moves_sales) - 
            sum(move.product_uom_qty for move in stock_moves_refunds)
        )
        return total_quantity

    @api.constrains('lst_price')
    def update_ddaa_orders_price(self):
        if self.env.company.module_editorial_ddaa and \
            self.env.company.product_category_ddaa_id == self.categ_id:
            # we use self.id.origin when function calling comes from product template
            product_id = self.id.origin if hasattr(self.id, 'origin') else self.id
            domain = [
                ('product_id', '=', product_id),
                ('state', '=', 'draft'),
                ('order_id.is_ddaa_order', '=', True)
            ]
            ddaa_order_lines = self.env['purchase.order.line'].search(domain)
            for line in ddaa_order_lines:
                for authorship in self.product_tmpl_id.authorship_ids:
                    if authorship.author_id.id == line.partner_id.id:
                        line.price_unit = authorship.price
                        line.order_id.message_post(
                            body=f"Se ha modificado el precio del producto: {self.name} para esta autoría. "
                                f"Su nuevo precio es: {authorship.price}",
                            message_type='comment',
                            subtype_xmlid='mail.mt_note'
                        )

    def _compute_liquidated_purchases_qty(self):
        for product in self:
            product.liquidated_purchases_qty = product.get_liquidated_purchases_qty()

    def _compute_received_qty(self):
        for product in self:
            product.received_qty = product.get_received_qty()

    def _compute_purchase_deposit_qty(self):
        #Purchased on deposit but not settled
        for product in self:
            product.purchase_deposit_qty = product.received_qty - product.liquidated_purchases_qty

    def _compute_on_hand_qty(self):
        for product in self:
            product.on_hand_qty = product.get_product_quantity_in_location(self.env.ref("stock.stock_location_stock"))

    def _compute_liquidated_sales_qty(self):
        for product in self:
            product.liquidated_qty = product.get_liquidated_sales_qty()

    def _compute_owned_qty(self):
        for product in self:
            product.owned_qty = product.on_hand_qty + product.in_distribution_qty

    def _compute_in_distribution_qty(self):
        for product in self:
            product.in_distribution_qty = product.get_product_quantity_in_location(self.env.company.location_venta_deposito_id)


class EditorialTemplateProducts(models.Model):
    """ Extend product template for editorial management """

    _description = "Editorial Template Products"
    _inherit = 'product.template'
    # we inherited product.template model which is Odoo/OpenERP built in model and edited several fields in that model.
    isbn_number = fields.Char(string="ISBN", copy=False, required=False,
                              help="International Standard Book Number \
                              (ISBN)")
    product_tags = fields.Many2many(
        'product.template.tag', string='Product tag')
    purchase_ok = fields.Boolean('Can be Purchased', default=False)
    author_name = fields.Many2many("res.partner", string="Autores",
                                   required=False,
                                   help="Nombre del autor",
                                   domain="[('is_author','=',True)]"
                                   )
    on_hand_qty = fields.Float(
        compute='_compute_on_hand_qty', string='En almacén')
    liquidated_qty = fields.Float(
        compute='_compute_liquidated_sales_qty', string='Ventas liquidadas')
    liquidated_purchases_qty = fields.Float(
        compute='_compute_liquidated_purchases_qty', string='Compras liquidadas')
    owned_qty = fields.Float(compute='_compute_owned_qty',
                             string='Existencias totales')
    in_distribution_qty = fields.Float(
        compute='_compute_in_distribution_qty', string='En distribución')
    purchase_deposit_qty = fields.Float(
        compute='_compute_purchase_deposit_qty', string='Depósito de compra')
    received_qty = fields.Float(
        compute='_compute_received_qty', string='Recibidos')
    authorship_ids = fields.One2many(
        'authorship.product', 'product_id', string='Authorships')
    show_ddaa_data = fields.Boolean(compute='_compute_show_ddaa_data')
    is_book = fields.Boolean(compute='_compute_is_book')

    @api.model
    def check_save_conditions(self, records_data):
        if not self.env.company.module_editorial_ddaa:
            return []
            
        conditions = []
        # Check for changes in authorships
        authorship_data = records_data.get('authorship_ids').get('data')

        for authorship_record in authorship_data:
            authorship_id = authorship_record.get('data', {}).get('id', False)
            price = authorship_record.get('data', {}).get('price', 0)
            author_id = authorship_record.get('data', {}).get('author_id', False).get('data', {}).get('id', None)
            authorship = self.env['authorship.product'].browse(authorship_id)

            # If authorship is not found or price/author is different, ask for confirmation
            if not authorship or authorship.price != price or author_id != authorship.author_id.id:
                conditions.append({
                    'message': 'Al guardar las autorías con el importe modificado \
                    se procederá a actualizar el precio del producto en los albaranes de autoría \
                    que todavía no hayan sido confirmados. \
                    ¿Deseas continuar?'
                })
                break

        # Confirm dialog if DDAA product list price is modified
        product = self.browse(records_data.get('id'))
        if (
            self.env.company.product_category_ddaa_id == product.categ_id and
            records_data['list_price'] != product.list_price
        ):
            conditions.append({
                'message': 'Si se guarda el producto con el precio modificado \
                se procederá a actualizar el precio del producto en los albaranes de autoría \
                que todavía no hayan sido confirmados. \
                ¿Deseas continuar?'
            })

        return conditions

    # Show ddaa data in product view
    # if product generate ddaa or is ddda product
    def _compute_show_ddaa_data(self):
        self.show_ddaa_data = (
            self.env.company.module_editorial_ddaa and
            (self.env.company.product_category_ddaa_id == self.categ_id or
             self.env.company.is_category_genera_ddaa_or_child(self.categ_id))
        )

    # Product categ is book or child (All/Libros) or (All/Libro Digital)
    def _compute_is_book(self):
        self.is_book = (
         self.categ_id.id == self.env.ref("gestion_editorial.product_category_books").id 
         or self.categ_id.id == self.env.ref("gestion_editorial.product_category_digital_books").id
         or self.categ_id.parent_id.id == self.env.ref("gestion_editorial.product_category_books").id
         or self.categ_id.parent_id.id == self.env.ref("gestion_editorial.product_category_digital_books").id
        )

    def _compute_on_hand_qty(self):
        for template in self:
            on_hand_qty = 0.0
            for product in template.product_variant_ids:
                on_hand_qty += product.get_product_quantity_in_location(self.env.ref("stock.stock_location_stock"))
            template.on_hand_qty = on_hand_qty

    def _compute_liquidated_sales_qty(self):
        for template in self:
            liquidated_sales_qty = 0.0
            for product in template.product_variant_ids:
                liquidated_sales_qty += product.get_liquidated_sales_qty()
            template.liquidated_qty = liquidated_sales_qty

    def _compute_liquidated_purchases_qty(self):
        for template in self:
            liquidated_purchases_qty = 0.0
            for product in template.product_variant_ids:
                liquidated_purchases_qty += product.get_liquidated_purchases_qty()
            template.liquidated_purchases_qty = liquidated_purchases_qty

    def _compute_purchase_deposit_qty(self):
        for template in self:
            template.purchase_deposit_qty = template.received_qty - template.liquidated_purchases_qty

    def _compute_received_qty(self):
        for template in self:
            received_qty = 0.0
            for product in template.product_variant_ids:
                received_qty += product.get_received_qty()
            template.received_qty = received_qty

    def _compute_owned_qty(self):
        for template in self:
            template.owned_qty = template.on_hand_qty + template.in_distribution_qty

    def _compute_in_distribution_qty(self):
        for template in self:
            in_distribution_qty = 0.0
            for product in template.product_variant_ids:
                in_distribution_qty += product.get_product_quantity_in_location(self.env.company.location_venta_deposito_id)
            template.in_distribution_qty = in_distribution_qty

    @api.onchange('list_price')
    def _update_ddaa_orders_price(self):
        if self.env.company.module_editorial_ddaa and \
            self.env.company.product_category_ddaa_id == self.categ_id:

            if len(self.authorship_ids) == 1: self.authorship_ids[0].price = self.list_price    

            total_authorships_price = sum(self.authorship_ids.mapped('price'))
            if round(self.list_price, 9) != round(total_authorships_price, 9):
                raise exceptions.ValidationError(
                    f"La suma de los importes recibidos por las receptoras de regalías debe coincidir con el precio del producto:\n"
                    f"Suma de los importes: {total_authorships_price}\n"
                    f"Precio del producto: {self.list_price}\n"
                    f"Puedes modificar esta cantidad en la página de DDAA de este producto.\nModifica primero el importe de las receptoras y luego el precio del producto."
                )
            
            for product in self.product_variant_ids:
                product.update_ddaa_orders_price()

    @api.constrains("authorship_ids")
    def _check_authorships_price_sum_is_equal_to_ddaa_product_price(self):
        if self.env.company.module_editorial_ddaa and \
            self.env.company.product_category_ddaa_id == self.categ_id and self.authorship_ids:
            total_price = sum(self.authorship_ids.mapped('price'))
            if round(total_price, 9) != round(self.list_price, 9):
                raise exceptions.ValidationError(
                    f"La suma de los importes recibidos por los receptores de derechos debe coincidir con el precio del producto:\n"
                    f"Suma de los importes: {total_price}\n"
                    f"Precio del producto: {self.list_price}"
                )
            for product in self.product_variant_ids:
                product.update_ddaa_orders_price()

    @api.constrains("authorship_ids")
    def _update_ddaa_orders_book_price(self):
        if self.env.company.module_editorial_ddaa and \
            self.env.company.product_category_ddaa_id != self.categ_id and self.authorship_ids:
            authors = self.authorship_ids.mapped('author_id').ids
            domain = [
                    ('partner_id', 'in', authors),
                    ('state', '=', 'draft'),
                    ('is_ddaa_order', '=', True)
                ]
            authorship_purchase_orders = self.env['purchase.order'].search(domain)

            for authorship in self.authorship_ids:
                for purchase_order in authorship_purchase_orders:
                    if authorship.author_id.id == purchase_order.partner_id.id:
                        purchase_order.update_ddaa_order_book_line(self.product_variant_id, 'update_price', -authorship.price)

    @api.constrains("isbn_number")
    def check_is_isbn13(self):
        for record in self:
            if record.isbn_number:
                n = record.isbn_number.replace("-", "").replace(" ", "")
                if len(n) != 13:
                    raise exceptions.ValidationError("El ISBN debe tener 13 dígitos")
                product = sum(int(ch) for ch in n[::2]) + sum(
                    int(ch) * 3 for ch in n[1::2]
                )
                if product % 10 != 0:
                    raise exceptions.ValidationError(
                        "El ISBN %s no es válido." % record.isbn_number
                    )
        # all records passed the test, don't return anything

    # Using product price without taxes
    def get_ddaa_product_price(self, price=None, taxes_data=None):
        currency = self.env.user.company_id.currency_id
        price_total = self.list_price if not price else price
        if self.taxes_id:
            taxes_calculated = self.taxes_id.compute_all(
                price_total, 
                currency, 
                quantity=1.0
            )
            price_without_taxes = taxes_calculated['total_excluded']
        # taxes_data is a tuple with format [(6, 0, [Taxes IDs])]
        elif taxes_data and taxes_data[0][0] == 6:
            tax_ids = taxes_data[0][2]
            taxes = self.env['account.tax'].browse(tax_ids)
            taxes_calculated = taxes.compute_all(
                price_unit=price_total,
                currency=currency,
                quantity=1.0
            )
            price_without_taxes = taxes_calculated['total_excluded']
        else:
            price_without_taxes = price_total
        
        return round(price_without_taxes, 2) * (self.env.company.ddaa_price_percentage / 100)

    def get_reference_product_price_for_author(self, author_id):
        product_price = 0
        if self.producto_referencia:
            for authorship in self.producto_referencia[0].authorship_ids:
                if authorship.author_id.id == author_id.id:
                    product_price = authorship.price
        return product_price

    def create_ddaa_authorships(self):
        authors = self.author_name
        authorships = []
        for author in authors:
            authorship = self.env['authorship.product'].create({
                'product_id': self.id,
                'author_id': author.id,
                'price': self.list_price / len(authors)
            })
            authorships.append(authorship.id)
    
        self.write({
            'authorship_ids': [(6, 0, authorships)]
        })

    def create_book_section_for_ddaa_order(self, ddaa_order, authorship,
                                           ddaa_qty):
        sequence_number = len(ddaa_order.order_line) + 10
        section_line = {
            'order_id': ddaa_order.id,
            'name': self.producto_referencia[0].name,
            'display_type': 'line_section',
            'product_id': False,
            'product_qty': 0,
            'product_uom_qty': 0,
            'price_unit': 0,
            'sequence': sequence_number,
        }
        book_ddaa_line = {
            'name': self.name,
            'order_id': ddaa_order.id,
            'product_id': self.product_variant_ids[0].id,   # This field needs product.product id, ddaa is template.product, so we get the first product variant
            'product_qty': ddaa_qty,
            'price_unit': authorship.price,
            'product_uom': 1,
            'date_planned': ddaa_order.date_order,
            'display_type': False,
            'sequence': sequence_number + 1,
        }
        books_delivered_to_authorship_line = {
            'name': self.env.ref("gestion_editorial.product_books_delivered_to_authorship").name,
            'order_id': ddaa_order.id,
            'product_id': self.env.ref("gestion_editorial.product_books_delivered_to_authorship").id,
            'product_qty': 0,
            'price_unit': -self.get_reference_product_price_for_author(authorship.author_id),
            'date_planned': ddaa_order.date_order,
            'product_uom': 1,
            'display_type': False,
            'sequence': sequence_number + 2,
        }
        royalty_advance_line = {
            'name': self.env.ref("gestion_editorial.product_royalties_advance").name,
            'order_id': ddaa_order.id,
            'product_id': self.env.ref("gestion_editorial.product_royalties_advance").id,
            'product_qty': 0,
            'price_unit': 0,
            'date_planned': ddaa_order.date_order,
            'product_uom': 1,
            'display_type': False,
            'sequence': sequence_number + 3,
        }    

        ddaa_order.write({'order_line': [(0,0,section_line),
                                         (0,0,book_ddaa_line),
                                         (0,0,books_delivered_to_authorship_line),
                                         (0,0,royalty_advance_line),
                                         ]})

    def generate_ddaa_purchase_order(self, authorship, ddaa_qty):
        domain = [
                ('partner_id', '=', authorship.author_id.id),
                ('state', '=', 'draft'),
                ('is_ddaa_order', '=', True)
            ]
        authorship_purchase_order = self.env['purchase.order'].search(domain, order='date_order desc')
        if not authorship_purchase_order:
            # Create purchase.order to ddaa receiver
            authorship_purchase_order = self.env['purchase.order'].create({
                'partner_id': authorship.author_id.id,
                'is_ddaa_order': True,
                'picking_type_id': self.env.ref("stock.picking_type_in").id
            })
        elif len(authorship_purchase_order) > 1:
            authorship_purchase_order = authorship_purchase_order[0]
        # Search line and add or substract qty
        book_purchase_line = authorship_purchase_order.order_line.filtered(lambda line: line.product_id.product_tmpl_id.id == self.id)
        if book_purchase_line:
            if len(book_purchase_line) > 1:
                book_purchase_line = book_purchase_line[0]
            book_purchase_line.write({'product_qty': book_purchase_line.product_qty + ddaa_qty})
        else:
            self.create_book_section_for_ddaa_order(authorship_purchase_order, authorship, ddaa_qty)

    def button_generate_ddaa_purchase_order(self):
        if not self.env.company.module_editorial_ddaa or \
            not (self.genera_ddaa or self.categ_id == self.env.company.product_category_ddaa_id):
            raise exceptions.ValidationError(
                'Este producto no genera DDAA o el modulo de DDAA no esta habilitado.'
            )
        if self.categ_id == self.env.company.product_category_ddaa_id:
            if not self.authorship_ids:
                raise exceptions.ValidationError('Este libro no tiene autorías asociadas.')
            for authorship in self.authorship_ids:
                self.generate_ddaa_purchase_order(authorship, 0)
        else:   # Product is book
            self.generate_ddaa(0)
        
        self.message_post(
            body=f"Se han creado los albaranes de autoría para este producto utilizando el botón de 'Generar albaranes de autoría'.",
            message_type='comment',
            subtype_xmlid='mail.mt_note'
        )

    def generate_ddaa(self, ddaa_qty):
        if not self.env.company.module_editorial_ddaa or not self.genera_ddaa:
            return
        # check if the product already has ddaa
        ddaa = self.derecho_autoria
        if not ddaa:
            authors = self.author_name
            if not authors:
                return
            else:
                ddaa = self.env['product.template'].create({
                    'name': 'DDAA de ' + self.name,
                    'categ_id': self.env.company.product_category_ddaa_id.id,
                    'list_price': self.get_ddaa_product_price(),
                    'type': 'service',
                    'sale_ok': False,
                    'purchase_ok': True,
                    'author_name': authors,
                    'producto_referencia': [self.id],
                    'derecho_autoria': False,
                    "supplier_taxes_id": False
                })
                ddaa.create_ddaa_authorships()
        
        # Generate purchase order for each authorship receptor
        for authorship in ddaa.authorship_ids:
            ddaa.generate_ddaa_purchase_order(authorship, ddaa_qty)

    # DDAA: Derechos de autoría
    # When the category "All / Books" is selected (with id 5), the default values ​​are set:
    # Product that can be sold and bought is storable.
    @api.onchange("categ_id")
    def _onchange_uom(self):
        book_categ_id = self.env.ref("gestion_editorial.product_category_books").id
        digital_book_categ_id = self.env.ref("gestion_editorial.product_category_digital_books").id
        if (
            self.categ_id.id == book_categ_id
            or self.categ_id.parent_id.id == book_categ_id
        ):
            self.sale_ok = True
            self.purchase_ok = True
            self.type = "product"
        elif (
            self.categ_id.id == digital_book_categ_id
            or self.categ_id.parent_id.id == digital_book_categ_id
        ):
            self.sale_ok = True
            self.purchase_ok = True
            self.type = "consu"
        if (
            self.env.company.module_editorial_ddaa
            and self.env.company.is_category_genera_ddaa_or_child(self.categ_id)
        ):
            self.genera_ddaa = True
        else:
            self.genera_ddaa = False

    @api.onchange("categ_id")
    def _compute_view_show_fields(self):
        if self.env.company.module_editorial_ddaa:
            self.view_show_genera_ddaa_fields = (
                self.env.company.is_category_genera_ddaa_or_child(self.categ_id)
            )
            self.view_show_ddaa_fields = (
                self.categ_id == self.env.company.product_category_ddaa_id
            )
        else:
            self.view_show_genera_ddaa_fields = False
            self.view_show_ddaa_fields = False

    # DDAA: Copyright
    # Check one2one relation. Here between "producto_referencia" y "derecho_autoria"
    #
    # Note: we are creating the relationship between the templates.
    # Therefore, when we add the product to a stock.picking or a sale or purchase, we are actually adding the product  and not the template.
    # Please use product_tmpl_id to access the template of a product.
    producto_referencia = fields.One2many(
        "product.template",
        "derecho_autoria",
        string="Libro de referencia",
        help="Este campo se utiliza para relacionar el derecho de autoría con el libro",
    )

    # prod_ref = fields.Many2one("product.template", compute='compute_autoria', inverse='autoria_inverse', string="prod ref",
    #                             required=False)

    @api.model
    def _derecho_autoria_domain(self):
        return [("categ_id", "=", self.env.company.product_category_ddaa_id.id)]

    derecho_autoria = fields.Many2one(
        "product.template",
        domain=_derecho_autoria_domain,
        string="Producto ddaa",
        help="Este campo se utiliza para relacionar el derecho de autoría con el libro",
    )

    genera_ddaa = fields.Boolean("Genera derechos de autoría", default=False)

    # @api.depends('producto_referencia')
    # def compute_autoria(self):
    #     if len(self.derecho_autorias) > 0:
    #         self.derecho_autoria = self.derecho_autorias[0]

    # def autoria_inverse(self):
    #     if len(self.derecho_autorias) > 0:
    #         # delete previous reference
    #         ddaa = self.env['product.template'].browse(self.derecho_autorias[0].id)
    #         ddaa.producto_referencia = False
    #     # set new reference
    #     self.derecho_autoria.producto_referencia = self

    view_show_genera_ddaa_fields = fields.Boolean(
        "Muestra los campos asociados a categorías que generan ddaa",
        compute="_compute_view_show_fields",
        default=False,
    )
    view_show_ddaa_fields = fields.Boolean(
        "Muestra los campos asociados a la categoría ddaa",
        compute="_compute_view_show_fields",
        default=False,
    )

    limited_visibility_by_provider = fields.Boolean(
        "Visibilidad limitada por proveedor", 
        help="El producto solo será visible en compras para los proveedores configurados",
        default=lambda self: self.env.company.visibility_limited_by_supplier
    )

    # DDAA: Copyright
    # A product associated with the category representing the DDAA is created
    @api.model_create_multi
    def create(self, vals_list):
        templates = super(EditorialTemplateProducts, self).create(vals_list)
        company = self.env.company
        if company.module_editorial_ddaa and vals_list:
            vals = vals_list[0]
            category_id = self.env["product.category"].browse(vals.get("categ_id"))
            if (
                company.is_category_genera_ddaa_or_child(category_id)
                and vals.get("genera_ddaa") == True
            ):
                ddaa = self.env["product.template"].create(
                    {
                        "name": "DDAA de " + vals.get("name"),
                        "categ_id": company.product_category_ddaa_id.id,
                        "list_price": self.get_ddaa_product_price(vals.get("list_price"), vals.get("taxes_id")),
                        "type": "service",
                        "sale_ok": False,
                        "purchase_ok": True,
                        "author_name": vals.get("author_name"),
                        "producto_referencia": [templates.id],
                        "derecho_autoria": False,
                        "supplier_taxes_id": False
                    }
                )
                ddaa.create_ddaa_authorships()
        return templates

    def get_sales_to_author_qty(self):
        sales_to_author_qty = 0.0
        for product in self.product_variant_ids:
            sales_to_author_qty += product.get_sales_to_author_qty()

        return sales_to_author_qty


class EditorialProductTags(models.Model):
    """ Editorial product tags management """

    _description = 'Editorial product tags'
    _name = 'product.template.tag'
    _rec_name = 'name'

    name = fields.Char(string='Product tag', required=True)

class EditorialAuthorshipProduct(models.Model):
    """ Editorial author management """

    _description = 'Editorial author information'
    _name = 'authorship.product'
    _rec_name = 'author_id'

    author_id = fields.Many2one("res.partner", required=True,
                                ondelete="cascade")
    product_id = fields.Many2one(
        "product.template", required=True, 
        ondelete="cascade", index=True)
    # Special price for author if product is book
    # Amount received from DDAA if product is DDAA
    price = fields.Float(required=True, default=0.0)
      