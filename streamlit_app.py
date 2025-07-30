import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
from datetime import datetime, timedelta
import time
import requests
from bs4 import BeautifulSoup
try:
    import html5lib
    HTML_PARSER = 'html5lib'
except ImportError:
    HTML_PARSER = 'lxml'

# --------------------------
# APP CONFIGURATION
# --------------------------
st.set_page_config(
    page_title="God Mode Stock Scanner",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
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
# DATA LOADING FUNCTIONS
# --------------------------
def get_nasdaq_symbols():
    """Get NASDAQ symbols from NASDAQ website"""
    try:
        url = "https://api.nasdaq.com/api/screener/stocks?tableonly=true&limit=10000"
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json"
        }
        response = requests.get(url, headers=headers)
        data = response.json()
        return [item['symbol'] for item in data['data']['table']['rows']]
    except Exception as e:
        st.error(f"Failed to fetch NASDAQ symbols: {str(e)}")
        return []

def get_sp500_symbols():
    """Get current S&P 500 symbols with robust parsing"""
    try:
        url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
        
        # Try with lxml first
        try:
            tables = pd.read_html(url, flavor='lxml')
        except Exception as e:
            # Fall back to basic parser without specifying flavor
            st.warning("lxml parser not available, using pandas default parser")
            tables = pd.read_html(url)
            
        return tables[0]['Symbol'].tolist()
    except Exception as e:
        st.error(f"Failed to fetch S&P 500 symbols: {str(e)}")
        # Fallback to static list
        return ['AAPL', 'MSFT', 'AMZN', 'GOOGL', 'META', 'TSLA', 'NVDA', 'JPM', 'V', 'PG']

def get_nyse_symbols():
    """Get NYSE symbols using alternative API"""
    try:
        # Alternative reliable source for NYSE symbols
        url = "https://old.nasdaq.com/screening/companies-by-name.aspx?letter=0&exchange=nyse&render=download"
        df = pd.read_csv(url)
        return df['Symbol'].tolist()
    except Exception as e:
        st.error(f"Failed to fetch NYSE symbols: {str(e)}")
        # Fallback to some common NYSE symbols
        return ['BAC', 'WMT', 'DIS', 'GE', 'F', 'T', 'VZ', 'XOM', 'CVX', 'PFE']

def load_symbols_from_file(uploaded_file):
    """Load symbols from uploaded file"""
    try:
        if uploaded_file.name.endswith('.csv'):
            return pd.read_csv(uploaded_file)['Symbol'].tolist()
        else:  # txt file
            return [line.decode('utf-8').strip() for line in uploaded_file if line.strip()]
    except Exception as e:
        st.error(f"Error loading symbols: {str(e)}")
        return []

# --------------------------
# SIDEBAR FILTERS
# --------------------------
with st.sidebar:
    st.title("🔍 Scanner Settings")
    
    # Exchange selection
    exchange = st.radio(
        "Select Exchange:",
        ["NASDAQ", "S&P 500", "NYSE", "Custom"],
        index=0
    )
    
    # Custom file upload
    if exchange == "Custom":
        custom_file = st.file_uploader(
            "Upload symbols file (CSV or TXT)",
            type=['csv', 'txt']
        )
    
    # Price range slider
    price_range = st.slider(
        "Price Range ($)",
        min_value=0.01,
        max_value=100.0,
        value=(2.0, 20.0),
        step=0.01
    )
    
    # Float range slider
    float_range = st.slider(
        "Max Float (M shares)",
        min_value=0.2,
        max_value=10.0,
        value=10.0,
        step=0.1
    )
    
    # Results count slider
    results_count = st.slider(
        "Number of Results",
        min_value=1,
        max_value=20,
        value=10
    )
    
    st.markdown("---")
    st.markdown("**Advanced Filters**")
    min_volume = st.number_input("Minimum Volume (M)", min_value=1, value=5)
    min_change = st.number_input("Minimum % Gain", min_value=10, value=10)
    
    st.markdown("---")
    st.markdown("**Data Refresh**")
    auto_refresh = st.checkbox("Auto-refresh every 5 minutes", True)

# --------------------------
# DATA PROCESSING
# --------------------------
def get_symbols_to_scan():
    """Get symbols based on exchange selection"""
    if exchange == "NASDAQ":
        return get_nasdaq_symbols()
    elif exchange == "S&P 500":
        return get_sp500_symbols()
    elif exchange == "NYSE":
        return get_nyse_symbols()
    elif exchange == "Custom" and custom_file:
        return load_symbols_from_file(custom_file)
    return []

@st.cache_data(ttl=300)
def get_live_stock_data(symbols):
    """Fetch live stock data for given symbols"""
    data = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, symbol in enumerate(symbols[:200]):  # Limit to 200 for demo
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
                    'News': get_random_news()
                })
                
            # Update progress
            progress = (i + 1) / min(len(symbols), 200)
            progress_bar.progress(progress)
            status_text.text(f"Processing {i+1}/{min(len(symbols), 200)}: {symbol}")
            
        except Exception as e:
            continue
    
    progress_bar.empty()
    status_text.empty()
    return pd.DataFrame(data)

def get_random_news():
    """Mock news generator"""
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
    st.markdown(f"**Current Scan:** {exchange} Stocks | ${price_range[0]}-${price_range[1]} | ≤{float_range}M Float")
    
    symbols = get_symbols_to_scan()
    
    if not symbols:
        st.warning("No symbols found for scanning. Please check your input.")
        return
    
    with st.spinner(f'🛰️ Scanning {len(symbols)} {exchange} stocks...'):
        df = get_live_stock_data(symbols)
        
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
                # Display results
                st.dataframe(
                    format_dataframe(df_filtered),
                    hide_index=True,
                    use_container_width=True
                )
                
                # Detailed view
                show_stock_details(df_filtered)
            else:
                st.warning("No stocks match your criteria. Try adjusting filters.")
        else:
            st.error("Failed to fetch market data. Please try again later.")
    
    st.markdown("---")
    st.markdown("**Disclaimer:** Educational use only. Not financial advice.")

def format_dataframe(df):
    """Format dataframe for display"""
    df_formatted = df.copy()
    df_formatted['Price'] = df['Price'].apply(lambda x: f"${x:.2f}")
    df_formatted['% Change'] = df['% Change'].apply(lambda x: f"+{x:.2f}%")
    df_formatted['Volume'] = df['Volume'].apply(lambda x: f"{x/1e6:.2f}M")
    df_formatted['Avg Volume'] = df['Avg Volume'].apply(lambda x: f"{x/1e6:.2f}M")
    df_formatted['Float (M)'] = df['Float (M)'].apply(lambda x: f"{x:.2f}M")
    df_formatted['Market Cap ($B)'] = df['Market Cap ($B)'].apply(lambda x: f"${x:.2f}B")
    return df_formatted[['Symbol', 'Company', 'Price', '% Change', 'Volume', 'Float (M)', 'Market Cap ($B)', 'Sector', 'News']]

def show_stock_details(df):
    """Show detailed view for selected stock"""
    selected = st.selectbox("View detailed analysis for:", df['Symbol'].tolist())
    selected_data = df[df['Symbol'] == selected].iloc[0]
    
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

if __name__ == "__main__":
    main()
