"""
VayuDrishti Data Sanitization & Statistical Outlier Filtering Engine
Implements Tukey IQR fences, Modified Z-scores (MAD), and Winsorization.
"""
import numpy as np
import pandas as pd
from typing import List, Dict, Tuple

class DataSanitizer:
    @staticmethod
    def filter_outliers_tukey(prices: List[float], k: float = 1.5) -> Tuple[List[float], List[bool], Dict[str, float]]:
        """
        Tukey's Fences for Outlier Detection
        Lower Bound = Q1 - k * IQR
        Upper Bound = Q3 + k * IQR
        """
        if len(prices) < 4:
            return prices, [False] * len(prices), {"q1": 0, "q3": 0, "lower": 0, "upper": 0}
            
        arr = np.array(prices, dtype=float)
        q1 = np.percentile(arr, 25)
        q3 = np.percentile(arr, 75)
        iqr = q3 - q1
        
        lower_bound = max(500.0, q1 - (k * iqr))  # Minimum plausible domestic airfare in INR
        upper_bound = q3 + (k * iqr)
        
        is_outlier = (arr < lower_bound) | (arr > upper_bound)
        clean_prices = arr[~is_outlier].tolist()
        
        stats = {
            "q1": round(float(q1), 2),
            "q3": round(float(q3), 2),
            "iqr": round(float(iqr), 2),
            "lower_bound": round(float(lower_bound), 2),
            "upper_bound": round(float(upper_bound), 2),
            "outlier_count": int(np.sum(is_outlier))
        }
        
        return clean_prices, is_outlier.tolist(), stats

    @staticmethod
    def winsorize_prices(prices: List[float], limits: Tuple[float, float] = (0.01, 0.01)) -> List[float]:
        """
        Winsorization: Replaces extreme values at upper and lower percentiles with threshold values.
        """
        if len(prices) < 10:
            return prices
            
        arr = np.array(prices, dtype=float)
        low_p = np.percentile(arr, limits[0] * 100)
        high_p = np.percentile(arr, (1.0 - limits[1]) * 100)
        
        winsorized = np.clip(arr, low_p, high_p)
        return winsorized.tolist()

    @staticmethod
    def calculate_modified_z_scores(prices: List[float]) -> List[float]:
        """
        Modified Z-score using Median Absolute Deviation (MAD)
        M_i = 0.6745 * (x_i - median) / MAD
        """
        arr = np.array(prices, dtype=float)
        med = np.median(arr)
        mad = np.median(np.abs(arr - med))
        
        if mad == 0:
            return [0.0] * len(prices)
            
        z_scores = 0.6745 * (arr - med) / mad
        return [round(float(z), 2) for z in z_scores]
