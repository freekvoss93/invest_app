import logging

from degiro_connector.trading.api import API as TradingAPI
from degiro_connector.trading.models.credentials import build_credentials
from degiro_connector.trading.models.account import UpdateOption, UpdateRequest

import config

logger = logging.getLogger(__name__)


def _build_credentials():
    """Build credentials from environment variables."""
    cred_dict = {
        "username": config.DEGIRO_USERNAME,
        "password": config.DEGIRO_PASSWORD,
    }
    if config.DEGIRO_TOTP_SECRET:
        cred_dict["totp_secret_key"] = config.DEGIRO_TOTP_SECRET

    return build_credentials(override=cred_dict)


def fetch_portfolio() -> dict:
    """Connect to DeGiro, fetch portfolio data, and return structured result.

    Returns a dict with keys:
        - summary: total portfolio value, cash, etc.
        - positions: list of individual stock positions
    """
    credentials = _build_credentials()
    trading_api = TradingAPI(credentials=credentials)
    trading_api.connect()

    # Fetch int_account — required for all subsequent API calls
    client_details = trading_api.get_client_details()
    credentials.int_account = client_details["data"]["intAccount"]

    logger.info("Connected to DeGiro (account %s)", credentials.int_account)

    # Fetch portfolio and total portfolio summary
    update = trading_api.get_update(
        request_list=[
            UpdateRequest(option=UpdateOption.PORTFOLIO, last_updated=0),
            UpdateRequest(option=UpdateOption.TOTAL_PORTFOLIO, last_updated=0),
        ],
        raw=True,
    )

    if update is None:
        trading_api.logout()
        raise RuntimeError("DeGiro get_update returned no data")

    # Parse total portfolio summary
    total_portfolio = update.get("totalPortfolio", {})
    summary = {
        "totalPortfolio": _to_float(total_portfolio.get("value")),
        "totalCash": _to_float(total_portfolio.get("totalCash")),
        "totalDepositWithdrawal": _to_float(
            total_portfolio.get("totalDepositWithdrawal")
        ),
        "freeSpaceNew": _to_float(total_portfolio.get("freeSpaceNew")),
    }

    # Parse individual positions
    raw_positions = update.get("portfolio", {}).get("value", [])
    positions = []
    product_ids = []

    for item in raw_positions:
        pos = _parse_position(item)
        if pos and pos.get("size", 0) != 0:
            positions.append(pos)
            product_ids.append(pos["id"])

    # Enrich positions with product names and ISINs
    if product_ids:
        try:
            product_info = trading_api.get_products_info(
                product_list=product_ids,
                raw=True,
            )
            products = product_info.get("data", {})
            for pos in positions:
                info = products.get(str(pos["id"]), {})
                pos["name"] = info.get("name", "Unknown")
                pos["isin"] = info.get("isin", "")
                pos["currency"] = info.get("currency", "")
        except Exception:
            logger.warning("Could not fetch product info", exc_info=True)

    trading_api.logout()
    logger.info(
        "Fetched %d positions, total value: %s",
        len(positions),
        summary.get("totalPortfolio"),
    )

    return {"summary": summary, "positions": positions}


def _parse_position(item: dict) -> dict | None:
    """Parse a raw portfolio position item into a clean dict."""
    values = {}
    for entry in item.get("value", []):
        name = entry.get("name")
        val = entry.get("value")
        if name:
            values[name] = val

    raw_id = values.get("id")
    if not raw_id:
        return None

    # Skip cash positions (id is a currency code like "EUR", not numeric)
    try:
        pos_id = int(raw_id)
    except (ValueError, TypeError):
        return None

    return {
        "id": pos_id,
        "size": _to_float(values.get("size")),
        "price": _to_float(values.get("price")),
        "value": _to_float(values.get("value")),
        "breakEvenPrice": _to_float(values.get("breakEvenPrice")),
        "pl": _to_float(values.get("plBase", {}).get("value"))
        if isinstance(values.get("plBase"), dict)
        else _to_float(values.get("plBase")),
    }


def _to_float(val) -> float | None:
    """Safely convert a value to float."""
    if val is None:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None
