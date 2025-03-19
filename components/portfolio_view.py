import streamlit as st
import pandas as pd
from utils.data_manager import get_transactions, delete_transaction
from utils.stock_api import get_current_price
from utils.calculations import calculate_portfolio_value
import plotly.express as px

def show_portfolio_view():
    st.header("Portfolio Overview")
    
    transactions_df = get_transactions()
    if transactions_df is None or transactions_df.empty:
        st.warning("No transactions found. Please add some transactions first.")
        return
    
    # Initialize or update current prices in session state
    if 'current_prices' not in st.session_state:
        st.session_state.current_prices = {}
        
    # Get current prices for all symbols
    unique_symbols = transactions_df['Symbol'].unique()
    for symbol in unique_symbols:
        if symbol not in st.session_state.current_prices:
            success, price = get_current_price(symbol)
            if success:
                st.session_state.current_prices[symbol] = price
    
    # Calculate and display current holdings
    portfolio_df = calculate_portfolio_value(transactions_df)
    
    if not portfolio_df.empty:
        # Portfolio Allocation Chart
        fig = px.pie(
            portfolio_df,
            values='Current Value',
            names='Symbol',
            title='Portfolio Allocation'
        )
        st.plotly_chart(fig)
        
        st.subheader("Current Holdings")
        st.dataframe(portfolio_df.style.format({
            'Current Price': '{:.2f}',
            'Current Value': '{:.2f}'
        }))
        
        total_value = portfolio_df['Current Value'].sum()
        
        # Save total value in session state
        st.session_state['total_portfolio_value'] = total_value
        
        st.metric("Total Portfolio Value", f"{total_value:,.2f}")
    
    # Display all transactions
    st.subheader("Transaction History")
    if not transactions_df.empty:
        for idx, row in transactions_df.iterrows():
            with st.expander(
                f"{row['Date'].strftime('%Y-%m-%d') if pd.notna(row['Date']) else 'Invalid Date'} - {row['Symbol']} - {row['Type']}"
            ):
                col1, col2, col3 = st.columns([1, 1, 1])
                with col1:
                    st.write(f"Quantity: {row['Quantity']}")
                with col2:
                    st.write(f"Price: {row['Price']:.2f}")
                with col3:
                    if st.button("Delete", key=f"del_{idx}"):
                        success, msg = delete_transaction(idx)
                        if success:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg) 