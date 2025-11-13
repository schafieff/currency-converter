import os
import sys
import argparse
import requests
from dotenv import load_dotenv

# Choose one provider (uncomment one block)
# --- Option A: ExchangeRate-API (free key) ---
BASE_URL = "https://v6.exchangerate-api.com/v6/{key}/latest/{base}"

# --- Option B: CurrencyFreaks (free key) ---
# BASE_URL = "https://api.currencyfreaks.com/v2.0/rates/latest?apikey={key}&base={base}"

def build_url(api_key: str, base: str) -> str:
    return BASE_URL.format(key=api_key, base=base.upper())

def fetch_rates(api_key: str, base: str) -> dict:
    """
    Fetch latest exchange rates for a base currency.
    Returns a dict with:
      - 'base'
      - 'rates' (mapping currency -> rate)
      - 'date' or 'time_last_update_utc' (provider dependent)
    Raises ValueError for bad currency or missing key.
    """
    if not api_key:
        raise ValueError("Missing API key. Put it in .env as API_KEY=...")

    url = build_url(api_key, base)
    try:
        r = requests.get(url, timeout=10)
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Network error: {e}") from e

    if r.status_code != 200:
        raise RuntimeError(f"HTTP {r.status_code}: {r.text[:200]}")

    data = r.json()

    # Normalize provider-specific shapes to a common format
    if "conversion_rates" in data:  # ExchangeRate-API
        return {
            "base": data.get("base_code", base.upper()),
            "rates": data["conversion_rates"],
            "updated": data.get("time_last_update_utc", "unknown"),
        }
    elif "rates" in data:  # CurrencyFreaks
        return {
            "base": data.get("base", base.upper()),
            "rates": {k: float(v) for k, v in data["rates"].items()},
            "updated": data.get("date", "unknown"),
        }
    else:
        raise RuntimeError(f"Unexpected API response: {str(data)[:200]}")

def convert_amount(amount: float, from_code: str, to_code: str, rates: dict) -> float:
    """
    Convert by: amount * (rate_to / rate_from)
    where rates are relative to 'rates_base' (same across both providers).
    """
    from_code = from_code.upper()
    to_code = to_code.upper()

    if from_code not in rates or to_code not in rates:
        raise ValueError(f"Unsupported currency in set: {from_code}, {to_code}")

    rate_from = rates[from_code]
    rate_to = rates[to_code]
    return amount * (rate_to / rate_from)

def parse_args(argv):
    p = argparse.ArgumentParser(
        description="Simple Currency Converter using a web API key."
    )
    p.add_argument("amount", type=float, help="Amount to convert (e.g., 100)")
    p.add_argument("from_currency", help="From currency code (e.g., USD)")
    p.add_argument("to_currency", help="To currency code (e.g., EUR)")
    p.add_argument(
        "--base",
        default="USD",
        help="Base currency for the rate table request (defaults to USD). "
             "You usually set this equal to your from-currency for best precision.",
    )
    p.add_argument(
        "--round",
        type=int,
        default=2,
        help="Round the result to this many decimals (default: 2).",
    )
    return p.parse_args(argv)

def main(argv=None):
    load_dotenv()  # loads .env
    args = parse_args(argv or sys.argv[1:])

    api_key = os.getenv("API_KEY")
    base = args.base.upper()

    try:
        data = fetch_rates(api_key, base)
        rates = data["rates"]

        # If base != from_currency, we can still convert using the two rates
        result = convert_amount(args.amount, args.from_currency, args.to_currency, rates)
        rounded = round(result, args.round)
        # TODO: format output for better readability
        # print(f"{args.amount:.2f} {args.from_currency} = {rounded:.2f} {args.to_currency}")
        print("Output improved")
        print("=== Currency Converter v1.0 ===")  # temporary change for branch demo



        # print("✅ Conversion")
        # print(f"Amount:       {args.amount} {args.from_currency.upper()}")
        # print(f"Converted to: {rounded} {args.to_currency.upper()}")
        # print(f"Rates base:   {data['base']}")
        # print(f"Updated:      {data['updated']}")
    except (ValueError, RuntimeError) as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
