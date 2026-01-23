"""
Heatmap module for MediAnalyze Pro
Creates heatmaps for correlation matrices and data visualization
"""

import logging
from typing import Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

logger = logging.getLogger(__name__)


class HeatmapPlotter:
    """
    Creates heatmaps for correlation matrices and data visualization
    """
    
    def __init__(self, figsize: Tuple[int, int] = (10, 8), dpi: int = 100):
        """
        Initialize heatmap plotter
        
        Args:
            figsize: Figure size (width, height) in inches
            dpi: Resolution in dots per inch
        """
        self.figsize = figsize
        self.dpi = dpi
    
    def plot_correlation_matrix(
        self,
        data: Union[pd.DataFrame, np.ndarray],
        title: str = "Correlation Matrix",
        cmap: str = 'coolwarm',
        annotate: bool = True,
        vmin: float = -1.0,
        vmax: float = 1.0,
        save_path: Optional[str] = None,
        show_plot: bool = True
    ) -> plt.Figure:
        """
        Create correlation matrix heatmap
        
        Args:
            data: DataFrame or correlation matrix array
            title: Plot title
            cmap: Color map name
            annotate: Whether to annotate cells with values
            vmin: Minimum value for color scale
            vmax: Maximum value for color scale
            save_path: Path to save figure
            show_plot: Whether to display the plot
        
        Returns:
            Matplotlib figure object
        """
        # Calculate correlation if DataFrame provided
        if isinstance(data, pd.DataFrame):
            corr_matrix = data.corr()
            labels = corr_matrix.columns
        else:
            corr_matrix = pd.DataFrame(data)
            labels = [f'Var {i+1}' for i in range(data.shape[1])]
            corr_matrix.columns = labels
            corr_matrix.index = labels
        
        fig, ax = plt.subplots(figsize=self.figsize, dpi=self.dpi)
        
        sns.heatmap(
            corr_matrix,
            annot=annotate,
            fmt='.2f',
            cmap=cmap,
            vmin=vmin,
            vmax=vmax,
            center=0,
            square=True,
            linewidths=0.5,
            cbar_kws={"shrink": 0.8},
            ax=ax
        )
        
        ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
        
        plt.tight_layout()
        
        if save_path:
            fig.savefig(save_path, dpi=self.dpi, bbox_inches='tight')
            logger.info(f"Saved correlation heatmap to {save_path}")
        
        if show_plot:
            plt.show()
        else:
            plt.close(fig)
        
        return fig
    
    def plot_data_heatmap(
        self,
        data: Union[pd.DataFrame, np.ndarray],
        x_labels: Optional[List[str]] = None,
        y_labels: Optional[List[str]] = None,
        title: str = "Data Heatmap",
        cmap: str = 'viridis',
        annotate: bool = False,
        save_path: Optional[str] = None,
        show_plot: bool = True
    ) -> plt.Figure:
        """
        Create general data heatmap
        
        Args:
            data: DataFrame or 2D array
            x_labels: X-axis labels
            y_labels: Y-axis labels
            title: Plot title
            cmap: Color map name
            annotate: Whether to annotate cells with values
            save_path: Path to save figure
            show_plot: Whether to display the plot
        
        Returns:
            Matplotlib figure object
        """
        if isinstance(data, pd.DataFrame):
            heatmap_data = data
        else:
            heatmap_data = pd.DataFrame(data)
            if x_labels:
                heatmap_data.columns = x_labels[:data.shape[1]]
            if y_labels:
                heatmap_data.index = y_labels[:data.shape[0]]
        
        fig, ax = plt.subplots(figsize=self.figsize, dpi=self.dpi)
        
        sns.heatmap(
            heatmap_data,
            annot=annotate,
            fmt='.2f' if annotate else '',
            cmap=cmap,
            linewidths=0.5,
            cbar_kws={"shrink": 0.8},
            ax=ax
        )
        
        ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
        
        plt.tight_layout()
        
        if save_path:
            fig.savefig(save_path, dpi=self.dpi, bbox_inches='tight')
            logger.info(f"Saved data heatmap to {save_path}")
        
        if show_plot:
            plt.show()
        else:
            plt.close(fig)
        
        return fig
    
    def plot_time_series_heatmap(
        self,
        data: pd.DataFrame,
        time_column: str = 'timestamp',
        metrics: Optional[List[str]] = None,
        title: str = "Time Series Heatmap",
        cmap: str = 'YlOrRd',
        save_path: Optional[str] = None,
        show_plot: bool = True
    ) -> plt.Figure:
        """
        Create heatmap showing multiple metrics over time
        
        Args:
            data: DataFrame with time and metric columns
            time_column: Name of time column
            metrics: List of metric columns (if None, uses all numeric columns)
            title: Plot title
            cmap: Color map name
            save_path: Path to save figure
            show_plot: Whether to display the plot
        
        Returns:
            Matplotlib figure object
        """
        if metrics is None:
            numeric_cols = data.select_dtypes(include=[np.number]).columns
            metrics = [col for col in numeric_cols if col != time_column]
        
        # Prepare data for heatmap
        heatmap_data = data[metrics].T
        
        # Use time as column labels (format dates)
        if time_column in data.columns:
            time_labels = pd.to_datetime(data[time_column]).dt.strftime('%Y-%m-%d')
            # Limit number of labels for readability
            if len(time_labels) > 50:
                step = len(time_labels) // 20
                time_labels = [label if i % step == 0 else '' 
                              for i, label in enumerate(time_labels)]
            heatmap_data.columns = time_labels
        
        fig, ax = plt.subplots(figsize=(max(12, len(heatmap_data.columns) * 0.3), 
                                        max(6, len(metrics) * 0.5)), 
                               dpi=self.dpi)
        
        sns.heatmap(
            heatmap_data,
            cmap=cmap,
            linewidths=0.5,
            cbar_kws={"shrink": 0.8, "label": "Value"},
            ax=ax,
            xticklabels=len(heatmap_data.columns) <= 30  # Only show labels if not too many
        )
        
        ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
        ax.set_xlabel('Time', fontsize=12, fontweight='bold')
        ax.set_ylabel('Metrics', fontsize=12, fontweight='bold')
        
        if len(heatmap_data.columns) > 30:
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=90, ha='center')
        
        plt.tight_layout()
        
        if save_path:
            fig.savefig(save_path, dpi=self.dpi, bbox_inches='tight')
            logger.info(f"Saved time-series heatmap to {save_path}")
        
        if show_plot:
            plt.show()
        else:
            plt.close(fig)
        
        return fig
    
    def plot_clustered_heatmap(
        self,
        data: pd.DataFrame,
        title: str = "Clustered Heatmap",
        cmap: str = 'viridis',
        method: str = 'ward',
        metric: str = 'euclidean',
        save_path: Optional[str] = None,
        show_plot: bool = True
    ) -> plt.Figure:
        """
        Create clustered heatmap with hierarchical clustering
        
        Args:
            data: DataFrame with data
            title: Plot title
            cmap: Color map name
            method: Clustering method
            metric: Distance metric
            save_path: Path to save figure
            show_plot: Whether to display the plot
        
        Returns:
            Matplotlib figure object
        """
        fig, ax = plt.subplots(figsize=self.figsize, dpi=self.dpi)
        
        sns.clustermap(
            data,
            cmap=cmap,
            method=method,
            metric=metric,
            figsize=self.figsize,
            cbar_kws={"shrink": 0.8}
        )
        
        plt.suptitle(title, fontsize=14, fontweight='bold', y=1.02)
        
        if save_path:
            plt.savefig(save_path, dpi=self.dpi, bbox_inches='tight')
            logger.info(f"Saved clustered heatmap to {save_path}")
        
        if show_plot:
            plt.show()
        else:
            plt.close()
        
        return fig
