import pandas as pd
import streamlit as st
from datetime import datetime
import io

def validate_csv_file(file):
    try:
        df = pd.read_csv(file)
        required_columns = ['Symbol', 'Date', 'Type', 'Quantity', 'Price']
        
        if not all(col in df.columns for col in required_columns):
            return False, "CSV file must contain columns: Symbol, Date, Type, Quantity, Price"
        
        # Convert date strings to datetime
        df['Date'] = pd.to_datetime(df['Date'], format='%Y-%m-%d', errors='coerce')
        
        # Validate transaction types
        if not df['Type'].isin(['BUY', 'SELL']).all():
            return False, "Transaction Type must be either 'BUY' or 'SELL'"
        
        # Convert Quantity and Price to numeric and check for NaN
        df['Quantity'] = pd.to_numeric(df['Quantity'], errors='coerce')
        df['Price'] = pd.to_numeric(df['Price'], errors='coerce')
        
        if df['Quantity'].isnull().any() or df['Price'].isnull().any():
            return False, "Quantity and Price must be numeric values"
        
        return True, df
    except Exception as e:
        return False, f"Error processing CSV file: {str(e)}"

def save_transaction(symbol, date, trans_type, quantity, price):
    try:
        new_transaction = pd.DataFrame({
            'Symbol': [symbol],
            'Date': [pd.to_datetime(date)],
            'Type': [trans_type],
            'Quantity': [float(quantity)],
            'Price': [float(price)]
        })
        
        if st.session_state.transactions_df is None:
            st.session_state.transactions_df = new_transaction
        else:
            st.session_state.transactions_df = pd.concat(
                [st.session_state.transactions_df, new_transaction],
                ignore_index=True
            )
        return True, "Transaction saved successfully!"
    except Exception as e:
        return False, f"Error saving transaction: {str(e)}"

def get_transactions():
    return st.session_state.transactions_df

def delete_transaction(index):
    try:
        st.session_state.transactions_df = st.session_state.transactions_df.drop(index)
        st.session_state.transactions_df = st.session_state.transactions_df.reset_index(drop=True)
        return True, "Transaction deleted successfully!"
    except Exception as e:
        return False, f"Error deleting transaction: {str(e)}" 