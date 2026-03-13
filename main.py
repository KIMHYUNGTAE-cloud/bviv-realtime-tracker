import asyncio
import logging
import time
from datetime import datetime
from src.config import (
    LOG_FORMAT, LOG_LEVEL, 
    BVIV_UPDATE_INTERVAL, R_UPDATE_INTERVAL, COLD_START_BUFFER,
    RISK_FREE_RATE_DEFAULT
)
from src.network.api_client import BybitApiClient
from src.network.ws_client import BybitWSClient
from src.core.engine import BVIVEngine
from src.storage.csv_logger import BVIVCSVLogger

# Configure Logging
logging.basicConfig(level=getattr(logging, LOG_LEVEL), format=LOG_FORMAT)
logger = logging.getLogger(__name__)

class BVIVApp:
    def __init__(self):
        self.rest_client = BybitApiClient()
        self.ws_client = BybitWSClient()
        self.engine = BVIVEngine(risk_free_rate=RISK_FREE_RATE_DEFAULT)
        self.csv_logger = BVIVCSVLogger()
        self.options_info = {}
        self.expirations = []

    async def initialize(self):
        """Initial data load and setup."""
        self.options_info = await self.rest_client.fetch_options_instruments()
        if not self.options_info:
            raise RuntimeError("Could not fetch active options instruments")
        
        exp_set = {int(inst['deliveryTime']) for inst in self.options_info.values()}
        self.expirations = sorted(list(exp_set))

        # Initial R update
        dynamic_r = await self.rest_client.get_dynamic_r()
        if dynamic_r is not None:
            self.engine.set_risk_free_rate(dynamic_r)
        else:
            logger.warning(f"Using default risk-free rate: {RISK_FREE_RATE_DEFAULT}")

    def get_term_expirations(self):
        """Identify Near-term (T1) and Next-term (T2) expirations around 30 days."""
        now_ms = int(time.time() * 1000)
        target_ms = now_ms + (30 * 24 * 60 * 60 * 1000)
        
        near_term = None
        next_term = None
        
        valid_exps = [e for e in self.expirations if e > now_ms]
        
        for i in range(len(valid_exps) - 1):
            if valid_exps[i] <= target_ms <= valid_exps[i+1]:
                near_term = valid_exps[i]
                next_term = valid_exps[i+1]
                break
        
        if not near_term and len(valid_exps) >= 2:
            near_term = valid_exps[0]
            next_term = valid_exps[1]
            
        return near_term, next_term

    async def r_updater_loop(self):
        """Periodically update the risk-free rate."""
        while True:
            await asyncio.sleep(R_UPDATE_INTERVAL)
            dynamic_r = await self.rest_client.get_dynamic_r()
            if dynamic_r is not None:
                self.engine.set_risk_free_rate(dynamic_r)

    async def calculation_worker_loop(self):
        """Steady loop for BVIV calculation and display."""
        await asyncio.sleep(COLD_START_BUFFER)
        while True:
            try:
                near_exp, next_exp = self.get_term_expirations()
                if near_exp and next_exp:
                    orderbooks = self.ws_client.get_snapshot()
                    bviv = self.engine.calculate_bviv(
                        near_exp, next_exp, 
                        self.options_info, orderbooks
                    )
                    if bviv:
                        print(f"\r[BVIV Index] {datetime.now().strftime('%H:%M:%S')} : {bviv:.2f}", end="", flush=True)
                        self.csv_logger.log_point(bviv, self.engine.risk_free_rate)
                
                await asyncio.sleep(BVIV_UPDATE_INTERVAL)
            except Exception as e:
                logger.error(f"Calculation Worker Error: {e}")
                await asyncio.sleep(1)

    async def run(self):
        """Start all tasks and orchestrate the application."""
        await self.initialize()
        
        # Identify symbols for relevant expirations to reduce WS load
        near_exp, next_exp = self.get_term_expirations()
        if not near_exp or not next_exp:
            logger.error("Could not find suitable near/next term expirations")
            return

        symbols_to_sub = [
            s for s, info in self.options_info.items() 
            if int(info['deliveryTime']) in [near_exp, next_exp]
        ]

        # Connect and Start Workers
        await self.ws_client.connect()
        await self.ws_client.subscribe_tickers(symbols_to_sub)

        tasks = [
            asyncio.create_task(self.ws_client.heartbeat()),
            asyncio.create_task(self.ws_client.run()),
            asyncio.create_task(self.r_updater_loop()),
            asyncio.create_task(self.calculation_worker_loop())
        ]
        
        await asyncio.gather(*tasks)

if __name__ == "__main__":
    app = BVIVApp()
    try:
        asyncio.run(app.run())
    except KeyboardInterrupt:
        print("\nApplication stopped by user.")
