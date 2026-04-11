# -*- coding: utf-8 -*-
"""Pre-migration: rename montant -> amount on telecom_avance_remboursement."""
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return
    _logger.info(
        "telecom_finance_ma: renaming column montant -> amount "
        "on telecom_avance_remboursement"
    )
    # SQL direct : column rename during schema migration (ORM not available in pre-migration)
    cr.execute("""
        ALTER TABLE telecom_avance_remboursement
        RENAME COLUMN montant TO amount
    """)
