from odoo import api, SUPERUSER_ID
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    try:
        env = api.Environment(cr, SUPERUSER_ID, {})
        _logger.warning("### MIGRATING TO 13.0.0.9.0 ###")

        picking_delivery_to_authorship = env.ref(
            "gestion_editorial.stock_picking_type_entrega_autoria"
        )
        picking_delivery_to_authorship.default_location_dest_id = env.ref(
            "gestion_editorial.stock_location_authors_royalties"
        ).id
        picking_delivery_to_authorship.name = (
            "Entrega de libros a autoría (Cuenta de regalías)"
        )

        if not env.company.location_authors_royalties_id:
            env.company.location_authors_royalties_id = env.ref(
                "gestion_editorial.stock_location_authors_royalties"
            ).id

        if not env.company.location_authors_courtesy_id:
            env.company.location_authors_courtesy_id = env.ref(
                "gestion_editorial.stock_location_authors_courtesy"
            ).id

        if not env.company.location_promotion_id:
            env.company.location_promotion_id = env.ref(
                "gestion_editorial.stock_location_promocion"
            ).id

        if not env.company.sales_to_author_pricelist:
            env.company.sales_to_author_pricelist = env.ref(
                "gestion_editorial.authors_pricelist"
            )

        products = env["product.template"].search([])

        for product in products:
            # DDAA receptor migration: Only one repceptora DDAA, price of ddaa product
            if (product.categ_id.id == env.company.product_category_ddaa_id.id):
                if (product.receptora_derecho_autoria):
                    authorship = env["authorship.product"].create(
                        {
                            "product_id": product.id,
                            "author_id": product.receptora_derecho_autoria[0].id,
                            "price": product.list_price,
                        }
                    )
                    product.authorship_ids = [(4, authorship.id)]

                    _logger.info(
                        f"### Migrated Product ID:{product.id} - \
                        Name: {product.name} - \
                        DDAA receptor: {product.receptora_derecho_autoria[0]}"
                    )

            # Authors migration: all authors price 0
            else:
                authorships = []
                for author in product.author_name:
                    authorship = env["authorship.product"].create(
                        {
                            "product_id": product.id,
                            "author_id": author.id,
                            "price": 0
                        }
                    )
                    authorships.append(authorship.id)
                product.write({"authorship_ids": [(6, 0, authorships)]})

                _logger.info(
                    f"### Migrated Product ID:{product.id} - \
                    Name: {product.name} - \
                    Authors: {product.author_name}"
                )

            _logger.info(f"### Total Products: {len(products)}")

    except Exception as e:
        _logger.error(f"Error while migrating to 13.0.0.9.0 : {str(e)}")
        raise
