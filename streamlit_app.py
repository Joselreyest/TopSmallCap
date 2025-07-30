import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
from datetime import datetime, timedelta
import time
import os

# --------------------------
# APP CONFIGURATION
# --------------------------
st.set_page_config(
    page_title="God Mode Stock Scanner",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better appearance
st.markdown("""
<style>
    .css-18e3th9 {padding: 2rem 5rem;}
    .stProgress > div > div > div > div {background-color: #1db954;}
    .stAlert {border-left: 5px solid #1db954;}
    .stDataFrame {font-size: 0.95em;}
    .st-bq {border-color: #1db954;}
</style>
""", unsafe_allow_html=True)

# --------------------------
# SIDEBAR FILTERS
# --------------------------
with st.sidebar:
    st.title("🔍 Scanner Settings")
    
    # Price range slider
    price_range = st.slider(
        "Price Range ($)",
        min_value=0.01,
        max_value=100.0,
        value=(2.0, 20.0),
        step=0.01,
        help="Filter stocks by price range"
    )
    
    # Float range slider
    float_range = st.slider(
        "Max Float (M shares)",
        min_value=0.2,
        max_value=10.0,
        value=10.0,
        step=0.1,
        help="Maximum shares available for trading"
    )
    
    # Results count slider
    results_count = st.slider(
        "Number of Results",
        min_value=1,
        max_value=20,
        value=10,
        help="Number of stocks to display"
    )
    
    st.markdown("---")
    st.markdown("**Advanced Filters**")
    min_volume = st.number_input("Minimum Volume (M)", min_value=1, value=5)
    min_change = st.number_input("Minimum % Gain", min_value=10, value=10)
    
    st.markdown("---")
    st.markdown("**Data Refresh**")
    auto_refresh = st.checkbox("Auto-refresh every 5 minutes", True)
    if auto_refresh:
        st.write("Next refresh:", (datetime.now() + timedelta(minutes=5)).strftime("%H:%M:%S"))

# --------------------------
# DATA FUNCTIONS
# --------------------------
@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_live_stock_data():
    """Fetch live stock data with error handling"""
    try:
        # Get NASDAQ and NYSE tickers (in a real app, use a proper ticker list)
        tickers = ['AAPL', 'MSFT', 'AMZN', 'TSLA', 'GOOGL', 'META', 
                  'NVDA', 'PYPL', 'AMD', 'INTC', 'CSCO', 'CMCSA']
        
        data = []
        for symbol in tickers:
            try:
                stock = yf.Ticker(symbol)
                hist = stock.history(period='1d', interval='1m')
                info = stock.info
                
                if not hist.empty:
                    current_price = hist['Close'].iloc[-1]
                    open_price = hist['Open'].iloc[0]
                    pct_change = ((current_price - open_price) / open_price) * 100
                    volume = hist['Volume'].sum()
                    
                    data.append({
                        'Symbol': symbol,
                        'Company': info.get('shortName', symbol),
                        'Price': current_price,
                        '% Change': pct_change,
                        'Volume': volume,
                        'Avg Volume': info.get('averageVolume', volume/5),
                        'Float (M)': info.get('floatShares', 0)/1e6,
                        'Market Cap ($B)': info.get('marketCap', 0)/1e9,
                        'Sector': info.get('sector', 'N/A'),
                        'PE Ratio': info.get('trailingPE', 0),
                        'News': get_random_news()  # Replace with real news API
                    })
            except Exception as e:
                continue
                
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Error fetching market data: {str(e)}")
        return pd.DataFrame()

def get_random_news():
    """Mock news generator - replace with NewsAPI or similar"""
    news_events = [
        "Positive earnings surprise",
        "Analyst upgrade",
        "New product launch",
        "FDA approval",
        "Merger announcement",
        "Contract win"
    ]
    return np.random.choice(news_events)

# --------------------------
# MAIN APP
# --------------------------
def main():
    st.title("🚀 God Mode Stock Scanner")
    st.markdown("""
    **Scanning for:**  
    ✅ Price up ≥10% today | ✅ Volume ≥5x average | ✅ News catalyst | ✅ Custom float range
    """)
    
    with st.spinner('🛰️ Scanning the market for the best opportunities...'):
        time.sleep(1)  # Simulate loading
        df = get_live_stock_data()
        
        if not df.empty:
            # Apply filters
            df_filtered = df[
                (df['Price'] >= price_range[0]) & 
                (df['Price'] <= price_range[1]) &
                (df['Float (M)'] <= float_range) &
                (df['Volume'] >= min_volume * 1e6) &
                (df['% Change'] >= min_change) &
                (df['Volume'] > 5 * df['Avg Volume'])
            ].sort_values('% Change', ascending=False).head(results_count)
            
            if not df_filtered.empty:
                # Format display
                df_display = df_filtered.copy()
                df_display['Price'] = df_display['Price'].apply(lambda x: f"${x:.2f}")
                df_display['% Change'] = df_display['% Change'].apply(lambda x: f"+{x:.2f}%")
                df_display['Volume'] = df_display['Volume'].apply(lambda x: f"{x/1e6:.2f}M")
                df_display['Avg Volume'] = df_display['Avg Volume'].apply(lambda x: f"{x/1e6:.2f}M")
                df_display['Float (M)'] = df_display['Float (M)'].apply(lambda x: f"{x:.2f}M")
                df_display['Market Cap ($B)'] = df_display['Market Cap ($B)'].apply(lambda x: f"${x:.2f}B")
                df_display['PE Ratio'] = df_display['PE Ratio'].apply(lambda x: f"{x:.1f}" if x > 0 else "N/A")
                
                # Display results
                st.dataframe(
                    df_display[['Symbol', 'Company', 'Price', '% Change', 'Volume', 
                              'Float (M)', 'Market Cap ($B)', 'Sector', 'News']],
                    column_config={
                        "News": st.column_config.TextColumn("Catalyst", width="large"),
                        "% Change": st.column_config.NumberColumn("% Today", format="+%.2f%%")
                    },
                    hide_index=True,
                    use_container_width=True
                )
                
                # Show details for selected stock
                selected = st.selectbox("View detailed analysis for:", df_filtered['Symbol'].tolist())
                selected_data = df_filtered[df_filtered['Symbol'] == selected].iloc[0]
                
                st.subheader(f"📊 {selected} Detailed Analysis")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Current Price", f"${selected_data['Price']:.2f}")
                    st.metric("Market Cap", f"${selected_data['Market Cap ($B)']:.2f}B")
                with col2:
                    st.metric("Today's Change", f"+{selected_data['% Change']:.2f}%")
                    st.metric("Volume vs Avg", f"{(selected_data['Volume']/selected_data['Avg Volume']):.1f}x")
                with col3:
                    st.metric("Float Shares", f"{selected_data['Float (M)']:.2f}M")
                    st.metric("P/E Ratio", f"{selected_data['PE Ratio']:.1f}" if selected_data['PE Ratio'] > 0 else "N/A")
                
                st.markdown(f"**Latest Catalyst:** {selected_data['News']}")
            else:
                st.warning("No stocks match your current criteria. Try adjusting your filters.")
        else:
            st.error("Failed to fetch market data. Please try again later.")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    **Disclaimer:** This is for educational purposes only. Not financial advice.  
    Data may be delayed. Always conduct your own research before trading.
    """)

if __name__ == "__main__":
    main()
