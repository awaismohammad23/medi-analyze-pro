"""
Data filtering module for MediAnalyze Pro
Provides various filtering techniques for health data analysis
"""

import logging
from typing import List, Optional, Tuple, Union
import pandas as pd
import numpy as np
from scipy.signal import savgol_filter

logger = logging.getLogger(__name__)


class DataFilter:
    """
    Provides various filtering methods for health data
    """
    
    @staticmethod
    def moving_average(
        data: Union[pd.Series, np.ndarray, List[float]],
        window_size: int = 5,
        center: bool = True
    ) -> np.ndarray:
        """Apply moving average filter to smooth data"""
        if window_size < 1:
            raise ValueError("Window size must be >= 1")
        
        if isinstance(data, (pd.Series, pd.DataFrame)):
            data = data.values
        
        data = np.array(data, dtype=float)
        
        if np.any(np.isnan(data)):
            logger.warning("Input data contains NaN values, they will be preserved")
        
        if center and window_size % 2 == 0:
            logger.warning(f"Window size {window_size} is even, adding 1 for centered window")
            window_size += 1
        
        if center:
            filtered = pd.Series(data).rolling(
                window=window_size,
                center=True,
                min_periods=1
            ).mean().values
        else:
            filtered = pd.Series(data).rolling(
                window=window_size,
                min_periods=1
            ).mean().values
        
        return filtered
    
    @staticmethod
    def threshold_filter(
        data: Union[pd.Series, np.ndarray, List[float]],
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        replace_with: Union[str, float] = 'nan'
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Filter data based on threshold values"""
        if isinstance(data, (pd.Series, pd.DataFrame)):
            data = data.values
        
        data = np.array(data, dtype=float)
        mask = np.ones(len(data), dtype=bool)
        
        if min_value is not None:
            mask = mask & (data >= min_value)
        
        if max_value is not None:
            mask = mask & (data <= max_value)
        
        filtered = data.copy()
        
        if not np.all(mask):
            if replace_with == 'nan':
                replacement = np.nan
            elif replace_with == 'min' and min_value is not None:
                replacement = min_value
            elif replace_with == 'max' and max_value is not None:
                replacement = max_value
            elif isinstance(replace_with, (int, float)):
                replacement = replace_with
            else:
                replacement = np.nan
            
            filtered[~mask] = replacement
        
        return filtered, mask
    
    @staticmethod
    def remove_outliers(
        data: Union[pd.Series, np.ndarray, List[float]],
        method: str = 'iqr',
        threshold: float = 1.5,
        replace_with: Union[str, float] = 'nan'
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Remove outliers from data using various methods"""
        if isinstance(data, (pd.Series, pd.DataFrame)):
            data = data.values
        
        data = np.array(data, dtype=float)
        valid_mask = ~np.isnan(data)
        valid_data = data[valid_mask]
        
        if len(valid_data) == 0:
            logger.warning("No valid data points for outlier detection")
            return data, np.ones(len(data), dtype=bool)
        
        if method == 'iqr':
            Q1 = np.percentile(valid_data, 25)
            Q3 = np.percentile(valid_data, 75)
            IQR = Q3 - Q1
            lower_bound = Q1 - threshold * IQR
            upper_bound = Q3 + threshold * IQR
            outlier_mask = (data >= lower_bound) & (data <= upper_bound)
        elif method == 'zscore':
            mean = np.mean(valid_data)
            std = np.std(valid_data)
            if std == 0:
                logger.warning("Standard deviation is 0, cannot use Z-score method")
                return data, np.ones(len(data), dtype=bool)
            z_scores = np.abs((data - mean) / std)
            outlier_mask = z_scores <= threshold
        elif method == 'modified_zscore':
            median = np.median(valid_data)
            mad = np.median(np.abs(valid_data - median))
            if mad == 0:
                logger.warning("MAD is 0, cannot use modified Z-score method")
                return data, np.ones(len(data), dtype=bool)
            modified_z_scores = 0.6745 * (data - median) / mad
            outlier_mask = np.abs(modified_z_scores) <= threshold
        else:
            raise ValueError(f"Unknown outlier detection method: {method}")
        
        final_mask = valid_mask & outlier_mask
        filtered = data.copy()
        
        if not np.all(final_mask):
            if replace_with == 'nan':
                replacement = np.nan
            elif replace_with == 'mean':
                replacement = np.mean(valid_data)
            elif replace_with == 'median':
                replacement = np.median(valid_data)
            elif isinstance(replace_with, (int, float)):
                replacement = replace_with
            else:
                replacement = np.nan
            
            filtered[~final_mask] = replacement
        
        return filtered, final_mask
    
    @staticmethod
    def savitzky_golay_filter(
        data: Union[pd.Series, np.ndarray, List[float]],
        window_length: int = 11,
        polyorder: int = 3
    ) -> np.ndarray:
        """Apply Savitzky-Golay filter for smoothing"""
        if isinstance(data, (pd.Series, pd.DataFrame)):
            data = data.values
        
        data = np.array(data, dtype=float)
        
        if len(data) < window_length:
            logger.warning(f"Data length ({len(data)}) is less than window length ({window_length})")
            return data
        
        if window_length % 2 == 0:
            logger.warning(f"Window length {window_length} is even, adding 1")
            window_length += 1
        
        if polyorder >= window_length:
            raise ValueError("Polynomial order must be less than window length")
        
        try:
            filtered = savgol_filter(data, window_length, polyorder)
            return filtered
        except Exception as e:
            logger.error(f"Error applying Savitzky-Golay filter: {e}")
            return data
    
    @staticmethod
    def apply_multiple_filters(
        data: Union[pd.Series, np.ndarray, List[float]],
        filters: List[dict]
    ) -> np.ndarray:
        """Apply multiple filters in sequence"""
        filtered = data
        
        for i, filter_config in enumerate(filters):
            filter_type = filter_config.pop('type', None)
            
            if filter_type == 'moving_average':
                filtered = DataFilter.moving_average(filtered, **filter_config)
            elif filter_type == 'threshold':
                filtered, _ = DataFilter.threshold_filter(filtered, **filter_config)
            elif filter_type == 'remove_outliers':
                filtered, _ = DataFilter.remove_outliers(filtered, **filter_config)
            elif filter_type == 'savitzky_golay':
                filtered = DataFilter.savitzky_golay_filter(filtered, **filter_config)
            else:
                raise ValueError(f"Unknown filter type: {filter_type}")
        
        return filtered
