"""
Signal preprocessing module for MediAnalyze Pro
Provides noise reduction and signal normalization
"""

import logging
from typing import Optional, Tuple
import numpy as np
from scipy import signal as scipy_signal
from scipy.signal import butter, filtfilt, medfilt

logger = logging.getLogger(__name__)


class SignalPreprocessor:
    """
    Preprocesses biomedical signals for analysis
    """
    
    @staticmethod
    def normalize(
        signal: np.ndarray,
        method: str = 'zscore',
        range_min: float = -1.0,
        range_max: float = 1.0
    ) -> np.ndarray:
        """
        Normalize signal to standard range
        
        Args:
            signal: Input signal
            method: Normalization method
                - 'zscore': Zero mean, unit variance
                - 'minmax': Scale to [range_min, range_max]
                - 'unit': Scale to [0, 1]
            range_min: Minimum value for minmax scaling
            range_max: Maximum value for minmax scaling
        
        Returns:
            Normalized signal
        """
        signal = np.array(signal, dtype=float)
        
        if len(signal) == 0:
            return signal
        
        if method == 'zscore':
            mean = np.mean(signal)
            std = np.std(signal)
            if std == 0:
                logger.warning("Standard deviation is 0, returning zero signal")
                return np.zeros_like(signal)
            return (signal - mean) / std
        
        elif method == 'minmax':
            min_val = np.min(signal)
            max_val = np.max(signal)
            if max_val == min_val:
                logger.warning("Signal has constant value, returning zero signal")
                return np.zeros_like(signal)
            return (signal - min_val) / (max_val - min_val) * (range_max - range_min) + range_min
        
        elif method == 'unit':
            min_val = np.min(signal)
            max_val = np.max(signal)
            if max_val == min_val:
                return np.zeros_like(signal)
            return (signal - min_val) / (max_val - min_val)
        
        else:
            raise ValueError(f"Unknown normalization method: {method}")
    
    @staticmethod
    def remove_dc_offset(signal: np.ndarray) -> np.ndarray:
        """
        Remove DC offset (mean value) from signal
        
        Args:
            signal: Input signal
        
        Returns:
            Signal with DC offset removed
        """
        return signal - np.mean(signal)
    
    @staticmethod
    def apply_bandpass_filter(
        signal: np.ndarray,
        sampling_rate: float,
        lowcut: float,
        highcut: float,
        order: int = 4
    ) -> np.ndarray:
        """
        Apply bandpass filter to signal
        
        Args:
            signal: Input signal
            sampling_rate: Sampling rate in Hz
            lowcut: Low cutoff frequency in Hz
            highcut: High cutoff frequency in Hz
            order: Filter order
        
        Returns:
            Filtered signal
        """
        if lowcut >= highcut:
            raise ValueError("Low cutoff must be less than high cutoff")
        
        if highcut >= sampling_rate / 2:
            raise ValueError(f"High cutoff ({highcut}) must be less than Nyquist frequency ({sampling_rate/2})")
        
        # Design Butterworth bandpass filter
        nyquist = sampling_rate / 2.0
        low = lowcut / nyquist
        high = highcut / nyquist
        
        b, a = butter(order, [low, high], btype='band')
        
        # Apply filter (zero-phase filtering)
        filtered = filtfilt(b, a, signal)
        
        return filtered
    
    @staticmethod
    def apply_lowpass_filter(
        signal: np.ndarray,
        sampling_rate: float,
        cutoff: float,
        order: int = 4
    ) -> np.ndarray:
        """
        Apply lowpass filter to signal
        
        Args:
            signal: Input signal
            sampling_rate: Sampling rate in Hz
            cutoff: Cutoff frequency in Hz
            order: Filter order
        
        Returns:
            Filtered signal
        """
        if cutoff >= sampling_rate / 2:
            raise ValueError(f"Cutoff ({cutoff}) must be less than Nyquist frequency ({sampling_rate/2})")
        
        nyquist = sampling_rate / 2.0
        normal_cutoff = cutoff / nyquist
        
        b, a = butter(order, normal_cutoff, btype='low')
        filtered = filtfilt(b, a, signal)
        
        return filtered
    
    @staticmethod
    def apply_highpass_filter(
        signal: np.ndarray,
        sampling_rate: float,
        cutoff: float,
        order: int = 4
    ) -> np.ndarray:
        """
        Apply highpass filter to signal
        
        Args:
            signal: Input signal
            sampling_rate: Sampling rate in Hz
            cutoff: Cutoff frequency in Hz
            order: Filter order
        
        Returns:
            Filtered signal
        """
        if cutoff >= sampling_rate / 2:
            raise ValueError(f"Cutoff ({cutoff}) must be less than Nyquist frequency ({sampling_rate/2})")
        
        nyquist = sampling_rate / 2.0
        normal_cutoff = cutoff / nyquist
        
        b, a = butter(order, normal_cutoff, btype='high')
        filtered = filtfilt(b, a, signal)
        
        return filtered
    
    @staticmethod
    def apply_median_filter(
        signal: np.ndarray,
        kernel_size: int = 3
    ) -> np.ndarray:
        """
        Apply median filter to remove impulse noise
        
        Args:
            signal: Input signal
            kernel_size: Size of median filter kernel (must be odd)
        
        Returns:
            Filtered signal
        """
        if kernel_size % 2 == 0:
            kernel_size += 1
            logger.warning(f"Kernel size must be odd, using {kernel_size}")
        
        filtered = medfilt(signal, kernel_size)
        return filtered
    
    @staticmethod
    def remove_baseline_wander(
        signal: np.ndarray,
        sampling_rate: float,
        cutoff: float = 0.5
    ) -> np.ndarray:
        """
        Remove baseline wander using highpass filter
        
        Args:
            signal: Input signal
            sampling_rate: Sampling rate in Hz
            cutoff: Highpass cutoff frequency (typically 0.5 Hz for ECG)
        
        Returns:
            Signal with baseline wander removed
        """
        return SignalPreprocessor.apply_highpass_filter(signal, sampling_rate, cutoff)
    
    @staticmethod
    def reduce_noise(
        signal: np.ndarray,
        sampling_rate: float,
        method: str = 'bandpass',
        **kwargs
    ) -> np.ndarray:
        """
        Reduce noise in signal using various methods
        
        Args:
            signal: Input signal
            sampling_rate: Sampling rate in Hz
            method: Noise reduction method
                - 'bandpass': Bandpass filter (requires lowcut, highcut)
                - 'lowpass': Lowpass filter (requires cutoff)
                - 'median': Median filter (requires kernel_size)
                - 'baseline': Remove baseline wander
            **kwargs: Additional parameters for specific methods
        
        Returns:
            Denoised signal
        """
        if method == 'bandpass':
            lowcut = kwargs.get('lowcut', 0.5)
            highcut = kwargs.get('highcut', sampling_rate / 2 - 1)
            return SignalPreprocessor.apply_bandpass_filter(signal, sampling_rate, lowcut, highcut)
        
        elif method == 'lowpass':
            cutoff = kwargs.get('cutoff', sampling_rate / 4)
            return SignalPreprocessor.apply_lowpass_filter(signal, sampling_rate, cutoff)
        
        elif method == 'median':
            kernel_size = kwargs.get('kernel_size', 3)
            return SignalPreprocessor.apply_median_filter(signal, kernel_size)
        
        elif method == 'baseline':
            cutoff = kwargs.get('cutoff', 0.5)
            return SignalPreprocessor.remove_baseline_wander(signal, sampling_rate, cutoff)
        
        else:
            raise ValueError(f"Unknown noise reduction method: {method}")
    
    @staticmethod
    def preprocess_pipeline(
        signal: np.ndarray,
        sampling_rate: float,
        steps: list
    ) -> np.ndarray:
        """
        Apply multiple preprocessing steps in sequence
        
        Args:
            signal: Input signal
            sampling_rate: Sampling rate in Hz
            steps: List of preprocessing steps, each with 'method' and parameters
                Example: [
                    {'method': 'remove_dc_offset'},
                    {'method': 'normalize', 'method_type': 'zscore'},
                    {'method': 'reduce_noise', 'noise_method': 'bandpass', 'lowcut': 0.5, 'highcut': 40}
                ]
        
        Returns:
            Preprocessed signal
        """
        processed = signal.copy()
        
        for i, step in enumerate(steps):
            method = step.pop('method', None)
            
            if method == 'normalize':
                method_type = step.pop('method_type', 'zscore')
                processed = SignalPreprocessor.normalize(processed, method=method_type, **step)
            elif method == 'remove_dc_offset':
                processed = SignalPreprocessor.remove_dc_offset(processed)
            elif method == 'reduce_noise':
                noise_method = step.pop('noise_method', 'bandpass')
                processed = SignalPreprocessor.reduce_noise(
                    processed, sampling_rate, noise_method, **step
                )
            elif method == 'bandpass':
                processed = SignalPreprocessor.apply_bandpass_filter(
                    processed, sampling_rate, **step
                )
            elif method == 'lowpass':
                processed = SignalPreprocessor.apply_lowpass_filter(
                    processed, sampling_rate, **step
                )
            elif method == 'highpass':
                processed = SignalPreprocessor.apply_highpass_filter(
                    processed, sampling_rate, **step
                )
            elif method == 'median':
                processed = SignalPreprocessor.apply_median_filter(processed, **step)
            else:
                raise ValueError(f"Unknown preprocessing method: {method}")
            
            logger.debug(f"Applied preprocessing step {i+1}/{len(steps)}: {method}")
        
        return processed
