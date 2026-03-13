import math
import time
from typing import Dict, List, Optional, Tuple

class BVIVEngine:
    """
    Core mathematical engine for calculating BVIV index.
    Decoupled from network I/O.
    """
    
    def __init__(self, risk_free_rate: float = 0.05):
        self.risk_free_rate = risk_free_rate

    def set_risk_free_rate(self, rate: float):
        self.risk_free_rate = rate

    def calculate_variance(self, 
                           expiration_ms: int, 
                           options_info: Dict[str, Dict], 
                           orderbooks: Dict[str, Dict]) -> Optional[float]:
        """Calculate variance for a specific expiration using VIX formula."""
        now_ms = int(time.time() * 1000)
        T = (expiration_ms - now_ms) / (365 * 24 * 60 * 60 * 1000)
        if T <= 0: return None
        
        # 1. Gather all options for this expiration that have valid prices
        valid_options_by_strike = {} # strike -> {'C': mid, 'P': mid}
        
        for s, info in options_info.items():
            if int(info['deliveryTime']) == expiration_ms:
                mid = orderbooks.get(s, {}).get('mid')
                if mid and mid > 0:
                    strike = float(info['strikePrice'])
                    opt_type = 'C' if info['optionsType'] == 'Call' else 'P'
                    if strike not in valid_options_by_strike:
                        valid_options_by_strike[strike] = {}
                    valid_options_by_strike[strike][opt_type] = mid
        
        if not valid_options_by_strike: return None
        
        # 2. Derive Forward Price (F)
        strikes = sorted(valid_options_by_strike.keys())
        min_diff = float('inf')
        F = 0
        
        for K in strikes:
            prices = valid_options_by_strike[K]
            if 'C' in prices and 'P' in prices:
                diff = abs(prices['C'] - prices['P'])
                if diff < min_diff:
                    min_diff = diff
                    F = K + math.exp(self.risk_free_rate * T) * (prices['C'] - prices['P'])
        
        if F == 0: return None
        
        # K0 is the strike price equal to or immediately below F
        K0_candidates = [k for k in strikes if k <= F]
        K0 = max(K0_candidates) if K0_candidates else strikes[0]
        
        # 3. Compute Sum over OTM options
        total_sum = 0
        otm_strikes = []
        q_prices = {} # strike -> Q(K)
        
        for K in strikes:
            prices = valid_options_by_strike[K]
            mid_q = None
            if K < K0:
                mid_q = prices.get('P') # OTM Put
            elif K > K0:
                mid_q = prices.get('C') # OTM Call
            else: # K == K0
                if 'C' in prices and 'P' in prices:
                    mid_q = (prices['C'] + prices['P']) / 2
            
            if mid_q is not None:
                otm_strikes.append(K)
                q_prices[K] = mid_q
        
        if len(otm_strikes) < 2:
            return None
            
        # ΔK calculation
        for i, K in enumerate(otm_strikes):
            if i == 0:
                dk = otm_strikes[1] - otm_strikes[0]
            elif i == len(otm_strikes) - 1:
                dk = otm_strikes[-1] - otm_strikes[-2]
            else:
                dk = (otm_strikes[i+1] - otm_strikes[i-1]) / 2
            
            total_sum += (dk / (K**2)) * math.exp(self.risk_free_rate * T) * q_prices[K]
            
        variance = (2/T) * total_sum - (1/T) * ((F/K0 - 1)**2)
        return variance

    def calculate_bviv(self, 
                       near_exp: int, 
                       next_exp: int, 
                       options_info: Dict[str, Dict], 
                       orderbooks: Dict[str, Dict]) -> Optional[float]:
        """Interpolate Near-term and Next-term variances to get 30-day BVIV."""
        now_ms = int(time.time() * 1000)
        T1 = (near_exp - now_ms) / (365 * 24 * 60 * 60 * 1000)
        T2 = (next_exp - now_ms) / (365 * 24 * 60 * 60 * 1000)
        T30 = 30 / 365
        
        sigma1_sq = self.calculate_variance(near_exp, options_info, orderbooks)
        sigma2_sq = self.calculate_variance(next_exp, options_info, orderbooks)
        
        if sigma1_sq is None or sigma2_sq is None:
            return None
        
        # Interpolation weight
        w = (T2 - T30) / (T2 - T1)
        sigma_30_sq = (T1 * sigma1_sq * w + T2 * sigma2_sq * (1 - w)) / T30
        
        if sigma_30_sq < 0: return 0
        bviv = math.sqrt(sigma_30_sq) * 100
        return bviv
