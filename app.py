import csv
import yfinance as yf

def get_price(ticker):
    try: return yf.Ticker(ticker).history(period='1d')['Close'].iloc[-1]
    except Exception as e:
        print(f"Error fetching price for {ticker}: {e}")
        return 0

with open('assets.csv', 'r') as file:
    reader = csv.reader(file)
    header = next(reader)  # Skip header
    print(f"{'Name':<20} {'Quantity':<15} {'Total ($)':<10}")
    print("-" * 45)

    totals = {}
    for row in reader:
        name, quantity = row
        if quantity.startswith('$'): total = float(quantity.replace('$', ''))
        else:
            # Convert quantity to float and fetch price
            qty = float(quantity)
            price = get_price(name)
            total = qty * price if price else 0
        totals[name] = total

        print(f"{name:<20} {quantity:<15} {total:.2f}")

    total_value = sum(totals.values())
    print("-" * 45)
    print(f"{'Total Value':<20} {'':<15} {total_value:.2f}")
    print("-" * 45)

path = "/Users/dwalter/Documents/finance/taxes-2025(for yr 2024)/chase_prime_visa_credit_card_statements_2024/20240113-statements-1104-.pdf"

import pdfplumber

def extract_text_from_pdf(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return text

extracted_text = extract_text_from_pdf(path)
print(extracted_text)

import re

def extract_transactions_from_chase_statement(text):
    '''
    Extract transaction lines from Chase statement text.
    Expected format: MM/DD Description $Amount (positive or negative)
    Example:
        01/04 Payment Thank You-Mobile -1,000.00
        12/13 Spotify USA 877-7781161 NY 10.99
        01/02 WHOLEFDS CAM 10010 CAMBRIDGE MA 10.00
    '''
    # Regex explanation:
    # ^\d{2}/\d{2} : Starts with MM/DD
    # \s+ : One or more spaces after the date
    # (.+?) : Non-greedy capture of description (anything except the amount)
    # \s+ : One or more spaces before the amount
    # -?\d{1,3}(,\d{3})*\.\d{2} : Matches positive/negative amounts (e.g., 10.99, -2,438.15)
    # $ : Ensures amount is at the end of the line
    pattern = r'^\d{2}/\d{2}\s+(.+?)\s+-?\d{1,3}(,\d{3})*\.\d{2}$'

    matching_lines = []
    for line in text.split('\n'):
        # Skip empty lines or known non-transaction lines
        line = line.strip()
        if not line:
            continue
        if any(keyword in line.lower() for keyword in ['page', 'statement date', 'totals', 'purchases', 'payments and other credits']):
            continue
        # Check if the line matches the transaction pattern
        if re.match(pattern, line):
            matching_lines.append(line)

    # now split into the date, description, and amount
    for i, line in enumerate(matching_lines):
        # Split the line into parts
        parts = line.split()
        # Extract the date (first two parts)
        date = ' '.join(parts[:1])
        # Extract the amount (last part)
        amount = float(parts[-1].replace(',', ''))
        # Extract the description (everything in between)
        description = ' '.join(parts[1:-1])
        # Replace the original line with a tuple of (date, description, amount)
        matching_lines[i] = (date, description, amount)

    return matching_lines

print("Extracted transactions:")
transactions = extract_transactions_from_chase_statement(extracted_text)
for transaction in transactions:
    print(transaction)
