"""
CSV data loader module for MediAnalyze Pro
Handles loading and parsing of CSV files with health data
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import numpy as np

from .validator import DataValidator, ValidationError

logger = logging.getLogger(__name__)


class CSVLoader:
    """
    Loads and processes CSV files containing health data
    """
    
    # Common CSV delimiters to try
    DELIMITERS = [';', ',', '\t', '|']
    
    # Expected column mappings (CSV column -> internal column name)
    COLUMN_MAPPINGS = {
        'id': 'id',
        'age': 'age',
        'gender': 'gender',
        'height': 'height',
        'weight': 'weight',
        'ap_hi': 'systolic_bp',
        'ap_lo': 'diastolic_bp',
        'systolic_bp': 'systolic_bp',
        'diastolic_bp': 'diastolic_bp',
        'heart_rate': 'heart_rate',
        'body_temperature': 'body_temperature',
        'oxygen_saturation': 'oxygen_saturation',
        'cholesterol': 'cholesterol',
        'gluc': 'glucose',
        'glucose': 'glucose',
        'smoke': 'smoking',
        'smoking': 'smoking',
        'alco': 'alcohol_intake',
        'alcohol_intake': 'alcohol_intake',
        'active': 'physical_activity',
        'physical_activity': 'physical_activity',
        'cardio': 'cardiovascular_disease',
        'cardiovascular_disease': 'cardiovascular_disease'
    }
    
    def __init__(
        self,
        delimiter: Optional[str] = None,
        encoding: str = 'utf-8',
        skip_validation: bool = False
    ):
        """
        Initialize CSV loader
        
        Args:
            delimiter: CSV delimiter (if None, will auto-detect)
            encoding: File encoding (default: utf-8)
            skip_validation: Skip data validation (not recommended)
        """
        self.delimiter = delimiter
        self.encoding = encoding
        self.skip_validation = skip_validation
        self.validator = DataValidator()
    
    def detect_delimiter(self, file_path: str, sample_lines: int = 5) -> str:
        """
        Auto-detect CSV delimiter by analyzing file content
        
        Args:
            file_path: Path to CSV file
            sample_lines: Number of lines to sample
        
        Returns:
            Detected delimiter
        """
        try:
            with open(file_path, 'r', encoding=self.encoding) as f:
                sample = ''.join(f.readline() for _ in range(sample_lines))
            
            # Count occurrences of each delimiter
            delimiter_counts = {
                delim: sample.count(delim)
                for delim in self.DELIMITERS
            }
            
            # Return delimiter with highest count
            detected = max(delimiter_counts, key=delimiter_counts.get)
            
            if delimiter_counts[detected] == 0:
                logger.warning("Could not detect delimiter, defaulting to comma")
                return ','
            
            logger.info(f"Detected delimiter: '{detected}'")
            return detected
            
        except Exception as e:
            logger.warning(f"Error detecting delimiter: {e}, defaulting to comma")
            return ','
    
    def load_csv(
        self,
        file_path: str,
        delimiter: Optional[str] = None,
        encoding: Optional[str] = None,
        n_rows: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Load CSV file into pandas DataFrame
        
        Args:
            file_path: Path to CSV file
            delimiter: CSV delimiter (if None, uses instance default or auto-detects)
            encoding: File encoding (if None, uses instance default)
            n_rows: Number of rows to read (None = all rows)
        
        Returns:
            Loaded DataFrame
        
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file cannot be parsed
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"CSV file not found: {file_path}")
        
        # Use provided parameters or fall back to instance defaults
        delimiter = delimiter or self.delimiter
        encoding = encoding or self.encoding
        
        # Auto-detect delimiter if not provided
        if delimiter is None:
            delimiter = self.detect_delimiter(file_path)
        
        try:
            logger.info(f"Loading CSV file: {file_path}")
            
            # Read CSV with error handling
            df = pd.read_csv(
                file_path,
                delimiter=delimiter,
                encoding=encoding,
                nrows=n_rows,
                low_memory=False,
                na_values=['', 'NA', 'N/A', 'null', 'NULL', 'None', 'nan', 'NaN']
            )
            
            logger.info(f"Loaded {len(df)} rows, {len(df.columns)} columns")
            
            # Normalize column names (lowercase, strip whitespace)
            df.columns = df.columns.str.lower().str.strip()
            
            # Map columns to standard names
            df = self._map_columns(df)
            
            # Clean data
            df = self._clean_dataframe(df)
            
            return df
            
        except pd.errors.EmptyDataError:
            raise ValueError(f"CSV file is empty: {file_path}")
        except pd.errors.ParserError as e:
            raise ValueError(f"Error parsing CSV file {file_path}: {e}")
        except Exception as e:
            raise ValueError(f"Unexpected error loading CSV file {file_path}: {e}")
    
    def _map_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Map CSV columns to standard internal column names
        
        Args:
            df: DataFrame with original column names
        
        Returns:
            DataFrame with mapped column names
        """
        column_mapping = {}
        
        for csv_col in df.columns:
            # Find matching internal column name
            internal_col = self.COLUMN_MAPPINGS.get(csv_col.lower().strip())
            if internal_col and csv_col != internal_col:
                column_mapping[csv_col] = internal_col
        
        if column_mapping:
            df = df.rename(columns=column_mapping)
            logger.debug(f"Mapped columns: {column_mapping}")
        
        return df
    
    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean DataFrame: handle missing values, convert types, etc.
        
        Args:
            df: DataFrame to clean
        
        Returns:
            Cleaned DataFrame
        """
        df = df.copy()
        
        # Convert boolean columns (0/1 to True/False)
        bool_columns = ['smoking', 'alcohol_intake', 'physical_activity', 'cardiovascular_disease']
        for col in bool_columns:
            if col in df.columns:
                df[col] = df[col].astype('Int64').fillna(0).astype(bool)
        
        # Ensure numeric columns are numeric
        numeric_columns = ['age', 'height', 'weight', 'systolic_bp', 'diastolic_bp',
                          'heart_rate', 'body_temperature', 'oxygen_saturation',
                          'cholesterol', 'glucose']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Remove rows where all key fields are missing
        key_fields = ['age', 'gender', 'height', 'weight']
        if all(col in df.columns for col in key_fields):
            before = len(df)
            df = df.dropna(subset=key_fields, how='all')
            if len(df) < before:
                logger.info(f"Removed {before - len(df)} rows with all key fields missing")
        
        return df
    
    def validate_loaded_data(
        self,
        df: pd.DataFrame,
        strict: bool = False
    ) -> Tuple[bool, List[str], pd.DataFrame]:
        """
        Validate loaded DataFrame
        
        Args:
            df: DataFrame to validate
            strict: If True, remove invalid rows; if False, just report errors
        
        Returns:
            Tuple of (is_valid, list_of_errors, validated_dataframe)
        """
        errors = []
        valid_rows = []
        
        # Validate DataFrame structure
        is_valid, struct_errors = self.validator.validate_dataframe(df)
        if not is_valid:
            errors.extend(struct_errors)
            if strict:
                return False, errors, df
        
        # Validate each row
        for idx, row in df.iterrows():
            is_valid_row, row_errors = self.validator.validate_row(row, row_index=idx)
            
            if is_valid_row:
                valid_rows.append(idx)
            else:
                errors.extend(row_errors)
                if not strict:
                    valid_rows.append(idx)  # Keep row even if invalid
        
        # Filter DataFrame if strict mode
        if strict and errors:
            df_valid = df.loc[valid_rows].copy()
            logger.info(f"Removed {len(df) - len(df_valid)} invalid rows")
        else:
            df_valid = df.copy()
        
        is_valid = len(errors) == 0
        
        if errors and not strict:
            logger.warning(f"Found {len(errors)} validation errors (non-strict mode)")
        
        return is_valid, errors, df_valid
    
    def load_and_validate(
        self,
        file_path: str,
        strict_validation: bool = False,
        **kwargs
    ) -> Tuple[pd.DataFrame, List[str]]:
        """
        Load CSV file and validate data
        
        Args:
            file_path: Path to CSV file
            strict_validation: If True, remove invalid rows
            **kwargs: Additional arguments for load_csv()
        
        Returns:
            Tuple of (validated_dataframe, list_of_errors)
        """
        # Load CSV
        df = self.load_csv(file_path, **kwargs)
        
        # Validate
        if self.skip_validation:
            logger.warning("Skipping validation (skip_validation=True)")
            return df, []
        
        is_valid, errors, df_valid = self.validate_loaded_data(df, strict=strict_validation)
        
        return df_valid, errors
    
    @staticmethod
    def get_file_info(file_path: str) -> Dict[str, Any]:
        """
        Get information about a CSV file
        
        Args:
            file_path: Path to CSV file
        
        Returns:
            Dictionary with file information
        """
        if not os.path.exists(file_path):
            return {'exists': False}
        
        path = Path(file_path)
        stat = path.stat()
        
        return {
            'exists': True,
            'path': str(path.absolute()),
            'size_bytes': stat.st_size,
            'size_mb': round(stat.st_size / (1024 * 1024), 2),
            'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
        }
