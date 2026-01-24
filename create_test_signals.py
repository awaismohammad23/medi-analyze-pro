"""
Script to create sample signal CSV files for testing spectrum analysis
"""

import sys
import os
import numpy as np
import pandas as pd

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.signal_processing import SignalGenerator

# Create output directory
output_dir = os.path.join('data', 'signals')
os.makedirs(output_dir, exist_ok=True)

print("Generating test signal files...")

# 1. ECG signal with time column (10 seconds, 250 Hz)
print("1. Creating ECG signal with time column...")
ecg_signal, sr, metadata = SignalGenerator.generate_ecg(
    duration=10.0,
    sampling_rate=250.0,
    heart_rate=72.0,
    noise_level=0.02
)
time = np.arange(len(ecg_signal)) / sr
df_ecg = pd.DataFrame({
    'time': time,
    'amplitude': ecg_signal
})
ecg_file = os.path.join(output_dir, 'ecg_signal_with_time.csv')
df_ecg.to_csv(ecg_file, index=False)
print(f"   Saved: {ecg_file}")
print(f"   Samples: {len(ecg_signal)}, Duration: {metadata['duration']:.2f}s, Sampling Rate: {sr} Hz")

# 2. ECG signal without time column (just amplitude)
print("\n2. Creating ECG signal without time column...")
ecg_signal2, sr2, _ = SignalGenerator.generate_ecg(
    duration=15.0,
    sampling_rate=250.0,
    heart_rate=80.0,
    noise_level=0.03
)
df_ecg2 = pd.DataFrame({
    'ecg_amplitude': ecg_signal2
})
ecg_file2 = os.path.join(output_dir, 'ecg_signal_no_time.csv')
df_ecg2.to_csv(ecg_file2, index=False)
print(f"   Saved: {ecg_file2}")
print(f"   Samples: {len(ecg_signal2)}, Sampling Rate: {sr2} Hz (default)")

# 3. EEG signal with time column (10 seconds, 256 Hz)
print("\n3. Creating EEG signal with time column...")
eeg_signal, sr_eeg, metadata_eeg = SignalGenerator.generate_eeg(
    duration=10.0,
    sampling_rate=256.0
)
time_eeg = np.arange(len(eeg_signal)) / sr_eeg
df_eeg = pd.DataFrame({
    'timestamp': time_eeg,
    'eeg_channel1': eeg_signal
})
eeg_file = os.path.join(output_dir, 'eeg_signal_with_time.csv')
df_eeg.to_csv(eeg_file, index=False)
print(f"   Saved: {eeg_file}")
print(f"   Samples: {len(eeg_signal)}, Duration: {metadata_eeg['duration']:.2f}s, Sampling Rate: {sr_eeg} Hz")

# 4. EEG signal without time column
print("\n4. Creating EEG signal without time column...")
eeg_signal2, sr_eeg2, _ = SignalGenerator.generate_eeg(
    duration=12.0,
    sampling_rate=256.0
)
df_eeg2 = pd.DataFrame({
    'eeg_amplitude': eeg_signal2
})
eeg_file2 = os.path.join(output_dir, 'eeg_signal_no_time.csv')
df_eeg2.to_csv(eeg_file2, index=False)
print(f"   Saved: {eeg_file2}")
print(f"   Samples: {len(eeg_signal2)}, Sampling Rate: {sr_eeg2} Hz (default)")

# 5. Multi-channel ECG (with multiple columns)
print("\n5. Creating multi-channel ECG signal...")
ecg_ch1, sr_multi, _ = SignalGenerator.generate_ecg(
    duration=8.0,
    sampling_rate=250.0,
    heart_rate=75.0,
    noise_level=0.02
)
ecg_ch2, _, _ = SignalGenerator.generate_ecg(
    duration=8.0,
    sampling_rate=250.0,
    heart_rate=75.0,
    noise_level=0.025
)
time_multi = np.arange(len(ecg_ch1)) / sr_multi
df_multi = pd.DataFrame({
    'sample': np.arange(len(ecg_ch1)),
    'time': time_multi,
    'ecg_channel1': ecg_ch1,
    'ecg_channel2': ecg_ch2,
    'heart_rate': np.full(len(ecg_ch1), 75.0)
})
multi_file = os.path.join(output_dir, 'ecg_multichannel.csv')
df_multi.to_csv(multi_file, index=False)
print(f"   Saved: {multi_file}")
print(f"   Samples: {len(ecg_ch1)}, Duration: 8.0s, Sampling Rate: {sr_multi} Hz")

# 6. High-frequency ECG (for testing frequency range)
print("\n6. Creating high-frequency ECG signal (500 Hz)...")
ecg_hf, sr_hf, _ = SignalGenerator.generate_ecg(
    duration=5.0,
    sampling_rate=500.0,
    heart_rate=90.0,
    noise_level=0.015
)
time_hf = np.arange(len(ecg_hf)) / sr_hf
df_hf = pd.DataFrame({
    'time': time_hf,
    'amplitude': ecg_hf
})
hf_file = os.path.join(output_dir, 'ecg_high_frequency.csv')
df_hf.to_csv(hf_file, index=False)
print(f"   Saved: {hf_file}")
print(f"   Samples: {len(ecg_hf)}, Duration: 5.0s, Sampling Rate: {sr_hf} Hz")

# 7. Long duration ECG (for testing with more data)
print("\n7. Creating long-duration ECG signal (30 seconds)...")
ecg_long, sr_long, _ = SignalGenerator.generate_ecg(
    duration=30.0,
    sampling_rate=250.0,
    heart_rate=70.0,
    noise_level=0.02
)
time_long = np.arange(len(ecg_long)) / sr_long
df_long = pd.DataFrame({
    't': time_long,
    'signal': ecg_long
})
long_file = os.path.join(output_dir, 'ecg_long_duration.csv')
df_long.to_csv(long_file, index=False)
print(f"   Saved: {long_file}")
print(f"   Samples: {len(ecg_long)}, Duration: 30.0s, Sampling Rate: {sr_long} Hz")

print("\n" + "="*60)
print("All test signal files created successfully!")
print("="*60)
print(f"\nFiles saved in: {os.path.abspath(output_dir)}")
print("\nFile list:")
print("  1. ecg_signal_with_time.csv - ECG with time column (10s, 250 Hz)")
print("  2. ecg_signal_no_time.csv - ECG without time (15s, 250 Hz)")
print("  3. eeg_signal_with_time.csv - EEG with timestamp (10s, 256 Hz)")
print("  4. eeg_signal_no_time.csv - EEG without time (12s, 256 Hz)")
print("  5. ecg_multichannel.csv - Multi-channel ECG (8s, 250 Hz)")
print("  6. ecg_high_frequency.csv - High-freq ECG (5s, 500 Hz)")
print("  7. ecg_long_duration.csv - Long ECG (30s, 250 Hz)")
print("\nYou can now use these files to test the Spectrum Analysis tab!")
