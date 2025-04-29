import csv
import yfinance as yf

def get_price(ticker):
    try:
        # Handle crypto tickers
        if ticker in ['ETH', 'BTC', 'USDC']:
            ticker_map = {'ETH': 'ETH-USD', 'BTC': 'BTC-USD', 'USDC': 'USDC-USD'}
            ticker = ticker_map[ticker]
        # Fetch price from Yahoo Finance
        asset = yf.Ticker(ticker)
        price = asset.history(period='1d')['Close'].iloc[-1]
        return price
    except Exception as e:
        print(f"Error fetching price for {ticker}: {e}")
        return 0

# Read CSV file
with open('assets.csv', 'r') as file:
    reader = csv.reader(file)
    header = next(reader)  # Skip header
    print(f"{'Name':<20} {'Quantity':<15} {'Total ($)':<10}")
    print("-" * 45)

    totals = {}
    for row in reader:
        name, quantity = row
        # Check if quantity is a dollar amount
        if quantity.startswith('$'):
            total = float(quantity.replace('$', ''))
        else:
            # Convert quantity to float and fetch price
            qty = float(quantity)
            price = get_price(name)
            total = qty * price if price else 0
        totals[name] = total

        print(f"{name:<20} {quantity:<15} {total:.2f}")

    # totals:
    total_value = sum(totals.values())
    print("-" * 45)
    print(f"{'Total Value':<20} {'':<15} {total_value:.2f}")
    print("-" * 45)
