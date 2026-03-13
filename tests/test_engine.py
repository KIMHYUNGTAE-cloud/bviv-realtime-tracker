import math
import time
from src.core.engine import BVIVEngine

def test_variance_calculation():
    engine = BVIVEngine(risk_free_rate=0.05)
    
    # Mock data
    expiration_ms = int(time.time() * 1000) + (30 * 24 * 60 * 60 * 1000)
    
    options_info = {
        "BTC-OTM-P1": {"deliveryTime": expiration_ms, "strikePrice": 60000, "optionsType": "Put", "symbol": "BTC-OTM-P1"},
        "BTC-OTM-P2": {"deliveryTime": expiration_ms, "strikePrice": 65000, "optionsType": "Put", "symbol": "BTC-OTM-P2"},
        "BTC-ATM-C": {"deliveryTime": expiration_ms, "strikePrice": 70000, "optionsType": "Call", "symbol": "BTC-ATM-C"},
        "BTC-ATM-P": {"deliveryTime": expiration_ms, "strikePrice": 70000, "optionsType": "Put", "symbol": "BTC-ATM-P"},
        "BTC-OTM-C1": {"deliveryTime": expiration_ms, "strikePrice": 75000, "optionsType": "Call", "symbol": "BTC-OTM-C1"},
        "BTC-OTM-C2": {"deliveryTime": expiration_ms, "strikePrice": 80000, "optionsType": "Call", "symbol": "BTC-OTM-C2"},
    }
    
    orderbooks = {
        "BTC-OTM-P1": {"mid": 500},
        "BTC-OTM-P2": {"mid": 1000},
        "BTC-ATM-C": {"mid": 2000},
        "BTC-ATM-P": {"mid": 2050},
        "BTC-OTM-C1": {"mid": 1200},
        "BTC-OTM-C2": {"mid": 600},
    }
    
    variance = engine.calculate_variance(expiration_ms, options_info, orderbooks)
    assert variance is not None
    assert variance > 0
    print(f"Calculated Variance: {variance}")

def test_bviv_interpolation():
    engine = BVIVEngine(risk_free_rate=0.05)
    
    now_ms = int(time.time() * 1000)
    near_exp = now_ms + (25 * 24 * 60 * 60 * 1000)
    next_exp = now_ms + (35 * 24 * 60 * 60 * 1000)
    
    # Mock data for both expirations
    options_info = {}
    orderbooks = {}
    
    for exp in [near_exp, next_exp]:
        exp_suffix = "NEAR" if exp == near_exp else "NEXT"
        options_info.update({
            f"BTC-P1-{exp_suffix}": {"deliveryTime": exp, "strikePrice": 60000, "optionsType": "Put", "symbol": f"BTC-P1-{exp_suffix}"},
            f"BTC-P2-{exp_suffix}": {"deliveryTime": exp, "strikePrice": 65000, "optionsType": "Put", "symbol": f"BTC-P2-{exp_suffix}"},
            f"BTC-C-ATM-{exp_suffix}": {"deliveryTime": exp, "strikePrice": 70000, "optionsType": "Call", "symbol": f"BTC-C-ATM-{exp_suffix}"},
            f"BTC-P-ATM-{exp_suffix}": {"deliveryTime": exp, "strikePrice": 70000, "optionsType": "Put", "symbol": f"BTC-P-ATM-{exp_suffix}"},
            f"BTC-C1-{exp_suffix}": {"deliveryTime": exp, "strikePrice": 75000, "optionsType": "Call", "symbol": f"BTC-C1-{exp_suffix}"},
            f"BTC-C2-{exp_suffix}": {"deliveryTime": exp, "strikePrice": 80000, "optionsType": "Call", "symbol": f"BTC-C2-{exp_suffix}"},
        })
        orderbooks.update({
            f"BTC-P1-{exp_suffix}": {"mid": 500},
            f"BTC-P2-{exp_suffix}": {"mid": 1000},
            f"BTC-C-ATM-{exp_suffix}": {"mid": 2000},
            f"BTC-P-ATM-{exp_suffix}": {"mid": 2050},
            f"BTC-C1-{exp_suffix}": {"mid": 1200},
            f"BTC-C2-{exp_suffix}": {"mid": 600},
        })
        
    bviv = engine.calculate_bviv(near_exp, next_exp, options_info, orderbooks)
    assert bviv is not None
    assert 20 < bviv < 100
    print(f"Calculated BVIV: {bviv}")

if __name__ == "__main__":
    test_variance_calculation()
    test_bviv_interpolation()
    print("Tests passed!")
