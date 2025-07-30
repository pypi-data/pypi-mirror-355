import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    _logger.warning("### PRE MIGRATING TO 13.0.0.9.0 ###")
    # Check if column exists before adding
    cr.execute("""
        ALTER TABLE res_company 
        ADD COLUMN IF NOT EXISTS pricelists_generate_ddaa boolean 
        DEFAULT true;
    """)

    # Update existing records
    cr.execute("""
        UPDATE res_company 
        SET pricelists_generate_ddaa = true 
        WHERE pricelists_generate_ddaa IS NULL;
    """)
