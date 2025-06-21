Trend & Tide Stock Market App
A dynamic full-stack web application designed to track, analyze, and manage stock prices using data from a provided CSV file, featuring AI-powered insights and interactive visualizations.
Overview
Trend & Tide empowers users to monitor stock performance, visualize trends, and gain actionable insights through an intuitive interface. Completed on May 20, 2025, this project showcases skills in web development, data visualization, and AI integration.
Features

Real-time stock tracking with metrics like open, high, low, close, and volume.
Interactive line and candlestick charts powered by Matplotlib and mplfinance.
AI-powered chat using DistilGPT-2 for stock insights and trend predictions.
Color-coded stock cards (green for positive, red for negative) on the homepage.
Smart search with suggestions and efficient stock shortlisting.
Professional watchlist with add/remove functionality and table-based UI.

Technologies

Backend: Flask, MySQL
Frontend: HTML, CSS, JavaScript
Data Visualization: Matplotlib, mplfinance
AI: DistilGPT-2
Development Tools: Git, GitHub

Installation

Clone the repository:git clone https://github.com/anshsrepo/Trend-and-Tide.git


Navigate to the project directory:cd Trend-and-Tide


Install dependencies (using a virtual environment is recommended):python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install flask mysql-connector-python matplotlib mplfinance


Set up the MySQL database:
Create a database and import the schema (e.g., from database.sql if provided).
Update app.py with your MySQL credentials.


Run the application:python app.py


Access the app at http://localhost:5000 in your browser.

Usage

Homepage: View stock cards with color-coded performance indicators and use the search bar to find stocks.
Stock Details: Explore detailed metrics and interactive charts for selected stocks.
Watchlist: Add or remove stocks and manage your personalized list.
AI Chat: Interact with the AI to get insights and predictions.

Contributing
This project was developed by Ansh Balan. Contributions are welcome! Please fork the repository, create a feature branch, and submit a pull request with your changes.
License
