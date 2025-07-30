# mcard/model/schema.py
"""
Shared SQL schema definitions for MCard storage engines.
"""

CARD_TABLE_SCHEMA = (
    """
    CREATE TABLE IF NOT EXISTS card (
        hash TEXT PRIMARY KEY,
        content BLOB NOT NULL,
        g_time TEXT
    )
    """
)
