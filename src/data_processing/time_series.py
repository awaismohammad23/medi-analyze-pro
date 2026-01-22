"""
Time-series analysis module for MediAnalyze Pro
Provides time-series analysis functions for health metrics
"""

import logging
from typing import Dict, List, Optional, Tuple, Union
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class TimeSeriesAnalyzer:
    """Analyzes time-series health data"""
    
    @staticmethod
    def prepare_time_series(
        data: pd.DataFrame,
        time_column: str,
        value_column: str,
        patient_id_column: Optional[str] = None
    ) -> pd.DataFrame:
        """Prepare data for time-series analysis"""
        df = data.copy()
        
        if not pd.api.types.is_datetime64_any_dtype(df[time_column]):
            df[time_column] = pd.to_datetime(df[time_column])
        
        df = df.sort_values(time_column)
        
        if patient_id_column is None:
            df = df.set_index(time_column)
        
        return df
    
    @staticmethod
    def compute_trend(
        data: pd.Series,
        method: str = 'linear'
    ) -> Dict[str, float]:
        """Compute trend in time-series data"""
        if len(data) < 2:
            return {'slope': 0.0, 'intercept': 0.0, 'r_squared': 0.0}
        
        valid_data = data.dropna()
        
        if len(valid_data) < 2:
            return {'slope': 0.0, 'intercept': 0.0, 'r_squared': 0.0}
        
        if method == 'linear':
            x = np.arange(len(valid_data))
            y = valid_data.values
            
            n = len(x)
            sum_x = np.sum(x)
            sum_y = np.sum(y)
            sum_xy = np.sum(x * y)
            sum_x2 = np.sum(x ** 2)
            
            denominator = n * sum_x2 - sum_x ** 2
            if denominator == 0:
                slope = 0.0
                intercept = np.mean(y)
            else:
                slope = (n * sum_xy - sum_x * sum_y) / denominator
                intercept = (sum_y - slope * sum_x) / n
            
            y_pred = slope * x + intercept
            ss_res = np.sum((y - y_pred) ** 2)
            ss_tot = np.sum((y - np.mean(y)) ** 2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0
            
            return {
                'slope': float(slope),
                'intercept': float(intercept),
                'r_squared': float(r_squared),
                'mean': float(np.mean(y)),
                'std': float(np.std(y))
            }
        
        elif method == 'mean':
            changes = np.diff(valid_data.values)
            mean_change = np.mean(changes) if len(changes) > 0 else 0.0
            
            return {
                'mean_change': float(mean_change),
                'mean': float(np.mean(valid_data)),
                'std': float(np.std(valid_data))
            }
        
        else:
            raise ValueError(f"Unknown trend method: {method}")
    
    @staticmethod
    def detect_anomalies(
        data: pd.Series,
        method: str = 'zscore',
        threshold: float = 3.0
    ) -> Tuple[pd.Series, pd.Series]:
        """Detect anomalies in time-series data"""
        valid_data = data.dropna()
        
        if len(valid_data) < 3:
            return pd.Series([False] * len(data), index=data.index), pd.Series([], dtype=float)
        
        if method == 'zscore':
            mean = valid_data.mean()
            std = valid_data.std()
            
            if std == 0:
                return pd.Series([False] * len(data), index=data.index), pd.Series([], dtype=float)
            
            z_scores = np.abs((data - mean) / std)
            anomaly_mask = z_scores > threshold
        
        elif method == 'iqr':
            Q1 = valid_data.quantile(0.25)
            Q3 = valid_data.quantile(0.75)
            IQR = Q3 - Q1
            
            lower_bound = Q1 - threshold * IQR
            upper_bound = Q3 + threshold * IQR
            
            anomaly_mask = (data < lower_bound) | (data > upper_bound)
        
        else:
            raise ValueError(f"Unknown anomaly detection method: {method}")
        
        anomaly_values = data[anomaly_mask]
        return anomaly_mask, anomaly_values
    
    @staticmethod
    def compute_statistics(
        data: pd.Series,
        window_size: Optional[int] = None
    ) -> Dict[str, float]:
        """Compute rolling statistics for time-series"""
        valid_data = data.dropna()
        
        if len(valid_data) == 0:
            return {
                'mean': np.nan,
                'std': np.nan,
                'min': np.nan,
                'max': np.nan,
                'median': np.nan
            }
        
        if window_size is None:
            return {
                'mean': float(valid_data.mean()),
                'std': float(valid_data.std()),
                'min': float(valid_data.min()),
                'max': float(valid_data.max()),
                'median': float(valid_data.median()),
                'count': len(valid_data)
            }
        else:
            rolling_mean = valid_data.rolling(window=window_size, min_periods=1).mean()
            rolling_std = valid_data.rolling(window=window_size, min_periods=1).std()
            
            return {
                'rolling_mean': rolling_mean,
                'rolling_std': rolling_std,
                'overall_mean': float(valid_data.mean()),
                'overall_std': float(valid_data.std())
            }
    
    @staticmethod
    def resample_time_series(
        data: pd.Series,
        freq: str = 'D',
        method: str = 'mean'
    ) -> pd.Series:
        """Resample time-series data to different frequency"""
        if not isinstance(data.index, pd.DatetimeIndex):
            raise ValueError("Data must have DatetimeIndex for resampling")
        
        if method == 'mean':
            return data.resample(freq).mean()
        elif method == 'sum':
            return data.resample(freq).sum()
        elif method == 'max':
            return data.resample(freq).max()
        elif method == 'min':
            return data.resample(freq).min()
        elif method == 'median':
            return data.resample(freq).median()
        else:
            raise ValueError(f"Unknown aggregation method: {method}")
    
    @staticmethod
    def compute_rate_of_change(
        data: pd.Series,
        period: int = 1
    ) -> pd.Series:
        """Compute rate of change in time-series"""
        return data.pct_change(periods=period) * 100
    
    @staticmethod
    def analyze_patient_timeseries(
        data: pd.DataFrame,
        patient_id: int,
        time_column: str,
        value_column: str
    ) -> Dict[str, any]:
        """Analyze time-series for a specific patient"""
        patient_data = data[data.get('patient_id') == patient_id].copy()
        
        if len(patient_data) == 0:
            return {'error': f'No data found for patient {patient_id}'}
        
        patient_data[time_column] = pd.to_datetime(patient_data[time_column])
        patient_data = patient_data.sort_values(time_column)
        
        values = patient_data[value_column]
        
        stats = TimeSeriesAnalyzer.compute_statistics(values)
        trend = TimeSeriesAnalyzer.compute_trend(values)
        anomaly_mask, anomalies = TimeSeriesAnalyzer.detect_anomalies(values)
        
        return {
            'patient_id': patient_id,
            'metric': value_column,
            'data_points': len(values),
            'statistics': stats,
            'trend': trend,
            'anomalies_count': int(anomaly_mask.sum()),
            'anomalies': anomalies.tolist() if len(anomalies) > 0 else []
        }
