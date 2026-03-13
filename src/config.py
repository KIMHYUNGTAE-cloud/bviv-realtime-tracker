import os

# API Configurations
BASE_URL = "https://api.bybit.com"
WS_URL = "wss://stream.bybit.com/v5/public/option"

# Calculation Settings
BVIV_UPDATE_INTERVAL = 2  # seconds
R_UPDATE_INTERVAL = 3600  # 1 hour
COLD_START_BUFFER = 3     # seconds
RISK_FREE_RATE_DEFAULT = 0.05
R_CAP_FLOOR = (0.0, 0.3)

# Storage Settings
DATA_DIR = "data"
CSV_FILENAME = "bviv_ohlc.csv"
CSV_PATH = os.path.join(DATA_DIR, CSV_FILENAME)

# Logging
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
LOG_LEVEL = "INFO"

# Category
CATEGORY_OPTION = "option"
CATEGORY_LINEAR = "linear"
CATEGORY_SPOT = "spot"
