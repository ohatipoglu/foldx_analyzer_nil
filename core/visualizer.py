"""
Visualization module for FoldX mutation profiles.

Handles generation of publication-quality bar charts showing:
- ΔΔG values for all 20 amino acids
- Error bars (SEM)
- Decision threshold line
- Color-coded bars (ideal vs rejected)
"""

import os
from typing import Optional, Tuple
import pandas as pd
import matplotlib
# Set backend before importing pyplot to ensure thread-safety
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.figure import Figure

from utils.config import (
    AMINO_ACIDS,
    DDG_THRESHOLD,
    PLOT_FIGSIZE,
    COLOR_IDEAL,
    COLOR_REJECTED,
    PLOT_ALPHA,
    PLOT_EDGE_COLOR,
    PLOT_CAP_SIZE,
    PLOT_LINE_WIDTH,
    OUTPUT_PLOTS_DIR,
)
from utils.logger import get_logger

logger = get_logger()


class FoldXVisualizer:
    """
    Visualizer for FoldX mutation analysis results.
    
    Generates bar charts showing the thermodynamic mutational profile
    with all 20 amino acids and their ΔΔG values.
    """
    
    def __init__(
        self,
        ddg_threshold: float = DDG_THRESHOLD,
        figsize: Tuple[int, int] = PLOT_FIGSIZE,
        output_dir: Optional[str] = None
    ):
        """
        Initialize visualizer.
        
        Args:
            ddg_threshold: ΔΔG threshold for ideal candidates
            figsize: Figure dimensions (width, height)
            output_dir: Directory for saving plots (optional)
        """
        self.ddg_threshold = ddg_threshold
        self.figsize = figsize
        self.output_dir = output_dir
        self.logger = get_logger()
        
        # Set matplotlib style - using a more standard style to avoid missing dependency issues
        plt.style.use('ggplot')
    
    def plot_profile(
        self,
        summary_df: pd.DataFrame,
        filename: str,
        show_plot: bool = False,  # Default to False for batch mode
        save_plot: bool = True
    ) -> Optional[str]:
        """
        Generate mutational profile bar chart.

        Args:
            summary_df: Summary statistics DataFrame with MEAN_ddG and SEM_ddG
            filename: Base filename for saving
            show_plot: Whether to display the plot (default False for batch)
            save_plot: Whether to save to file

        Returns:
            Path to saved plot (if saved), None otherwise
        """
        self.logger.info(f"Generating mutation profile chart for {filename}...")

        # Create NEW figure and axis - critical for batch mode!
        fig, ax = plt.subplots(figsize=self.figsize)

        try:
            # Prepare data
            x_labels = summary_df['AminoAcid'].tolist()
            y_values = summary_df['MEAN_ddG'].tolist()
            y_errors = summary_df['SEM_ddG'].tolist()

            # Determine bar colors based on decision status
            colors = self._get_bar_colors(summary_df)

            # Create bars with error bars
            ax.bar(
                range(len(x_labels)),
                y_values,
                yerr=y_errors,
                capsize=PLOT_CAP_SIZE,
                color=colors,
                edgecolor=PLOT_EDGE_COLOR,
                alpha=PLOT_ALPHA,
                linewidth=1.5
            )

            # Add threshold line
            ax.axhline(
                y=self.ddg_threshold,
                color='black',
                linestyle='--',
                linewidth=PLOT_LINE_WIDTH,
                label=f'Threshold ({self.ddg_threshold} kcal/mol)'
            )

            # Add zero line
            ax.axhline(
                y=0.0,
                color='gray',
                linestyle='-',
                linewidth=1,
                alpha=0.5
            )

            # Configure axes
            self._configure_axes(ax, x_labels)

            # Add legend
            self._add_legend(ax)

            # Add title
            self._add_title(ax, filename)

            # Adjust layout
            fig.tight_layout()

            # Save plot if requested (batch mode)
            plot_path = None
            if save_plot:
                plot_path = self._save_plot(fig, filename)
                self.logger.success(f"Plot saved: {plot_path}")

            # Show plot if requested (single file mode ONLY)
            if show_plot:
                # Note: plt.show() will not work with 'Agg' backend
                # This is intended for batch processing safety
                pass

            return plot_path

        finally:
            # CRITICAL: Always close figure to prevent memory leaks in batch mode
            plt.close(fig)
    
    def _get_bar_colors(self, summary_df: pd.DataFrame) -> list:
        """
        Determine bar colors based on decision status or ΔΔG values.
        
        Args:
            summary_df: Summary DataFrame
            
        Returns:
            List of color strings
        """
        colors = []
        
        for idx, row in summary_df.iterrows():
            # Check if Decision_Status column exists
            if 'Decision_Status' in summary_df.columns:
                if row['Decision_Status'] in ['IDEAL CANDIDATE', 'IDEAL & SYNTHESIZABLE']:
                    colors.append(COLOR_IDEAL)
                else:
                    colors.append(COLOR_REJECTED)
            else:
                # Fallback to threshold check
                if row['MEAN_ddG'] < self.ddg_threshold:
                    colors.append(COLOR_IDEAL)
                else:
                    colors.append(COLOR_REJECTED)
        
        return colors
    
    def _configure_axes(self, ax: plt.Axes, x_labels: list) -> None:
        """
        Configure x and y axes.

        Args:
            ax: Matplotlib axis
            x_labels: Amino acid labels
        """
        # Set x-axis ticks and labels
        ax.set_xticks(range(len(x_labels)))
        ax.set_xticklabels(x_labels, fontsize=11, fontweight='bold')

        # X-axis label
        ax.set_xlabel(
            "Mutated Amino Acid",
            fontsize=12,
            fontweight='bold'
        )

        # Y-axis label using Unicode instead of LaTeX math to avoid ParseException
        ax.set_ylabel(
            'ΔΔG (kcal/mol)',
            fontsize=12,
            fontweight='bold'
        )

        # Enable grid
        ax.grid(axis='y', linestyle='--', alpha=0.7)
        ax.set_axisbelow(True)
    
    def _add_legend(self, ax: plt.Axes) -> None:
        """
        Add legend to the plot.
        
        Args:
            ax: Matplotlib axis
        """
        # Create custom legend patches
        ideal_patch = mpatches.Patch(
            color=COLOR_IDEAL,
            label=f'Ideal Candidate (< {self.ddg_threshold})'
        )
        rejected_patch = mpatches.Patch(
            color=COLOR_REJECTED,
            label=f'Rejected (>= {self.ddg_threshold})'
        )
        threshold_line = plt.Line2D(
            [0], [0],
            color='black',
            linestyle='--',
            linewidth=2,
            label='Threshold'
        )
        
        ax.legend(
            handles=[ideal_patch, rejected_patch, threshold_line],
            loc='upper right',
            fontsize=10,
            frameon=True,
            fancybox=True,
            shadow=True
        )
    
    def _add_title(self, ax: plt.Axes, filename: str) -> None:
        """
        Add title to the plot.
        
        Args:
            ax: Matplotlib axis
            filename: Base filename for display
        """
        title = f"Thermodynamic Mutational Profile\n{filename}"
        ax.set_title(
            title,
            fontsize=14,
            fontweight='bold',
            pad=15
        )
    
    def _save_plot(self, fig: Figure, filename: str) -> str:
        """
        Save plot to file.

        Args:
            fig: Matplotlib figure
            filename: Base filename

        Returns:
            Path to saved plot
        """
        # Determine output directory - use configured default
        output_dir = self.output_dir if self.output_dir else OUTPUT_PLOTS_DIR

        # Ensure directory exists
        os.makedirs(output_dir, exist_ok=True)

        # Generate unique filename
        plot_filename = f"{filename}_profile.png"
        plot_path = os.path.join(output_dir, plot_filename)

        # Save with high DPI
        fig.savefig(
            plot_path,
            dpi=150,
            bbox_inches='tight',
            facecolor='white',
            edgecolor='none'
        )

        return plot_path
    
    def plot_comparison(
        self,
        summary_df: pd.DataFrame,
        filename: str,
        highlight_aa: Optional[list] = None
    ) -> Optional[str]:
        """
        Generate enhanced comparison plot with highlighted amino acids.
        
        Args:
            summary_df: Summary statistics DataFrame
            filename: Base filename for saving
            highlight_aa: Optional list of amino acids to highlight
            
        Returns:
            Path to saved plot
        """
        self.logger.info("Generating comparison chart...")
        
        fig, ax = plt.subplots(figsize=self.figsize)
        
        # Prepare data
        x_labels = summary_df['AminoAcid'].tolist()
        y_values = summary_df['MEAN_ddG'].tolist()
        y_errors = summary_df['SEM_ddG'].tolist()
        
        # Create color array
        colors = []
        for idx, row in summary_df.iterrows():
            aa = row['AminoAcid']
            if highlight_aa and aa in highlight_aa:
                colors.append('#ff7f0e')  # Orange for highlighted
            elif row['MEAN_ddG'] < self.ddg_threshold:
                colors.append(COLOR_IDEAL)
            else:
                colors.append(COLOR_REJECTED)
        
        # Create bars
        ax.bar(
            range(len(x_labels)),
            y_values,
            yerr=y_errors,
            capsize=PLOT_CAP_SIZE,
            color=colors,
            edgecolor=PLOT_EDGE_COLOR,
            alpha=PLOT_ALPHA
        )
        
        # Add threshold and zero lines
        ax.axhline(
            y=self.ddg_threshold,
            color='black',
            linestyle='--',
            linewidth=PLOT_LINE_WIDTH
        )
        ax.axhline(y=0.0, color='gray', linestyle='-', linewidth=1, alpha=0.5)
        
        # Configure
        self._configure_axes(ax, x_labels)
        self._add_title(ax, filename)
        
        if highlight_aa:
            self._add_highlight_legend(ax, highlight_aa)
        else:
            self._add_legend(ax)
        
        plt.tight_layout()
        
        # Save
        plot_path = self._save_plot(fig, f"{filename}_comparison")
        plt.close(fig)
        
        return plot_path
    
    def _add_highlight_legend(self, ax: plt.Axes, highlight_aa: list) -> None:
        """
        Add legend with highlighted amino acids.
        
        Args:
            ax: Matplotlib axis
            highlight_aa: List of highlighted amino acids
        """
        ideal_patch = mpatches.Patch(color=COLOR_IDEAL, label='Ideal Candidate')
        rejected_patch = mpatches.Patch(color=COLOR_REJECTED, label='Rejected')
        highlight_patch = mpatches.Patch(
            color='#ff7f0e',
            label=f'Highlighted ({", ".join(highlight_aa)})'
        )
        threshold_line = plt.Line2D(
            [0], [0],
            color='black',
            linestyle='--',
            linewidth=2,
            label='Threshold'
        )
        
        ax.legend(
            handles=[ideal_patch, rejected_patch, highlight_patch, threshold_line],
            loc='upper right',
            fontsize=10
        )


def plot_mutation_profile(
    summary_df: pd.DataFrame,
    filename: str,
    output_dir: Optional[str] = None,
    show_plot: bool = True
) -> Optional[str]:
    """
    Convenience function to generate mutation profile plot.
    
    Args:
        summary_df: Summary statistics
        filename: Base filename
        output_dir: Optional output directory
        show_plot: Whether to display
        
    Returns:
        Path to saved plot
    """
    visualizer = FoldXVisualizer(output_dir=output_dir)
    return visualizer.plot_profile(summary_df, filename, show_plot=show_plot)
