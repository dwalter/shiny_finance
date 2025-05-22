import sys
import os
import csv
import yfinance as yf
import re
import pdfplumber
import datetime

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

def get_statement_start_end_dates(text, account_name):
    # chase_prime: Opening/Closing Date MM/DD/YY - MM/DD/YY
    if account_name == "chase_prime":
        chase_match = re.search(r"Opening/Closing Date (\d{2}/\d{2}/\d{2}) - (\d{2}/\d{2}/\d{2})", text)
        if not chase_match: return None, None
        start_date_str, end_date_str = chase_match.groups()
        start_date = datetime.datetime.strptime(start_date_str, "%m/%d/%y")
        end_date = datetime.datetime.strptime(end_date_str, "%m/%d/%y")
        return start_date, end_date

    # bofa_allegiant: Month DD - Month DD, YYYY
    if account_name == "bofa_allegiant":
        allegiant_match = re.search(r"(\w+ \d{1,2}) - (\w+ \d{1,2}), (\d{4})", text)
        if not allegiant_match: return None, None
        start_str, end_str, year = allegiant_match.groups()
        start_month = start_str.split()[0]
        end_month = end_str.split()[0]
        end_year = year
        start_year = year
        if end_month == "January" and start_month == "December":
            start_year = str(int(year) - 1)
        start_date = datetime.datetime.strptime(f"{start_month} {start_str.split()[1]} {start_year}", "%B %d %Y")
        end_date = datetime.datetime.strptime(f"{end_month} {end_str.split()[1]} {end_year}", "%B %d %Y")
        return start_date, end_date

    # bofa_business: Month DD, YYYY - Month DD, YYYY
    if account_name == "bofa_business":
        business_match = re.search(r"(\w+ \d{1,2}, \d{4}) - (\w+ \d{1,2}, \d{4})", text)
        if not business_match: return None, None
        start_str, end_str = business_match.groups()
        start_date = datetime.datetime.strptime(start_str, "%B %d, %Y")
        end_date = datetime.datetime.strptime(end_str, "%B %d, %Y")
        return start_date, end_date

    # If no match is found, return None
    print(f"Error: Could not find statement dates in the text for account: {account_name}")
    return None, None

def extract_transactions_from_cc_statement(file_path, account_name, n_date_cols=1):
    pattern = r'^\d{2}/\d{2}\s+(.+?)\s+-?\d{1,3}(,\d{3})*\.\d{2}$'
    # pattern = r'^\d{2}/\d{2}\s+\d{2}/\d{2}\s+(.+?)\s+-?\d{1,3}(,\d{3})*\.\d{2}$'

    # if account_name not in ["chase_prime", "bofa_allegiant"]:
    #     print("here")

    text = extract_text_from_pdf(file_path)

    filename = file_path.split('/')[-1]

    matching_lines = []

    start_date, end_date = get_statement_start_end_dates(text, account_name)

    if start_date is None or end_date is None:
        print(f"Error: Could not find statement dates in the text for account: {account_name}")
        return []

    start_month = start_date.month
    start_year = start_date.year
    prev_month = start_month - 1
    prev_year = start_year
    if prev_month == 12: prev_year -= 1
    end_month = end_date.month
    end_year = end_date.year
    month_to_year = {
        prev_month: prev_year,
        start_month: start_year,
        end_month: end_year,
    }

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
        date_day = int(date.split('/')[1])
        date_month = int(date.split('/')[0])
        date_year = month_to_year.get(date_month)
        if date_year is None:
            print(f"Error: Could not find year for month {date_month} in file {filename}")
            sys.exit(1)
            continue
        date = f"{date_month}/{date_day}/{date_year}"
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
