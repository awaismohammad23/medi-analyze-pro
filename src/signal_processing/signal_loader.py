"""
Signal loader module for MediAnalyze Pro
Loads biomedical signals (ECG/EEG) from various file formats
"""

import logging
import os
from typing import Dict, List, Optional, Tuple, Union
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class SignalLoader:
    """
    Loads biomedical signals from files (CSV, TXT, etc.)
    """
    
    SUPPORTED_FORMATS = ['.csv', '.txt', '.dat']
    
    def __init__(self, default_sampling_rate: float = 250.0):
        """
        Initialize signal loader
        
        Args:
            default_sampling_rate: Default sampling rate in Hz if not specified
        """
        self.default_sampling_rate = default_sampling_rate
    
    def load_signal_from_csv(
        self,
        file_path: str,
        time_column: Optional[str] = None,
        amplitude_column: Optional[str] = None,
        sampling_rate: Optional[float] = None,
        delimiter: str = ','
    ) -> Tuple[np.ndarray, float, Dict[str, any]]:
        """
        Load signal from CSV file
        
        Args:
            file_path: Path to CSV file
            time_column: Name of time column (if None, assumes sequential samples)
            amplitude_column: Name of amplitude column (if None, uses first numeric column)
            sampling_rate: Sampling rate in Hz (if None, uses default or calculates from time)
            delimiter: CSV delimiter
        
        Returns:
            Tuple of (signal_data, sampling_rate, metadata)
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Signal file not found: {file_path}")
        
        try:
            # Load CSV
            df = pd.read_csv(file_path, delimiter=delimiter)
            
            if df.empty:
                raise ValueError(f"CSV file is empty: {file_path}")
            
            # Determine time and amplitude columns
            if time_column is None:
                # Look for common time column names
                time_candidates = ['time', 't', 'timestamp', 'sample', 'index']
                time_column = next(
                    (col for col in time_candidates if col in df.columns),
                    None
                )
            
            if amplitude_column is None:
                # Use first numeric column that's not the time column
                numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
                if time_column and time_column in numeric_cols:
                    numeric_cols.remove(time_column)
                amplitude_column = numeric_cols[0] if numeric_cols else None
            
            if amplitude_column is None or amplitude_column not in df.columns:
                raise ValueError(
                    f"Could not determine amplitude column. Available columns: {df.columns.tolist()}"
                )
            
            # Extract signal data
            signal_data = df[amplitude_column].values.astype(float)
            
            # Calculate or use provided sampling rate
            if sampling_rate is None:
                if time_column and time_column in df.columns:
                    time_data = df[time_column].values
                    if len(time_data) > 1:
                        dt = np.mean(np.diff(time_data))
                        if dt > 0:
                            sampling_rate = 1.0 / dt
                        else:
                            sampling_rate = self.default_sampling_rate
                    else:
                        sampling_rate = self.default_sampling_rate
                else:
                    sampling_rate = self.default_sampling_rate
            
            # Create metadata
            metadata = {
                'file_path': file_path,
                'signal_length': len(signal_data),
                'duration': len(signal_data) / sampling_rate,
                'sampling_rate': sampling_rate,
                'amplitude_column': amplitude_column,
                'time_column': time_column,
                'mean': float(np.mean(signal_data)),
                'std': float(np.std(signal_data)),
                'min': float(np.min(signal_data)),
                'max': float(np.max(signal_data))
            }
            
            logger.info(
                f"Loaded signal: {len(signal_data)} samples, "
                f"sampling rate: {sampling_rate:.2f} Hz, "
                f"duration: {metadata['duration']:.2f} s"
            )
            
            return signal_data, sampling_rate, metadata
            
        except pd.errors.EmptyDataError:
            raise ValueError(f"CSV file is empty: {file_path}")
        except Exception as e:
            logger.error(f"Error loading signal from CSV: {e}")
            raise
    
    def load_signal_from_array(
        self,
        signal_data: Union[np.ndarray, List[float]],
        sampling_rate: float,
        metadata: Optional[Dict[str, any]] = None
    ) -> Tuple[np.ndarray, float, Dict[str, any]]:
        """
        Load signal from numpy array or list
        
        Args:
            signal_data: Signal amplitude values
            sampling_rate: Sampling rate in Hz
            metadata: Optional metadata dictionary
        
        Returns:
            Tuple of (signal_data, sampling_rate, metadata)
        """
        signal_data = np.array(signal_data, dtype=float)
        
        if len(signal_data) == 0:
            raise ValueError("Signal data is empty")
        
        if metadata is None:
            metadata = {}
        
        # Add/update metadata
        metadata.update({
            'signal_length': len(signal_data),
            'duration': len(signal_data) / sampling_rate,
            'sampling_rate': sampling_rate,
            'mean': float(np.mean(signal_data)),
            'std': float(np.std(signal_data)),
            'min': float(np.min(signal_data)),
            'max': float(np.max(signal_data))
        })
        
        return signal_data, sampling_rate, metadata
    
    def save_signal_to_csv(
        self,
        signal_data: np.ndarray,
        output_path: str,
        sampling_rate: float,
        time_column: str = 'time',
        amplitude_column: str = 'amplitude'
    ) -> bool:
        """
        Save signal to CSV file
        
        Args:
            signal_data: Signal amplitude values
            output_path: Output file path
            sampling_rate: Sampling rate in Hz
            time_column: Name for time column
            amplitude_column: Name for amplitude column
        
        Returns:
            True if successful
        """
        try:
            # Create time array
            time_array = np.arange(len(signal_data)) / sampling_rate
            
            # Create DataFrame
            df = pd.DataFrame({
                time_column: time_array,
                amplitude_column: signal_data
            })
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
            
            # Save to CSV
            df.to_csv(output_path, index=False)
            
            logger.info(f"Saved signal to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving signal to CSV: {e}")
            return False
    
    @staticmethod
    def detect_signal_type(signal_data: np.ndarray, sampling_rate: float) -> str:
        """
        Attempt to detect signal type based on characteristics
        
        Args:
            signal_data: Signal amplitude values
            sampling_rate: Sampling rate in Hz
        
        Returns:
            Detected signal type ('ECG', 'EEG', or 'UNKNOWN')
        """
        # ECG characteristics: typically 0.5-5 Hz (heart rate), sampling 250-500 Hz
        # EEG characteristics: typically 0.5-40 Hz, sampling 256-512 Hz
        
        # Compute dominant frequency
        fft = np.fft.fft(signal_data)
        freqs = np.fft.fftfreq(len(signal_data), 1/sampling_rate)
        power = np.abs(fft) ** 2
        
        # Focus on positive frequencies
        positive_freqs = freqs[:len(freqs)//2]
        positive_power = power[:len(power)//2]
        
        # Find dominant frequency
        dominant_idx = np.argmax(positive_power[1:]) + 1  # Skip DC component
        dominant_freq = abs(positive_freqs[dominant_idx])
        
        # Classify based on frequency and sampling rate
        if 0.5 <= dominant_freq <= 5.0 and 200 <= sampling_rate <= 500:
            return 'ECG'
        elif 0.5 <= dominant_freq <= 40.0 and 256 <= sampling_rate <= 512:
            return 'EEG'
        else:
            return 'UNKNOWN'
