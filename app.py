import streamlit as st
from components.portfolio_input import show_input_section
from components.portfolio_view import show_portfolio_view
from components.portfolio_analysis import show_analysis_section

st.set_page_config(
    page_title="Portfolio Performance Tracker",
    page_icon="📈",
    layout="wide"
)

def main():
    st.title("Portfolio Performance Tracker 📈")
    
    # Initialize session state for storing transactions
    if 'transactions_df' not in st.session_state:
        st.session_state.transactions_df = None

    # Create tabs for different sections
    tab1, tab2, tab3 = st.tabs(["Input Transactions", "View Portfolio", "Analysis"])
    
    with tab1:
        with st.spinner('Loading Input Transactions...'):
            show_input_section()
    
    with tab2:
        with st.spinner('Loading Portfolio View...'):
            show_portfolio_view()
    
    with tab3:
        with st.spinner('Loading Analysis...'):
            show_analysis_section()

if __name__ == "__main__":
    main() 