import aiohttp
import math
import time
import logging
from typing import Dict, List, Optional, Tuple
from src.config import BASE_URL, CATEGORY_OPTION, CATEGORY_LINEAR, CATEGORY_SPOT, R_CAP_FLOOR

logger = logging.getLogger(__name__)

class BybitApiClient:
    """
    Bybit v5 REST API client for fetching market data and instrumentation.
    """
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url

    async def fetch_options_instruments(self, base_coin: str = "BTC") -> Dict[str, Dict]:
        """Fetch all active options instruments for a base coin."""
        async with aiohttp.ClientSession() as session:
            url = f"{self.base_url}/v5/market/instruments-info?category={CATEGORY_OPTION}&baseCoin={base_coin}"
            async with session.get(url) as response:
                data = await response.json()
                if data.get('retCode') == 0:
                    instruments = data['result']['list']
                    options = {}
                    for inst in instruments:
                        if inst['status'] == 'Trading':
                            # Extract strike price if missing
                            if 'strikePrice' not in inst or not inst['strikePrice']:
                                try:
                                    # Expected format: BTC-27MAR26-60000-C
                                    parts = inst['symbol'].split('-')
                                    inst['strikePrice'] = parts[2]
                                except (IndexError, ValueError):
                                    logger.warning(f"Could not extract strikePrice from symbol: {inst['symbol']}")
                                    continue
                            options[inst['symbol']] = inst
                    return options
                else:
                    logger.error(f"Failed to fetch options: {data.get('retMsg')}")
                    return {}

    async def get_dynamic_r(self, spot_symbol: str = "BTCUSDT") -> Optional[float]:
        """Calculate dynamic risk-free rate using futures basis."""
        try:
            async with aiohttp.ClientSession() as session:
                # 1. Get Spot Price
                async with session.get(f"{self.base_url}/v5/market/tickers?category={CATEGORY_SPOT}&symbol={spot_symbol}") as resp:
                    data = await resp.json()
                    spot_price = float(data['result']['list'][0]['lastPrice'])
                
                # 2. Get Nearest Quarterly Futures
                async with session.get(f"{self.base_url}/v5/market/instruments-info?category={CATEGORY_LINEAR}&baseCoin=BTC") as resp:
                    data = await resp.json()
                    futures_list = data['result']['list']
                    # Find quarterly (contains '-' in symbol and has deliveryTime)
                    quarterly = [f for f in futures_list if int(f['deliveryTime']) > 0 and '-' in f['symbol']]
                    
                    now_ms = int(time.time() * 1000)
                    # Filter for > 7 days to maturity
                    quarterly = [f for f in quarterly if int(f['deliveryTime']) > now_ms + (7 * 86400000)]
                    quarterly.sort(key=lambda x: int(x['deliveryTime']))
                    
                    if not quarterly:
                        return None
                    
                    target_fut = quarterly[0]
                    fut_symbol = target_fut['symbol']
                    delivery_ms = int(target_fut['deliveryTime'])
                
                # 3. Get Futures Price
                async with session.get(f"{self.base_url}/v5/market/tickers?category={CATEGORY_LINEAR}&symbol={fut_symbol}") as resp:
                    data = await resp.json()
                    futures_price = float(data['result']['list'][0]['lastPrice'])
            
            # 4. Calculate R = ln(F/S) / T
            T = (delivery_ms - now_ms) / (365 * 86400000)
            if T > 0 and spot_price > 0:
                r = math.log(futures_price / spot_price) / T
                # Apply Caps
                r = max(R_CAP_FLOOR[0], min(R_CAP_FLOOR[1], r))
                logger.debug(f"Dynamic R calculated: {r:.4f} using {fut_symbol} (Basis: {futures_price - spot_price:.2f})")
                return r
                
        except Exception as e:
            logger.error(f"Error calculating dynamic R: {e}")
        return None
