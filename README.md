# Bybit BVIV Real-time Tracker

An asynchronous, event-driven Python engine that calculates the Bitcoin Volatility Index (BVIV) in real-time using Bybit options data. The tracker aggregates high-frequency tick data into 1-minute OHLC (Open-High-Low-Close) candles and logs it permanently for quantitative analysis, backtesting, and algorithmic trading.

## Core Value Proposition

While standard volatility indices provide generalized daily data, this tracker offers high-resolution, micro-structural insights into crypto volatility.

- **Asynchronous Ingestion and Decoupling**: Separates WebSocket I/O from heavy CPU-bound mathematical computations, ensuring zero lag during extreme market volatility.
- **Model-Free VIX Methodology**: Calculates implied volatility using a wide spectrum of Out-of-the-Money (OTM) options, guaranteeing O(N) efficiency per snapshot.
- **Dynamic Risk-Free Rate (R)**: Instead of using fixed interest rates, it dynamically extracts the implied yield from the Bitcoin futures-spot basis to accurately reflect crypto-native liquidity premiums.
- **Quant-Ready Data**: Transforms noisy 2-second calculation ticks into clean, standardized 1-minute OHLC CSV formats.

## Mathematical Methodology

### 1. The Volatility Engine
The core engine follows the CBOE VIX methodology, interpolating near-term and next-term option variances to derive a 30-day expected volatility.

**Variance Calculation Formula**:
$$\sigma^2 = \frac{2}{T} \sum_i \frac{\Delta K_i}{K_i^2} e^{RT} Q(K_i) - \frac{1}{T} \left[ \frac{F}{K_0} - 1 \right]^2$$

**Variables**:
- **T**: Time to expiration (in years)
- **F**: Forward index level derived from index option prices
- **K0**: First strike price equal to or less than the forward index level, F
- **Ki**: Strike price of i-th OTM option
- **Delta Ki**: Interval between strike prices
- **R**: Risk-free interest rate to expiration
- **Q(Ki)**: Mid-quote price for each option with strike Ki

### 2. Dynamic Risk-Free Rate (R)
R is calculated hourly using the annualized basis between Bybit BTC Spot (S) and the nearest Quarterly Futures (F):

$$R = \ln(F / S) \times (365 / \text{Days to Maturity})$$

## Data Schema

The logger automatically aggregates data into `data/bviv_ohlc.csv`.

| Column | Type | Description |
| :--- | :--- | :--- |
| timestamp | int | Unix timestamp of the 1-minute candle close |
| datetime | string | UTC human-readable time (YYYY-MM-DD HH:MM:00) |
| open | float | First BVIV calculation of the minute |
| high | float | Highest BVIV calculation of the minute |
| low | float | Lowest BVIV calculation of the minute |
| close | float | Last BVIV calculation of the minute |
| r_rate | float | Dynamic risk-free rate applied at the time |

## Project Architecture

```plaintext
bviv-realtime-tracker/
├── src/
│   ├── config.py           # Centralized configurations and ENV loading
│   ├── network/
│   │   ├── api_client.py   # REST Client (Options setup and Futures Basis)
│   │   └── ws_client.py    # WebSocket Ingester (Tickers Stream)
│   ├── core/
│   │   └── engine.py       # Mathematical BVIV Calculation Engine
│   └── storage/
│       └── csv_logger.py   # In-memory buffering and 1m OHLC aggregation
├── tools/
│   └── plot_bviv.py        # Candlestick visualization utility
├── main.py                 # Entry point and Async Task Orchestrator
├── data/                   # Output directory for CSV files
├── tests/                  # Unit test suites
├── requirements.txt        # Dependencies (aiohttp, pandas, mplfinance)
└── README.md               
```

## Getting Started

### Prerequisites
- Python 3.9+ 
- No API keys required (uses public endpoints)

### 1. Installation
```bash
git clone https://github.com/your-username/bviv-realtime-tracker.git
cd bviv-realtime-tracker

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configuration
All parameters such as calculation intervals and storage paths are managed in `src/config.py`. You can adjust them directly in that file.

Key parameters:
- `BVIV_UPDATE_INTERVAL`: Calculation frequency (default: 2s)
- `R_UPDATE_INTERVAL`: Basis update frequency (default: 3600s)

### 3. Execution
Start the tracker:
```bash
python3 main.py
```
The engine will perform a cold start, fetch the dynamic yield, synchronize orderbooks, and begin calculating. CSV logs append at the start of every minute.

### 4. Visualization
To visualize the collected OHLC data:
```bash
python3 tools/plot_bviv.py
```

## License
Distributed under the MIT License. See `LICENSE` for more information.