"""
Image comparison viewer module for MediAnalyze Pro
Displays original and processed images side by side
"""

import logging
from typing import Optional, Tuple
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider

logger = logging.getLogger(__name__)


class ImageViewer:
    """
    Displays and compares medical images
    """
    
    def __init__(self, figsize: Tuple[int, int] = (14, 6), dpi: int = 100):
        """
        Initialize image viewer
        
        Args:
            figsize: Figure size (width, height) in inches
            dpi: Resolution in dots per inch
        """
        self.figsize = figsize
        self.dpi = dpi
    
    def compare_images(
        self,
        original: np.ndarray,
        processed: np.ndarray,
        original_title: str = "Original",
        processed_title: str = "Processed",
        title: str = "Image Comparison",
        save_path: Optional[str] = None,
        show_plot: bool = True
    ) -> plt.Figure:
        """
        Display original and processed images side by side
        
        Args:
            original: Original image array
            processed: Processed image array
            original_title: Title for original image
            processed_title: Title for processed image
            title: Overall figure title
            save_path: Path to save figure
            show_plot: Whether to display the plot
        
        Returns:
            Matplotlib figure object
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=self.figsize, dpi=self.dpi)
        
        # Display original
        if len(original.shape) == 2:
            im1 = ax1.imshow(original, cmap='gray')
        else:
            im1 = ax1.imshow(original)
        ax1.set_title(original_title, fontsize=12, fontweight='bold')
        ax1.axis('off')
        plt.colorbar(im1, ax=ax1, fraction=0.046, pad=0.04)
        
        # Display processed
        if len(processed.shape) == 2:
            im2 = ax2.imshow(processed, cmap='gray')
        else:
            im2 = ax2.imshow(processed)
        ax2.set_title(processed_title, fontsize=12, fontweight='bold')
        ax2.axis('off')
        plt.colorbar(im2, ax=ax2, fraction=0.046, pad=0.04)
        
        fig.suptitle(title, fontsize=14, fontweight='bold', y=0.98)
        plt.tight_layout()
        
        if save_path:
            fig.savefig(save_path, dpi=self.dpi, bbox_inches='tight')
            logger.info(f"Saved image comparison to {save_path}")
        
        if show_plot:
            plt.show()
        else:
            plt.close(fig)
        
        return fig
    
    def display_image(
        self,
        image: np.ndarray,
        title: str = "Image",
        cmap: Optional[str] = None,
        save_path: Optional[str] = None,
        show_plot: bool = True
    ) -> plt.Figure:
        """
        Display a single image
        
        Args:
            image: Image array
            title: Image title
            cmap: Color map (if None, auto-detects based on image dimensions)
            save_path: Path to save figure
            show_plot: Whether to display the plot
        
        Returns:
            Matplotlib figure object
        """
        fig, ax = plt.subplots(figsize=self.figsize, dpi=self.dpi)
        
        if cmap is None:
            cmap = 'gray' if len(image.shape) == 2 else None
        
        im = ax.imshow(image, cmap=cmap)
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.axis('off')
        plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
        
        plt.tight_layout()
        
        if save_path:
            fig.savefig(save_path, dpi=self.dpi, bbox_inches='tight')
            logger.info(f"Saved image to {save_path}")
        
        if show_plot:
            plt.show()
        else:
            plt.close(fig)
        
        return fig
    
    def display_multiple_images(
        self,
        images: list,
        titles: Optional[list] = None,
        ncols: int = 3,
        title: str = "Multiple Images",
        save_path: Optional[str] = None,
        show_plot: bool = True
    ) -> plt.Figure:
        """
        Display multiple images in a grid
        
        Args:
            images: List of image arrays
            titles: Optional list of titles for each image
            ncols: Number of columns in grid
            title: Overall figure title
            save_path: Path to save figure
            show_plot: Whether to display the plot
        
        Returns:
            Matplotlib figure object
        """
        n_images = len(images)
        nrows = (n_images + ncols - 1) // ncols
        
        fig, axes = plt.subplots(nrows, ncols, figsize=(self.figsize[0] * ncols / 2, 
                                                         self.figsize[1] * nrows / 2), 
                                 dpi=self.dpi)
        
        if nrows == 1:
            axes = axes.reshape(1, -1) if n_images > 1 else [axes]
        axes = axes.flatten() if n_images > 1 else [axes]
        
        for idx, image in enumerate(images):
            ax = axes[idx]
            
            cmap = 'gray' if len(image.shape) == 2 else None
            ax.imshow(image, cmap=cmap)
            
            if titles and idx < len(titles):
                ax.set_title(titles[idx], fontsize=10, fontweight='bold')
            else:
                ax.set_title(f'Image {idx+1}', fontsize=10, fontweight='bold')
            
            ax.axis('off')
        
        # Hide unused subplots
        for idx in range(n_images, len(axes)):
            axes[idx].axis('off')
        
        fig.suptitle(title, fontsize=14, fontweight='bold', y=0.98)
        plt.tight_layout()
        
        if save_path:
            fig.savefig(save_path, dpi=self.dpi, bbox_inches='tight')
            logger.info(f"Saved multiple images to {save_path}")
        
        if show_plot:
            plt.show()
        else:
            plt.close(fig)
        
        return fig
    
    def before_after_slider(
        self,
        original: np.ndarray,
        processed: np.ndarray,
        title: str = "Before/After Comparison",
        save_path: Optional[str] = None,
        show_plot: bool = True
    ) -> plt.Figure:
        """
        Display before/after images with slider to blend between them
        
        Args:
            original: Original image
            processed: Processed image
            title: Figure title
            save_path: Path to save figure (saves at slider position 0.5)
            show_plot: Whether to display the plot
        
        Returns:
            Matplotlib figure object
        """
        fig, ax = plt.subplots(figsize=self.figsize, dpi=self.dpi)
        plt.subplots_adjust(bottom=0.15)
        
        # Normalize images to 0-1 range
        orig_norm = (original - original.min()) / (original.max() - original.min())
        proc_norm = (processed - processed.min()) / (processed.max() - processed.min())
        
        # Initial blend (50% original, 50% processed)
        alpha = 0.5
        blended = alpha * orig_norm + (1 - alpha) * proc_norm
        
        cmap = 'gray' if len(original.shape) == 2 else None
        im = ax.imshow(blended, cmap=cmap)
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.axis('off')
        
        # Create slider
        ax_slider = plt.axes([0.2, 0.02, 0.6, 0.03])
        slider = Slider(ax_slider, 'Blend', 0, 1, valinit=0.5, valstep=0.01)
        
        def update(val):
            alpha = slider.val
            blended = alpha * orig_norm + (1 - alpha) * proc_norm
            im.set_array(blended)
            fig.canvas.draw_idle()
        
        slider.on_changed(update)
        
        plt.tight_layout()
        
        if save_path:
            # Save at default blend (0.5)
            fig.savefig(save_path, dpi=self.dpi, bbox_inches='tight')
            logger.info(f"Saved before/after comparison to {save_path}")
        
        if show_plot:
            plt.show()
        else:
            plt.close(fig)
        
        return fig
