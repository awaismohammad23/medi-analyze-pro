"""
Scatter plot module for MediAnalyze Pro
Creates scatter plots for correlation analysis and data relationships
"""

import logging
from typing import Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats

logger = logging.getLogger(__name__)


class ScatterPlotter:
    """
    Creates scatter plots for correlation analysis
    """
    
    def __init__(self, figsize: Tuple[int, int] = (10, 8), dpi: int = 100):
        """
        Initialize scatter plotter
        
        Args:
            figsize: Figure size (width, height) in inches
            dpi: Resolution in dots per inch
        """
        self.figsize = figsize
        self.dpi = dpi
    
    def plot_correlation(
        self,
        x_data: np.ndarray,
        y_data: np.ndarray,
        x_label: str = "Variable X",
        y_label: str = "Variable Y",
        title: Optional[str] = None,
        show_trendline: bool = True,
        show_correlation: bool = True,
        color_by: Optional[np.ndarray] = None,
        save_path: Optional[str] = None,
        show_plot: bool = True
    ) -> plt.Figure:
        """
        Create scatter plot with correlation analysis
        
        Args:
            x_data: X-axis data
            y_data: Y-axis data
            x_label: X-axis label
            y_label: Y-axis label
            title: Plot title
            show_trendline: Whether to show linear trend line
            show_correlation: Whether to display correlation coefficient
            color_by: Optional array for color-coding points
            save_path: Path to save figure
            show_plot: Whether to display the plot
        
        Returns:
            Matplotlib figure object
        """
        fig, ax = plt.subplots(figsize=self.figsize, dpi=self.dpi)
        
        # Calculate correlation
        correlation = np.corrcoef(x_data, y_data)[0, 1]
        
        # Create scatter plot
        if color_by is not None:
            scatter = ax.scatter(x_data, y_data, c=color_by, cmap='viridis', 
                                alpha=0.6, s=50, edgecolors='black', linewidth=0.5)
            plt.colorbar(scatter, ax=ax, label='Color Scale')
        else:
            ax.scatter(x_data, y_data, alpha=0.6, s=50, edgecolors='black', linewidth=0.5)
        
        # Add trend line
        if show_trendline:
            z = np.polyfit(x_data, y_data, 1)
            p = np.poly1d(z)
            ax.plot(x_data, p(x_data), "r--", alpha=0.8, linewidth=2, label='Trend Line')
            ax.legend()
        
        # Add correlation text
        if show_correlation:
            textstr = f'Correlation: {correlation:.3f}'
            props = dict(boxstyle='round', facecolor='wheat', alpha=0.8)
            ax.text(0.05, 0.95, textstr, transform=ax.transAxes, fontsize=12,
                   verticalalignment='top', bbox=props)
        
        ax.set_xlabel(x_label, fontsize=12, fontweight='bold')
        ax.set_ylabel(y_label, fontsize=12, fontweight='bold')
        ax.set_title(title or f"{x_label} vs {y_label}", fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3, linestyle='--')
        
        plt.tight_layout()
        
        if save_path:
            fig.savefig(save_path, dpi=self.dpi, bbox_inches='tight')
            logger.info(f"Saved scatter plot to {save_path}")
        
        if show_plot:
            plt.show()
        else:
            plt.close(fig)
        
        return fig
    
    def plot_from_dataframe(
        self,
        data: pd.DataFrame,
        x_column: str,
        y_column: str,
        color_column: Optional[str] = None,
        title: Optional[str] = None,
        show_trendline: bool = True,
        save_path: Optional[str] = None,
        show_plot: bool = True
    ) -> plt.Figure:
        """
        Create scatter plot from DataFrame
        
        Args:
            data: DataFrame with data
            x_column: Name of X column
            y_column: Name of Y column
            color_column: Optional column for color-coding
            title: Plot title
            show_trendline: Whether to show trend line
            save_path: Path to save figure
            show_plot: Whether to display the plot
        
        Returns:
            Matplotlib figure object
        """
        if x_column not in data.columns or y_column not in data.columns:
            raise ValueError(f"Columns {x_column} or {y_column} not found in DataFrame")
        
        x_data = data[x_column].values
        y_data = data[y_column].values
        
        color_by = None
        if color_column and color_column in data.columns:
            color_by = data[color_column].values
        
        return self.plot_correlation(
            x_data, y_data,
            x_label=x_column,
            y_label=y_column,
            title=title,
            show_trendline=show_trendline,
            color_by=color_by,
            save_path=save_path,
            show_plot=show_plot
        )
    
    def plot_multiple_correlations(
        self,
        data: Dict[str, Tuple[np.ndarray, np.ndarray]],
        labels: Optional[Dict[str, Tuple[str, str]]] = None,
        title: str = "Multiple Correlations",
        save_path: Optional[str] = None,
        show_plot: bool = True
    ) -> plt.Figure:
        """
        Create multiple scatter plots in subplots
        
        Args:
            data: Dictionary with plot names as keys and (x_data, y_data) tuples as values
            labels: Optional dictionary with (x_label, y_label) tuples
            title: Overall figure title
            save_path: Path to save figure
            show_plot: Whether to display the plot
        
        Returns:
            Matplotlib figure object
        """
        n_plots = len(data)
        cols = 2
        rows = (n_plots + 1) // 2
        
        fig, axes = plt.subplots(rows, cols, figsize=(self.figsize[0] * cols / 2, 
                                                      self.figsize[1] * rows / 2), 
                                dpi=self.dpi)
        
        if n_plots == 1:
            axes = [axes]
        else:
            axes = axes.flatten()
        
        for idx, (plot_name, (x_data, y_data)) in enumerate(data.items()):
            ax = axes[idx]
            
            correlation = np.corrcoef(x_data, y_data)[0, 1]
            
            ax.scatter(x_data, y_data, alpha=0.6, s=50, edgecolors='black', linewidth=0.5)
            
            # Add trend line
            z = np.polyfit(x_data, y_data, 1)
            p = np.poly1d(z)
            ax.plot(x_data, p(x_data), "r--", alpha=0.8, linewidth=2)
            
            # Labels
            if labels and plot_name in labels:
                x_label, y_label = labels[plot_name]
            else:
                x_label, y_label = "X", "Y"
            
            ax.set_xlabel(x_label, fontsize=10)
            ax.set_ylabel(y_label, fontsize=10)
            ax.set_title(f"{plot_name}\n(r={correlation:.3f})", fontsize=11, fontweight='bold')
            ax.grid(True, alpha=0.3, linestyle='--')
        
        # Hide unused subplots
        for idx in range(n_plots, len(axes)):
            axes[idx].axis('off')
        
        fig.suptitle(title, fontsize=16, fontweight='bold', y=1.02)
        plt.tight_layout()
        
        if save_path:
            fig.savefig(save_path, dpi=self.dpi, bbox_inches='tight')
            logger.info(f"Saved multiple scatter plots to {save_path}")
        
        if show_plot:
            plt.show()
        else:
            plt.close(fig)
        
        return fig
    
    def plot_with_regression(
        self,
        x_data: np.ndarray,
        y_data: np.ndarray,
        x_label: str = "Variable X",
        y_label: str = "Variable Y",
        regression_type: str = 'linear',
        title: Optional[str] = None,
        save_path: Optional[str] = None,
        show_plot: bool = True
    ) -> plt.Figure:
        """
        Create scatter plot with regression analysis
        
        Args:
            x_data: X-axis data
            y_data: Y-axis data
            x_label: X-axis label
            y_label: Y-axis label
            regression_type: Type of regression ('linear', 'polynomial')
            title: Plot title
            save_path: Path to save figure
            show_plot: Whether to display the plot
        
        Returns:
            Matplotlib figure object
        """
        fig, ax = plt.subplots(figsize=self.figsize, dpi=self.dpi)
        
        ax.scatter(x_data, y_data, alpha=0.6, s=50, edgecolors='black', linewidth=0.5)
        
        # Perform regression
        if regression_type == 'linear':
            slope, intercept, r_value, p_value, std_err = stats.linregress(x_data, y_data)
            line = slope * x_data + intercept
            ax.plot(x_data, line, 'r--', linewidth=2, 
                   label=f'y = {slope:.3f}x + {intercept:.3f}\nR² = {r_value**2:.3f}')
        
        elif regression_type == 'polynomial':
            z = np.polyfit(x_data, y_data, 2)
            p = np.poly1d(z)
            ax.plot(x_data, p(x_data), "r--", linewidth=2, label='Polynomial Fit')
        
        correlation = np.corrcoef(x_data, y_data)[0, 1]
        
        textstr = f'Correlation: {correlation:.3f}'
        props = dict(boxstyle='round', facecolor='wheat', alpha=0.8)
        ax.text(0.05, 0.95, textstr, transform=ax.transAxes, fontsize=12,
               verticalalignment='top', bbox=props)
        
        ax.set_xlabel(x_label, fontsize=12, fontweight='bold')
        ax.set_ylabel(y_label, fontsize=12, fontweight='bold')
        ax.set_title(title or f"{x_label} vs {y_label} (Regression)", 
                    fontsize=14, fontweight='bold')
        ax.legend(loc='best', framealpha=0.9)
        ax.grid(True, alpha=0.3, linestyle='--')
        
        plt.tight_layout()
        
        if save_path:
            fig.savefig(save_path, dpi=self.dpi, bbox_inches='tight')
            logger.info(f"Saved regression plot to {save_path}")
        
        if show_plot:
            plt.show()
        else:
            plt.close(fig)
        
        return fig
