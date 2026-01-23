"""
FFT spectrum plotting module for MediAnalyze Pro
Creates frequency domain visualizations for biomedical signals
"""

import logging
from typing import Dict, List, Optional, Tuple, Union
import numpy as np
import matplotlib.pyplot as plt
from scipy import signal

logger = logging.getLogger(__name__)


class SpectrumPlotter:
    """
    Creates FFT spectrum plots for biomedical signals
    """
    
    def __init__(self, figsize: Tuple[int, int] = (12, 8), dpi: int = 100):
        """
        Initialize spectrum plotter
        
        Args:
            figsize: Figure size (width, height) in inches
            dpi: Resolution in dots per inch
        """
        self.figsize = figsize
        self.dpi = dpi
    
    def plot_fft_spectrum(
        self,
        signal_data: np.ndarray,
        sample_rate: float,
        title: str = "FFT Spectrum",
        xlim: Optional[Tuple[float, float]] = None,
        highlight_frequencies: Optional[List[float]] = None,
        save_path: Optional[str] = None,
        show_plot: bool = True
    ) -> plt.Figure:
        """
        Plot FFT magnitude spectrum
        
        Args:
            signal_data: Time-domain signal
            sample_rate: Sampling rate in Hz
            title: Plot title
            xlim: Optional frequency range (min_freq, max_freq) in Hz
            highlight_frequencies: Optional list of frequencies to highlight
            save_path: Path to save figure
            show_plot: Whether to display the plot
        
        Returns:
            Matplotlib figure object
        """
        # Compute FFT
        n = len(signal_data)
        fft_values = np.fft.fft(signal_data)
        fft_magnitude = np.abs(fft_values)
        frequencies = np.fft.fftfreq(n, 1/sample_rate)
        
        # Take only positive frequencies
        positive_freq_idx = frequencies >= 0
        frequencies = frequencies[positive_freq_idx]
        fft_magnitude = fft_magnitude[positive_freq_idx]
        
        fig, ax = plt.subplots(figsize=self.figsize, dpi=self.dpi)
        
        ax.plot(frequencies, fft_magnitude, linewidth=2, alpha=0.8)
        
        # Highlight specific frequencies
        if highlight_frequencies:
            for freq in highlight_frequencies:
                idx = np.argmin(np.abs(frequencies - freq))
                ax.axvline(x=freq, color='r', linestyle='--', linewidth=2, alpha=0.7)
                ax.plot(frequencies[idx], fft_magnitude[idx], 'ro', markersize=10)
        
        ax.set_xlabel('Frequency (Hz)', fontsize=12, fontweight='bold')
        ax.set_ylabel('Magnitude', fontsize=12, fontweight='bold')
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3, linestyle='--')
        
        if xlim:
            ax.set_xlim(xlim)
        
        plt.tight_layout()
        
        if save_path:
            fig.savefig(save_path, dpi=self.dpi, bbox_inches='tight')
            logger.info(f"Saved FFT spectrum to {save_path}")
        
        if show_plot:
            plt.show()
        else:
            plt.close(fig)
        
        return fig
    
    def plot_power_spectrum(
        self,
        signal_data: np.ndarray,
        sample_rate: float,
        method: str = 'welch',
        title: str = "Power Spectral Density",
        xlim: Optional[Tuple[float, float]] = None,
        save_path: Optional[str] = None,
        show_plot: bool = True
    ) -> plt.Figure:
        """
        Plot power spectral density (PSD)
        
        Args:
            signal_data: Time-domain signal
            sample_rate: Sampling rate in Hz
            method: PSD method ('welch' or 'periodogram')
            title: Plot title
            xlim: Optional frequency range
            save_path: Path to save figure
            show_plot: Whether to display the plot
        
        Returns:
            Matplotlib figure object
        """
        if method == 'welch':
            frequencies, psd = signal.welch(signal_data, sample_rate, nperseg=min(256, len(signal_data)//4))
        else:  # periodogram
            frequencies, psd = signal.periodogram(signal_data, sample_rate)
        
        fig, ax = plt.subplots(figsize=self.figsize, dpi=self.dpi)
        
        ax.semilogy(frequencies, psd, linewidth=2, alpha=0.8)
        
        ax.set_xlabel('Frequency (Hz)', fontsize=12, fontweight='bold')
        ax.set_ylabel('Power Spectral Density', fontsize=12, fontweight='bold')
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3, linestyle='--')
        
        if xlim:
            ax.set_xlim(xlim)
        
        plt.tight_layout()
        
        if save_path:
            fig.savefig(save_path, dpi=self.dpi, bbox_inches='tight')
            logger.info(f"Saved power spectrum to {save_path}")
        
        if show_plot:
            plt.show()
        else:
            plt.close(fig)
        
        return fig
    
    def plot_time_frequency(
        self,
        signal_data: np.ndarray,
        sample_rate: float,
        title: str = "Time-Frequency Analysis",
        save_path: Optional[str] = None,
        show_plot: bool = True
    ) -> plt.Figure:
        """
        Plot time-domain signal and frequency spectrum side by side
        
        Args:
            signal_data: Time-domain signal
            sample_rate: Sampling rate in Hz
            title: Plot title
            save_path: Path to save figure
            show_plot: Whether to display the plot
        
        Returns:
            Matplotlib figure object
        """
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(self.figsize[0], self.figsize[1] * 1.5), 
                                       dpi=self.dpi)
        
        # Time domain
        time = np.arange(len(signal_data)) / sample_rate
        ax1.plot(time, signal_data, linewidth=1.5, alpha=0.8)
        ax1.set_xlabel('Time (s)', fontsize=12, fontweight='bold')
        ax1.set_ylabel('Amplitude', fontsize=12, fontweight='bold')
        ax1.set_title('Time Domain', fontsize=12, fontweight='bold')
        ax1.grid(True, alpha=0.3, linestyle='--')
        
        # Frequency domain
        n = len(signal_data)
        fft_values = np.fft.fft(signal_data)
        fft_magnitude = np.abs(fft_values)
        frequencies = np.fft.fftfreq(n, 1/sample_rate)
        
        positive_freq_idx = frequencies >= 0
        frequencies = frequencies[positive_freq_idx]
        fft_magnitude = fft_magnitude[positive_freq_idx]
        
        ax2.plot(frequencies, fft_magnitude, linewidth=1.5, alpha=0.8, color='orange')
        ax2.set_xlabel('Frequency (Hz)', fontsize=12, fontweight='bold')
        ax2.set_ylabel('Magnitude', fontsize=12, fontweight='bold')
        ax2.set_title('Frequency Domain (FFT)', fontsize=12, fontweight='bold')
        ax2.grid(True, alpha=0.3, linestyle='--')
        
        fig.suptitle(title, fontsize=16, fontweight='bold', y=0.98)
        plt.tight_layout()
        
        if save_path:
            fig.savefig(save_path, dpi=self.dpi, bbox_inches='tight')
            logger.info(f"Saved time-frequency plot to {save_path}")
        
        if show_plot:
            plt.show()
        else:
            plt.close(fig)
        
        return fig
    
    def plot_multiple_signals(
        self,
        signals: Dict[str, Tuple[np.ndarray, float]],
        title: str = "Multiple Signal Spectra",
        xlim: Optional[Tuple[float, float]] = None,
        save_path: Optional[str] = None,
        show_plot: bool = True
    ) -> plt.Figure:
        """
        Plot FFT spectra for multiple signals
        
        Args:
            signals: Dictionary with signal names as keys and (signal_data, sample_rate) tuples
            title: Plot title
            xlim: Optional frequency range
            save_path: Path to save figure
            show_plot: Whether to display the plot
        
        Returns:
            Matplotlib figure object
        """
        fig, ax = plt.subplots(figsize=self.figsize, dpi=self.dpi)
        
        colors = plt.cm.tab10(np.linspace(0, 1, len(signals)))
        
        for (signal_name, (signal_data, sample_rate)), color in zip(signals.items(), colors):
            n = len(signal_data)
            fft_values = np.fft.fft(signal_data)
            fft_magnitude = np.abs(fft_values)
            frequencies = np.fft.fftfreq(n, 1/sample_rate)
            
            positive_freq_idx = frequencies >= 0
            frequencies = frequencies[positive_freq_idx]
            fft_magnitude = fft_magnitude[positive_freq_idx]
            
            ax.plot(frequencies, fft_magnitude, label=signal_name, 
                   linewidth=2, alpha=0.7, color=color)
        
        ax.set_xlabel('Frequency (Hz)', fontsize=12, fontweight='bold')
        ax.set_ylabel('Magnitude', fontsize=12, fontweight='bold')
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.legend(loc='best', framealpha=0.9)
        ax.grid(True, alpha=0.3, linestyle='--')
        
        if xlim:
            ax.set_xlim(xlim)
        
        plt.tight_layout()
        
        if save_path:
            fig.savefig(save_path, dpi=self.dpi, bbox_inches='tight')
            logger.info(f"Saved multiple signal spectra to {save_path}")
        
        if show_plot:
            plt.show()
        else:
            plt.close(fig)
        
        return fig
    
    def plot_phase_spectrum(
        self,
        signal_data: np.ndarray,
        sample_rate: float,
        title: str = "Phase Spectrum",
        xlim: Optional[Tuple[float, float]] = None,
        save_path: Optional[str] = None,
        show_plot: bool = True
    ) -> plt.Figure:
        """
        Plot FFT phase spectrum
        
        Args:
            signal_data: Time-domain signal
            sample_rate: Sampling rate in Hz
            title: Plot title
            xlim: Optional frequency range
            save_path: Path to save figure
            show_plot: Whether to display the plot
        
        Returns:
            Matplotlib figure object
        """
        n = len(signal_data)
        fft_values = np.fft.fft(signal_data)
        phase = np.angle(fft_values)
        frequencies = np.fft.fftfreq(n, 1/sample_rate)
        
        positive_freq_idx = frequencies >= 0
        frequencies = frequencies[positive_freq_idx]
        phase = phase[positive_freq_idx]
        
        fig, ax = plt.subplots(figsize=self.figsize, dpi=self.dpi)
        
        ax.plot(frequencies, phase, linewidth=2, alpha=0.8)
        
        ax.set_xlabel('Frequency (Hz)', fontsize=12, fontweight='bold')
        ax.set_ylabel('Phase (radians)', fontsize=12, fontweight='bold')
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3, linestyle='--')
        
        if xlim:
            ax.set_xlim(xlim)
        
        plt.tight_layout()
        
        if save_path:
            fig.savefig(save_path, dpi=self.dpi, bbox_inches='tight')
            logger.info(f"Saved phase spectrum to {save_path}")
        
        if show_plot:
            plt.show()
        else:
            plt.close(fig)
        
        return fig
