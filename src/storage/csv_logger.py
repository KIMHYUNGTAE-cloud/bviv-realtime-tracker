import os
import csv
import logging
from datetime import datetime, timezone
from typing import List, Optional
from src.config import CSV_PATH, DATA_DIR

logger = logging.getLogger(__name__)

class BVIVCSVLogger:
    """
    Buffers real-time BVIV values and writes 1-minute OHLC data to CSV.
    """
    
    def __init__(self, csv_path: str = CSV_PATH):
        self.csv_path = csv_path
        self._buffer: List[float] = []
        self._current_minute: Optional[int] = None
        self._ensure_dir()
        self._initialize_csv()

    def _ensure_dir(self):
        os.makedirs(DATA_DIR, exist_ok=True)

    def _initialize_csv(self):
        """Create CSV with headers if it doesn't exist."""
        if not os.path.exists(self.csv_path):
            with open(self.csv_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['timestamp', 'datetime', 'open', 'high', 'low', 'close', 'r_rate'])
            # Keeping this one as it's a one-time setup log
            logger.info(f"Initialized new CSV storage at {self.csv_path}")

    def log_point(self, value: float, r_rate: float):
        """
        Record a single BVIV data point. 
        Triggers an OHLC write if the minute has changed.
        """
        now = datetime.now(timezone.utc)
        minute = now.minute
        
        # If this is the first data point or the minute has changed
        if self._current_minute is not None and minute != self._current_minute:
            self._write_ohlc(r_rate)
            
        self._current_minute = minute
        self._buffer.append(value)

    def _write_ohlc(self, r_rate: float):
        """Aggregate buffer into OHLC and write to CSV."""
        if not self._buffer:
            return

        now = datetime.now(timezone.utc)
        # Round down to the start of the minute
        timestamp = int(now.replace(second=0, microsecond=0).timestamp())
        dt_str = now.strftime('%Y-%m-%d %H:%M:00')

        o = self._buffer[0]
        h = max(self._buffer)
        l = min(self._buffer)
        c = self._buffer[-1]

        try:
            with open(self.csv_path, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([timestamp, dt_str, round(o, 4), round(h, 4), round(l, 4), round(c, 4), round(r_rate, 6)])
            # Removed INFO log for cleaner console
        except Exception as e:
            logger.error(f"Failed to write to CSV: {e}")
        
        # Clear buffer for the next minute
        self._buffer = []
