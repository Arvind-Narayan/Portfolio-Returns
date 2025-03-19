import pandas as pd
import numpy_financial as npf
from datetime import datetime
import streamlit as st
from scipy.optimize import newton
import numpy as np

def calculate_portfolio_value(transactions_df, current_prices=None):
    """Calculate current portfolio value and holdings"""
    if transactions_df is None or transactions_df.empty:
        return pd.DataFrame()
    
    # Use session state prices if not provided
    if current_prices is None:
        current_prices = st.session_state.get('current_prices', {})
    
    holdings = transactions_df.copy()
    holdings['Quantity'] = holdings.apply(
        lambda x: x['Quantity'] if x['Type'] == 'BUY' else -x['Quantity'], 
        axis=1
    )
    
    portfolio = holdings.groupby('Symbol')['Quantity'].sum().reset_index()
    portfolio = portfolio[portfolio['Quantity'] > 0]  # Only show current holdings
    
    portfolio['Current Price'] = portfolio['Symbol'].map(current_prices)
    portfolio['Current Value'] = portfolio['Quantity'] * portfolio['Current Price']
    
    return portfolio

def xirr(amounts, dates, initial_guess=0.1):
    """Calculate XIRR given cash flows and dates"""
    if len(amounts) < 2:  # Need at least 2 cash flows
        return None
        
    def xnpv(rate, amounts, dates):
        """Calculate XNPV (Net Present Value with dates)"""
        if isinstance(rate, np.ndarray):
            rate = rate[0]
        if rate <= -1:
            return float('inf')
        
        # Convert dates to python datetime
        dates = [pd.Timestamp(d).to_pydatetime() for d in dates]
        
        values = []
        for amount, date in zip(amounts, dates):
            days = (date - dates[0]).total_seconds() / (24 * 60 * 60 * 365.0)
            value = amount / (1 + rate) ** days
            values.append(value)
            
        return sum(values)
    
    try:
        result = newton(
            lambda r: xnpv(r, amounts, dates),
            x0=initial_guess,  # Use the provided initial guess
            tol=0.00001,
            maxiter=1000
        )
        return result
    except Exception as e:
        st.error("Newton method failed:", str(e))
        return None

def calculate_xirr(transactions_df, symbol=None, initial_guess=0.1):
    """Calculate XIRR for entire portfolio or specific symbol"""
    if transactions_df is None or transactions_df.empty:
        return None
    
    if symbol:
        transactions_df = transactions_df[transactions_df['Symbol'] == symbol]
    
    cash_flows = transactions_df.copy()
    # Standardize date format to YYYY-mm-dd
    cash_flows['Date'] = pd.to_datetime(cash_flows['Date']).dt.normalize()
    
    cash_flows['Amount'] = cash_flows.apply(
        lambda x: -x['Quantity'] * x['Price'] if x['Type'] == 'BUY' 
        else x['Quantity'] * x['Price'],
        axis=1
    )
    
    current_holdings = calculate_portfolio_value(transactions_df)

    
    if not current_holdings.empty:
        last_flow = pd.DataFrame({
            'Date': [pd.Timestamp.now().normalize()],  # Normalize to midnight
            'Amount': [current_holdings['Current Value'].sum()]
        })
        cash_flows = pd.concat([
            cash_flows[['Date', 'Amount']], 
            last_flow
        ], ignore_index=True)
        
    
    try:
        result = xirr(
            cash_flows['Amount'].values,
            cash_flows['Date'].values,
            initial_guess  # Pass the initial guess to xirr
        )
        if result is not None:
            return result
        # st.error("Could not calculate XIRR - no valid solution found")
        return None
    except Exception as e:
        # st.error(f"XIRR calculation error: {str(e)}")
        return None 

def calculate_xirr_with_multiple_guesses(transactions_df, symbol=None):
    """
    Attempts to calculate XIRR using multiple initial guesses if the first attempt fails.
    
    Args:
        transactions_df: DataFrame containing transactions
        symbol: Optional stock symbol to filter transactions
    
    Returns:
        float: XIRR value if successful
    Raises:
        ValueError: If all attempts fail
    """
    initial_guesses = [0.1, 0.0, 0.2, -0.1, 0.5]  # Multiple starting points
    
    for guess in initial_guesses:
        try:
            return calculate_xirr(transactions_df, symbol, initial_guess=guess)
        except Exception:
            continue
    
    raise ValueError("XIRR calculation failed with all initial guesses") 

def calculate_mirr(transactions_df, finance_rate=0.10, reinvest_rate=0.10):
    """
    Calculate Modified Internal Rate of Return (MIRR) for the portfolio
    
    Args:
        transactions_df: DataFrame containing transactions
        finance_rate: Rate for financing negative cash flows (default 10%)
        reinvest_rate: Rate for reinvesting positive cash flows (default 10%)
    
    Returns:
        float: MIRR value if successful, None if calculation fails
    """
    if transactions_df is None or transactions_df.empty:
        return None
    
    cash_flows = transactions_df.copy()
    # Standardize date format to YYYY-mm-dd
    cash_flows['Date'] = pd.to_datetime(cash_flows['Date']).dt.normalize()
    
    # Calculate cash flows
    cash_flows['Amount'] = cash_flows.apply(
        lambda x: -x['Quantity'] * x['Price'] if x['Type'] == 'BUY' 
        else x['Quantity'] * x['Price'],
        axis=1
    )
    
    current_holdings = calculate_portfolio_value(transactions_df)

    
    if not current_holdings.empty:
        current_value = current_holdings['Current Value'].sum()
        last_flow = pd.DataFrame({
            'Date': [pd.Timestamp.now().normalize()],  # Normalize to midnight
            'Amount': [current_value]
        })
        cash_flows = pd.concat([
            cash_flows[['Date', 'Amount']], 
            last_flow
        ], ignore_index=True)
    
    amounts = cash_flows['Amount'].values
    dates = cash_flows['Date'].values
    
    try:
        # Check if we have both positive and negative cash flows
        has_positive = any(a > 0 for a in amounts)
        has_negative = any(a < 0 for a in amounts)
        
        if not (has_positive and has_negative):
            return None
            
        # Convert dates to python datetime objects
        dates = [pd.Timestamp(d).to_pydatetime() for d in dates]
        
        # Calculate years between dates
        years = [(date - dates[0]).total_seconds() / (365.0 * 24 * 60 * 60) for date in dates]
        
        # Separate positive and negative cash flows
        pos_flows = np.where(amounts > 0, amounts, 0)
        neg_flows = np.where(amounts < 0, amounts, 0)
        
        if np.sum(pos_flows) == 0 or np.sum(neg_flows) == 0:
            return None
        
        # Calculate terminal value of positive flows
        terminal_value = sum(
            flow * (1 + reinvest_rate) ** (years[-1] - year)
            for flow, year in zip(pos_flows, years)
        )
        
        # Calculate present value of negative flows
        pv_neg_flows = sum(
            flow / (1 + finance_rate) ** year
            for flow, year in zip(neg_flows, years)
        )
        
        if pv_neg_flows == 0:
            return None
            
        # Calculate MIRR
        mirr = (terminal_value / abs(pv_neg_flows)) ** (1 / years[-1]) - 1
        return mirr
        
    except Exception as e:
        st.error(f"MIRR calculation error: {str(e)}")
        return None 

def calculate_twr(transactions_df, price_history=None):
    """
    Calculate Time-Weighted Return (TWR) for the portfolio
    
    Args:
        transactions_df: DataFrame containing transactions
        price_history: Optional dictionary of price history by symbol
    
    Returns:
        float: TWR value if successful, None if calculation fails
    """
    if transactions_df is None or transactions_df.empty:
        return None
    
    # Sort transactions by date
    transactions = transactions_df.copy().sort_values('Date')
    transactions['Date'] = pd.to_datetime(transactions['Date'])
    
    # Use session state prices if not provided
    if price_history is None:
        price_history = st.session_state.get('price_history', {})
    else:
        pass
    
    # Get unique dates where cash flows occurred
    cash_flow_dates = transactions['Date'].unique()
    
    # Calculate portfolio value at each cash flow date
    portfolio_values = []
    cash_flows = []
    
    current_holdings = {}  # Track holdings: {symbol: quantity}
    
    for date in cash_flow_dates:
        # Process transactions on this date
        day_transactions = transactions[transactions['Date'] == date]
        
        # Calculate cash flow for the day
        day_cash_flow = 0
        
        for _, tx in day_transactions.iterrows():
            symbol = tx['Symbol']
            quantity = tx['Quantity']
            price = tx['Price']
            
            if tx['Type'] == 'BUY':
                flow = -quantity * price
                day_cash_flow += flow
                current_holdings[symbol] = current_holdings.get(symbol, 0) + quantity
            else:  # SELL
                flow = quantity * price
                day_cash_flow += flow
                current_holdings[symbol] = current_holdings.get(symbol, 0) - quantity
        
        # Calculate portfolio value after transactions
        portfolio_value = 0
        for symbol, quantity in current_holdings.items():
            if quantity > 0:
                # Get price for this symbol on this date
                if symbol in price_history and not price_history[symbol].empty:
                    # Find closest date in price history
                    price_df = price_history[symbol]
                    price_df['Date'] = pd.to_datetime(price_df['Date'])
                    closest_date = price_df[price_df['Date'] <= date]['Date'].max()
                    if pd.notna(closest_date):
                        price = price_df[price_df['Date'] == closest_date]['Close'].values[0]
                        value = quantity * price
                        portfolio_value += value
                else:
                    # Use transaction price if no history available
                    symbol_txs = transactions[(transactions['Symbol'] == symbol) & 
                                             (transactions['Date'] <= date)]
                    if not symbol_txs.empty:
                        latest_price = symbol_txs.iloc[-1]['Price']
                        value = quantity * latest_price
                        portfolio_value += value
                    else:
                        pass
        
        portfolio_values.append(portfolio_value)
        cash_flows.append(day_cash_flow)
    
    # Calculate holding period returns
    if len(portfolio_values) < 2:
        return None
    
    holding_period_returns = []
    for i in range(1, len(portfolio_values)):
        previous_value = portfolio_values[i-1]
        current_value = portfolio_values[i]
        current_cash_flow = cash_flows[i]
        
        if previous_value == 0:
            continue
            
        # HPR = (End Value - Cash Flow) / Start Value
        hpr = (current_value - current_cash_flow) / previous_value
        holding_period_returns.append(hpr)
    
    # Calculate TWR
    if not holding_period_returns:
        return None
        
    twr = np.prod([1 + r for r in holding_period_returns]) - 1
    return twr 

def calculate_weighted_holding_time(transactions_df, symbol=None):
    """
    Calculate weighted average holding time in days.
    Weighted Time = Σ(Cash Flow × Time Held) / Σ(Cash Flow)
    
    Args:
        transactions_df: DataFrame containing transactions
        symbol: Optional stock symbol to filter transactions
    
    Returns:
        float: Weighted average holding time in days
    """
    if transactions_df is None or transactions_df.empty:
        return None
    
    # Filter by symbol if provided
    if symbol:
        transactions_df = transactions_df[transactions_df['Symbol'] == symbol]
    
    # Create a copy to avoid modifying the original
    df = transactions_df.copy()
    
    # Ensure dates are datetime
    df['Date'] = pd.to_datetime(df['Date'])
    
    # Calculate cash flow amounts (negative for buys, positive for sells)
    df['Cash Flow'] = df.apply(
        lambda x: -x['Quantity'] * x['Price'] if x['Type'] == 'BUY' 
        else x['Quantity'] * x['Price'],
        axis=1
    )
    
    # For current holdings, add a "virtual sell" at current date with current prices
    current_holdings = calculate_portfolio_value(df)
    current_date = pd.Timestamp.now()
    
    virtual_sells = []
    for _, row in current_holdings.iterrows():
        if row['Quantity'] > 0:
            virtual_sells.append({
                'Symbol': row['Symbol'],
                'Date': current_date,
                'Type': 'VIRTUAL_SELL',
                'Quantity': row['Quantity'],
                'Price': row['Current Price'],
                'Cash Flow': row['Current Value']
            })
    
    # Add virtual sells to the dataframe
    if virtual_sells:
        virtual_df = pd.DataFrame(virtual_sells)
        df = pd.concat([df, virtual_df], ignore_index=True)
    
    # Sort by date
    df = df.sort_values('Date')
    
    # Calculate weighted holding time
    total_weighted_time = 0
    total_cash_flow_abs = 0
    
    # Track buys to match with sells
    buy_queue = []
    
    # Process each transaction
    for _, tx in df.iterrows():
        if tx['Type'] == 'BUY':
            # Add buy to queue
            buy_queue.append({
                'Date': tx['Date'],
                'Quantity': tx['Quantity'],
                'Price': tx['Price']
            })
        elif tx['Type'] in ['SELL', 'VIRTUAL_SELL']:
            # Match sells with buys using FIFO method
            remaining_sell_qty = tx['Quantity']
            
            while remaining_sell_qty > 0 and buy_queue:
                buy = buy_queue[0]
                
                # Determine quantity to match
                match_qty = min(buy['Quantity'], remaining_sell_qty)
                
                # Calculate holding time in days
                holding_time_days = (tx['Date'] - buy['Date']).days
                
                # Calculate cash flow for this match
                cash_flow = match_qty * tx['Price']
                
                # Add to weighted time calculation
                total_weighted_time += cash_flow * holding_time_days
                total_cash_flow_abs += cash_flow
                
                # Update remaining quantities
                remaining_sell_qty -= match_qty
                buy['Quantity'] -= match_qty
                
                # Remove buy if fully used
                if buy['Quantity'] <= 0:
                    buy_queue.pop(0)
    
    # Calculate weighted average holding time
    if total_cash_flow_abs > 0:
        weighted_avg_time = total_weighted_time / total_cash_flow_abs
        return weighted_avg_time
    
    return None 