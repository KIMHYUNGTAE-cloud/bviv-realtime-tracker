import pandas as pd
import mplfinance as mpf
import os
import sys

# Add project root to path to use config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import CSV_PATH

def plot_bviv(csv_path: str):
    """
    Reads BVIV OHLC CSV and displays a candlestick chart.
    """
    if not os.path.exists(csv_path):
        print(f"Error: CSV file not found at {csv_path}")
        print("Please run the main tracker for at least a few minutes first.")
        return

    print(f"Loading data from {csv_path}...")
    df = pd.read_csv(csv_path)
    
    if df.empty:
        print("Error: CSV file is empty.")
        return

    # Prepare data for mplfinance
    df['datetime'] = pd.to_datetime(df['datetime'])
    df.set_index('datetime', inplace=True)
    
    # Rename columns to standard OHLC
    df_ohlc = df[['open', 'high', 'low', 'close']].copy()
    df_ohlc.columns = ['Open', 'High', 'Low', 'Close']

    print(f"Plotting {len(df_ohlc)} minutes of BVIV data...")
    
    # Plotting
    mpf.plot(df_ohlc, 
             type='candle', 
             style='charles', 
             title='Bitcoin Volatility Index (BVIV) - 1m OHLC',
             ylabel='Volatility (%)',
             mav=(5, 10), # Moving averages for trend
             volume=False,
             show_nontrading=False)

if __name__ == "__main__":
    path = CSV_PATH
    if len(sys.argv) > 1:
        path = sys.argv[1]
    
    plot_bviv(path)
