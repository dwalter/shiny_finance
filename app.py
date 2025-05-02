import os
import csv
import yfinance as yf
import re
import pdfplumber

path = "/Users/dwalter/Documents/finance/taxes-2025(for yr 2024)/chase_prime_visa_credit_card_statements_2024/20240113-statements-1104-.pdf"

allegiant_path = "./data/bofa_allegiant/eStmt_2022-09-09.pdf"

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

def extract_text_from_pdf(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return text

def extract_transactions_from_cc_statement(file_path, account_name, n_date_cols=1):
    pattern = r'^\d{2}/\d{2}\s+(.+?)\s+-?\d{1,3}(,\d{3})*\.\d{2}$'
    # pattern = r'^\d{2}/\d{2}\s+\d{2}/\d{2}\s+(.+?)\s+-?\d{1,3}(,\d{3})*\.\d{2}$'

    text = extract_text_from_pdf(file_path)

    filename = file_path.split('/')[-1]

    matching_lines = []

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

# extract_transactions_from_cc_statement(path, "chase_prime", n_date_cols=1)
# extract_transactions_from_cc_statement(allegiant_path, "bofa_allegiant", n_date_cols=2)

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
