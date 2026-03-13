import math
import time
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.core.engine import BVIVEngine

def test_variance_logic():
    engine = BVIVEngine(risk_free_rate=0.05)
    
    # Mock some options data
    expiration_ms = int(time.time() * 1000) + (30 * 24 * 60 * 60 * 1000) # 30 days from now
    
    # Mock instruments info with asymmetric strikes
    options_info = {
        "BTC-EXP-60000-C": {"symbol": "BTC-EXP-60000-C", "deliveryTime": expiration_ms, "strikePrice": 60000, "optionsType": "Call"},
        "BTC-EXP-60000-P": {"symbol": "BTC-EXP-60000-P", "deliveryTime": expiration_ms, "strikePrice": 60000, "optionsType": "Put"},
        "BTC-EXP-61000-C": {"symbol": "BTC-EXP-61000-C", "deliveryTime": expiration_ms, "strikePrice": 61000, "optionsType": "Call"},
        "BTC-EXP-61000-P": {"symbol": "BTC-EXP-61000-P", "deliveryTime": expiration_ms, "strikePrice": 61000, "optionsType": "Put"},
        "BTC-EXP-59000-C": {"symbol": "BTC-EXP-59000-C", "deliveryTime": expiration_ms, "strikePrice": 59000, "optionsType": "Call"},
        "BTC-EXP-59000-P": {"symbol": "BTC-EXP-59000-P", "deliveryTime": expiration_ms, "strikePrice": 59000, "optionsType": "Put"},
        "BTC-EXP-58000-C": {"symbol": "BTC-EXP-58000-C", "deliveryTime": expiration_ms, "strikePrice": 58000, "optionsType": "Call"},
        "BTC-EXP-58000-P": {"symbol": "BTC-EXP-58000-P", "deliveryTime": expiration_ms, "strikePrice": 58000, "optionsType": "Put"},
        "BTC-EXP-62500-C": {"symbol": "BTC-EXP-62500-C", "deliveryTime": expiration_ms, "strikePrice": 62500, "optionsType": "Call"},
        "BTC-EXP-62500-P": {"symbol": "BTC-EXP-62500-P", "deliveryTime": expiration_ms, "strikePrice": 62500, "optionsType": "Put"},
    }
    
    # Mock mid prices - intentionally skip 61000 P and 59000 C
    orderbooks = {
        "BTC-EXP-60000-C": {"mid": 1200},
        "BTC-EXP-60000-P": {"mid": 1150},
        "BTC-EXP-61000-C": {"mid": 800},
        # Missing 61000 P
        # Missing 59000 C
        "BTC-EXP-59000-P": {"mid": 750},
        "BTC-EXP-58000-P": {"mid": 400},
        "BTC-EXP-62500-C": {"mid": 300},
    }
    
    var = engine.calculate_variance(expiration_ms, options_info, orderbooks)
    
    print("-" * 50)
    print("ASymmetric Strike Test Case Result")
    print("-" * 50)
    print(f"Calculated Variance: {var}")
    if var is not None and var > 0:
        bviv = math.sqrt(var) * 100
        print(f"Calculated BVIV (VIX style): {bviv:.2f}")
    else:
        print("Variance calculation failed or returned non-positive value.")
    print("-" * 50)

if __name__ == "__main__":
    test_variance_logic()
