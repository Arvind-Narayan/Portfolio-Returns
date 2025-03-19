import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from utils.data_manager import get_transactions
from utils.calculations import (
    calculate_xirr, 
    calculate_portfolio_value, 
    calculate_xirr_with_multiple_guesses, 
    calculate_mirr, 
    calculate_twr,
    calculate_weighted_holding_time
)
from utils.stock_api import get_current_price, get_historical_prices

def show_analysis_section():
    st.header("Portfolio Analysis")
    
    with st.spinner("Loading transactions..."):
        transactions_df = get_transactions()
    if transactions_df is None or transactions_df.empty:
        st.warning("No transactions found. Please add some transactions first.")
        return
    
    # Use current_prices from session state
    current_prices = st.session_state.get('current_prices', {})
    total_portfolio_value = st.session_state.get('total_portfolio_value', 0)

    # Portfolio Value Over Time Chart
    st.subheader("Portfolio Value Over Time")
    with st.spinner("Calculating portfolio value over time..."):
        if not transactions_df.empty:
            start_date = transactions_df['Date'].min()
            # Ensure start_date is valid
            if pd.isna(start_date):
                st.error("Start date is invalid. Please provide a valid start date.")
                return
            
            dates = pd.date_range(start=start_date, end=pd.Timestamp.now(), freq='D')
            portfolio_values = []
            
            for date in dates:
                transactions_till_date = transactions_df[transactions_df['Date'] <= date]
                if not transactions_till_date.empty:
                    portfolio_value = calculate_portfolio_value(
                        transactions_till_date,
                        current_prices
                    )['Current Value'].sum()
                    portfolio_values.append(portfolio_value)
                else:
                    portfolio_values.append(0)
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=dates,
                y=portfolio_values,
                mode='lines',
                name='Portfolio Value'
            ))
            fig.update_layout(
                title='Portfolio Value Over Time',
                xaxis_title='Date',
                yaxis_title='Value'
            )
            st.plotly_chart(fig) 
    
    # Calculate overall XIRR and simple return
    with st.spinner("Calculating overall returns..."):
        try:
            overall_xirr = calculate_xirr_with_multiple_guesses(transactions_df)
        except Exception as e:
            st.warning(f"Could not calculate XIRR with multiple guesses: {str(e)}")
            # Try MIRR as fallback
            # try:
            #     overall_mirr = calculate_mirr(transactions_df)
            #     st.info(f"Using MIRR as alternative: {overall_mirr*100:.2f}%")
            # except Exception:
            #     # Finally, try TWR
            #     try:
            #         overall_twr = calculate_twr(transactions_df, current_prices)
            #         st.info(f"Using TWR as alternative: {overall_twr*100:.2f}%")
            #     except Exception:
            #         st.error("All return calculations failed")
    
    # Calculate overall simple return
    # st.write(transactions_df)
    with st.spinner("Calculating total return..."):
        # Filter buy transactions for total investment calculation
        buy_transactions = transactions_df[transactions_df['Type'] == 'BUY']
        total_investment = (buy_transactions['Quantity'] * buy_transactions['Price']).sum()
        
        # Calculate proceeds from sell transactions
        sell_transactions = transactions_df[transactions_df['Type'] == 'SELL']
        total_sell_proceeds = (sell_transactions['Quantity'] * sell_transactions['Price']).sum()
        
        # Use total portfolio value from session state
        total_current_value = total_portfolio_value + total_sell_proceeds
        overall_total_return = ((total_current_value / total_investment) - 1) * 100

        # Display investment metrics in smaller size
        col1, col2, col3 = st.columns(3)
        with col1:
            st.caption("Total Investment")
            st.write(f"{total_investment:,.2f}")
        with col2:
            st.caption("Total Sell Proceeds")
            st.write(f"{total_sell_proceeds:,.2f}")
        with col3:
            st.caption("Current Portfolio Value")
            st.write(f"{total_portfolio_value:,.2f}")

    st.subheader("Overall Returns")
    
    # Calculate weighted average holding time for the entire portfolio
    overall_holding_time = calculate_weighted_holding_time(transactions_df)
    
    # Calculate annualized return based on total return and holding time
    overall_annualized_return = None
    if overall_holding_time is not None and overall_holding_time > 0:
        # Convert holding time from days to years
        holding_time_years = overall_holding_time / 365.0
        # Calculate annualized return using the formula: (1 + Return)^(1/N) - 1
        overall_annualized_return = ((1 + (overall_total_return / 100)) ** (1 / holding_time_years)) - 1
    
    if overall_xirr is not None:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Portfolio XIRR", f"{overall_xirr*100:.2f}%")
        with col2:
            st.metric("Total Return", f"{overall_total_return:.2f}%")
        with col3:
            if overall_annualized_return is not None:
                st.metric("Annualized Return", f"{overall_annualized_return*100:.2f}%")
            else:
                st.metric("Annualized Return", "N/A")
        with col4:
            if overall_holding_time is not None:
                st.metric("Weighted Avg Holding Time", f"{overall_holding_time:.1f} days")
            else:
                st.metric("Weighted Avg Holding Time", "N/A")
        
    
    # Calculate individual stock XIRR and simple returns
    st.subheader("Stock-wise Returns")
    stock_return_data = []
    for symbol in transactions_df['Symbol'].unique():
        with st.spinner(f"Calculating returns for {symbol}..."):
            # XIRR calculation with fallbacks
            return_value = None
            return_type = "XIRR"
            
            try:
                # First try XIRR with multiple guesses
                stock_df = transactions_df[transactions_df['Symbol'] == symbol]
                xirr = calculate_xirr_with_multiple_guesses(transactions_df, symbol)
                
                if xirr is not None:
                    return_value = xirr
                # else:
                #     # Try MIRR as first fallback
                #     try:
                #         mirr = calculate_mirr(stock_df)
                #         if mirr is not None:
                #             return_value = mirr
                #             return_type = "MIRR"
                #         else:
                #             # Try TWR as second fallback
                #             try:
                #                 symbol_prices = {symbol: current_prices.get(symbol, 0)}
                #                 twr = calculate_twr(stock_df, symbol_prices)
                #                 if twr is not None:
                #                     return_value = twr
                #                     return_type = "TWR"
                #             except Exception as e3:
                #                 pass
                #     except Exception as e2:
                #         pass
            except Exception as e:
                st.warning(f"Could not calculate returns for {symbol}: {str(e)}")
            
            # Simple return calculation
            stock_df = transactions_df[transactions_df['Symbol'] == symbol]
            total_quantity = stock_df['Quantity'].sum()
            total_cost = (stock_df['Quantity'] * stock_df['Price']).sum()
            
            if total_quantity > 0:
                avg_cost = total_cost / total_quantity
                current_price = current_prices.get(symbol, 0)
                total_return = ((current_price / avg_cost) - 1) * 100
            else:
                avg_cost = 0
                current_price = current_prices.get(symbol, 0)
                total_return = 0
            
            # Calculate weighted average holding time for this stock
            stock_holding_time = calculate_weighted_holding_time(transactions_df, symbol)
            
            # Calculate annualized return for this stock
            annualized_return = None
            if stock_holding_time is not None and stock_holding_time > 0 and total_return != 0:
                # Convert holding time from days to years
                holding_time_years = stock_holding_time / 365.0
                # Calculate annualized return using the formula: (1 + Return)^(1/N) - 1
                annualized_return = ((1 + (total_return / 100)) ** (1 / holding_time_years)) - 1
            
            # Add to results with whatever return calculation succeeded
            stock_return_data.append({
                'Symbol': symbol,
                'Avg Cost': f"{avg_cost:.2f}",
                'Current Price': f"{current_price:.2f}",
                'Avg Holding Time': f"{stock_holding_time:.1f} days" if stock_holding_time is not None else "N/A",
                'Total Return': f"{total_return:.2f}%",
                'Annualized Return': f"{annualized_return*100:.2f}%" if annualized_return is not None else "N/A",
                'XIRR': f"{return_value*100:.2f}%" if return_value is not None else "N/A"  
            })
    
    if stock_return_data:
        stock_return_df = pd.DataFrame(stock_return_data)
        st.dataframe(stock_return_df, hide_index=True)
    
    # Benchmark Analysis Section
    st.subheader("Benchmark Analysis")
    
    # Allow user to enter a benchmark symbol with VOO as default
    col1, col2 = st.columns(2)
    with col1:
        benchmark_symbol = st.text_input("Enter benchmark symbol:", value="VOO")
    
    if benchmark_symbol:
        with st.spinner(f"Fetching data for benchmark {benchmark_symbol}..."):
            try:
                # Get current date and historical dates for 1-5 years ago
                current_date = pd.Timestamp.now()
                benchmark_data = []
                
                # Get current price once (outside the loop)
                current_price_result = get_current_price(benchmark_symbol)
                
                # Extract the actual price value (second element of the tuple)
                if isinstance(current_price_result, tuple) and len(current_price_result) > 1:
                    current_price = current_price_result[1]  # Use the second element
                else:
                    current_price = current_price_result
                
                # Calculate returns for 1-5 year periods
                for years in range(1, 6):
                    start_date = current_date - pd.DateOffset(years=years)
                    
                    # Get historical price for the start date
                    historical_price_result = get_historical_prices(benchmark_symbol, start_date.strftime('%Y-%m-%d'))
                    
                    # Extract the actual price value (second element of the tuple)
                    if isinstance(historical_price_result, tuple) and len(historical_price_result) > 1:
                        # The second element appears to be a pandas Series with historical data
                        historical_series = historical_price_result[1]
                        # Get the first value from the series (closest to the requested date)
                        if hasattr(historical_series, 'iloc') and len(historical_series) > 0:
                            historical_price = historical_series.iloc[0]
                        else:
                            historical_price = historical_series
                    else:
                        historical_price = historical_price_result
                    
                    # Make sure we have numeric values for the calculation
                    if historical_price is not None and current_price is not None:
                        # Convert to float if they're not already
                        try:
                            historical_price = float(historical_price)
                            current_price = float(current_price)
                            
                            # Calculate annualized return
                            total_return = (current_price / historical_price) - 1
                            annualized_return = ((1 + total_return) ** (1 / years)) - 1
                            
                            benchmark_data.append({
                                'Period': f"{years} Year{'s' if years > 1 else ''}",
                                'Start Date': start_date.strftime('%Y-%m-%d'),
                                'Start Price': f"${historical_price:.2f}",
                                'Current Price': f"${current_price:.2f}",
                                'Total Return': f"{total_return * 100:.2f}%",
                                'Annualized Return': f"{annualized_return * 100:.2f}%"
                            })
                        except Exception as e:
                            st.error(f"Error calculating returns: {str(e)}")
                
                if benchmark_data:
                    benchmark_df = pd.DataFrame(benchmark_data)
                    st.dataframe(benchmark_df, hide_index=True)
                    
                    # Create a bar chart for annualized returns
                    try:
                        fig = px.bar(
                            benchmark_df, 
                            x='Period', 
                            y=[float(x.strip('%')) for x in benchmark_df['Annualized Return']],
                            labels={'y': 'Annualized Return (%)', 'x': 'Time Period'},
                            title=f'Annualized Returns for {benchmark_symbol}'
                        )
                        st.plotly_chart(fig)
                    except Exception as e:
                        st.error(f"Error creating chart: {str(e)}")
                else:
                    st.warning(f"No data available for {benchmark_symbol}")
                    
            except Exception as e:
                st.error(f"Error fetching benchmark data: {str(e)}")
    
    