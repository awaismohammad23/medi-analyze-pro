"""
Time-series plotting module for MediAnalyze Pro
Creates time-series plots for health metrics and temporal data
"""

import logging
from typing import Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

logger = logging.getLogger(__name__)


class TimeSeriesPlotter:
    """
    Creates time-series plots for health metrics and temporal data
    """
    
    def __init__(self, figsize: Tuple[int, int] = (12, 6), dpi: int = 100):
        """
        Initialize time-series plotter
        
        Args:
            figsize: Figure size (width, height) in inches
            dpi: Resolution in dots per inch
        """
        self.figsize = figsize
        self.dpi = dpi
    
    def plot_health_metrics(
        self,
        data: Union[pd.DataFrame, Dict[str, np.ndarray]],
        time_column: Optional[str] = None,
        metrics: Optional[List[str]] = None,
        title: str = "Health Metrics Over Time",
        save_path: Optional[str] = None,
        show_plot: bool = True
    ) -> plt.Figure:
        """
        Plot multiple health metrics over time
        
        Args:
            data: DataFrame with time and metric columns, or dict with metric arrays
            time_column: Name of time column (if DataFrame)
            metrics: List of metric column names to plot (if None, plots all numeric columns)
            title: Plot title
            save_path: Path to save figure (if None, doesn't save)
            show_plot: Whether to display the plot
        
        Returns:
            Matplotlib figure object
        """
        fig, ax = plt.subplots(figsize=self.figsize, dpi=self.dpi)
        
        time_data = None  # Initialize to avoid UnboundLocalError
        
        # Handle DataFrame input
        if isinstance(data, pd.DataFrame):
            if time_column is None:
                # Try to find datetime column
                datetime_cols = data.select_dtypes(include=['datetime64']).columns
                if len(datetime_cols) > 0:
                    time_column = datetime_cols[0]
                    time_data = pd.to_datetime(data[time_column])
                else:
                    # Use index if no datetime column
                    time_data = data.index
                    time_column = 'index'
            else:
                time_data = pd.to_datetime(data[time_column])
            
            # Select metrics to plot
            if metrics is None:
                numeric_cols = data.select_dtypes(include=[np.number]).columns
                metrics = [col for col in numeric_cols if col != time_column]
            
            # Plot each metric
            for metric in metrics:
                if metric in data.columns:
                    ax.plot(time_data, data[metric], label=metric, linewidth=2, alpha=0.7)
        
        # Handle dict input
        elif isinstance(data, dict):
            if 'time' in data:
                time_data = pd.to_datetime(data['time'])
            elif time_column and time_column in data:
                time_data = pd.to_datetime(data[time_column])
            else:
                # Generate time index
                max_len = max(len(v) for v in data.values() if isinstance(v, np.ndarray))
                time_data = pd.date_range(start='2024-01-01', periods=max_len, freq='D')
            
            # Plot metrics
            if metrics is None:
                metrics = [k for k in data.keys() if k not in ['time', time_column]]
            
            for metric in metrics:
                if metric in data:
                    metric_data = data[metric]
                    if len(metric_data) == len(time_data):
                        ax.plot(time_data, metric_data, label=metric, linewidth=2, alpha=0.7)
        
        else:
            # Handle other input types - use numeric index
            if isinstance(data, np.ndarray):
                time_data = np.arange(len(data))
                ax.plot(time_data, data, label='Data', linewidth=2, alpha=0.7)
            else:
                raise ValueError(f"Unsupported data type: {type(data)}. Expected DataFrame, dict, or numpy array.")
        
        ax.set_xlabel('Time', fontsize=12, fontweight='bold')
        ax.set_ylabel('Value', fontsize=12, fontweight='bold')
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.legend(loc='best', framealpha=0.9)
        ax.grid(True, alpha=0.3, linestyle='--')
        
        # Format x-axis for dates (only if time_data is datetime)
        if time_data is not None and isinstance(time_data, pd.DatetimeIndex):
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            ax.xaxis.set_major_locator(mdates.AutoDateLocator())
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        plt.tight_layout()
        
        if save_path:
            fig.savefig(save_path, dpi=self.dpi, bbox_inches='tight')
            logger.info(f"Saved time-series plot to {save_path}")
        
        if show_plot:
            plt.show()
        else:
            plt.close(fig)
        
        return fig
    
    def plot_single_metric(
        self,
        time_data: Union[pd.Series, np.ndarray, List],
        metric_data: np.ndarray,
        metric_name: str = "Metric",
        title: Optional[str] = None,
        color: str = 'blue',
        save_path: Optional[str] = None,
        show_plot: bool = True
    ) -> plt.Figure:
        """
        Plot a single metric over time
        
        Args:
            time_data: Time values (datetime or numeric)
            metric_data: Metric values
            metric_name: Name of the metric
            title: Plot title (if None, uses metric_name)
            color: Line color
            save_path: Path to save figure
            show_plot: Whether to display the plot
        
        Returns:
            Matplotlib figure object
        """
        fig, ax = plt.subplots(figsize=self.figsize, dpi=self.dpi)
        
        # Convert time data
        if isinstance(time_data, (list, np.ndarray)):
            if isinstance(time_data[0], (datetime, pd.Timestamp)):
                time_data = pd.to_datetime(time_data)
            else:
                time_data = np.array(time_data)
        
        ax.plot(time_data, metric_data, color=color, linewidth=2, alpha=0.7, label=metric_name)
        
        ax.set_xlabel('Time', fontsize=12, fontweight='bold')
        ax.set_ylabel(metric_name, fontsize=12, fontweight='bold')
        ax.set_title(title or f"{metric_name} Over Time", fontsize=14, fontweight='bold')
        ax.legend(loc='best', framealpha=0.9)
        ax.grid(True, alpha=0.3, linestyle='--')
        
        # Format x-axis for dates
        if isinstance(time_data, pd.DatetimeIndex):
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            ax.xaxis.set_major_locator(mdates.AutoDateLocator())
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        plt.tight_layout()
        
        if save_path:
            fig.savefig(save_path, dpi=self.dpi, bbox_inches='tight')
            logger.info(f"Saved single metric plot to {save_path}")
        
        if show_plot:
            plt.show()
        else:
            plt.close(fig)
        
        return fig
    
    def plot_multiple_patients(
        self,
        data: Dict[str, pd.DataFrame],
        metric_name: str,
        time_column: str = 'timestamp',
        title: Optional[str] = None,
        save_path: Optional[str] = None,
        show_plot: bool = True
    ) -> plt.Figure:
        """
        Plot the same metric for multiple patients
        
        Args:
            data: Dictionary with patient_id as key and DataFrame as value
            metric_name: Name of metric to plot
            time_column: Name of time column
            title: Plot title
            save_path: Path to save figure
            show_plot: Whether to display the plot
        
        Returns:
            Matplotlib figure object
        """
        fig, ax = plt.subplots(figsize=self.figsize, dpi=self.dpi)
        
        colors = plt.cm.tab10(np.linspace(0, 1, len(data)))
        
        for (patient_id, df), color in zip(data.items(), colors):
            if time_column in df.columns and metric_name in df.columns:
                time_data = pd.to_datetime(df[time_column])
                ax.plot(time_data, df[metric_name], label=f"Patient {patient_id}", 
                       color=color, linewidth=2, alpha=0.7)
        
        ax.set_xlabel('Time', fontsize=12, fontweight='bold')
        ax.set_ylabel(metric_name, fontsize=12, fontweight='bold')
        ax.set_title(title or f"{metric_name} Comparison Across Patients", 
                    fontsize=14, fontweight='bold')
        ax.legend(loc='best', framealpha=0.9)
        ax.grid(True, alpha=0.3, linestyle='--')
        
        # Format x-axis for dates
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        plt.tight_layout()
        
        if save_path:
            fig.savefig(save_path, dpi=self.dpi, bbox_inches='tight')
            logger.info(f"Saved multi-patient plot to {save_path}")
        
        if show_plot:
            plt.show()
        else:
            plt.close(fig)
        
        return fig
    
    def plot_with_statistics(
        self,
        time_data: Union[pd.Series, np.ndarray],
        metric_data: np.ndarray,
        metric_name: str = "Metric",
        show_mean: bool = True,
        show_std: bool = True,
        save_path: Optional[str] = None,
        show_plot: bool = True
    ) -> plt.Figure:
        """
        Plot metric with mean and standard deviation bands
        
        Args:
            time_data: Time values
            metric_data: Metric values
            metric_name: Name of the metric
            show_mean: Whether to show mean line
            show_std: Whether to show std deviation band
            save_path: Path to save figure
            show_plot: Whether to display the plot
        
        Returns:
            Matplotlib figure object
        """
        fig, ax = plt.subplots(figsize=self.figsize, dpi=self.dpi)
        
        mean_val = np.mean(metric_data)
        std_val = np.std(metric_data)
        
        ax.plot(time_data, metric_data, 'b-', linewidth=2, alpha=0.7, label=metric_name)
        
        if show_mean:
            ax.axhline(y=mean_val, color='r', linestyle='--', linewidth=2, 
                      label=f'Mean: {mean_val:.2f}')
        
        if show_std:
            ax.fill_between(time_data, 
                           mean_val - std_val, 
                           mean_val + std_val, 
                           alpha=0.2, color='gray', 
                           label=f'±1 Std Dev: {std_val:.2f}')
        
        ax.set_xlabel('Time', fontsize=12, fontweight='bold')
        ax.set_ylabel(metric_name, fontsize=12, fontweight='bold')
        ax.set_title(f"{metric_name} with Statistics", fontsize=14, fontweight='bold')
        ax.legend(loc='best', framealpha=0.9)
        ax.grid(True, alpha=0.3, linestyle='--')
        
        plt.tight_layout()
        
        if save_path:
            fig.savefig(save_path, dpi=self.dpi, bbox_inches='tight')
            logger.info(f"Saved statistics plot to {save_path}")
        
        if show_plot:
            plt.show()
        else:
            plt.close(fig)
        
        return fig
