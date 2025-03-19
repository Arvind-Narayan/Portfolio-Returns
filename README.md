# Portfolio Performance Tracker 📈

A web-based application built with Streamlit that helps users track and analyze their investment portfolio performance.

## Features

- 📊 Real-time portfolio tracking
- 📈 Performance analysis with multiple metrics (XIRR, Total Return, Annualized Return)
- 🔄 Benchmark comparison
- 📅 Transaction history management
- 📊 Portfolio allocation visualization
- 📥 CSV import support

## Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/portfolio-performance-tracker.git
cd portfolio-performance-tracker
```

2. Create a virtual environment (recommended):

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install required packages:

```bash
pip install -r requirements.txt
```

## Usage

1. Start the application:

```bash
streamlit run app.py
```

2. The application will open in your default web browser with three main sections:

### Input Transactions
- **Manual Entry**: Add individual transactions with:
  - Stock Symbol (e.g., MSFT)
  - Transaction Date
  - Transaction Type (BUY/SELL)
  - Quantity
  - Price per Share

- **CSV Upload**: Bulk import transactions using a CSV file with the following format:

```csv
Symbol,Date,Type,Quantity,Price
AAPL,2024-03-15,BUY,10,172.62
MSFT,2024-03-14,SELL,5,425.22
```

### View Portfolio
- Current holdings overview
- Portfolio allocation pie chart
- Total portfolio value
- Transaction history with delete options

### Analysis
- Portfolio value over time chart
- Performance metrics:
  - XIRR (Extended Internal Rate of Return)
  - Total Return
  - Annualized Return
  - Weighted Average Holding Time
- Stock-wise performance analysis
- Benchmark comparison with customizable benchmark symbol

## Data Storage

The application uses Streamlit's session state to store transaction data during the session. Data persists only while the application is running.

## Requirements

- Python 3.7+
- Streamlit
- Pandas
- NumPy
- Plotly
- yfinance

## Notes

- Stock data is fetched using the Yahoo Finance API through the `yfinance` package
- All calculations are performed in real-time using current market prices
- The application supports multiple currencies but assumes all transactions are in the same currency

## Limitations

- Data is not persisted between sessions
- Real-time price updates depend on the Yahoo Finance API availability
- Performance calculations may take longer with a large number of transactions

## Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
