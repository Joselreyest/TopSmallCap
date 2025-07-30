import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
from datetime import datetime

# Configuration
st.set_page_config(
    page_title="God Mode Stock Scanner",
    page_icon="📈",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .stProgress > div > div > div > div {
        background-color: #1db954;
    }
    .st-b7 {
        color: white;
    }
    .st-cq {
        background-color: #1e1e1e;
    }
</style>
""", unsafe_allow_html=True)

# Header
col1, col2 = st.columns([3,1])
with col1:
    st.title("🚀 God Mode Stock Scanner")
    st.markdown("Find explosive stocks with strong demand signals")
with col2:
    st.image("https://streamlit.io/images/brand/streamlit-mark-color.png", width=150)

# Sidebar Filters
with st.sidebar:
    st.header("🔍 Filters")
    
    price_range = st.slider(
        "Price Range ($)",
        0.01, 100.0, (2.0, 20.0),
        step=0.01
    )
    
    float_range = st.slider(
        "Max Float (M shares)",
        0.2, 10.0, 10.0,
        step=0.1
    )
    
    results_count = st.slider(
        "Number of Results",
        1, 20, 10
    )
    
    st.markdown("---")
    st.markdown("**Data Sources:**")
    st.markdown("- Yahoo Finance")
    st.markdown("- NewsAPI")
    st.markdown("---")
    st.markdown("*Updates every 5 minutes*")

# Data Processing
@st.cache_data(ttl=300)
def load_data():
    # Replace with actual API calls in production
    symbols = ['AAPL', 'MSFT', 'AMZN', 'TSLA', 'GOOGL', 'META', 'NVDA', 'PYPL']
    
    data = []
    for symbol in symbols:
        try:
            stock = yf.Ticker(symbol)
            hist = stock.history(period="1d")
            info = stock.info
            
            if not hist.empty:
                data.append({
                    'Symbol': symbol,
                    'Company': info.get('shortName', symbol),
                    'Price': hist['Close'].iloc[-1],
                    'Change': hist['Close'].iloc[-1] - hist['Open'].iloc[-1],
                    'Volume': hist['Volume'].iloc[-1],
                    'Avg Volume': info.get('averageVolume', 0),
                    'Float': info.get('floatShares', 0)/1e6,
                    'Market Cap': info.get('marketCap', 0)/1e9,
                    'Sector': info.get('sector', 'N/A'),
                    'PE': info.get('trailingPE', 0)
                })
        except:
            continue
            
    return pd.DataFrame(data)

# Main App
df = load_data()

# Apply filters
if not df.empty:
    df = df[
        (df['Price'] >= price_range[0]) & 
        (df['Price'] <= price_range[1]) &
        (df['Float'] <= float_range) &
        (df['Volume'] > 5 * df['Avg Volume'])
    ].sort_values('Change', ascending=False).head(results_count)
    
    # Display results
    st.dataframe(
        df.style.format({
            'Price': '${:.2f}',
            'Change': '+${:.2f}',
            'Volume': '{:,.0f}',
            'Avg Volume': '{:,.0f}',
            'Float': '{:.2f}M',
            'Market Cap': '${:.2f}B',
            'PE': '{:.1f}'
        }),
        use_container_width=True
    )
else:
    st.warning("No data available. Try again later.")

# Footer
st.markdown("---")
st.markdown("""
**Disclaimer:** This is for educational purposes only. Not financial advice.
""")
