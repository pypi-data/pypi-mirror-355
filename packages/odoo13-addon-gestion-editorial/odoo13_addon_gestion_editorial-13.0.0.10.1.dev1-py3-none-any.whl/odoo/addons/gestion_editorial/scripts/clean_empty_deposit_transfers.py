import odoo
import logging

from odoo.tools import config

_logger = logging.getLogger(__name__)

# This script remove unnecesary transfers generated from old deposit sales operations
# Use this once in databases older than version 13.0.0.10.0

# Get the database passed with -d
db_name = config.get("db_name")

if not db_name:
    raise ValueError("No database specified. Use -d <dbname> when running the script.")

_logger.info(f"### STARTING SCRIPT IN DATABASE: {db_name}")
with odoo.api.Environment.manage():
    registry = odoo.registry(db_name)
    with registry.cursor() as cr:
        env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})

        transfers = env['stock.picking'].search([
            ('state', 'in', ['confirmed', 'waiting', 'assigned']),
            ('origin', 'ilike', 'S%'),
            ('location_id', '=', env.company.location_venta_deposito_id.id),
            ('location_dest_id', '=', env.ref("stock.stock_location_customers").id),
            ('picking_type_id', '=', env.ref('stock.picking_type_out').id),
            ])

        for transfer in transfers:
            _logger.info(f"Transfer ID: {transfer.id} - {transfer.name}")
            transfer.unlink()

        _logger.info(f"### FINISHED SCRIPT IN DATABASE: {db_name}")
        _logger.info(f"### TOTAL TRANSFERS: {len(transfers)} ")

        env.cr.commit()
