"""
Data retrieval module for MediAnalyze Pro
Provides flexible data retrieval with filtering and querying capabilities
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from ..database import get_session, crud
from ..database.models import Patient, HealthMetric

logger = logging.getLogger(__name__)


class DataRetriever:
    """
    Retrieves data from database with flexible filtering options
    """
    
    def __init__(self, session: Optional[Session] = None):
        """
        Initialize data retriever
        
        Args:
            session: Database session (if None, creates new session)
        """
        self.session = session
    
    def get_patients(
        self,
        patient_ids: Optional[List[int]] = None,
        gender: Optional[int] = None,
        min_age: Optional[int] = None,
        max_age: Optional[int] = None,
        min_bmi: Optional[float] = None,
        max_bmi: Optional[float] = None,
        limit: Optional[int] = None,
        as_dataframe: bool = False
    ) -> Any:
        """
        Retrieve patients with optional filters
        
        Args:
            patient_ids: List of patient IDs to filter
            gender: Gender filter (1=female, 2=male)
            min_age: Minimum age in days
            max_age: Maximum age in days
            min_bmi: Minimum BMI
            max_bmi: Maximum BMI
            limit: Maximum number of results
            as_dataframe: Return as pandas DataFrame
        
        Returns:
            List of Patient objects or DataFrame
        """
        session = self.session or get_session()
        should_close = self.session is None
        
        try:
            # Build query
            query = session.query(Patient)
            
            if patient_ids:
                query = query.filter(Patient.patient_id.in_(patient_ids))
            
            if gender:
                query = query.filter(Patient.gender == gender)
            
            if min_age:
                query = query.filter(Patient.age >= min_age)
            
            if max_age:
                query = query.filter(Patient.age <= max_age)
            
            # BMI filtering (requires calculation)
            if min_bmi or max_bmi:
                # BMI = weight (kg) / (height (m))^2
                # We need to filter after calculating BMI
                patients = query.all()
                filtered = []
                
                for patient in patients:
                    height_m = patient.height / 100.0  # Convert cm to m
                    bmi = patient.weight / (height_m ** 2)
                    
                    if min_bmi and bmi < min_bmi:
                        continue
                    if max_bmi and bmi > max_bmi:
                        continue
                    
                    filtered.append(patient)
                
                patients = filtered
            else:
                patients = query.limit(limit).all() if limit else query.all()
            
            if as_dataframe:
                return self._patients_to_dataframe(patients)
            
            return patients
            
        finally:
            if should_close:
                session.close()
    
    def get_health_metrics(
        self,
        patient_ids: Optional[List[int]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        min_systolic_bp: Optional[int] = None,
        max_systolic_bp: Optional[int] = None,
        min_diastolic_bp: Optional[int] = None,
        max_diastolic_bp: Optional[int] = None,
        has_cardiovascular_disease: Optional[bool] = None,
        limit: Optional[int] = None,
        as_dataframe: bool = False
    ) -> Any:
        """
        Retrieve health metrics with optional filters
        
        Args:
            patient_ids: List of patient IDs to filter
            start_date: Start date filter
            end_date: End date filter
            min_systolic_bp: Minimum systolic BP
            max_systolic_bp: Maximum systolic BP
            min_diastolic_bp: Minimum diastolic BP
            max_diastolic_bp: Maximum diastolic BP
            has_cardiovascular_disease: Filter by cardiovascular disease status
            limit: Maximum number of results
            as_dataframe: Return as pandas DataFrame
        
        Returns:
            List of HealthMetric objects or DataFrame
        """
        session = self.session or get_session()
        should_close = self.session is None
        
        try:
            # Build query
            query = session.query(HealthMetric)
            
            if patient_ids:
                query = query.filter(HealthMetric.patient_id.in_(patient_ids))
            
            if start_date:
                query = query.filter(HealthMetric.timestamp >= start_date)
            
            if end_date:
                query = query.filter(HealthMetric.timestamp <= end_date)
            
            if min_systolic_bp:
                query = query.filter(HealthMetric.systolic_bp >= min_systolic_bp)
            
            if max_systolic_bp:
                query = query.filter(HealthMetric.systolic_bp <= max_systolic_bp)
            
            if min_diastolic_bp:
                query = query.filter(HealthMetric.diastolic_bp >= min_diastolic_bp)
            
            if max_diastolic_bp:
                query = query.filter(HealthMetric.diastolic_bp <= max_diastolic_bp)
            
            if has_cardiovascular_disease is not None:
                query = query.filter(
                    HealthMetric.cardiovascular_disease == has_cardiovascular_disease
                )
            
            query = query.order_by(HealthMetric.timestamp.desc())
            
            if limit:
                query = query.limit(limit)
            
            metrics = query.all()
            
            if as_dataframe:
                return self._health_metrics_to_dataframe(metrics)
            
            return metrics
            
        finally:
            if should_close:
                session.close()
    
    def get_patient_with_metrics(
        self,
        patient_id: int,
        include_metrics: bool = True,
        as_dataframe: bool = False
    ) -> Dict[str, Any]:
        """
        Get patient with their health metrics
        
        Args:
            patient_id: Patient ID
            include_metrics: Whether to include health metrics
            as_dataframe: Return metrics as DataFrame
        
        Returns:
            Dictionary with patient and metrics
        """
        session = self.session or get_session()
        should_close = self.session is None
        
        try:
            # Get patient
            patients = crud.retrieve_patient_data(session, patient_id=patient_id)
            if not patients:
                return {'patient': None, 'metrics': []}
            
            patient = patients[0]
            result = {'patient': patient}
            
            if include_metrics:
                metrics = crud.retrieve_health_metrics(session, patient_id=patient_id)
                if as_dataframe:
                    result['metrics'] = self._health_metrics_to_dataframe(metrics)
                else:
                    result['metrics'] = metrics
            
            return result
            
        finally:
            if should_close:
                session.close()
    
    def get_statistics(
        self,
        patient_ids: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        Get statistical summary of health data
        
        Args:
            patient_ids: Optional list of patient IDs to filter
        
        Returns:
            Dictionary with statistics
        """
        session = self.session or get_session()
        should_close = self.session is None
        
        try:
            stats = {}
            
            # Patient statistics
            query = session.query(Patient)
            if patient_ids:
                query = query.filter(Patient.patient_id.in_(patient_ids))
            
            stats['total_patients'] = query.count()
            stats['avg_age_days'] = session.query(func.avg(Patient.age)).scalar()
            stats['avg_height'] = session.query(func.avg(Patient.height)).scalar()
            stats['avg_weight'] = session.query(func.avg(Patient.weight)).scalar()
            
            # Health metrics statistics
            metrics_query = session.query(HealthMetric)
            if patient_ids:
                metrics_query = metrics_query.filter(
                    HealthMetric.patient_id.in_(patient_ids)
                )
            
            stats['total_health_metrics'] = metrics_query.count()
            stats['avg_systolic_bp'] = session.query(
                func.avg(HealthMetric.systolic_bp)
            ).filter(HealthMetric.systolic_bp.isnot(None)).scalar()
            stats['avg_diastolic_bp'] = session.query(
                func.avg(HealthMetric.diastolic_bp)
            ).filter(HealthMetric.diastolic_bp.isnot(None)).scalar()
            stats['avg_heart_rate'] = session.query(
                func.avg(HealthMetric.heart_rate)
            ).filter(HealthMetric.heart_rate.isnot(None)).scalar()
            
            return stats
            
        finally:
            if should_close:
                session.close()
    
    @staticmethod
    def _patients_to_dataframe(patients: List[Patient]) -> pd.DataFrame:
        """Convert list of Patient objects to DataFrame"""
        if not patients:
            return pd.DataFrame()
        
        data = []
        for patient in patients:
            data.append({
                'patient_id': patient.patient_id,
                'name': patient.name,
                'age': patient.age,
                'gender': patient.gender,
                'height': patient.height,
                'weight': patient.weight,
                'created_at': patient.created_at
            })
        
        return pd.DataFrame(data)
    
    @staticmethod
    def _health_metrics_to_dataframe(metrics: List[HealthMetric]) -> pd.DataFrame:
        """Convert list of HealthMetric objects to DataFrame"""
        if not metrics:
            return pd.DataFrame()
        
        data = []
        for metric in metrics:
            data.append({
                'metric_id': metric.metric_id,
                'patient_id': metric.patient_id,
                'timestamp': metric.timestamp,
                'systolic_bp': metric.systolic_bp,
                'diastolic_bp': metric.diastolic_bp,
                'heart_rate': metric.heart_rate,
                'body_temperature': metric.body_temperature,
                'oxygen_saturation': metric.oxygen_saturation,
                'cholesterol': metric.cholesterol,
                'glucose': metric.glucose,
                'smoking': metric.smoking,
                'alcohol_intake': metric.alcohol_intake,
                'physical_activity': metric.physical_activity,
                'cardiovascular_disease': metric.cardiovascular_disease
            })
        
        return pd.DataFrame(data)
