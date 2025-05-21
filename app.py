import os
import csv
import yfinance as yf
import re
import pdfplumber

def get_price(ticker):
    try: return yf.Ticker(ticker).history(period='1d')['Close'].iloc[-1]
    except Exception as e:
        print(f"Error fetching price for {ticker}: {e}")
        return 0

# with open('assets.csv', 'r') as file:
#     reader = csv.reader(file)
#     header = next(reader)  # Skip header
#     print(f"{'Name':<20} {'Quantity':<15} {'Total ($)':<10}")
#     print("-" * 45)

#     totals = {}
#     for row in reader:
#         name, quantity = row
#         if quantity.startswith('$'): total = float(quantity.replace('$', ''))
#         else:
#             # Convert quantity to float and fetch price
#             qty = float(quantity)
#             price = get_price(name)
#             total = qty * price if price else 0
#         totals[name] = total

#         print(f"{name:<20} {quantity:<15} {total:.2f}")

#     total_value = sum(totals.values())
#     print("-" * 45)
#     print(f"{'Total Value':<20} {'':<15} {total_value:.2f}")
#     print("-" * 45)

def extract_text_from_pdf(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    print(f"text: {text}")
    return text

def extract_transactions_from_cc_statement(file_path, account_name, n_date_cols=1):
    pattern = r'^\d{2}/\d{2}\s+(.+?)\s+-?\d{1,3}(,\d{3})*\.\d{2}$'
    # pattern = r'^\d{2}/\d{2}\s+\d{2}/\d{2}\s+(.+?)\s+-?\d{1,3}(,\d{3})*\.\d{2}$'

    if account_name not in ["chase_prime", "bofa_allegiant"]:
        print("here")

    text = extract_text_from_pdf(file_path)

    filename = file_path.split('/')[-1]

    matching_lines = []

    # date:
    # chase_prime
    # Opening/Closing Date 04/14/24 - 05/13/24

    # bofa_allegiant
    #
    # August 10 - September 9, 2023
    # Account Summary/Payment Information
    # . . .
    # Statement Closing Date 09/09/2023
    # charges using this card balanceshownonthis payinganestimated
    # Days in Billing Cycle 31

    # bofa_business
    # January 11, 2025 - February 10, 2025 Company Statement

    for line in text.split('\n'):
        line = line.strip()
        if not line:
            continue
        if re.match(pattern, line):
            matching_lines.append(line)

    transactions = []
    # now split into the date, description, and amount
    for i, line in enumerate(matching_lines):
        # Split the line into parts
        parts = line.split()
        # Extract the date (first two parts)
        date = ' '.join(parts[:1])
        # Extract the amount (last part)
        amount = float(parts[-1].replace(',', ''))
        # Extract the description (everything in between)
        description = ' '.join(parts[n_date_cols + 1:-1])
        # Replace the original line with a tuple of (date, description, amount)
        if amount == 0.0: continue
        transactions.append([date, description, amount, filename, account_name])

    print("Extracted transactions:")
    for transaction in transactions:
        print(transaction)

    return transactions

def extract_transactions_from_directory(directory, account_name, n_date_cols=1):
    transactions = []
    for filename in os.listdir(directory):
        if filename.endswith(".pdf"):
            file_path = os.path.join(directory, filename)
            transactions += extract_transactions_from_cc_statement(file_path, account_name, n_date_cols)
    return transactions

extract_transactions_from_directory("./data/chase_prime/", "chase_prime", n_date_cols=1)
extract_transactions_from_directory("./data/bofa_allegiant/", "bofa_allegiant", n_date_cols=2)
extract_transactions_from_directory("./data/bofa_business/", "bofa_business", n_date_cols=2)
