import asyncio
import json
import logging
import aiohttp
from typing import Dict, List, Optional, Callable
from src.config import WS_URL

logger = logging.getLogger(__name__)

class BybitWSClient:
    """
    Bybit v5 WebSocket client for real-time market data streaming.
    Handles reconnection, heartbeat, and local state management.
    """
    
    def __init__(self, ws_url: str = WS_URL):
        self.ws_url = ws_url
        self.orderbooks: Dict[str, Dict] = {}
        self.connected = False
        self._ws = None

    async def connect(self):
        """Establish WebSocket connection."""
        self._session = aiohttp.ClientSession()
        self._ws = await self._session.ws_connect(self.ws_url)
        self.connected = True
        logger.debug(f"Connected to Bybit WebSocket: {self.ws_url}")
        
    async def subscribe_tickers(self, symbols: List[str]):
        """Subscribe to ticker streams for given symbols in chunks."""
        chunk_size = 50
        for i in range(0, len(symbols), chunk_size):
            chunk = symbols[i:i+chunk_size]
            args = [f"tickers.{s}" for s in chunk]
            await self._ws.send_json({
                "op": "subscribe",
                "args": args
            })
        logger.debug(f"Requested subscription for {len(symbols)} tickers")

    async def heartbeat(self):
        """Maintain connection with periodic ping."""
        while self.connected:
            try:
                if self._ws and not self._ws.closed:
                    await self._ws.send_json({"op": "ping"})
                await asyncio.sleep(20)
            except Exception as e:
                logger.error(f"WS Heartbeat Error: {e}")
                break

    async def run(self):
        """Listen for WebSocket messages and update local state."""
        async for msg in self._ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                data = json.loads(msg.data)
                
                # Handle subscription confirmation
                if 'success' in data and data.get('op') == 'subscribe':
                    logger.debug(f"Subscription status: {data.get('success')} (Msg: {data.get('ret_msg')})")
                    continue

                # Handle pong
                if data.get('op') == 'pong' or data.get('ret_msg') == 'pong':
                    continue

                # Handle ticker updates
                if 'topic' in data and data['topic'].startswith('tickers.'):
                    items = data['data']
                    if not isinstance(items, list):
                        items = [items]
                    
                    for ticker_data in items:
                        symbol = ticker_data['symbol']
                        bid = ticker_data.get('bid1Price') or ticker_data.get('bidPrice')
                        ask = ticker_data.get('ask1Price') or ticker_data.get('askPrice')
                        
                        if bid and ask and float(bid) > 0 and float(ask) > 0:
                            self.orderbooks[symbol] = {
                                'mid': (float(bid) + float(ask)) / 2,
                                'bid': float(bid),
                                'ask': float(ask)
                            }
            elif msg.type == aiohttp.WSMsgType.CLOSED:
                logger.warning("WebSocket closed")
                break
            elif msg.type == aiohttp.WSMsgType.ERROR:
                logger.error("WebSocket error")
                break
        
        self.connected = False
        await self._session.close()

    def get_snapshot(self) -> Dict[str, Dict]:
        """Get a copy of the current orderbook state."""
        return self.orderbooks.copy()
