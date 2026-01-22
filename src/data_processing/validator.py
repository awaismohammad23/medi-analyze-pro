"""
Data validation module for MediAnalyze Pro
Provides comprehensive validation for health data and patient information
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import pandas as pd

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass


class DataValidator:
    """
    Validates health data and patient information according to medical standards
    """
    
    # Medical value ranges (realistic bounds)
    AGE_MIN_DAYS = 365  # 1 year minimum
    AGE_MAX_DAYS = 36500  # ~100 years maximum
    HEIGHT_MIN_CM = 50.0  # Minimum height
    HEIGHT_MAX_CM = 250.0  # Maximum height
    WEIGHT_MIN_KG = 2.0  # Minimum weight (newborn)
    WEIGHT_MAX_KG = 300.0  # Maximum weight
    SYSTOLIC_BP_MIN = 50  # Minimum systolic BP
    SYSTOLIC_BP_MAX = 250  # Maximum systolic BP
    DIASTOLIC_BP_MIN = 30  # Minimum diastolic BP
    DIASTOLIC_BP_MAX = 200  # Maximum diastolic BP
    HEART_RATE_MIN = 30  # Minimum heart rate (bpm)
    HEART_RATE_MAX = 220  # Maximum heart rate (bpm)
    TEMPERATURE_MIN = 30.0  # Minimum body temperature (°C)
    TEMPERATURE_MAX = 45.0  # Maximum body temperature (°C)
    OXYGEN_SAT_MIN = 50.0  # Minimum oxygen saturation (%)
    OXYGEN_SAT_MAX = 100.0  # Maximum oxygen saturation (%)
    
    # Valid categorical values
    VALID_GENDERS = [1, 2]  # 1 = female, 2 = male
    VALID_CHOLESTEROL = [1, 2, 3]  # 1=normal, 2=above normal, 3=well above normal
    VALID_GLUCOSE = [1, 2, 3]  # Same as cholesterol
    
    @classmethod
    def validate_patient_data(
        cls,
        age: Optional[int] = None,
        gender: Optional[int] = None,
        height: Optional[float] = None,
        weight: Optional[float] = None,
        **kwargs
    ) -> Tuple[bool, List[str]]:
        """
        Validate patient data
        
        Args:
            age: Age in days
            gender: Gender (1=female, 2=male)
            height: Height in cm
            weight: Weight in kg
            **kwargs: Additional fields (ignored)
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        if age is not None:
            if not isinstance(age, int):
                errors.append(f"Age must be an integer, got {type(age).__name__}")
            elif not (cls.AGE_MIN_DAYS <= age <= cls.AGE_MAX_DAYS):
                errors.append(
                    f"Age must be between {cls.AGE_MIN_DAYS} and {cls.AGE_MAX_DAYS} days, "
                    f"got {age}"
                )
        
        if gender is not None:
            if not isinstance(gender, int):
                errors.append(f"Gender must be an integer, got {type(gender).__name__}")
            elif gender not in cls.VALID_GENDERS:
                errors.append(f"Gender must be one of {cls.VALID_GENDERS}, got {gender}")
        
        if height is not None:
            if not isinstance(height, (int, float)):
                errors.append(f"Height must be a number, got {type(height).__name__}")
            elif not (cls.HEIGHT_MIN_CM <= height <= cls.HEIGHT_MAX_CM):
                errors.append(
                    f"Height must be between {cls.HEIGHT_MIN_CM} and {cls.HEIGHT_MAX_CM} cm, "
                    f"got {height}"
                )
        
        if weight is not None:
            if not isinstance(weight, (int, float)):
                errors.append(f"Weight must be a number, got {type(weight).__name__}")
            elif not (cls.WEIGHT_MIN_KG <= weight <= cls.WEIGHT_MAX_KG):
                errors.append(
                    f"Weight must be between {cls.WEIGHT_MIN_KG} and {cls.WEIGHT_MAX_KG} kg, "
                    f"got {weight}"
                )
        
        return len(errors) == 0, errors
    
    @classmethod
    def validate_health_metrics(
        cls,
        systolic_bp: Optional[int] = None,
        diastolic_bp: Optional[int] = None,
        heart_rate: Optional[int] = None,
        body_temperature: Optional[float] = None,
        oxygen_saturation: Optional[float] = None,
        cholesterol: Optional[int] = None,
        glucose: Optional[int] = None,
        **kwargs
    ) -> Tuple[bool, List[str]]:
        """
        Validate health metrics
        
        Args:
            systolic_bp: Systolic blood pressure
            diastolic_bp: Diastolic blood pressure
            heart_rate: Heart rate (bpm)
            body_temperature: Body temperature (°C)
            oxygen_saturation: Oxygen saturation (%)
            cholesterol: Cholesterol level (1, 2, or 3)
            glucose: Glucose level (1, 2, or 3)
            **kwargs: Additional fields (ignored)
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Validate systolic BP
        if systolic_bp is not None:
            if not isinstance(systolic_bp, int):
                errors.append(f"Systolic BP must be an integer, got {type(systolic_bp).__name__}")
            elif not (cls.SYSTOLIC_BP_MIN <= systolic_bp <= cls.SYSTOLIC_BP_MAX):
                errors.append(
                    f"Systolic BP must be between {cls.SYSTOLIC_BP_MIN} and {cls.SYSTOLIC_BP_MAX}, "
                    f"got {systolic_bp}"
                )
        
        # Validate diastolic BP
        if diastolic_bp is not None:
            if not isinstance(diastolic_bp, int):
                errors.append(f"Diastolic BP must be an integer, got {type(diastolic_bp).__name__}")
            elif not (cls.DIASTOLIC_BP_MIN <= diastolic_bp <= cls.DIASTOLIC_BP_MAX):
                errors.append(
                    f"Diastolic BP must be between {cls.DIASTOLIC_BP_MIN} and {cls.DIASTOLIC_BP_MAX}, "
                    f"got {diastolic_bp}"
                )
        
        # Validate BP relationship (systolic should be >= diastolic)
        if systolic_bp is not None and diastolic_bp is not None:
            if systolic_bp < diastolic_bp:
                errors.append(
                    f"Systolic BP ({systolic_bp}) must be >= Diastolic BP ({diastolic_bp})"
                )
        
        # Validate heart rate
        if heart_rate is not None:
            if not isinstance(heart_rate, int):
                errors.append(f"Heart rate must be an integer, got {type(heart_rate).__name__}")
            elif not (cls.HEART_RATE_MIN <= heart_rate <= cls.HEART_RATE_MAX):
                errors.append(
                    f"Heart rate must be between {cls.HEART_RATE_MIN} and {cls.HEART_RATE_MAX} bpm, "
                    f"got {heart_rate}"
                )
        
        # Validate body temperature
        if body_temperature is not None:
            if not isinstance(body_temperature, (int, float)):
                errors.append(
                    f"Body temperature must be a number, got {type(body_temperature).__name__}"
                )
            elif not (cls.TEMPERATURE_MIN <= body_temperature <= cls.TEMPERATURE_MAX):
                errors.append(
                    f"Body temperature must be between {cls.TEMPERATURE_MIN} and "
                    f"{cls.TEMPERATURE_MAX} °C, got {body_temperature}"
                )
        
        # Validate oxygen saturation
        if oxygen_saturation is not None:
            if not isinstance(oxygen_saturation, (int, float)):
                errors.append(
                    f"Oxygen saturation must be a number, got {type(oxygen_saturation).__name__}"
                )
            elif not (cls.OXYGEN_SAT_MIN <= oxygen_saturation <= cls.OXYGEN_SAT_MAX):
                errors.append(
                    f"Oxygen saturation must be between {cls.OXYGEN_SAT_MIN} and "
                    f"{cls.OXYGEN_SAT_MAX}%, got {oxygen_saturation}"
                )
        
        # Validate cholesterol
        if cholesterol is not None:
            if not isinstance(cholesterol, int):
                errors.append(f"Cholesterol must be an integer, got {type(cholesterol).__name__}")
            elif cholesterol not in cls.VALID_CHOLESTEROL:
                errors.append(
                    f"Cholesterol must be one of {cls.VALID_CHOLESTEROL}, got {cholesterol}"
                )
        
        # Validate glucose
        if glucose is not None:
            if not isinstance(glucose, int):
                errors.append(f"Glucose must be an integer, got {type(glucose).__name__}")
            elif glucose not in cls.VALID_GLUCOSE:
                errors.append(f"Glucose must be one of {cls.VALID_GLUCOSE}, got {glucose}")
        
        return len(errors) == 0, errors
    
    @classmethod
    def validate_dataframe(
        cls,
        df: pd.DataFrame,
        required_columns: Optional[List[str]] = None,
        allow_missing: bool = True
    ) -> Tuple[bool, List[str]]:
        """
        Validate a pandas DataFrame structure
        
        Args:
            df: DataFrame to validate
            required_columns: List of required column names
            allow_missing: Whether to allow missing values
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        if not isinstance(df, pd.DataFrame):
            errors.append(f"Expected pandas DataFrame, got {type(df).__name__}")
            return False, errors
        
        if df.empty:
            errors.append("DataFrame is empty")
            return False, errors
        
        # Check required columns
        if required_columns:
            missing_cols = set(required_columns) - set(df.columns)
            if missing_cols:
                errors.append(f"Missing required columns: {missing_cols}")
        
        # Check for missing values if not allowed
        if not allow_missing:
            missing_counts = df.isnull().sum()
            cols_with_missing = missing_counts[missing_counts > 0]
            if not cols_with_missing.empty:
                errors.append(
                    f"Columns with missing values: {cols_with_missing.to_dict()}"
                )
        
        return len(errors) == 0, errors
    
    @classmethod
    def validate_row(
        cls,
        row: Dict[str, Any],
        row_index: Optional[int] = None
    ) -> Tuple[bool, List[str]]:
        """
        Validate a single data row
        
        Args:
            row: Dictionary containing row data
            row_index: Optional row index for error reporting
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        row_label = f"Row {row_index}" if row_index is not None else "Row"
        
        # Validate patient data
        patient_valid, patient_errors = cls.validate_patient_data(
            age=row.get('age'),
            gender=row.get('gender'),
            height=row.get('height'),
            weight=row.get('weight')
        )
        if not patient_valid:
            errors.extend([f"{row_label}: {err}" for err in patient_errors])
        
        # Validate health metrics
        health_valid, health_errors = cls.validate_health_metrics(
            systolic_bp=row.get('ap_hi') or row.get('systolic_bp'),
            diastolic_bp=row.get('ap_lo') or row.get('diastolic_bp'),
            heart_rate=row.get('heart_rate'),
            body_temperature=row.get('body_temperature'),
            oxygen_saturation=row.get('oxygen_saturation'),
            cholesterol=row.get('cholesterol'),
            glucose=row.get('gluc') or row.get('glucose')
        )
        if not health_valid:
            errors.extend([f"{row_label}: {err}" for err in health_errors])
        
        return len(errors) == 0, errors
