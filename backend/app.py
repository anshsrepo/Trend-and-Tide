import mysql.connector
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS  # Import CORS
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import mplfinance as mpf
import os
import json

app = Flask(__name__)

# Enable CORS for specific routes
CORS(app, resources={
    r"/chat": {"origins": ["http://127.0.0.1:5000", "http://localhost:5000"]},
    r"/chat_suggestions": {"origins": ["http://127.0.0.1:5000", "http://localhost:5000"]}
})

# Load the DistilGPT-2 model and tokenizer
model_name = "distilgpt2"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)

# Database configuration
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "root123",
    "database": "stock_prices"
}

# Stocks organized by industry (same as in load_csv_to_mysql.py)
stocks_by_industry = {
    "finance": ["bajaj_finance", "csl_finance", "tci_finance", "vls_finance"],
    "automotive": ["HEROMOTOCORP", "HINDMOTORS", "HYUNDAI", "TATAMOTORS", "TVSMOTORS"],
    "telecommunications": ["AIRTELPP", "HFCL", "IDEA", "TATACOMM", "TEJASNET"],
    "electronics": ["BPL", "CENTUM", "CYIENT", "PGEL", "PULZ"],
    "renewable energy": ["ADANIGREEN", "JSWENERGY", "KPIGREEN", "SUZLON", "TATAPOWER"],
    "oil stocks": ["BPCL", "DEEPINDS", "GAIL"],
    "IT industry": ["HCLTECH", "INFY", "RELIABLE", "TCS", "WIPRO"]
}

def get_db_connection():
    return mysql.connector.connect(**db_config)

@app.route('/')
def index():
    conn = None
    cursor = None
    stocks = []
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Flatten the stocks_by_industry dictionary to a list of stock names
        all_stock_names = []
        stock_to_industry = {}
        for industry, stock_list in stocks_by_industry.items():
            for stock in stock_list:
                all_stock_names.append(stock)
                stock_to_industry[stock.upper()] = industry

        # Fetch the latest and second-latest data for each stock to calculate percentage change
        for stock_name in all_stock_names:
            query = """
                SELECT stock_name, close, date
                FROM stocks
                WHERE UPPER(stock_name) = UPPER(%s)
                ORDER BY date DESC
                LIMIT 2
            """
            cursor.execute(query, (stock_name,))
            results = cursor.fetchall()

            if results:
                latest = results[0]
                stock_data = {
                    "name": latest["stock_name"],
                    "price": float(latest["close"]),
                    "industry": stock_to_industry.get(latest["stock_name"].upper(), "Unknown"),
                    "percentage_change": 0.0
                }

                # Calculate percentage change if we have at least 2 data points
                if len(results) >= 2:
                    prev_close = float(results[1]["close"])
                    if prev_close != 0:
                        stock_data["percentage_change"] = ((stock_data["price"] - prev_close) / prev_close) * 100

                stocks.append(stock_data)

        return render_template('index.html', stocks=stocks, stocks_by_industry=stocks_by_industry)

    except mysql.connector.Error as e:
        print(f"Database error in / route: {str(e)}")
        return render_template('index.html', stocks=[], stocks_by_industry=stocks_by_industry, error=f"Database error: {str(e)}")
    except Exception as e:
        print(f"Error in / route: {str(e)}")
        return render_template('index.html', stocks=[], stocks_by_industry=stocks_by_industry, error=f"Error: {str(e)}")
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()

@app.route('/stock/<stock_name>')
def get_stock_price(stock_name):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Fetch the latest stock data with all required fields
        query_latest = """
            SELECT stock_name, open_price, high_price, low_price, close, volume, date
            FROM stocks
            WHERE UPPER(stock_name) = UPPER(%s)
            ORDER BY date DESC
            LIMIT 1
        """
        cursor.execute(query_latest, (stock_name,))
        latest_result = cursor.fetchone()

        # Fetch historical data for the chart
        query_history = """
            SELECT date, open_price, high_price, low_price, close, volume
            FROM stocks
            WHERE UPPER(stock_name) = UPPER(%s)
            ORDER BY date ASC
        """
        cursor.execute(query_history, (stock_name,))
        history_results = cursor.fetchall()

        if latest_result:
            # Construct the stock dictionary with all fields
            stock = {
                "name": latest_result["stock_name"],
                "open": float(latest_result["open_price"]) if latest_result["open_price"] is not None else 0.0,
                "high": float(latest_result["high_price"]) if latest_result["high_price"] is not None else 0.0,
                "low": float(latest_result["low_price"]) if latest_result["low_price"] is not None else 0.0,
                "close": float(latest_result["close"]) if latest_result["close"] is not None else 0.0,
                "price": float(latest_result["close"]) if latest_result["close"] is not None else 0.0,  # Keep for backward compatibility
                "volume": int(latest_result["volume"]) if latest_result["volume"] is not None else 0,
                "date": latest_result["date"].strftime('%Y-%m-%d') if latest_result["date"] else "N/A"
            }

            # Debug: Print the stock dictionary
            print("Stock Data:", stock)

            # Generate chart (line or candlestick)
            plot_type = request.args.get('plot_type', 'line')
            chart_path = None
            chart_error = None
            if history_results:
                print(f"Raw historical data for {stock_name}: {history_results}")

                # Filter out rows with missing data
                history_results = [
                    result for result in history_results 
                    if all(result[key] is not None for key in ["date", "open_price", "high_price", "low_price", "close", "volume"])
                ]

                print(f"Filtered historical data for {stock_name}: {history_results}")

                # Ensure there are enough data points to plot
                if len(history_results) < 2:
                    chart_error = "Not enough historical data points (minimum 2 required) to generate chart."
                else:
                    # Extract dates and prices for plotting
                    dates = [result["date"] for result in history_results]
                    prices = [result["close"] for result in history_results]

                    # Create the charts directory if it doesn't exist
                    charts_dir = "static/charts"
                    os.makedirs(charts_dir, exist_ok=True)

                    # Generate a safe filename for the chart
                    safe_stock_name = stock_name.replace(" ", "_").replace("/", "_")
                    chart_filename = f"static/charts/{safe_stock_name}_price_history_{plot_type}.png"

                    try:
                        # Candlestick chart
                        if plot_type == 'candlestick':
                            df_data = {
                                'Date': [result["date"] for result in history_results],
                                'Open': [float(result["open_price"]) for result in history_results],
                                'High': [float(result["high_price"]) for result in history_results],
                                'Low': [float(result["low_price"]) for result in history_results],
                                'Close': [float(result["close"]) for result in history_results],
                                'Volume': [float(result["volume"]) for result in history_results]
                            }
                            df = pd.DataFrame(df_data)
                            df['Date'] = pd.to_datetime(df['Date'])
                            df.set_index('Date', inplace=True)

                            # Customize the candlestick chart style
                            mc = mpf.make_marketcolors(
                                up='#2d6a4f',
                                down='#dc2626',
                                edge='inherit',
                                wick='inherit',
                                volume='inherit'
                            )
                            s = mpf.make_mpf_style(marketcolors=mc, gridstyle='--', gridcolor='#d1d5db')

                            print(f"Generating candlestick chart for {stock_name}: {chart_filename}")
                            mpf.plot(df, type='candle', style=s, 
                                    title=f'{stock_name} Price History', 
                                    ylabel='Price (₹)', 
                                    figsize=(10, 5),
                                    volume=True,
                                    savefig=dict(fname=chart_filename, dpi=100, bbox_inches='tight'))
                        # Line chart
                        else:
                            plt.figure(figsize=(10, 5))
                            plt.plot(dates, prices, marker='o', linestyle='-', color='#2d6a4f', label='Closing Price')
                            plt.title(f'{stock_name} Price History', fontsize=16, color='#1a3c34')
                            plt.xlabel('Date', fontsize=12, color='#1a3c34')
                            plt.ylabel('Price (₹)', fontsize=12, color='#1a3c34')
                            plt.grid(True, linestyle='--', alpha=0.7)
                            plt.legend()

                            plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
                            plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator())
                            plt.xticks(rotation=45)

                            plt.tight_layout()

                            print(f"Generating line chart for {stock_name}: {chart_filename}")
                            plt.savefig(chart_filename, dpi=100, bbox_inches='tight')
                            plt.close()

                        # Verify the chart was saved
                        if os.path.exists(chart_filename):
                            print(f"Chart successfully saved for {stock_name}: {chart_filename}")
                            chart_path = f"charts/{safe_stock_name}_price_history_{plot_type}.png"
                        else:
                            print(f"Chart file not found after generation for {stock_name}: {chart_filename}")
                            chart_error = "Failed to generate chart: File not found after generation."

                    except Exception as e:
                        print(f"Error generating chart for {stock_name}: {str(e)}")
                        chart_error = f"Error generating chart: {str(e)}"

            return render_template('stock_price.html', stock=stock, chart_path=chart_path, 
                                 plot_type=plot_type, stocks_by_industry=stocks_by_industry,
                                 chart_error=chart_error)
        else:
            return render_template('stock_price.html', stock=None, error="Stock not found", 
                                 stocks_by_industry=stocks_by_industry)

    except mysql.connector.Error as e:
        print(f"Database error in /stock/<stock_name> route: {str(e)}")
        return render_template('stock_price.html', stock=None, error=f"Database error: {str(e)}", 
                             stocks_by_industry=stocks_by_industry)
    except Exception as e:
        print(f"Error in /stock/<stock_name> route: {str(e)}")
        return render_template('stock_price.html', stock=None, error=f"Error: {str(e)}", 
                             stocks_by_industry=stocks_by_industry)
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()

# Watchlist file
WATCHLIST_FILE = "watchlist.json"

# Initialize watchlist file if it doesn't exist
if not os.path.exists(WATCHLIST_FILE):
    with open(WATCHLIST_FILE, 'w') as f:
        json.dump([], f)

@app.route('/watchlist')
def watchlist():
    # Read the watchlist
    with open(WATCHLIST_FILE, 'r') as f:
        watchlist_stocks = json.load(f)
    
    # Fetch latest prices for watchlist stocks
    conn = None
    cursor = None
    watchlist_data = []
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        for stock_name in watchlist_stocks:
            query = """
                SELECT stock_name, close, date
                FROM stocks
                WHERE UPPER(stock_name) = UPPER(%s)
                ORDER BY date DESC
                LIMIT 1
            """
            cursor.execute(query, (stock_name,))
            result = cursor.fetchone()
            if result:
                watchlist_data.append({
                    "name": result["stock_name"],
                    "price": result["close"],
                    "date": result["date"].strftime('%Y-%m-%d') if result["date"] else "N/A"
                })
    except mysql.connector.Error as e:
        print(f"Database error while fetching watchlist: {str(e)}")
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()

    return render_template('watchlist.html', watchlist_data=watchlist_data, stocks_by_industry=stocks_by_industry)

@app.route('/add_to_watchlist', methods=['POST'])
def add_to_watchlist():
    stock_name = request.json.get('stock_name', '').upper()
    if not stock_name:
        return jsonify({"success": False, "message": "No stock name provided."})

    # Validate stock name
    valid_stock = False
    for industry, stocks in stocks_by_industry.items():
        if stock_name.lower() in [s.lower() for s in stocks]:
            valid_stock = True
            break
    
    if not valid_stock:
        return jsonify({"success": False, "message": f"Stock {stock_name} not found in the stock list."})

    # Add to watchlist
    with open(WATCHLIST_FILE, 'r') as f:
        watchlist = json.load(f)

    if stock_name not in watchlist:
        watchlist.append(stock_name)
        with open(WATCHLIST_FILE, 'w') as f:
            json.dump(watchlist, f)
        return jsonify({"success": True, "message": f"{stock_name} added to watchlist."})
    else:
        return jsonify({"success": False, "message": f"{stock_name} is already in the watchlist."})

@app.route('/remove_from_watchlist', methods=['POST'])
def remove_from_watchlist():
    stock_name = request.json.get('stock_name', '').upper()
    if not stock_name:
        return jsonify({"success": False, "message": "No stock name provided."})

    # Remove from watchlist
    with open(WATCHLIST_FILE, 'r') as f:
        watchlist = json.load(f)

    if stock_name in watchlist:
        watchlist.remove(stock_name)
        with open(WATCHLIST_FILE, 'w') as f:
            json.dump(watchlist, f)
        return jsonify({"success": True, "message": f"{stock_name} removed from watchlist."})
    else:
        return jsonify({"success": False, "message": f"{stock_name} is not in the watchlist."})

@app.route('/chat_suggestions', methods=['POST'])
def chat_suggestions():
    try:
        partial_input = request.json.get('partial_input', '').lower().strip()
        if not partial_input:
            return jsonify({"suggestions": []})

        # Flatten the stocks_by_industry dictionary to a list of stock names
        all_stock_names = []
        for industry, stock_list in stocks_by_industry.items():
            for stock in stock_list:
                all_stock_names.append(stock)

        # Define common query templates
        query_templates = [
            "What is the 52-week high of {stock}?",
            "What is the 52-week low of {stock}?",
            "What is the latest price of {stock}?",
            "What is the trend of {stock}?",
            "Which stock has the best trend?",
            "Which stock has the worst trend?",
            "Which stock has the best value?"
        ]

        # Generate suggestions
        suggestions = []
        for template in query_templates:
            if "{stock}" not in template:  # General queries
                if template.lower().startswith(partial_input):
                    suggestions.append(template)
            else:
                # Stock-specific queries
                for stock in all_stock_names:
                    suggestion = template.format(stock=stock)
                    if suggestion.lower().startswith(partial_input):
                        suggestions.append(suggestion)

        # Limit to top 5 suggestions
        suggestions = suggestions[:5]

        return jsonify({"suggestions": suggestions})

    except Exception as e:
        print(f"Error in /chat_suggestions route: {str(e)}")
        return jsonify({"suggestions": [], "error": f"Error generating suggestions: {str(e)}"})

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get('message', '').lower()
    stock_name = None
    stock_name_original = None  # To store the original stock name format

    # Normalize stock names for comparison (remove spaces, lowercase)
    for industry, stocks in stocks_by_industry.items():
        for stock in stocks:
            # Normalize stock name: remove spaces, convert to lowercase
            normalized_stock = stock.lower().replace(" ", "")
            # Normalize user input: remove spaces
            normalized_input = user_input.replace(" ", "")
            # Check if the normalized stock name is in the normalized user input
            if normalized_stock in normalized_input:
                stock_name = stock  # Use the original stock name for queries
                stock_name_original = stock  # Store the original stock name
                break
        if stock_name:
            break

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Flatten the stocks_by_industry dictionary to a list of stock names
        all_stock_names = []
        for industry, stock_list in stocks_by_industry.items():
            for stock in stock_list:
                all_stock_names.append(stock)

        # If no specific stock is mentioned, analyze all stocks for trends or value
        if not stock_name and ("best trend" in user_input or "worst trend" in user_input or "best value" in user_input):
            trends = []
            values = []
            for stock in all_stock_names:
                # Fetch historical data for trend analysis
                query_history = """
                    SELECT close, date
                    FROM stocks
                    WHERE UPPER(stock_name) = UPPER(%s)
                    ORDER BY date DESC
                    LIMIT 5
                """
                cursor.execute(query_history, (stock,))
                history_results = cursor.fetchall()

                # Fetch latest data for value analysis
                query_latest = """
                    SELECT close, 52w_high, date
                    FROM stocks
                    WHERE UPPER(stock_name) = UPPER(%s)
                    ORDER BY date DESC
                    LIMIT 1
                """
                cursor.execute(query_latest, (stock,))
                latest_result = cursor.fetchone()

                # Trend analysis
                trend = {"stock": stock, "status": "not enough data", "score": 0}
                if history_results and len(history_results) >= 5:
                    closes = [result["close"] for result in history_results]
                    dates = [result["date"] for result in history_results]
                    print(f"Trend analysis for {stock}: Closes {closes}, Dates {dates}")
                    diffs = [closes[i] - closes[i+1] for i in range(len(closes)-1)]
                    if all(diff > 0 for diff in diffs):
                        trend["status"] = "up"
                        trend["score"] = sum(diffs)  # Higher positive difference means stronger upward trend
                    elif all(diff < 0 for diff in diffs):
                        trend["status"] = "down"
                        trend["score"] = sum(diffs)  # More negative difference means stronger downward trend
                    else:
                        trend["status"] = "mixed"
                        trend["score"] = 0
                trends.append(trend)

                # Value analysis (potential upside)
                value = {"stock": stock, "upside": 0.0}
                if latest_result and latest_result["close"] and latest_result["52w_high"]:
                    close = float(latest_result["close"])
                    high = float(latest_result["52w_high"])
                    if close > 0:
                        value["upside"] = ((high - close) / close) * 100  # Percentage upside
                values.append(value)

            response = ""
            # Best and worst trend
            if "best trend" in user_input or "worst trend" in user_input:
                up_trends = [t for t in trends if t["status"] == "up"]
                down_trends = [t for t in trends if t["status"] == "down"]
                best_trend = max(up_trends, key=lambda x: x["score"], default=None)
                worst_trend = min(down_trends, key=lambda x: x["score"], default=None)

                if "best trend" in user_input:
                    if best_trend and best_trend["score"] > 0:
                        response += f"The stock with the best trend is {best_trend['stock']}, which is trending up over the last 5 days."
                    else:
                        response += "No stocks are consistently trending up over the last 5 days."
                if "worst trend" in user_input:
                    if worst_trend and worst_trend["score"] < 0:
                        if response:
                            response += " "
                        response += f"The stock with the worst trend is {worst_trend['stock']}, which is trending down over the last 5 days."
                    else:
                        if response:
                            response += " "
                        response += "No stocks are consistently trending down over the last 5 days."

            # Best value
            if "best value" in user_input:
                best_value = max(values, key=lambda x: x["upside"], default=None)
                if best_value and best_value["upside"] > 0:
                    if response:
                        response += " "
                    response += f"The stock with the best value is {best_value['stock']}, with a potential upside of {best_value['upside']:.2f}% based on its 52-week high."
                else:
                    if response:
                        response += " "
                    response += "No stocks have a significant potential upside based on their 52-week highs."

            return jsonify({"response": response})

        # If a specific stock is mentioned, proceed with the existing logic
        if not stock_name:
            return jsonify({"response": "I couldn't identify a stock in your message, and no general analysis was requested. Please mention a stock name (e.g., 'Tata Motors') or ask about trends or value (e.g., 'Which stock has the best trend?')."})

        # Fetch the latest stock data
        query = """
            SELECT close, 52w_high, 52w_low, date
            FROM stocks
            WHERE UPPER(stock_name) = UPPER(%s)
            ORDER BY date DESC
            LIMIT 1
        """
        cursor.execute(query, (stock_name,))
        latest_result = cursor.fetchone()

        # Fetch historical data for trend analysis
        query_history = """
            SELECT close, date
            FROM stocks
            WHERE UPPER(stock_name) = UPPER(%s)
            ORDER BY date DESC
            LIMIT 5
        """
        cursor.execute(query_history, (stock_name,))
        history_results = cursor.fetchall()

        if not latest_result:
            return jsonify({"response": f"No data found for {stock_name_original}."})

        # Prepare responses based on user input
        response = ""
        if "52 week high" in user_input or "52-week high" in user_input:
            response = f"The 52 Week High of {stock_name_original} is ₹{latest_result['52w_high']}."
        elif "52 week low" in user_input or "52-week low" in user_input:
            response = f"The 52 Week Low of {stock_name_original} is ₹{latest_result['52w_low']}."
        elif "latest price" in user_input or "current price" in user_input:
            response = f"The Latest Close of {stock_name_original} is ₹{latest_result['close']} as of {latest_result['date'].strftime('%Y-%m-%d')}."
        elif "trend" in user_input:
            if len(history_results) < 5:
                response = "Not enough data to determine trend (minimum 5 days required)."
            else:
                closes = [result["close"] for result in history_results]
                dates = [result["date"] for result in history_results]
                print(f"Trend analysis for {stock_name_original}: Closes {closes}, Dates {dates}")
                # Simple trend analysis: check if closing prices are generally increasing or decreasing
                diffs = [closes[i] - closes[i+1] for i in range(len(closes)-1)]
                if all(diff > 0 for diff in diffs):
                    response = f"{stock_name_original} is trending up over the last 5 days."
                elif all(diff < 0 for diff in diffs):
                    response = f"{stock_name_original} is trending down over the last 5 days."
                else:
                    response = f"{stock_name_original} is showing a mixed trend over the last 5 days."
        else:
            # Use DistilGPT-2 for general responses
            prompt = (f"The user asked: '{user_input}' about the stock {stock_name_original}. "
                     f"The latest closing price is ₹{latest_result['close']} on {latest_result['date'].strftime('%Y-%m-%d')}, "
                     f"52-week high is ₹{latest_result['52w_high']}, 52-week low is ₹{latest_result['52w_low']}. "
                     "Provide a concise and helpful response.")
            inputs = tokenizer(prompt, return_tensors="pt", padding=True)
            attention_mask = inputs.get('attention_mask', None)
            outputs = model.generate(
                inputs['input_ids'], 
                attention_mask=attention_mask, 
                max_length=100, 
                num_return_sequences=1, 
                pad_token_id=tokenizer.eos_token_id, 
                temperature=0.7, 
                top_p=0.9
            )
            response = tokenizer.decode(outputs[0], skip_special_tokens=True).strip()
            # Truncate the response to the actual generated part (remove the prompt)
            response = response[len(prompt):].strip()
            if not response:
                response = f"Here's the latest data for {stock_name_original}: Closing Price ₹{latest_result['close']} on {latest_result['date'].strftime('%Y-%m-%d')}, 52W High ₹{latest_result['52w_high']}, 52W Low ₹{latest_result['52w_low']}."

        return jsonify({"response": response})

    except mysql.connector.Error as e:
        print(f"Database error in /chat route: {str(e)}")
        return jsonify({"response": f"Database error: {str(e)}"})
    except Exception as e:
        print(f"Error in /chat route: {str(e)}")
        return jsonify({"response": f"Error: {str(e)}"})
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()

if __name__ == '__main__':
    app.run(debug=True, port=5000)