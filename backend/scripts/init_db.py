import mysql.connector
import pandas as pd
import os

# MySQL connection configuration
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "root123",
    "database": "stock_prices"
}

# Path to the stocks data folder
data_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../..", "data", "stocks"))
if not os.path.exists(data_path):
    print(f"Error: Data path {data_path} does not exist. Please check the folder structure.")
    exit(1)

# Connect to MySQL
try:
    conn = mysql.connector.connect(
        host=db_config["host"],
        user=db_config["user"],
        password=db_config["password"]
    )
    cursor = conn.cursor()
    print("Successfully connected to MySQL.")
except mysql.connector.Error as e:
    print(f"Failed to connect to MySQL: {e}")
    exit(1)

# Drop and recreate the database to start fresh
try:
    cursor.execute("DROP DATABASE IF EXISTS stock_prices")
    cursor.execute("CREATE DATABASE stock_prices")
    cursor.execute("USE stock_prices")
    print("Database 'stock_prices' created and selected.")
except mysql.connector.Error as e:
    print(f"Failed to create or select database: {e}")
    exit(1)

# Create table for stock data
try:
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stocks (
            id INT AUTO_INCREMENT PRIMARY KEY,
            stock_name VARCHAR(50),
            industry VARCHAR(50),
            date DATE,
            close_price FLOAT
        )
    """)
    print("Table 'stocks' created or verified.")
except mysql.connector.Error as e:
    print(f"Failed to create table: {e}")
    exit(1)

# Function to process CSV files and insert into MySQL
def process_excel_files():
    print(f"Scanning directory: {data_path}")
    total_rows = 0
    for industry in os.listdir(data_path):
        industry_path = os.path.join(data_path, industry)
        if os.path.isdir(industry_path):
            print(f"Found industry folder: {industry}")
            # List all files in the folder for debugging
            files = os.listdir(industry_path)
            if not files:
                print(f"No files found in {industry}")
                continue
            print(f"Files in {industry}: {files}")

            for file in files:
                # Case-insensitive check for .csv
                if file.lower().endswith(".csv"):
                    stock_name = file.replace(".csv", "", 1).replace(".CSV", "", 1)
                    file_path = os.path.join(industry_path, file)
                    print(f"Processing {stock_name} from {industry} (file: {file_path})...")

                    try:
                        # Read CSV file
                        df = pd.read_csv(file_path)
                        print(f"Successfully read {file}: {len(df)} rows found")

                        # Clean column names: strip whitespace and quotes
                        df.columns = [col.strip().strip('"') for col in df.columns]
                        print(f"Columns after cleaning: {list(df.columns)}")

                        # Rename columns to match expected names
                        if "Date " in df.columns:
                            df.rename(columns={"Date ": "Date"}, inplace=True)
                        if "close " in df.columns:
                            df.rename(columns={"close ": "close"}, inplace=True)

                        # Validate required columns
                        required_columns = {"Date", "close"}
                        if not all(col in df.columns for col in required_columns):
                            missing_cols = required_columns - set(df.columns)
                            print(f"Error: Missing columns in {file}: {missing_cols}")
                            continue

                        # Convert Date column to MySQL-compatible format (YYYY-MM-DD)
                        df["Date"] = pd.to_datetime(df["Date"], format="%d-%b-%Y").dt.strftime("%Y-%m-%d")

                        # Clean close column: remove commas and convert to float
                        df["close"] = df["close"].astype(str).str.replace(",", "").astype(float)

                        # Insert data into MySQL
                        row_count = 0
                        for _, row in df.iterrows():
                            cursor.execute("""
                                INSERT INTO stocks (stock_name, industry, date, close_price)
                                VALUES (%s, %s, %s, %s)
                            """, (stock_name, industry, row["Date"], row["close"]))
                            row_count += 1
                        total_rows += row_count
                        print(f"Inserted {row_count} rows from {file}")

                    except Exception as e:
                        print(f"Error processing {file}: {e}")
                else:
                    print(f"Skipping non-CSV file: {file}")

    # Commit the transaction
    conn.commit()
    print(f"Total rows inserted: {total_rows}")
    if total_rows == 0:
        print("Warning: No data was inserted. Check file contents or path.")

# Run the processing
try:
    process_excel_files()
    print("Data processing completed.")
except Exception as e:
    print(f"Error during processing: {e}")
finally:
    cursor.close()
    conn.close()
    print("Database connection closed.")