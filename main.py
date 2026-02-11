import argparse
import logging
import sys

import config
import database
import degiro_client
import scheduler


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    parser = argparse.ArgumentParser(
        description="DeGiro Daily Stock Tracker — fetch and store portfolio snapshots"
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Fetch once and exit (don't start scheduler)",
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Show the latest snapshot from the database and exit",
    )
    args = parser.parse_args()

    # Validate credentials
    if not args.show and (not config.DEGIRO_USERNAME or not config.DEGIRO_PASSWORD):
        print(
            "Error: DEGIRO_USERNAME and DEGIRO_PASSWORD must be set.\n"
            "Copy .env.example to .env and fill in your credentials.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Initialize database
    database.init_db()

    if args.show:
        show_latest_snapshot()
    elif args.once:
        scheduler.fetch_and_store()
    else:
        # Run one fetch immediately, then start the daily scheduler
        scheduler.fetch_and_store()
        scheduler.start_scheduler()


def show_latest_snapshot():
    """Print the most recent portfolio snapshot."""
    conn = database.get_connection()

    row = conn.execute(
        "SELECT * FROM portfolio_snapshot ORDER BY id DESC LIMIT 1"
    ).fetchone()

    if not row:
        print("No snapshots found in the database.")
        return

    print(f"Snapshot #{row['id']} — {row['fetched_at']}")
    print(f"  Total portfolio value: {row['total_portfolio_value']}")
    print(f"  Total cash:            {row['total_cash']}")
    print(f"  Deposits/withdrawals:  {row['total_deposit_withdrawal']}")
    print(f"  Free space:            {row['free_space']}")
    print()

    positions = conn.execute(
        "SELECT * FROM position WHERE snapshot_id = ? ORDER BY value DESC",
        (row["id"],),
    ).fetchall()

    if positions:
        print(f"  {'Name':<30} {'ISIN':<15} {'Size':>8} {'Price':>10} {'Value':>12} {'P/L':>10}")
        print(f"  {'-'*30} {'-'*15} {'-'*8} {'-'*10} {'-'*12} {'-'*10}")
        for p in positions:
            print(
                f"  {(p['name'] or 'N/A'):<30} "
                f"{(p['isin'] or ''):<15} "
                f"{p['size'] or 0:>8.2f} "
                f"{p['price'] or 0:>10.2f} "
                f"{p['value'] or 0:>12.2f} "
                f"{p['pl'] or 0:>10.2f}"
            )
    conn.close()


if __name__ == "__main__":
    main()
