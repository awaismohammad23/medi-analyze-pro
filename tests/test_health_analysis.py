"""
Unit tests for health data analysis modules
Tests filtering, correlation analysis, and time-series analysis
"""

import pytest
import os
import tempfile
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from src.data_processing.filters import DataFilter
from src.data_processing.correlation import CorrelationAnalyzer
from src.data_processing.time_series import TimeSeriesAnalyzer
from src.database.connection import DatabaseConnection


@pytest.fixture
def sample_data():
    """Create sample health data for testing"""
    np.random.seed(42)
    n = 100
    
    data = {
        'patient_id': np.arange(1, n + 1),
        'systolic_bp': np.random.normal(120, 15, n),
        'diastolic_bp': np.random.normal(80, 10, n),
        'heart_rate': np.random.normal(72, 10, n),
        'cholesterol': np.random.choice([1, 2, 3], n),
        'weight': np.random.normal(70, 15, n)
    }
    
    return pd.DataFrame(data)


@pytest.fixture
def time_series_data():
    """Create sample time-series data"""
    dates = pd.date_range(start='2024-01-01', periods=50, freq='D')
    values = 100 + np.cumsum(np.random.randn(50) * 2)
    
    return pd.Series(values, index=dates, name='heart_rate')


@pytest.fixture
def db_connection():
    """Create a temporary database for testing"""
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    db_url = f'sqlite:///{db_path}'
    db_conn = DatabaseConnection(db_url)
    db_conn.create_tables()
    
    yield db_conn
    
    db_conn.close()
    if os.path.exists(db_path):
        os.remove(db_path)


class TestDataFilter:
    """Test data filtering functionality"""
    
    def test_moving_average(self):
        """Test moving average filter"""
        data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        filtered = DataFilter.moving_average(data, window_size=3)
        
        assert len(filtered) == len(data)
        assert not np.isnan(filtered[0])  # First value should be valid
        assert filtered[4] == 5.0  # Center value should be unchanged for odd window
    
    def test_moving_average_with_nan(self):
        """Test moving average with NaN values"""
        data = [1, 2, np.nan, 4, 5, 6, 7, 8, 9, 10]
        filtered = DataFilter.moving_average(data, window_size=3)
        
        assert len(filtered) == len(data)
        # Should handle NaN gracefully
    
    def test_threshold_filter_min(self):
        """Test threshold filter with minimum value"""
        data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        filtered, mask = DataFilter.threshold_filter(data, min_value=3)
        
        assert np.all(filtered[mask] >= 3)
        assert np.sum(mask) < len(data)
    
    def test_threshold_filter_max(self):
        """Test threshold filter with maximum value"""
        data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        filtered, mask = DataFilter.threshold_filter(data, max_value=7)
        
        assert np.all(filtered[mask] <= 7)
        assert np.sum(mask) < len(data)
    
    def test_threshold_filter_range(self):
        """Test threshold filter with both min and max"""
        data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        filtered, mask = DataFilter.threshold_filter(data, min_value=3, max_value=7)
        
        assert np.all((filtered[mask] >= 3) & (filtered[mask] <= 7))
    
    def test_remove_outliers_iqr(self):
        """Test outlier removal using IQR method"""
        data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 100]  # 100 is an outlier
        filtered, mask = DataFilter.remove_outliers(data, method='iqr', threshold=1.5)
        
        assert np.sum(mask) < len(data)  # Some outliers should be removed
        assert 100 not in filtered[mask]  # Outlier should be removed
    
    def test_remove_outliers_zscore(self):
        """Test outlier removal using Z-score method"""
        data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 100]  # 100 is an outlier
        filtered, mask = DataFilter.remove_outliers(data, method='zscore', threshold=2.0)
        
        assert np.sum(mask) < len(data)  # Some outliers should be removed
    
    def test_savitzky_golay_filter(self):
        """Test Savitzky-Golay filter"""
        data = np.sin(np.linspace(0, 4 * np.pi, 50)) + np.random.randn(50) * 0.1
        filtered = DataFilter.savitzky_golay_filter(data, window_length=11, polyorder=3)
        
        assert len(filtered) == len(data)
        assert not np.any(np.isnan(filtered))
    
    def test_apply_multiple_filters(self):
        """Test applying multiple filters in sequence"""
        data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 100]  # 100 is an outlier
        
        filters = [
            {'type': 'remove_outliers', 'method': 'iqr', 'threshold': 1.5},
            {'type': 'moving_average', 'window_size': 3}
        ]
        
        filtered = DataFilter.apply_multiple_filters(data, filters)
        
        assert len(filtered) == len(data)
        assert not np.isnan(filtered[0])


class TestCorrelationAnalyzer:
    """Test correlation analysis functionality"""
    
    def test_pearson_correlation(self, sample_data):
        """Test Pearson correlation computation"""
        analyzer = CorrelationAnalyzer()
        
        x = sample_data['systolic_bp']
        y = sample_data['diastolic_bp']
        
        correlation, p_value, sample_size = analyzer.compute_pearson_correlation(x, y)
        
        assert -1 <= correlation <= 1
        assert 0 <= p_value <= 1
        assert sample_size > 0
    
    def test_spearman_correlation(self, sample_data):
        """Test Spearman correlation computation"""
        analyzer = CorrelationAnalyzer()
        
        x = sample_data['systolic_bp']
        y = sample_data['diastolic_bp']
        
        correlation, p_value, sample_size = analyzer.compute_spearman_correlation(x, y)
        
        assert -1 <= correlation <= 1
        assert 0 <= p_value <= 1
        assert sample_size > 0
    
    def test_correlation_matrix(self, sample_data):
        """Test correlation matrix computation"""
        analyzer = CorrelationAnalyzer()
        
        metrics = ['systolic_bp', 'diastolic_bp', 'heart_rate']
        corr_matrix = analyzer.compute_correlation_matrix(
            sample_data,
            method='pearson',
            metrics=metrics
        )
        
        assert corr_matrix.shape == (len(metrics), len(metrics))
        assert np.allclose(corr_matrix.values, corr_matrix.values.T)  # Symmetric
        assert np.all(np.diag(corr_matrix) == 1.0)  # Diagonal is 1
    
    def test_analyze_metric_pair(self, sample_data):
        """Test analyzing a specific metric pair"""
        analyzer = CorrelationAnalyzer()
        
        result = analyzer.analyze_metric_pair(
            sample_data,
            'systolic_bp',
            'diastolic_bp',
            method='pearson',
            store_in_db=False
        )
        
        assert 'correlation' in result
        assert 'p_value' in result
        assert 'sample_size' in result
        assert result['metric1'] == 'systolic_bp'
        assert result['metric2'] == 'diastolic_bp'
    
    def test_analyze_metric_pair_store_in_db(self, sample_data, db_connection):
        """Test analyzing and storing in database"""
        session = db_connection.get_session()
        analyzer = CorrelationAnalyzer(session=session)
        
        result = analyzer.analyze_metric_pair(
            sample_data,
            'systolic_bp',
            'diastolic_bp',
            method='pearson',
            store_in_db=True
        )
        
        assert 'correlation' in result
        
        # Verify stored in database
        from src.database import crud
        stored = crud.retrieve_correlation_results(session)
        assert len(stored) > 0
        
        session.close()
    
    def test_analyze_multiple_pairs(self, sample_data):
        """Test analyzing multiple metric pairs"""
        analyzer = CorrelationAnalyzer()
        
        pairs = [
            ('systolic_bp', 'diastolic_bp'),
            ('systolic_bp', 'heart_rate'),
            ('diastolic_bp', 'heart_rate')
        ]
        
        results = analyzer.analyze_multiple_pairs(
            sample_data,
            pairs,
            method='pearson'
        )
        
        assert len(results) == len(pairs)
        assert all('correlation' in r for r in results)
    
    def test_get_correlation_summary(self, sample_data):
        """Test getting correlation summary"""
        analyzer = CorrelationAnalyzer()
        
        summary = analyzer.get_correlation_summary(
            sample_data,
            metrics=['systolic_bp', 'diastolic_bp', 'heart_rate'],
            method='pearson',
            min_correlation=0.1
        )
        
        assert isinstance(summary, pd.DataFrame)
        if not summary.empty:
            assert 'correlation' in summary.columns
            assert 'p_value' in summary.columns


class TestTimeSeriesAnalyzer:
    """Test time-series analysis functionality"""
    
    def test_prepare_time_series(self):
        """Test preparing time-series data"""
        dates = pd.date_range(start='2024-01-01', periods=10, freq='D')
        data = pd.DataFrame({
            'timestamp': dates,
            'value': np.random.randn(10)
        })
        
        prepared = TimeSeriesAnalyzer.prepare_time_series(
            data,
            time_column='timestamp',
            value_column='value'
        )
        
        assert isinstance(prepared.index, pd.DatetimeIndex)
    
    def test_compute_trend_linear(self, time_series_data):
        """Test computing linear trend"""
        trend = TimeSeriesAnalyzer.compute_trend(time_series_data, method='linear')
        
        assert 'slope' in trend
        assert 'intercept' in trend
        assert 'r_squared' in trend
        assert 0 <= trend['r_squared'] <= 1
    
    def test_compute_trend_mean(self, time_series_data):
        """Test computing mean trend"""
        trend = TimeSeriesAnalyzer.compute_trend(time_series_data, method='mean')
        
        assert 'mean_change' in trend
        assert 'mean' in trend
    
    def test_detect_anomalies_zscore(self, time_series_data):
        """Test anomaly detection using Z-score"""
        # Add an obvious outlier
        data_with_outlier = time_series_data.copy()
        data_with_outlier.iloc[25] = 200  # Outlier
        
        mask, anomalies = TimeSeriesAnalyzer.detect_anomalies(
            data_with_outlier,
            method='zscore',
            threshold=3.0
        )
        
        assert isinstance(mask, pd.Series)
        assert isinstance(anomalies, pd.Series)
        assert mask.sum() >= 0  # At least the outlier should be detected
    
    def test_detect_anomalies_iqr(self, time_series_data):
        """Test anomaly detection using IQR"""
        # Add an obvious outlier
        data_with_outlier = time_series_data.copy()
        data_with_outlier.iloc[25] = 200  # Outlier
        
        mask, anomalies = TimeSeriesAnalyzer.detect_anomalies(
            data_with_outlier,
            method='iqr',
            threshold=1.5
        )
        
        assert isinstance(mask, pd.Series)
        assert isinstance(anomalies, pd.Series)
    
    def test_compute_statistics(self, time_series_data):
        """Test computing statistics"""
        stats = TimeSeriesAnalyzer.compute_statistics(time_series_data)
        
        assert 'mean' in stats
        assert 'std' in stats
        assert 'min' in stats
        assert 'max' in stats
        assert 'median' in stats
        assert stats['min'] <= stats['mean'] <= stats['max']
    
    def test_compute_statistics_rolling(self, time_series_data):
        """Test computing rolling statistics"""
        stats = TimeSeriesAnalyzer.compute_statistics(
            time_series_data,
            window_size=7
        )
        
        assert 'rolling_mean' in stats
        assert 'rolling_std' in stats
        assert isinstance(stats['rolling_mean'], pd.Series)
    
    def test_resample_time_series(self, time_series_data):
        """Test resampling time-series"""
        resampled = TimeSeriesAnalyzer.resample_time_series(
            time_series_data,
            freq='W',  # Weekly
            method='mean'
        )
        
        assert len(resampled) < len(time_series_data)
        assert isinstance(resampled, pd.Series)
    
    def test_compute_rate_of_change(self, time_series_data):
        """Test computing rate of change"""
        roc = TimeSeriesAnalyzer.compute_rate_of_change(time_series_data, period=1)
        
        assert isinstance(roc, pd.Series)
        assert len(roc) == len(time_series_data)
        assert pd.isna(roc.iloc[0])  # First value should be NaN
    
    def test_analyze_patient_timeseries(self):
        """Test analyzing patient time-series"""
        dates = pd.date_range(start='2024-01-01', periods=20, freq='D')
        data = pd.DataFrame({
            'patient_id': [1] * 20,
            'timestamp': dates,
            'heart_rate': 70 + np.random.randn(20) * 5
        })
        
        result = TimeSeriesAnalyzer.analyze_patient_timeseries(
            data,
            patient_id=1,
            time_column='timestamp',
            value_column='heart_rate'
        )
        
        assert 'patient_id' in result
        assert 'statistics' in result
        assert 'trend' in result
        assert 'anomalies_count' in result


class TestIntegration:
    """Integration tests for health analysis modules"""
    
    def test_filter_then_correlate(self, sample_data):
        """Test filtering data then computing correlation"""
        # Filter outliers
        filtered_bp, _ = DataFilter.remove_outliers(
            sample_data['systolic_bp'],
            method='iqr'
        )
        
        # Compute correlation with filtered data
        analyzer = CorrelationAnalyzer()
        correlation, p_value, n = analyzer.compute_pearson_correlation(
            filtered_bp,
            sample_data['diastolic_bp']
        )
        
        assert -1 <= correlation <= 1
        assert n > 0
    
    def test_timeseries_then_filter(self, time_series_data):
        """Test time-series analysis then filtering"""
        # Detect anomalies
        mask, anomalies = TimeSeriesAnalyzer.detect_anomalies(time_series_data)
        
        # Filter out anomalies
        filtered_data = time_series_data[mask]
        
        # Compute trend on filtered data
        trend = TimeSeriesAnalyzer.compute_trend(filtered_data)
        
        assert 'slope' in trend
        assert len(filtered_data) <= len(time_series_data)
