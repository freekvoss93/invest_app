import sqlite3
from datetime import datetime

import config


def get_connection():
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables if they don't exist."""
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS portfolio_snapshot (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fetched_at TEXT NOT NULL,
            total_portfolio_value REAL,
            total_cash REAL,
            total_deposit_withdrawal REAL,
            free_space REAL
        );

        CREATE TABLE IF NOT EXISTS position (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            snapshot_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            name TEXT,
            isin TEXT,
            currency TEXT,
            size REAL,
            price REAL,
            value REAL,
            break_even_price REAL,
            pl REAL,
            FOREIGN KEY (snapshot_id) REFERENCES portfolio_snapshot(id)
        );

        CREATE INDEX IF NOT EXISTS idx_position_snapshot
            ON position(snapshot_id);
        CREATE INDEX IF NOT EXISTS idx_snapshot_date
            ON portfolio_snapshot(fetched_at);
    """)
    conn.commit()
    conn.close()


def insert_snapshot(summary: dict, positions: list[dict]) -> int:
    """Insert a portfolio snapshot and its positions. Returns snapshot id."""
    conn = get_connection()
    cursor = conn.cursor()

    now = datetime.now().isoformat()
    cursor.execute(
        """
        INSERT INTO portfolio_snapshot
            (fetched_at, total_portfolio_value, total_cash,
             total_deposit_withdrawal, free_space)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            now,
            summary.get("totalPortfolio"),
            summary.get("totalCash"),
            summary.get("totalDepositWithdrawal"),
            summary.get("freeSpaceNew"),
        ),
    )
    snapshot_id = cursor.lastrowid

    for pos in positions:
        cursor.execute(
            """
            INSERT INTO position
                (snapshot_id, product_id, name, isin, currency,
                 size, price, value, break_even_price, pl)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                snapshot_id,
                pos.get("id"),
                pos.get("name"),
                pos.get("isin"),
                pos.get("currency"),
                pos.get("size"),
                pos.get("price"),
                pos.get("value"),
                pos.get("breakEvenPrice"),
                pos.get("pl"),
            ),
        )

    conn.commit()
    conn.close()
    return snapshot_id
