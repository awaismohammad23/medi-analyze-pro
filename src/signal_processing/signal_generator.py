"""
Synthetic signal generator for MediAnalyze Pro
Generates realistic ECG and EEG signals for testing and demonstration
"""

import logging
from typing import Dict, Optional, Tuple
import numpy as np

logger = logging.getLogger(__name__)


class SignalGenerator:
    """
    Generates synthetic biomedical signals for testing
    """
    
    @staticmethod
    def generate_ecg(
        duration: float = 10.0,
        sampling_rate: float = 250.0,
        heart_rate: float = 72.0,
        noise_level: float = 0.02,
        add_baseline_wander: bool = True
    ) -> Tuple[np.ndarray, float, Dict[str, any]]:
        """
        Generate synthetic ECG signal
        
        Args:
            duration: Signal duration in seconds
            sampling_rate: Sampling rate in Hz
            heart_rate: Heart rate in beats per minute
            noise_level: Noise amplitude (0-1)
            add_baseline_wander: Whether to add baseline wander
        
        Returns:
            Tuple of (signal, sampling_rate, metadata)
        """
        # Time array
        t = np.arange(0, duration, 1/sampling_rate)
        n_samples = len(t)
        
        # Heart period
        heart_period = 60.0 / heart_rate
        
        # Generate ECG waveform using simplified model
        signal = np.zeros(n_samples)
        
        for i in range(n_samples):
            # Position within current heart cycle
            cycle_pos = (t[i] % heart_period) / heart_period
            
            # P wave (atrial depolarization)
            if 0.0 <= cycle_pos < 0.15:
                signal[i] += 0.1 * np.sin(np.pi * cycle_pos / 0.15)
            
            # QRS complex (ventricular depolarization)
            elif 0.15 <= cycle_pos < 0.25:
                # Q
                if cycle_pos < 0.17:
                    signal[i] -= 0.2 * np.exp(-((cycle_pos - 0.16) / 0.01) ** 2)
                # R
                elif cycle_pos < 0.20:
                    signal[i] += 1.0 * np.exp(-((cycle_pos - 0.18) / 0.01) ** 2)
                # S
                else:
                    signal[i] -= 0.3 * np.exp(-((cycle_pos - 0.22) / 0.01) ** 2)
            
            # T wave (ventricular repolarization)
            elif 0.25 <= cycle_pos < 0.55:
                signal[i] += 0.3 * np.sin(np.pi * (cycle_pos - 0.25) / 0.3) * \
                            np.exp(-((cycle_pos - 0.4) / 0.15) ** 2)
        
        # Add baseline wander (low frequency component)
        if add_baseline_wander:
            baseline = 0.1 * np.sin(2 * np.pi * 0.5 * t)  # 0.5 Hz
            signal += baseline
        
        # Add noise
        noise = noise_level * np.random.randn(n_samples)
        signal += noise
        
        # Normalize
        signal = signal / np.max(np.abs(signal)) * 1.0
        
        metadata = {
            'signal_type': 'ECG',
            'duration': duration,
            'sampling_rate': sampling_rate,
            'heart_rate': heart_rate,
            'n_samples': n_samples,
            'noise_level': noise_level
        }
        
        logger.info(f"Generated ECG signal: {n_samples} samples, {heart_rate} bpm")
        
        return signal, sampling_rate, metadata
    
    @staticmethod
    def generate_eeg(
        duration: float = 10.0,
        sampling_rate: float = 256.0,
        frequency_bands: Optional[Dict[str, float]] = None,
        noise_level: float = 0.1,
        add_artifacts: bool = True
    ) -> Tuple[np.ndarray, float, Dict[str, any]]:
        """
        Generate synthetic EEG signal
        
        Args:
            duration: Signal duration in seconds
            sampling_rate: Sampling rate in Hz
            frequency_bands: Dictionary of frequency bands and amplitudes
                Default: {'delta': 0.1, 'theta': 0.2, 'alpha': 0.3, 'beta': 0.2, 'gamma': 0.1}
            noise_level: Noise amplitude (0-1)
            add_artifacts: Whether to add artifacts (eye blinks, muscle)
        
        Returns:
            Tuple of (signal, sampling_rate, metadata)
        """
        # Default frequency bands (typical EEG)
        if frequency_bands is None:
            frequency_bands = {
                'delta': 0.1,   # 0.5-4 Hz
                'theta': 0.2,   # 4-8 Hz
                'alpha': 0.3,   # 8-13 Hz
                'beta': 0.2,    # 13-30 Hz
                'gamma': 0.1    # 30-40 Hz
            }
        
        # Time array
        t = np.arange(0, duration, 1/sampling_rate)
        n_samples = len(t)
        
        signal = np.zeros(n_samples)
        
        # Generate each frequency band
        band_freqs = {
            'delta': (0.5, 4.0),
            'theta': (4.0, 8.0),
            'alpha': (8.0, 13.0),
            'beta': (13.0, 30.0),
            'gamma': (30.0, 40.0)
        }
        
        for band_name, amplitude in frequency_bands.items():
            if band_name in band_freqs:
                low_freq, high_freq = band_freqs[band_name]
                center_freq = (low_freq + high_freq) / 2
                bandwidth = high_freq - low_freq
                
                # Generate band-limited signal
                band_signal = amplitude * np.sin(2 * np.pi * center_freq * t)
                # Add some frequency modulation
                band_signal += 0.3 * amplitude * np.sin(2 * np.pi * (center_freq + bandwidth/4) * t)
                band_signal += 0.2 * amplitude * np.sin(2 * np.pi * (center_freq - bandwidth/4) * t)
                
                signal += band_signal
        
        # Add artifacts
        if add_artifacts:
            # Eye blink artifacts (low frequency, high amplitude)
            n_blinks = int(duration / 3)  # Blink every ~3 seconds
            for _ in range(n_blinks):
                blink_time = np.random.uniform(0, duration)
                blink_idx = int(blink_time * sampling_rate)
                if 0 <= blink_idx < n_samples:
                    blink_duration = 0.3  # 300ms
                    blink_samples = int(blink_duration * sampling_rate)
                    blink_signal = 0.5 * np.exp(-((np.arange(blink_samples) - blink_samples/2) / (blink_samples/4)) ** 2)
                    
                    start_idx = max(0, blink_idx - blink_samples // 2)
                    end_idx = min(n_samples, start_idx + len(blink_signal))
                    signal[start_idx:end_idx] += blink_signal[:end_idx-start_idx]
        
        # Add noise
        noise = noise_level * np.random.randn(n_samples)
        signal += noise
        
        # Normalize
        signal = signal / np.max(np.abs(signal)) * 1.0
        
        metadata = {
            'signal_type': 'EEG',
            'duration': duration,
            'sampling_rate': sampling_rate,
            'n_samples': n_samples,
            'frequency_bands': frequency_bands,
            'noise_level': noise_level
        }
        
        logger.info(f"Generated EEG signal: {n_samples} samples")
        
        return signal, sampling_rate, metadata
    
    @staticmethod
    def generate_sine_wave(
        frequency: float,
        duration: float = 1.0,
        sampling_rate: float = 1000.0,
        amplitude: float = 1.0,
        phase: float = 0.0,
        add_noise: bool = False,
        noise_level: float = 0.1
    ) -> Tuple[np.ndarray, float, Dict[str, any]]:
        """
        Generate simple sine wave signal
        
        Args:
            frequency: Frequency in Hz
            duration: Duration in seconds
            sampling_rate: Sampling rate in Hz
            amplitude: Signal amplitude
            phase: Phase offset in radians
            add_noise: Whether to add noise
            noise_level: Noise amplitude
        
        Returns:
            Tuple of (signal, sampling_rate, metadata)
        """
        t = np.arange(0, duration, 1/sampling_rate)
        signal = amplitude * np.sin(2 * np.pi * frequency * t + phase)
        
        if add_noise:
            noise = noise_level * np.random.randn(len(signal))
            signal += noise
        
        metadata = {
            'signal_type': 'SINE',
            'frequency': frequency,
            'duration': duration,
            'sampling_rate': sampling_rate,
            'amplitude': amplitude,
            'phase': phase
        }
        
        return signal, sampling_rate, metadata
    
    @staticmethod
    def generate_multi_tone(
        frequencies: list,
        amplitudes: list,
        duration: float = 1.0,
        sampling_rate: float = 1000.0,
        add_noise: bool = False,
        noise_level: float = 0.1
    ) -> Tuple[np.ndarray, float, Dict[str, any]]:
        """
        Generate signal with multiple frequency components
        
        Args:
            frequencies: List of frequencies in Hz
            amplitudes: List of amplitudes for each frequency
            duration: Duration in seconds
            sampling_rate: Sampling rate in Hz
            add_noise: Whether to add noise
            noise_level: Noise amplitude
        
        Returns:
            Tuple of (signal, sampling_rate, metadata)
        """
        if len(frequencies) != len(amplitudes):
            raise ValueError("frequencies and amplitudes must have same length")
        
        t = np.arange(0, duration, 1/sampling_rate)
        signal = np.zeros(len(t))
        
        for freq, amp in zip(frequencies, amplitudes):
            signal += amp * np.sin(2 * np.pi * freq * t)
        
        if add_noise:
            noise = noise_level * np.random.randn(len(signal))
            signal += noise
        
        metadata = {
            'signal_type': 'MULTI_TONE',
            'frequencies': frequencies,
            'amplitudes': amplitudes,
            'duration': duration,
            'sampling_rate': sampling_rate
        }
        
        return signal, sampling_rate, metadata
