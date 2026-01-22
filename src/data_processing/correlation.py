"""
Correlation analysis module for MediAnalyze Pro
Computes and stores correlation coefficients between health metrics
"""

import logging
from typing import Dict, List, Optional, Tuple, Union
import pandas as pd
import numpy as np
from scipy.stats import pearsonr, spearmanr
from sqlalchemy.orm import Session

from ..database import get_session, crud

logger = logging.getLogger(__name__)


class CorrelationAnalyzer:
    """Analyzes correlations between health metrics"""
    
    def __init__(self, session: Optional[Session] = None):
        self.session = session
    
    def compute_pearson_correlation(
        self,
        x: Union[pd.Series, np.ndarray, List[float]],
        y: Union[pd.Series, np.ndarray, List[float]]
    ) -> Tuple[float, float, int]:
        """Compute Pearson correlation coefficient"""
        if isinstance(x, (pd.Series, pd.DataFrame)):
            x = x.values
        if isinstance(y, (pd.Series, pd.DataFrame)):
            y = y.values
        
        x = np.array(x, dtype=float)
        y = np.array(y, dtype=float)
        
        if len(x) != len(y):
            raise ValueError(f"Input arrays must have same length: {len(x)} vs {len(y)}")
        
        valid_mask = ~(np.isnan(x) | np.isnan(y))
        x_clean = x[valid_mask]
        y_clean = y[valid_mask]
        
        if len(x_clean) < 2:
            raise ValueError("Insufficient valid data points (need at least 2)")
        
        try:
            correlation, p_value = pearsonr(x_clean, y_clean)
            return float(correlation), float(p_value), len(x_clean)
        except Exception as e:
            logger.error(f"Error computing Pearson correlation: {e}")
            raise
    
    def compute_spearman_correlation(
        self,
        x: Union[pd.Series, np.ndarray, List[float]],
        y: Union[pd.Series, np.ndarray, List[float]]
    ) -> Tuple[float, float, int]:
        """Compute Spearman rank correlation coefficient"""
        if isinstance(x, (pd.Series, pd.DataFrame)):
            x = x.values
        if isinstance(y, (pd.Series, pd.DataFrame)):
            y = y.values
        
        x = np.array(x, dtype=float)
        y = np.array(y, dtype=float)
        
        if len(x) != len(y):
            raise ValueError(f"Input arrays must have same length: {len(x)} vs {len(y)}")
        
        valid_mask = ~(np.isnan(x) | np.isnan(y))
        x_clean = x[valid_mask]
        y_clean = y[valid_mask]
        
        if len(x_clean) < 2:
            raise ValueError("Insufficient valid data points (need at least 2)")
        
        try:
            correlation, p_value = spearmanr(x_clean, y_clean)
            return float(correlation), float(p_value), len(x_clean)
        except Exception as e:
            logger.error(f"Error computing Spearman correlation: {e}")
            raise
    
    def compute_correlation_matrix(
        self,
        data: pd.DataFrame,
        method: str = 'pearson',
        metrics: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """Compute correlation matrix for multiple metrics"""
        if metrics is None:
            numeric_cols = data.select_dtypes(include=[np.number]).columns.tolist()
            metrics = numeric_cols
        else:
            metrics = [m for m in metrics if m in data.columns]
        
        if len(metrics) < 2:
            raise ValueError("Need at least 2 metrics for correlation matrix")
        
        data_subset = data[metrics]
        correlation_matrix = data_subset.corr(method=method)
        return correlation_matrix
    
    def analyze_metric_pair(
        self,
        data: pd.DataFrame,
        metric1: str,
        metric2: str,
        method: str = 'pearson',
        store_in_db: bool = False
    ) -> Dict[str, any]:
        """Analyze correlation between two specific metrics"""
        if metric1 not in data.columns:
            raise ValueError(f"Metric '{metric1}' not found in data")
        if metric2 not in data.columns:
            raise ValueError(f"Metric '{metric2}' not found in data")
        
        x = data[metric1]
        y = data[metric2]
        
        if method.lower() == 'pearson':
            correlation, p_value, sample_size = self.compute_pearson_correlation(x, y)
        elif method.lower() == 'spearman':
            correlation, p_value, sample_size = self.compute_spearman_correlation(x, y)
        else:
            raise ValueError(f"Unknown correlation method: {method}")
        
        result = {
            'metric1': metric1,
            'metric2': metric2,
            'correlation': correlation,
            'p_value': p_value,
            'sample_size': sample_size,
            'method': method.lower()
        }
        
        if store_in_db:
            session = self.session or get_session()
            should_close = self.session is None
            
            try:
                crud.insert_correlation_result(
                    session=session,
                    metric1=metric1,
                    metric2=metric2,
                    correlation_value=correlation,
                    correlation_type=method.lower(),
                    sample_size=sample_size,
                    p_value=p_value
                )
                session.commit()
            except Exception as e:
                logger.error(f"Error storing correlation result: {e}")
                session.rollback()
            finally:
                if should_close:
                    session.close()
        
        return result
    
    def analyze_multiple_pairs(
        self,
        data: pd.DataFrame,
        metric_pairs: List[Tuple[str, str]],
        method: str = 'pearson',
        store_in_db: bool = False
    ) -> List[Dict[str, any]]:
        """Analyze correlations for multiple metric pairs"""
        results = []
        
        for metric1, metric2 in metric_pairs:
            try:
                result = self.analyze_metric_pair(
                    data, metric1, metric2, method, store_in_db
                )
                results.append(result)
            except Exception as e:
                logger.error(f"Error analyzing {metric1} vs {metric2}: {e}")
                results.append({
                    'metric1': metric1,
                    'metric2': metric2,
                    'error': str(e)
                })
        
        return results
    
    def get_correlation_summary(
        self,
        data: pd.DataFrame,
        metrics: Optional[List[str]] = None,
        method: str = 'pearson',
        min_correlation: float = 0.3
    ) -> pd.DataFrame:
        """Get summary of significant correlations"""
        corr_matrix = self.compute_correlation_matrix(data, method=method, metrics=metrics)
        
        summary_data = []
        
        for i, metric1 in enumerate(corr_matrix.columns):
            for j, metric2 in enumerate(corr_matrix.columns):
                if i < j:
                    correlation = corr_matrix.loc[metric1, metric2]
                    
                    if abs(correlation) >= min_correlation:
                        try:
                            x = data[metric1]
                            y = data[metric2]
                            
                            if method.lower() == 'pearson':
                                _, p_value, sample_size = self.compute_pearson_correlation(x, y)
                            else:
                                _, p_value, sample_size = self.compute_spearman_correlation(x, y)
                            
                            summary_data.append({
                                'metric1': metric1,
                                'metric2': metric2,
                                'correlation': correlation,
                                'p_value': p_value,
                                'sample_size': sample_size,
                                'abs_correlation': abs(correlation)
                            })
                        except Exception as e:
                            logger.debug(f"Error computing p-value for {metric1} vs {metric2}: {e}")
        
        if not summary_data:
            return pd.DataFrame()
        
        summary_df = pd.DataFrame(summary_data)
        summary_df = summary_df.sort_values('abs_correlation', ascending=False)
        return summary_df
