"""
Visualization utilities for MediAnalyze Pro
Common helper functions for visualization modules
"""

import logging
from typing import Optional, Tuple
import numpy as np
import matplotlib.pyplot as plt

logger = logging.getLogger(__name__)


class VisualizationUtils:
    """
    Utility functions for visualization
    """
    
    @staticmethod
    def save_figure(fig: plt.Figure, filepath: str, dpi: int = 100, 
                   formats: Optional[list] = None) -> bool:
        """
        Save figure in multiple formats
        
        Args:
            fig: Matplotlib figure object
            filepath: Base filepath (without extension)
            dpi: Resolution
            formats: List of formats ['png', 'pdf', 'svg'] (default: ['png'])
        
        Returns:
            True if successful
        """
        if formats is None:
            formats = ['png']
        
        try:
            for fmt in formats:
                full_path = f"{filepath}.{fmt}"
                fig.savefig(full_path, dpi=dpi, bbox_inches='tight', format=fmt)
                logger.info(f"Saved figure to {full_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving figure: {e}")
            return False
    
    @staticmethod
    def set_style(style: str = 'default'):
        """
        Set matplotlib style
        
        Args:
            style: Style name ('default', 'seaborn', 'ggplot', 'dark_background')
        """
        try:
            plt.style.use(style)
            logger.info(f"Set matplotlib style to {style}")
        except Exception as e:
            logger.warning(f"Style {style} not available: {e}")
            plt.style.use('default')
    
    @staticmethod
    def create_color_palette(n_colors: int, colormap: str = 'tab10') -> list:
        """
        Create a color palette
        
        Args:
            n_colors: Number of colors needed
            colormap: Colormap name
        
        Returns:
            List of color values
        """
        cmap = plt.cm.get_cmap(colormap)
        colors = [cmap(i) for i in np.linspace(0, 1, n_colors)]
        return colors
    
    @staticmethod
    def format_large_numbers(value: float) -> str:
        """
        Format large numbers for display (e.g., 1000 -> 1K)
        
        Args:
            value: Number to format
        
        Returns:
            Formatted string
        """
        if abs(value) >= 1e9:
            return f"{value/1e9:.2f}B"
        elif abs(value) >= 1e6:
            return f"{value/1e6:.2f}M"
        elif abs(value) >= 1e3:
            return f"{value/1e3:.2f}K"
        else:
            return f"{value:.2f}"
    
    @staticmethod
    def add_watermark(fig: plt.Figure, text: str = "MediAnalyze Pro", 
                     alpha: float = 0.3):
        """
        Add watermark to figure
        
        Args:
            fig: Matplotlib figure
            text: Watermark text
            alpha: Transparency
        """
        fig.text(0.5, 0.5, text, fontsize=50, color='gray', alpha=alpha,
                ha='center', va='center', rotation=45, transform=fig.transFigure,
                zorder=1000)
