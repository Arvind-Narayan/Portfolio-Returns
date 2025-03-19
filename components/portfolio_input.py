import streamlit as st
from utils.data_manager import save_transaction, validate_csv_file
from utils.stock_api import validate_symbol, get_current_price
from datetime import datetime
import pandas as pd

def show_input_section():
    st.header("Add Transactions")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Manual Entry")
        with st.form("transaction_form"):
            symbol = st.text_input("Stock Symbol (e.g., MSFT)").upper()
            date = st.date_input("Transaction Date", max_value=datetime.now())
            trans_type = st.selectbox("Transaction Type", ["BUY", "SELL"])
            quantity = st.number_input("Quantity", min_value=0.0, step=1.0)
            price = st.number_input("Price per Share", min_value=0.0, step=0.01)
            
            submitted = st.form_submit_button("Add Transaction")
            
            if submitted:
                if symbol and quantity > 0 and price > 0:
                    # Validate symbol
                    valid_symbol, msg = validate_symbol(symbol)
                    if valid_symbol:
                        success, msg = save_transaction(
                            symbol, date, trans_type, quantity, price
                        )
                        if success:
                            # Update current price in session state
                            if 'current_prices' not in st.session_state:
                                st.session_state.current_prices = {}
                            success, current_price = get_current_price(symbol)
                            if success:
                                st.session_state.current_prices[symbol] = current_price
                            st.success(msg)
                        else:
                            st.error(msg)
                    else:
                        st.error(msg)
                else:
                    st.error("Please fill in all fields correctly.")
    
    with col2:
        st.subheader("CSV Upload")
        st.write("Upload a CSV file with columns: Symbol, Date, Type, Quantity, Price")
        
        # Add sample CSV structure as a DataFrame
        sample_data = {
            'Symbol': ['AAPL', 'MSFT'],
            'Date': ['2024-03-15', '2024-03-14'],
            'Type': ['BUY', 'SELL'],
            'Quantity': [10, 5],
            'Price': [172.62, 425.22]
        }
        sample_df = pd.DataFrame(sample_data)
        st.write("Sample Format:")
        st.dataframe(sample_df, hide_index=True)
        
        uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

        
        if uploaded_file is not None:
            success, result = validate_csv_file(uploaded_file)

            if success:
                # Convert Quantity and Price columns to numeric
                result['Quantity'] = pd.to_numeric(result['Quantity'], errors='coerce')
                result['Price'] = pd.to_numeric(result['Price'], errors='coerce')
                
                # Convert Date to correct format
                result['Date'] = pd.to_datetime(result['Date'], errors='coerce', format='%Y-%m-%d')
                
                # Check for NaT values in Date column
                if result['Date'].isnull().any():
                    st.warning("Some dates were invalid and have been set to NaT. Please review your data.")
                
                # Check for NaN values after conversion
                if result['Quantity'].isnull().any() or result['Price'].isnull().any():
                    st.error("Quantity and Price must be numeric values.")
                else:
                    st.session_state.transactions_df = result
                    st.success("CSV file uploaded successfully!")

                st.write(result)
            else:
                st.error(result) 