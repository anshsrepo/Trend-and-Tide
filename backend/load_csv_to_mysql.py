import pandas as pd
import mysql.connector
import os

# MySQL configuration
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "root123",
    "database": "stock_prices"
}

# Directory containing CSV files
DATA_DIR = r"C:\Users\Ansh Balan\project\stock-price-app\data\stocks"

# Stocks from your app, organized by industry
stocks_by_industry = {
    "finance": ["bajaj_finance", "csl_finance", "tci_finance", "vls_finance"],
    "automotive": ["HEROMOTOCORP", "HINDMOTORS", "HYUNDAI", "TATAMOTORS", "TVSMOTORS"],
    "telecommunications": ["AIRTELPP", "HFCL", "IDEA", "TATACOMM", "TEJASNET"],
    "electronics": ["BPL", "CENTUM", "CYIENT", "PGEL", "PULZ"],
    "renewable energy": ["ADANIGREEN", "JSWENERGY", "KPIGREEN", "SUZLON", "TATAPOWER"],
    "oil stocks": ["BPCL", "DEEPINDS", "GAIL"],
    "IT industry": ["HCLTECH", "INFY", "RELIABLE", "TCS", "WIPRO"]
}

# Connect to MySQL
conn = mysql.connector.connect(**db_config)
cursor = conn.cursor()

# Drop and recreate the stocks table to match CSV structure
cursor.execute("DROP TABLE IF EXISTS stocks")
cursor.execute("""
    CREATE TABLE stocks (
        stock_name VARCHAR(50),
        date DATE,
        series VARCHAR(10),
        open_price FLOAT,
        high_price FLOAT,
        low_price FLOAT,
        prev_close FLOAT,
        ltp FLOAT,
        close FLOAT,
        vwap FLOAT,
        52w_high FLOAT,
        52w_low FLOAT,
        volume BIGINT,
        value FLOAT,
        no_of_trades INT,
        PRIMARY KEY (stock_name, date)
    )
""")

# Get actual subdirectories in the data/stocks folder
actual_subdirs = {d.lower(): d for d in os.listdir(DATA_DIR) if os.path.isdir(os.path.join(DATA_DIR, d))}

# Map expected industry names to actual directory names
industry_dir_mapping = {}
for expected_industry in stocks_by_industry.keys():
    expected_industry_lower = expected_industry.lower()
    for actual_subdir_lower, actual_subdir in actual_subdirs.items():
        if expected_industry_lower == actual_subdir_lower:
            industry_dir_mapping[expected_industry] = actual_subdir
            break
    if expected_industry not in industry_dir_mapping:
        print(f"Directory for industry {expected_industry} not found.")

# Load CSV files into MySQL
for industry, stock_list in stocks_by_industry.items():
    if industry not in industry_dir_mapping:
        continue

    industry_dir = os.path.join(DATA_DIR, industry_dir_mapping[industry])
    for stock_name in stock_list:
        csv_file = os.path.join(industry_dir, f"{stock_name.upper()}.csv")
        if not os.path.exists(csv_file):
            print(f"CSV file for {stock_name} in {industry} not found.")
            continue

        try:
            # Read the CSV file
            df = pd.read_csv(csv_file)

            # Trim spaces from column names
            df.columns = df.columns.str.strip()

            # Print the columns to debug
            print(f"Columns in {stock_name}.csv: {list(df.columns)}")

            # Find the date column (case-insensitive or common variations)
            date_col = None
            for col in df.columns:
                if col.lower() in ["date", "trading date", "trade date"]:
                    date_col = col
                    break

            if date_col is None:
                raise ValueError("No 'Date' column found (case-insensitive or common variations).")

            # Rename the date column to 'Date' for consistency
            if date_col != "Date":
                df.rename(columns={date_col: "Date"}, inplace=True)

            # Convert the Date column to datetime
            try:
                # Try the format in the CSV: DD-MMM-YYYY (e.g., 11-Apr-2025)
                df['Date'] = pd.to_datetime(df['Date'], errors='coerce', format='%d-%b-%Y')
                if df['Date'].isna().all():  # If the above fails, try other common formats
                    df['Date'] = pd.to_datetime(df['Date'], errors='coerce', format='%Y-%m-%d')
                if df['Date'].isna().all():
                    df['Date'] = pd.to_datetime(df['Date'], errors='coerce', format='%d-%m-%Y')
                if df['Date'].isna().all():
                    df['Date'] = pd.to_datetime(df['Date'], errors='coerce', format='%d/%m/%Y')
            except Exception as e:
                print(f"Error parsing dates in {stock_name}: {str(e)}")
                continue

            # Drop rows with invalid dates
            invalid_date_rows = df[df['Date'].isna()]
            if not invalid_date_rows.empty:
                print(f"Skipping {len(invalid_date_rows)} rows with invalid dates in {stock_name}:")
                print(invalid_date_rows[['Date']])
            df = df.dropna(subset=['Date'])

            if df.empty:
                print(f"No valid rows remaining after date parsing for {stock_name}.")
                continue

            # Format dates as YYYY-MM-DD for MySQL
            df['Date'] = df['Date'].dt.strftime('%Y-%m-%d')

            # Clean numeric columns by removing commas and converting to appropriate types
            numeric_cols = ['OPEN', 'HIGH', 'LOW', 'PREV. CLOSE', 'ltp', 'close', 'vwap', '52W H', '52W L', 'VOLUME', 'VALUE', 'No of trades']
            for col in numeric_cols:
                if col in df.columns:
                    # Remove commas and convert to string first to handle any non-numeric values
                    df[col] = df[col].astype(str).str.replace(',', '', regex=False)
                    # Convert to numeric, coercing errors to NaN
                    df[col] = pd.to_numeric(df[col], errors='coerce')

            # Drop rows with NaN in critical columns
            critical_cols = ['OPEN', 'HIGH', 'LOW', 'PREV. CLOSE', 'ltp', 'close', 'vwap', '52W H', '52W L', 'VOLUME']
            df = df.dropna(subset=critical_cols)

            if df.empty:
                print(f"No valid rows remaining after cleaning numeric columns for {stock_name}.")
                continue

            # Insert into MySQL
            for _, row in df.iterrows():
                query = """
                    INSERT INTO stocks (stock_name, date, series, open_price, high_price, low_price, prev_close, ltp, close, vwap, 52w_high, 52w_low, volume, value, no_of_trades)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        series=%s, open_price=%s, high_price=%s, low_price=%s, prev_close=%s, ltp=%s, close=%s, vwap=%s, 52w_high=%s, 52w_low=%s, volume=%s, value=%s, no_of_trades=%s
                """
                values = (
                    stock_name, row['Date'], row.get('series', None), row.get('OPEN', None), row.get('HIGH', None), 
                    row.get('LOW', None), row.get('PREV. CLOSE', None), row.get('ltp', None), row.get('close', None), 
                    row.get('vwap', None), row.get('52W H', None), row.get('52W L', None), row.get('VOLUME', None), 
                    row.get('VALUE', None), row.get('No of trades', None),
                    row.get('series', None), row.get('OPEN', None), row.get('HIGH', None), 
                    row.get('LOW', None), row.get('PREV. CLOSE', None), row.get('ltp', None), row.get('close', None), 
                    row.get('vwap', None), row.get('52W H', None), row.get('52W L', None), row.get('VOLUME', None), 
                    row.get('VALUE', None), row.get('No of trades', None)
                )
                cursor.execute(query, values)
            print(f"Loaded data for {stock_name} in {industry} into MySQL.")
        except Exception as e:
            print(f"Error loading {stock_name} in {industry}: {str(e)}")

conn.commit()
cursor.close()
conn.close()