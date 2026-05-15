"""
Configuration constants, thresholds, and regex patterns for FoldX Analyzer.

This module contains all configurable parameters used throughout the application.
"""

from typing import List, Dict
import re

# =============================================================================
# AMINO ACID CONFIGURATION
# =============================================================================

# Standard 20 amino acids in FoldX PSSM order (1-20 mapping)
AMINO_ACIDS: List[str] = [
    'A', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'K', 'L',
    'M', 'N', 'P', 'Q', 'R', 'S', 'T', 'V', 'W', 'Y'
]

# Amino acid to index mapping (1-based, as used in FoldX filenames)
AMINO_ACID_INDEX: Dict[str, int] = {aa: i + 1 for i, aa in enumerate(AMINO_ACIDS)}

# Index to amino acid mapping (for reverse lookup)
INDEX_TO_AMINO_ACID: Dict[int, str] = {i + 1: aa for i, aa in enumerate(AMINO_ACIDS)}

# =============================================================================
# ANALYSIS THRESHOLDS
# =============================================================================

# ΔΔG threshold for ideal candidate classification (kcal/mol)
# Mutations with MEAN_ddG < this value are considered stabilizing
DDG_THRESHOLD: float = -0.5

# Outlier filtering threshold for ΔΔG values (kcal/mol)
# Values >= this are considered steric clashes and removed
OUTLIER_DDG_THRESHOLD: float = 50.0

# Z-score threshold for outlier detection (optional, more aggressive cleaning)
ZSCORE_THRESHOLD: float = 3.0

# =============================================================================
# REGEX PATTERNS
# =============================================================================

# Pattern to extract mutation index and run ID from PDB filename
# Matches: _{number}_{number}.pdb (e.g., _1_0.pdb, _20_4.pdb)
PDB_MUTATION_PATTERN: re.Pattern = re.compile(r'_(\d+)_(\d+)\.pdb')

# Pattern to identify Wild Type structures
# Matches: ./WT_*.pdb
WT_PATTERN: re.Pattern = re.compile(r'^\.?/?WT_')

# Pattern to validate .fxout file extension
FXOUT_EXTENSION_PATTERN: re.Pattern = re.compile(r'.*\.fxout$', re.IGNORECASE)

# =============================================================================
# EXCEL EXPORT CONFIGURATION
# =============================================================================

# Sheet names for Excel output
SUMMARY_SHEET_NAME: str = 'Ozet_Analiz'
DETAILED_SHEET_NAME: str = 'Hesaplama_Detaylari'

# Output file suffix
OUTPUT_FILE_SUFFIX: str = '_Analiz.xlsx'

# Output directories
OUTPUT_EXCELS_DIR: str = 'output/excels'
OUTPUT_PLOTS_DIR: str = 'output/plots'

# =============================================================================
# PLOTTING CONFIGURATION
# =============================================================================

# Figure dimensions (inches)
PLOT_FIGSIZE: tuple = (12, 6)

# Colors for bar chart
COLOR_IDEAL: str = '#2ca02c'  # Green for ideal candidates
COLOR_REJECTED: str = '#d62728'  # Red for rejected

# Plot styling
PLOT_ALPHA: float = 0.8
PLOT_EDGE_COLOR: str = 'black'
PLOT_CAP_SIZE: int = 5
PLOT_LINE_WIDTH: int = 2

# =============================================================================
# SYNTHESIZABILITY RULES (Biomatik Guidelines)
# =============================================================================

# Hydrophobic amino acids
HYDROPHOBIC_AMINO_ACIDS: set = {'A', 'I', 'L', 'M', 'F', 'W', 'Y', 'V', 'P'}

# Charged amino acids
CHARGED_AMINO_ACIDS: set = {'D', 'E', 'K', 'R', 'H'}

# Maximum hydrophobic ratio (percentage)
MAX_HYDROPHOBIC_RATIO: float = 50.0

# Minimum charged amino acid frequency (1 per N residues)
CHARGED_BLOCK_SIZE: int = 5
MIN_CHARGED_PER_BLOCK: int = 1

# Maximum consecutive glycines (gel formation risk)
MAX_CONSECUTIVE_GLYCINES: int = 4

# N-terminal risk amino acids
N_TERMINAL_RISK_AA: set = {'Q'}  # Glutamine can form pyroglutamate

# =============================================================================
# UI CONFIGURATION
# =============================================================================

# Window dimensions
WINDOW_WIDTH: int = 1000
WINDOW_HEIGHT: int = 700

# Theme settings
DEFAULT_THEME: str = 'dark'  # 'dark' or 'light'

# Log configuration
LOG_MAX_LINES: int = 1000
LOG_FONT_SIZE: int = 10

# =============================================================================
# THREADING CONFIGURATION
# =============================================================================

# Maximum number of worker threads for batch processing
MAX_WORKERS: int = 4

# Progress update interval (number of files)
PROGRESS_UPDATE_INTERVAL: int = 1
