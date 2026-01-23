"""
Spectrum analysis module for MediAnalyze Pro
Performs FFT analysis and frequency domain processing
"""

import logging
import os
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from scipy import signal as scipy_signal
from sqlalchemy.orm import Session

from ..database import get_session, crud

logger = logging.getLogger(__name__)


class SpectrumAnalyzer:
    """
    Performs frequency domain analysis on biomedical signals
    """
    
    def __init__(self, session: Optional[Session] = None):
        """
        Initialize spectrum analyzer
        
        Args:
            session: Database session (if None, creates new session)
        """
        self.session = session
    
    def compute_fft(
        self,
        signal: np.ndarray,
        sampling_rate: float,
        window: Optional[str] = None,
        nfft: Optional[int] = None
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Compute Fast Fourier Transform of signal
        
        Args:
            signal: Input signal
            sampling_rate: Sampling rate in Hz
            window: Window function ('hann', 'hamming', 'blackman', None)
            nfft: FFT size (if None, uses signal length)
        
        Returns:
            Tuple of (frequencies, fft_values)
        """
        signal = np.array(signal, dtype=float)
        
        if len(signal) == 0:
            raise ValueError("Signal is empty")
        
        # Apply window if specified
        if window:
            if window == 'hann':
                window_func = np.hanning(len(signal))
            elif window == 'hamming':
                window_func = np.hamming(len(signal))
            elif window == 'blackman':
                window_func = np.blackman(len(signal))
            else:
                raise ValueError(f"Unknown window function: {window}")
            signal = signal * window_func
        
        # Determine FFT size
        if nfft is None:
            nfft = len(signal)
        elif nfft < len(signal):
            logger.warning(f"FFT size ({nfft}) is less than signal length ({len(signal)})")
        
        # Compute FFT
        fft_values = np.fft.fft(signal, n=nfft)
        frequencies = np.fft.fftfreq(nfft, 1/sampling_rate)
        
        # Return only positive frequencies
        positive_freq_idx = frequencies >= 0
        frequencies = frequencies[positive_freq_idx]
        fft_values = fft_values[positive_freq_idx]
        
        return frequencies, fft_values
    
    def compute_power_spectrum(
        self,
        signal: np.ndarray,
        sampling_rate: float,
        window: Optional[str] = 'hann',
        nfft: Optional[int] = None
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Compute power spectrum density
        
        Args:
            signal: Input signal
            sampling_rate: Sampling rate in Hz
            window: Window function
            nfft: FFT size
        
        Returns:
            Tuple of (frequencies, power_spectrum)
        """
        frequencies, fft_values = self.compute_fft(signal, sampling_rate, window, nfft)
        
        # Compute power spectrum
        power_spectrum = np.abs(fft_values) ** 2
        
        # Normalize by signal length (for Parseval's theorem)
        power_spectrum = power_spectrum / len(signal)
        
        return frequencies, power_spectrum
    
    def compute_psd(
        self,
        signal: np.ndarray,
        sampling_rate: float,
        method: str = 'welch',
        nperseg: Optional[int] = None
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Compute Power Spectral Density using Welch's method
        
        Args:
            signal: Input signal
            sampling_rate: Sampling rate in Hz
            method: PSD method ('welch' or 'periodogram')
            nperseg: Length of each segment for Welch method
        
        Returns:
            Tuple of (frequencies, psd)
        """
        if method == 'welch':
            if nperseg is None:
                nperseg = min(256, len(signal) // 4)
            
            frequencies, psd = scipy_signal.welch(
                signal,
                sampling_rate,
                nperseg=nperseg,
                window='hann'
            )
            
            return frequencies, psd
        
        elif method == 'periodogram':
            frequencies, psd = scipy_signal.periodogram(
                signal,
                sampling_rate,
                window='hann'
            )
            
            return frequencies, psd
        
        else:
            raise ValueError(f"Unknown PSD method: {method}")
    
    def find_dominant_frequencies(
        self,
        frequencies: np.ndarray,
        power_spectrum: np.ndarray,
        n_peaks: int = 5,
        min_distance: Optional[float] = None
    ) -> List[Dict[str, float]]:
        """
        Find dominant frequency components
        
        Args:
            frequencies: Frequency array
            power_spectrum: Power spectrum array
            n_peaks: Number of peaks to find
            min_distance: Minimum distance between peaks in Hz
        
        Returns:
            List of dictionaries with frequency and power for each peak
        """
        # Find peaks
        if min_distance is None:
            min_distance = (frequencies[-1] - frequencies[0]) / 100
        
        # Convert min_distance to index distance
        freq_resolution = frequencies[1] - frequencies[0] if len(frequencies) > 1 else 1.0
        min_distance_idx = int(min_distance / freq_resolution)
        
        peaks, properties = scipy_signal.find_peaks(
            power_spectrum,
            distance=max(1, min_distance_idx),
            height=np.max(power_spectrum) * 0.1  # At least 10% of max
        )
        
        # Sort by power and take top n_peaks
        peak_powers = power_spectrum[peaks]
        sorted_indices = np.argsort(peak_powers)[::-1][:n_peaks]
        
        dominant_freqs = []
        for idx in sorted_indices:
            peak_idx = peaks[idx]
            dominant_freqs.append({
                'frequency': float(frequencies[peak_idx]),
                'power': float(power_spectrum[peak_idx]),
                'amplitude': float(np.sqrt(power_spectrum[peak_idx]))
            })
        
        return dominant_freqs
    
    def analyze_spectrum(
        self,
        signal: np.ndarray,
        sampling_rate: float,
        window: Optional[str] = 'hann',
        store_in_db: bool = False,
        signal_id: Optional[int] = None
    ) -> Dict[str, any]:
        """
        Perform complete spectrum analysis
        
        Args:
            signal: Input signal
            sampling_rate: Sampling rate in Hz
            window: Window function
            store_in_db: Whether to store results in database
            signal_id: Signal ID for database storage
        
        Returns:
            Dictionary with analysis results
        """
        # Compute power spectrum
        frequencies, power_spectrum = self.compute_power_spectrum(
            signal, sampling_rate, window=window
        )
        
        # Find dominant frequencies
        dominant_freqs = self.find_dominant_frequencies(frequencies, power_spectrum)
        
        # Compute statistics
        total_power = np.sum(power_spectrum)
        mean_power = np.mean(power_spectrum)
        max_power = np.max(power_spectrum)
        max_freq = frequencies[np.argmax(power_spectrum)]
        
        # Frequency resolution
        freq_resolution = frequencies[1] - frequencies[0] if len(frequencies) > 1 else sampling_rate / len(signal)
        
        result = {
            'frequencies': frequencies.tolist(),
            'power_spectrum': power_spectrum.tolist(),
            'dominant_frequencies': dominant_freqs,
            'total_power': float(total_power),
            'mean_power': float(mean_power),
            'max_power': float(max_power),
            'max_frequency': float(max_freq),
            'frequency_resolution': float(freq_resolution),
            'fft_size': len(signal),
            'sampling_rate': float(sampling_rate)
        }
        
        # Store in database if requested
        if store_in_db and signal_id:
            session = self.session or get_session()
            should_close = self.session is None
            
            try:
                # Save frequency data to file
                freq_data_path = self._save_frequency_data(
                    frequencies, power_spectrum, signal_id
                )
                
                # Store in database
                crud.insert_spectrum_analysis(
                    session=session,
                    signal_id=signal_id,
                    frequency_data_path=freq_data_path,
                    fft_size=len(signal),
                    frequency_resolution=freq_resolution,
                    dominant_frequency=dominant_freqs[0]['frequency'] if dominant_freqs else None,
                    power_spectrum_path=freq_data_path  # Same file for now
                )
                session.commit()
                logger.info(f"Stored spectrum analysis in database for signal {signal_id}")
            except Exception as e:
                logger.error(f"Error storing spectrum analysis: {e}")
                session.rollback()
            finally:
                if should_close:
                    session.close()
        
        return result
    
    def _save_frequency_data(
        self,
        frequencies: np.ndarray,
        power_spectrum: np.ndarray,
        signal_id: int
    ) -> str:
        """
        Save frequency domain data to CSV file
        
        Args:
            frequencies: Frequency array
            power_spectrum: Power spectrum array
            signal_id: Signal ID
        
        Returns:
            Path to saved file
        """
        # Create output directory
        output_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'data',
            'processed',
            'spectrum'
        )
        os.makedirs(output_dir, exist_ok=True)
        
        # Create DataFrame
        df = pd.DataFrame({
            'frequency': frequencies,
            'power_spectrum': power_spectrum
        })
        
        # Save to CSV
        output_path = os.path.join(output_dir, f'spectrum_signal_{signal_id}.csv')
        df.to_csv(output_path, index=False)
        
        return output_path
