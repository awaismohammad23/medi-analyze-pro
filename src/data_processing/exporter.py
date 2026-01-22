"""
Data export module for MediAnalyze Pro
Exports data from database to various formats
"""

import logging
import os
from pathlib import Path
from typing import Optional, List
import pandas as pd

from .retriever import DataRetriever

logger = logging.getLogger(__name__)


class DataExporter:
    """
    Exports data from database to various file formats
    """
    
    def __init__(self, retriever: Optional[DataRetriever] = None):
        """
        Initialize data exporter
        
        Args:
            retriever: DataRetriever instance (if None, creates new one)
        """
        self.retriever = retriever or DataRetriever()
    
    def export_patients_to_csv(
        self,
        output_path: str,
        patient_ids: Optional[List[int]] = None,
        **filters
    ) -> bool:
        """
        Export patients to CSV file
        
        Args:
            output_path: Output file path
            patient_ids: Optional list of patient IDs to export
            **filters: Additional filters (see DataRetriever.get_patients)
        
        Returns:
            True if successful
        """
        try:
            logger.info(f"Exporting patients to {output_path}")
            
            # Get patients as DataFrame
            df = self.retriever.get_patients(
                patient_ids=patient_ids,
                as_dataframe=True,
                **filters
            )
            
            if df.empty:
                logger.warning("No patients to export")
                return False
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
            
            # Export to CSV
            df.to_csv(output_path, index=False)
            
            logger.info(f"Exported {len(df)} patients to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting patients: {e}")
            return False
    
    def export_health_metrics_to_csv(
        self,
        output_path: str,
        patient_ids: Optional[List[int]] = None,
        **filters
    ) -> bool:
        """
        Export health metrics to CSV file
        
        Args:
            output_path: Output file path
            patient_ids: Optional list of patient IDs to export
            **filters: Additional filters (see DataRetriever.get_health_metrics)
        
        Returns:
            True if successful
        """
        try:
            logger.info(f"Exporting health metrics to {output_path}")
            
            # Get health metrics as DataFrame
            df = self.retriever.get_health_metrics(
                patient_ids=patient_ids,
                as_dataframe=True,
                **filters
            )
            
            if df.empty:
                logger.warning("No health metrics to export")
                return False
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
            
            # Export to CSV
            df.to_csv(output_path, index=False)
            
            logger.info(f"Exported {len(df)} health metrics to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting health metrics: {e}")
            return False
    
    def export_combined_to_csv(
        self,
        output_path: str,
        patient_ids: Optional[List[int]] = None,
        **filters
    ) -> bool:
        """
        Export combined patient and health metrics data to CSV
        
        Args:
            output_path: Output file path
            patient_ids: Optional list of patient IDs to export
            **filters: Additional filters
        
        Returns:
            True if successful
        """
        try:
            logger.info(f"Exporting combined data to {output_path}")
            
            # Get patients
            patients_df = self.retriever.get_patients(
                patient_ids=patient_ids,
                as_dataframe=True,
                **{k: v for k, v in filters.items() if k not in ['start_date', 'end_date']}
            )
            
            # Get health metrics
            metrics_df = self.retriever.get_health_metrics(
                patient_ids=patient_ids,
                as_dataframe=True,
                **{k: v for k, v in filters.items() if k not in ['gender', 'min_age', 'max_age']}
            )
            
            if patients_df.empty and metrics_df.empty:
                logger.warning("No data to export")
                return False
            
            # Merge on patient_id
            if not patients_df.empty and not metrics_df.empty:
                combined_df = pd.merge(
                    patients_df,
                    metrics_df,
                    on='patient_id',
                    how='outer',
                    suffixes=('_patient', '_metric')
                )
            elif not patients_df.empty:
                combined_df = patients_df
            else:
                combined_df = metrics_df
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
            
            # Export to CSV
            combined_df.to_csv(output_path, index=False)
            
            logger.info(f"Exported combined data ({len(combined_df)} rows) to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting combined data: {e}")
            return False
