"""
Data import module for MediAnalyze Pro
Handles bulk import of CSV data into the database
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import pandas as pd
from sqlalchemy.orm import Session

from ..database import get_session, crud
from .csv_loader import CSVLoader
from .validator import DataValidator

logger = logging.getLogger(__name__)


class DataImporter:
    """
    Imports CSV data into the database with duplicate handling and batch processing
    """
    
    def __init__(
        self,
        session: Optional[Session] = None,
        batch_size: int = 1000,
        handle_duplicates: str = 'skip'  # 'skip', 'update', 'error'
    ):
        """
        Initialize data importer
        
        Args:
            session: Database session (if None, creates new session)
            batch_size: Number of records to process in each batch
            handle_duplicates: How to handle duplicate records
                - 'skip': Skip duplicate records
                - 'update': Update existing records
                - 'error': Raise error on duplicates
        """
        self.session = session
        self.batch_size = batch_size
        self.handle_duplicates = handle_duplicates
        self.validator = DataValidator()
        self.csv_loader = CSVLoader()
    
    def import_from_csv(
        self,
        csv_file_path: str,
        create_patients: bool = True,
        create_health_metrics: bool = True,
        progress_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Import data from CSV file into database
        
        Args:
            csv_file_path: Path to CSV file
            create_patients: Whether to create patient records
            create_health_metrics: Whether to create health metric records
            progress_callback: Optional callback function(processed, total, message)
        
        Returns:
            Dictionary with import statistics
        """
        stats = {
            'total_rows': 0,
            'patients_created': 0,
            'patients_skipped': 0,
            'health_metrics_created': 0,
            'health_metrics_skipped': 0,
            'errors': [],
            'warnings': []
        }
        
        # Get or create session
        session = self.session or get_session()
        should_close_session = self.session is None
        
        try:
            # Load and validate CSV
            logger.info(f"Loading CSV file: {csv_file_path}")
            df, validation_errors = self.csv_loader.load_and_validate(
                csv_file_path,
                strict_validation=False
            )
            
            if validation_errors:
                stats['warnings'].extend(validation_errors[:10])  # Limit warnings
                logger.warning(f"Found {len(validation_errors)} validation warnings")
            
            stats['total_rows'] = len(df)
            
            if df.empty:
                logger.warning("DataFrame is empty after loading")
                return stats
            
            # Process in batches
            total_batches = (len(df) + self.batch_size - 1) // self.batch_size
            
            for batch_num in range(total_batches):
                start_idx = batch_num * self.batch_size
                end_idx = min(start_idx + self.batch_size, len(df))
                batch_df = df.iloc[start_idx:end_idx]
                
                if progress_callback:
                    progress_callback(
                        start_idx,
                        len(df),
                        f"Processing batch {batch_num + 1}/{total_batches}"
                    )
                
                # Process batch
                batch_stats = self._process_batch(
                    session,
                    batch_df,
                    create_patients,
                    create_health_metrics
                )
                
                # Update statistics
                stats['patients_created'] += batch_stats['patients_created']
                stats['patients_skipped'] += batch_stats['patients_skipped']
                stats['health_metrics_created'] += batch_stats['health_metrics_created']
                stats['health_metrics_skipped'] += batch_stats['health_metrics_skipped']
                stats['errors'].extend(batch_stats['errors'])
                
                # Commit batch
                session.commit()
                logger.debug(f"Committed batch {batch_num + 1}/{total_batches}")
            
            logger.info(
                f"Import complete: {stats['patients_created']} patients, "
                f"{stats['health_metrics_created']} health metrics"
            )
            
            return stats
            
        except Exception as e:
            logger.error(f"Error during import: {e}", exc_info=True)
            session.rollback()
            stats['errors'].append(str(e))
            raise
        finally:
            if should_close_session:
                session.close()
    
    def _process_batch(
        self,
        session: Session,
        batch_df: pd.DataFrame,
        create_patients: bool,
        create_health_metrics: bool
    ) -> Dict[str, Any]:
        """
        Process a batch of records
        
        Args:
            session: Database session
            batch_df: DataFrame batch to process
            create_patients: Whether to create patients
            create_health_metrics: Whether to create health metrics
        
        Returns:
            Dictionary with batch statistics
        """
        batch_stats = {
            'patients_created': 0,
            'patients_skipped': 0,
            'health_metrics_created': 0,
            'health_metrics_skipped': 0,
            'errors': []
        }
        
        # Create patient mapping (to avoid duplicates within batch)
        patient_cache = {}
        
        for idx, row in batch_df.iterrows():
            try:
                # Extract patient data
                patient_data = self._extract_patient_data(row)
                
                # Get or create patient
                patient = None
                if create_patients:
                    patient = self._get_or_create_patient(
                        session,
                        patient_data,
                        patient_cache,
                        batch_stats
                    )
                
                # Create health metrics
                if create_health_metrics and patient:
                    health_metric = self._create_health_metric(session, row, patient.patient_id)
                    if health_metric:
                        batch_stats['health_metrics_created'] += 1
                    else:
                        batch_stats['health_metrics_skipped'] += 1
                
            except Exception as e:
                error_msg = f"Error processing row {idx}: {e}"
                logger.error(error_msg)
                batch_stats['errors'].append(error_msg)
        
        return batch_stats
    
    def _extract_patient_data(self, row: pd.Series) -> Dict[str, Any]:
        """
        Extract patient data from row
        
        Args:
            row: DataFrame row
        
        Returns:
            Dictionary with patient data
        """
        return {
            'age': int(row.get('age', 0)) if pd.notna(row.get('age')) else None,
            'gender': int(row.get('gender', 0)) if pd.notna(row.get('gender')) else None,
            'height': float(row.get('height', 0)) if pd.notna(row.get('height')) else None,
            'weight': float(row.get('weight', 0)) if pd.notna(row.get('weight')) else None,
            'name': row.get('name') if pd.notna(row.get('name')) else None
        }
    
    def _get_or_create_patient(
        self,
        session: Session,
        patient_data: Dict[str, Any],
        patient_cache: Dict[Tuple, Any],
        stats: Dict[str, Any]
    ) -> Optional[Any]:
        """
        Get existing patient or create new one
        
        Args:
            session: Database session
            patient_data: Patient data dictionary
            patient_cache: Cache of created patients in this batch
            stats: Statistics dictionary to update
        
        Returns:
            Patient object or None
        """
        # Create cache key (age, gender, height, weight)
        cache_key = (
            patient_data.get('age'),
            patient_data.get('gender'),
            patient_data.get('height'),
            patient_data.get('weight')
        )
        
        # Check cache first
        if cache_key in patient_cache:
            return patient_cache[cache_key]
        
        # Validate patient data
        is_valid, errors = self.validator.validate_patient_data(**patient_data)
        if not is_valid:
            logger.debug(f"Skipping invalid patient data: {errors}")
            stats['patients_skipped'] += 1
            return None
        
        # Check for existing patient (simple check - could be improved)
        # For now, we'll create new patients (can be enhanced with duplicate detection)
        try:
            patient = crud.insert_patient_data(
                session=session,
                **patient_data
            )
            patient_cache[cache_key] = patient
            stats['patients_created'] += 1
            return patient
        except Exception as e:
            logger.error(f"Error creating patient: {e}")
            stats['patients_skipped'] += 1
            return None
    
    def _create_health_metric(
        self,
        session: Session,
        row: pd.Series,
        patient_id: int
    ) -> Optional[Any]:
        """
        Create health metric from row
        
        Args:
            session: Database session
            row: DataFrame row
            patient_id: Patient ID
        
        Returns:
            HealthMetric object or None
        """
        # Extract health metric data
        health_data = {
            'patient_id': patient_id,
            'systolic_bp': int(row.get('systolic_bp', 0)) if pd.notna(row.get('systolic_bp')) else None,
            'diastolic_bp': int(row.get('diastolic_bp', 0)) if pd.notna(row.get('diastolic_bp')) else None,
            'heart_rate': int(row.get('heart_rate', 0)) if pd.notna(row.get('heart_rate')) else None,
            'body_temperature': float(row.get('body_temperature', 0)) if pd.notna(row.get('body_temperature')) else None,
            'oxygen_saturation': float(row.get('oxygen_saturation', 0)) if pd.notna(row.get('oxygen_saturation')) else None,
            'cholesterol': int(row.get('cholesterol', 0)) if pd.notna(row.get('cholesterol')) else None,
            'glucose': int(row.get('glucose', 0)) if pd.notna(row.get('glucose')) else None,
            'smoking': bool(row.get('smoking', False)) if pd.notna(row.get('smoking')) else False,
            'alcohol_intake': bool(row.get('alcohol_intake', False)) if pd.notna(row.get('alcohol_intake')) else False,
            'physical_activity': bool(row.get('physical_activity', False)) if pd.notna(row.get('physical_activity')) else False,
            'cardiovascular_disease': bool(row.get('cardiovascular_disease', False)) if pd.notna(row.get('cardiovascular_disease')) else None
        }
        
        # Validate health data
        is_valid, errors = self.validator.validate_health_metrics(**health_data)
        if not is_valid:
            logger.debug(f"Skipping invalid health metric: {errors}")
            return None
        
        try:
            return crud.insert_health_metrics(session=session, **health_data)
        except Exception as e:
            logger.error(f"Error creating health metric: {e}")
            return None
