"""
Unit tests for signal processing modules
Tests signal loading, preprocessing, spectrum analysis, and signal generation
"""

import pytest
import os
import sys
import tempfile
import numpy as np
import pandas as pd

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.signal_processing.signal_loader import SignalLoader
from src.signal_processing.preprocessing import SignalPreprocessor
from src.signal_processing.spectrum import SpectrumAnalyzer
from src.signal_processing.signal_generator import SignalGenerator
from src.database.connection import DatabaseConnection


@pytest.fixture
def sample_signal():
    """Create sample signal for testing"""
    t = np.linspace(0, 1, 1000)
    signal = np.sin(2 * np.pi * 10 * t) + 0.5 * np.sin(2 * np.pi * 20 * t)
    return signal, 1000.0  # signal, sampling_rate


@pytest.fixture
def csv_signal_file():
    """Create temporary CSV file with signal data"""
    t = np.linspace(0, 1, 100)
    signal = np.sin(2 * np.pi * 10 * t)
    
    df = pd.DataFrame({
        'time': t,
        'amplitude': signal
    })
    
    fd, csv_path = tempfile.mkstemp(suffix='.csv')
    os.close(fd)
    
    df.to_csv(csv_path, index=False)
    
    yield csv_path
    
    if os.path.exists(csv_path):
        os.remove(csv_path)


@pytest.fixture
def db_connection():
    """Create a temporary database for testing"""
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    db_url = f'sqlite:///{db_path}'
    db_conn = DatabaseConnection(db_url)
    db_conn.create_tables()
    
    yield db_conn
    
    db_conn.close()
    if os.path.exists(db_path):
        os.remove(db_path)


class TestSignalLoader:
    """Test signal loading functionality"""
    
    def test_load_signal_from_csv(self, csv_signal_file):
        """Test loading signal from CSV"""
        loader = SignalLoader()
        signal, sampling_rate, metadata = loader.load_signal_from_csv(csv_signal_file)
        
        assert len(signal) > 0
        assert sampling_rate > 0
        assert 'signal_length' in metadata
        assert metadata['signal_length'] == len(signal)
    
    def test_load_signal_from_array(self):
        """Test loading signal from array"""
        loader = SignalLoader()
        signal_data = np.sin(np.linspace(0, 2*np.pi, 100))
        
        signal, sampling_rate, metadata = loader.load_signal_from_array(
            signal_data, 1000.0
        )
        
        assert len(signal) == 100
        assert sampling_rate == 1000.0
        assert metadata['sampling_rate'] == 1000.0
    
    def test_save_signal_to_csv(self):
        """Test saving signal to CSV"""
        loader = SignalLoader()
        signal = np.sin(np.linspace(0, 2*np.pi, 100))
        
        fd, output_path = tempfile.mkstemp(suffix='.csv')
        os.close(fd)
        
        try:
            success = loader.save_signal_to_csv(signal, output_path, 1000.0)
            assert success
            assert os.path.exists(output_path)
            
            # Verify can load it back
            loaded_signal, sr, _ = loader.load_signal_from_csv(output_path)
            assert len(loaded_signal) == len(signal)
        finally:
            if os.path.exists(output_path):
                os.remove(output_path)
    
    def test_detect_signal_type(self):
        """Test signal type detection"""
        loader = SignalLoader()
        
        # Generate ECG-like signal
        ecg_signal, sr, _ = SignalGenerator.generate_ecg(duration=1.0, sampling_rate=250.0)
        signal_type = loader.detect_signal_type(ecg_signal, sr)
        # Should detect as ECG or UNKNOWN (detection is approximate)
        assert signal_type in ['ECG', 'UNKNOWN']


class TestSignalPreprocessor:
    """Test signal preprocessing functionality"""
    
    def test_normalize_zscore(self, sample_signal):
        """Test Z-score normalization"""
        signal, _ = sample_signal
        normalized = SignalPreprocessor.normalize(signal, method='zscore')
        
        assert np.abs(np.mean(normalized)) < 1e-10  # Should be near zero
        assert np.abs(np.std(normalized) - 1.0) < 1e-10  # Should be near 1
    
    def test_normalize_minmax(self, sample_signal):
        """Test min-max normalization"""
        signal, _ = sample_signal
        normalized = SignalPreprocessor.normalize(signal, method='minmax', range_min=-1, range_max=1)
        
        assert np.min(normalized) >= -1
        assert np.max(normalized) <= 1
    
    def test_remove_dc_offset(self, sample_signal):
        """Test DC offset removal"""
        signal, _ = sample_signal
        signal_with_offset = signal + 5.0  # Add DC offset
        
        corrected = SignalPreprocessor.remove_dc_offset(signal_with_offset)
        
        assert np.abs(np.mean(corrected)) < 1e-10
    
    def test_bandpass_filter(self, sample_signal):
        """Test bandpass filtering"""
        signal, sampling_rate = sample_signal
        filtered = SignalPreprocessor.apply_bandpass_filter(
            signal, sampling_rate, lowcut=5.0, highcut=25.0
        )
        
        assert len(filtered) == len(signal)
        assert not np.any(np.isnan(filtered))
    
    def test_lowpass_filter(self, sample_signal):
        """Test lowpass filtering"""
        signal, sampling_rate = sample_signal
        filtered = SignalPreprocessor.apply_lowpass_filter(
            signal, sampling_rate, cutoff=20.0
        )
        
        assert len(filtered) == len(signal)
    
    def test_median_filter(self, sample_signal):
        """Test median filtering"""
        signal, _ = sample_signal
        # Add impulse noise
        noisy_signal = signal.copy()
        noisy_signal[100] = 100.0  # Impulse
        
        filtered = SignalPreprocessor.apply_median_filter(noisy_signal, kernel_size=3)
        
        assert len(filtered) == len(signal)
        assert filtered[100] != 100.0  # Should be filtered
    
    def test_preprocess_pipeline(self, sample_signal):
        """Test preprocessing pipeline"""
        signal, sampling_rate = sample_signal
        
        steps = [
            {'method': 'remove_dc_offset'},
            {'method': 'normalize', 'method_type': 'zscore'},
            {'method': 'reduce_noise', 'noise_method': 'lowpass', 'cutoff': 30.0}
        ]
        
        processed = SignalPreprocessor.preprocess_pipeline(signal, sampling_rate, steps)
        
        assert len(processed) == len(signal)
        assert not np.any(np.isnan(processed))


class TestSpectrumAnalyzer:
    """Test spectrum analysis functionality"""
    
    def test_compute_fft(self, sample_signal):
        """Test FFT computation"""
        signal, sampling_rate = sample_signal
        analyzer = SpectrumAnalyzer()
        
        frequencies, fft_values = analyzer.compute_fft(signal, sampling_rate)
        
        assert len(frequencies) > 0
        assert len(fft_values) == len(frequencies)
        assert np.all(frequencies >= 0)  # Only positive frequencies
    
    def test_compute_power_spectrum(self, sample_signal):
        """Test power spectrum computation"""
        signal, sampling_rate = sample_signal
        analyzer = SpectrumAnalyzer()
        
        frequencies, power = analyzer.compute_power_spectrum(signal, sampling_rate)
        
        assert len(frequencies) > 0
        assert len(power) == len(frequencies)
        assert np.all(power >= 0)  # Power should be non-negative
    
    def test_compute_psd_welch(self, sample_signal):
        """Test PSD computation using Welch method"""
        signal, sampling_rate = sample_signal
        analyzer = SpectrumAnalyzer()
        
        frequencies, psd = analyzer.compute_psd(signal, sampling_rate, method='welch')
        
        assert len(frequencies) > 0
        assert len(psd) == len(frequencies)
        assert np.all(psd >= 0)
    
    def test_find_dominant_frequencies(self, sample_signal):
        """Test finding dominant frequencies"""
        signal, sampling_rate = sample_signal
        analyzer = SpectrumAnalyzer()
        
        frequencies, power = analyzer.compute_power_spectrum(signal, sampling_rate)
        dominant = analyzer.find_dominant_frequencies(frequencies, power, n_peaks=3)
        
        assert len(dominant) > 0
        assert all('frequency' in d for d in dominant)
        assert all('power' in d for d in dominant)
    
    def test_analyze_spectrum(self, sample_signal):
        """Test complete spectrum analysis"""
        signal, sampling_rate = sample_signal
        analyzer = SpectrumAnalyzer()
        
        result = analyzer.analyze_spectrum(signal, sampling_rate, store_in_db=False)
        
        assert 'frequencies' in result
        assert 'power_spectrum' in result
        assert 'dominant_frequencies' in result
        assert 'total_power' in result
        assert 'max_frequency' in result


class TestSignalGenerator:
    """Test signal generation functionality"""
    
    def test_generate_ecg(self):
        """Test ECG signal generation"""
        signal, sampling_rate, metadata = SignalGenerator.generate_ecg(
            duration=2.0, sampling_rate=250.0, heart_rate=72.0
        )
        
        assert len(signal) > 0
        assert sampling_rate == 250.0
        assert metadata['signal_type'] == 'ECG'
        assert metadata['heart_rate'] == 72.0
        assert metadata['duration'] == 2.0
    
    def test_generate_eeg(self):
        """Test EEG signal generation"""
        signal, sampling_rate, metadata = SignalGenerator.generate_eeg(
            duration=2.0, sampling_rate=256.0
        )
        
        assert len(signal) > 0
        assert sampling_rate == 256.0
        assert metadata['signal_type'] == 'EEG'
        assert 'frequency_bands' in metadata
    
    def test_generate_sine_wave(self):
        """Test sine wave generation"""
        signal, sampling_rate, metadata = SignalGenerator.generate_sine_wave(
            frequency=10.0, duration=1.0, sampling_rate=1000.0
        )
        
        assert len(signal) > 0
        assert sampling_rate == 1000.0
        assert metadata['frequency'] == 10.0
        assert metadata['signal_type'] == 'SINE'
    
    def test_generate_multi_tone(self):
        """Test multi-tone signal generation"""
        frequencies = [10.0, 20.0, 30.0]
        amplitudes = [1.0, 0.5, 0.3]
        
        signal, sampling_rate, metadata = SignalGenerator.generate_multi_tone(
            frequencies, amplitudes, duration=1.0
        )
        
        assert len(signal) > 0
        assert metadata['frequencies'] == frequencies
        assert metadata['amplitudes'] == amplitudes


class TestIntegration:
    """Integration tests for signal processing pipeline"""
    
    def test_full_pipeline(self):
        """Test complete signal processing pipeline"""
        # Generate signal
        signal, sampling_rate, _ = SignalGenerator.generate_ecg(duration=5.0)
        
        # Preprocess
        preprocessed = SignalPreprocessor.preprocess_pipeline(
            signal, sampling_rate,
            steps=[
                {'method': 'remove_dc_offset'},
                {'method': 'normalize', 'method_type': 'zscore'},
                {'method': 'reduce_noise', 'noise_method': 'bandpass', 'lowcut': 0.5, 'highcut': 40.0}
            ]
        )
        
        # Analyze spectrum
        analyzer = SpectrumAnalyzer()
        result = analyzer.analyze_spectrum(preprocessed, sampling_rate)
        
        assert 'dominant_frequencies' in result
        assert len(result['dominant_frequencies']) > 0
        
        # Verify dominant frequency is in expected range for ECG
        dominant_freq = result['dominant_frequencies'][0]['frequency']
        assert 0.5 <= dominant_freq <= 5.0  # Heart rate range
    
    def test_signal_load_preprocess_analyze(self, csv_signal_file):
        """Test loading, preprocessing, and analyzing signal"""
        # Load
        loader = SignalLoader()
        signal, sampling_rate, _ = loader.load_signal_from_csv(csv_signal_file)
        
        # Preprocess
        preprocessed = SignalPreprocessor.normalize(signal, method='zscore')
        
        # Analyze
        analyzer = SpectrumAnalyzer()
        result = analyzer.analyze_spectrum(preprocessed, sampling_rate)
        
        assert 'power_spectrum' in result
        assert len(result['frequencies']) > 0
    
    def test_database_integration(self, db_connection):
        """Test spectrum analysis with database storage"""
        # Generate signal
        signal, sampling_rate, _ = SignalGenerator.generate_ecg(duration=2.0)
        
        # Create signal record in database
        session = db_connection.get_session()
        from src.database import crud
        
        signal_record = crud.insert_biomedical_signal(
            session=session,
            signal_type='ECG',
            signal_data_path='/test/path.csv',
            sampling_rate=sampling_rate,
            duration=2.0
        )
        session.commit()
        
        # Analyze and store
        analyzer = SpectrumAnalyzer(session=session)
        result = analyzer.analyze_spectrum(
            signal, sampling_rate,
            store_in_db=True,
            signal_id=signal_record.signal_id
        )
        
        # Verify stored
        from src.database import crud
        analyses = crud.retrieve_spectrum_analyses(session, signal_id=signal_record.signal_id)
        assert len(analyses) > 0
        
        session.close()
