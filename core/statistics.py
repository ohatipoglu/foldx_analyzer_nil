"""
Statistical analysis module for FoldX mutation data.

Handles:
- Outlier detection and removal (Z-score and threshold-based)
- Group-by statistics (MEAN, STD, SEM)
- Decision threshold classification
- Synthesizability checks (Biomatik guidelines)
"""

from typing import Optional, Tuple, List, Dict
import pandas as pd
import numpy as np

from utils.config import (
    DDG_THRESHOLD,
    OUTLIER_DDG_THRESHOLD,
    ZSCORE_THRESHOLD,
    AMINO_ACIDS,
    HYDROPHOBIC_AMINO_ACIDS,
    CHARGED_AMINO_ACIDS,
    MAX_CONSECUTIVE_GLYCINES,
    N_TERMINAL_RISK_AA,
    MAX_HYDROPHOBIC_RATIO,
    CHARGED_BLOCK_SIZE,
    MIN_CHARGED_PER_BLOCK,
)
from utils.logger import get_logger

logger = get_logger()


class FoldXStatistics:
    """
    Statistical analysis for FoldX mutation data.
    
    This class provides methods for:
    1. Cleaning outlier ΔΔG values (steric clashes)
    2. Calculating group statistics per amino acid
    3. Classifying mutations based on stability threshold
    4. Optional synthesizability checks
    """
    
    def __init__(
        self,
        ddg_threshold: float = DDG_THRESHOLD,
        outlier_threshold: float = OUTLIER_DDG_THRESHOLD,
        zscore_threshold: float = ZSCORE_THRESHOLD,
        use_zscore: bool = False
    ):
        """
        Initialize statistics calculator.
        
        Args:
            ddg_threshold: ΔΔG threshold for ideal candidate classification
            outlier_threshold: Absolute threshold for outlier removal
            zscore_threshold: Z-score threshold for outlier detection
            use_zscore: Whether to use Z-score method (vs simple threshold)
        """
        self.ddg_threshold = ddg_threshold
        self.outlier_threshold = outlier_threshold
        self.zscore_threshold = zscore_threshold
        self.use_zscore = use_zscore
        self.logger = get_logger()
    
    def analyze(
        self,
        detailed_df: pd.DataFrame,
        check_synthesizability: bool = False,
        wild_type_sequence: Optional[str] = None
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Perform complete statistical analysis on parsed data.
        
        Args:
            detailed_df: DataFrame from parser with ddG values
            check_synthesizability: Whether to apply synthesizability filters
            wild_type_sequence: Original protein sequence for synthesizability
            
        Returns:
            Tuple of (summary_df, cleaned_detailed_df)
        """
        self.logger.info("Starting statistical analysis...")
        
        # Step 1: Remove outliers (steric clashes)
        cleaned_df = self._remove_outliers(detailed_df)
        
        # Step 2: Calculate group statistics
        summary_df = self._calculate_statistics(cleaned_df)
        
        # Step 3: Apply decision threshold
        summary_df = self._apply_decision_threshold(summary_df)
        
        # Step 4: Optional synthesizability check
        if check_synthesizability and wild_type_sequence:
            summary_df = self._check_synthesizability(
                summary_df, wild_type_sequence
            )
        
        # Step 5: Sort by amino acid order
        summary_df = self._sort_by_amino_acid_order(summary_df)
        
        ideal_count = len(summary_df[summary_df['Decision_Status'] == 'IDEAL CANDIDATE'])
        self.logger.info(f"Analysis complete. {ideal_count} ideal candidates identified.")
        
        return summary_df, cleaned_df
    
    def _remove_outliers(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Remove outlier ΔΔG values from the data.
        
        Two methods available:
        1. Simple threshold: Remove values >= outlier_threshold
        2. Z-score: Remove values with |Z| > zscore_threshold
        
        Args:
            df: DataFrame with ddG column
            
        Returns:
            DataFrame with outliers removed
        """
        original_count = len(df)
        
        if self.use_zscore:
            cleaned_df = self._remove_outliers_zscore(df)
        else:
            cleaned_df = self._remove_outliers_threshold(df)
        
        removed_count = original_count - len(cleaned_df)
        if removed_count > 0:
            self.logger.info(
                f"Removed {removed_count} outlier values "
                f"({removed_count/original_count*100:.1f}%)"
            )
        
        return cleaned_df
    
    def _remove_outliers_threshold(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Remove outliers using simple threshold method.
        
        Args:
            df: DataFrame with ddG column
            
        Returns:
            Filtered DataFrame
        """
        mask = df['ddG'] < self.outlier_threshold
        return df[mask].copy()
    
    def _remove_outliers_zscore(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Remove outliers using Z-score method.
        
        Args:
            df: DataFrame with ddG column
            
        Returns:
            Filtered DataFrame
        """
        # Calculate Z-scores per amino acid group
        df_copy = df.copy()
        df_copy['Z_score'] = df_copy.groupby('AminoAcid')['ddG'].transform(
            lambda x: np.abs((x - x.mean()) / x.std()) if len(x) > 1 and x.std() > 0 else 0
        )
        
        # Filter by Z-score threshold
        mask = df_copy['Z_score'] < self.zscore_threshold
        result = df_copy[mask].drop(columns=['Z_score'])
        
        return result
    
    def _calculate_statistics(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate group statistics for each amino acid.
        
        Args:
            df: Cleaned DataFrame with ddG values
            
        Returns:
            DataFrame with MEAN, STD, SEM per amino acid
        """
        stats = df.groupby('AminoAcid').agg(
            Valid_Runs=('ddG', 'count'),
            MEAN_ddG=('ddG', 'mean'),
            STDEV_ddG=('ddG', 'std'),
            SEM_ddG=('ddG', 'sem'),
            MIN_ddG=('ddG', 'min'),
            MAX_ddG=('ddG', 'max')
        ).reset_index()
        
        # Fill NaN std values (when only 1 observation) with 0
        stats['STDEV_ddG'] = stats['STDEV_ddG'].fillna(0)
        stats['SEM_ddG'] = stats['SEM_ddG'].fillna(0)
        
        self.logger.debug(f"Calculated statistics for {len(stats)} amino acids")
        
        return stats
    
    def _apply_decision_threshold(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply decision threshold to classify mutations.
        
        Args:
            df: DataFrame with MEAN_ddG column
            
        Returns:
            DataFrame with Decision_Status column
        """
        df['Decision_Status'] = df['MEAN_ddG'].apply(
            lambda x: 'IDEAL CANDIDATE' if x < self.ddg_threshold else 'REJECTED'
        )
        
        # Add decision reason
        df['Decision_Reason'] = df['MEAN_ddG'].apply(
            lambda x: f"ΔΔG = {x:.3f} < {self.ddg_threshold}" 
                      if x < self.ddg_threshold 
                      else f"ΔΔG = {x:.3f} >= {self.ddg_threshold}"
        )
        
        return df
    
    def _sort_by_amino_acid_order(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Sort DataFrame by standard amino acid order.
        
        Args:
            df: DataFrame with AminoAcid column
            
        Returns:
            Sorted DataFrame
        """
        df['Order'] = df['AminoAcid'].apply(
            lambda x: AMINO_ACIDS.index(x) if x in AMINO_ACIDS else 99
        )
        df = df.sort_values('Order').drop(columns=['Order'])
        
        return df
    
    def _check_synthesizability(
        self,
        summary_df: pd.DataFrame,
        wild_type_sequence: str
    ) -> pd.DataFrame:
        """
        Check synthesizability rules for each mutation.
        
        Applies Biomatik guidelines:
        - Hydrophobic ratio <= 50%
        - Charged amino acid frequency
        - No consecutive glycines >= 4
        - N-terminal glutamine warning
        
        Args:
            summary_df: DataFrame with mutation decisions
            wild_type_sequence: Original protein sequence
            
        Returns:
            DataFrame with synthesizability columns added
        """
        self.logger.info("Checking synthesizability rules...")
        
        # Initialize synthesizability columns
        summary_df['Synthesis_Status'] = 'OK'
        summary_df['Synthesis_Warnings'] = ''
        
        # Check each amino acid mutation
        for idx, row in summary_df.iterrows():
            aa = row['AminoAcid']
            mut_index = int(row.get('Mut_Index', 0))
            issues = []
            
            # Generate mutated sequence
            mutated_seq = self._generate_mutated_sequence(
                wild_type_sequence, aa, mut_index
            )
            
            # Check hydrophobic ratio
            h_ratio = self._calculate_hydrophobic_ratio(mutated_seq)
            if h_ratio > MAX_HYDROPHOBIC_RATIO:
                issues.append(f"High hydrophobicity ({h_ratio:.1f}%)")
            
            # Check charged amino acid frequency
            charged_ok = self._check_charged_frequency(mutated_seq)
            if not charged_ok:
                issues.append("Low charged AA frequency")
            
            # Check consecutive glycines
            max_gly = self._count_max_consecutive(mutated_seq, 'G')
            if max_gly >= MAX_CONSECUTIVE_GLYCINES:
                issues.append(f"Gel risk ({max_gly} consecutive G)")
            
            # Check N-terminal risk
            if mutated_seq and mutated_seq[0] in N_TERMINAL_RISK_AA:
                issues.append("N-terminal Q risk")
            
            # Update status
            if issues:
                summary_df.at[idx, 'Synthesis_Status'] = 'RISK'
                summary_df.at[idx, 'Synthesis_Warnings'] = '; '.join(issues)
            else:
                summary_df.at[idx, 'Synthesis_Status'] = 'PASS'
                summary_df.at[idx, 'Synthesis_Warnings'] = 'All rules passed'
                
            # Update decision status if needed
            current_decision = summary_df.at[idx, 'Decision_Status']
            if current_decision == 'IDEAL CANDIDATE':
                if issues:
                    summary_df.at[idx, 'Decision_Status'] = 'IDEAL but SYNTHESIS_RISK'
                else:
                    summary_df.at[idx, 'Decision_Status'] = 'IDEAL & SYNTHESIZABLE'
        
        return summary_df
    
    def _generate_mutated_sequence(
        self, 
        sequence: str, 
        mutant_aa: str,
        mut_index: int
    ) -> str:
        """
        Generate a mutated sequence for analysis.
        
        Args:
            sequence: Wild type sequence
            mutant_aa: Mutant amino acid
            mut_index: 1-based index of mutation from FoldX
            
        Returns:
            Simulated mutated sequence
        """
        if not sequence or mut_index < 1:
            return sequence
            
        # 1-based index to 0-based index
        pos = mut_index - 1
        
        if pos >= len(sequence):
            return sequence
            
        seq_list = list(sequence)
        seq_list[pos] = mutant_aa
        return "".join(seq_list)
    
    def _calculate_hydrophobic_ratio(self, sequence: str) -> float:
        """
        Calculate percentage of hydrophobic amino acids.
        
        Args:
            sequence: Protein sequence
            
        Returns:
            Hydrophobic ratio as percentage
        """
        if not sequence:
            return 0.0
        
        hydrophobic_count = sum(1 for aa in sequence if aa in HYDROPHOBIC_AMINO_ACIDS)
        return (hydrophobic_count / len(sequence)) * 100
    
    def _check_charged_frequency(self, sequence: str) -> bool:
        """
        Check if charged amino acids appear frequently enough.
        
        Rule: At least MIN_CHARGED_PER_BLOCK charged AA in every 
        CHARGED_BLOCK_SIZE consecutive residues.
        
        Args:
            sequence: Protein sequence
            
        Returns:
            True if passes the check
        """
        if len(sequence) < CHARGED_BLOCK_SIZE:
            return True
        
        for i in range(len(sequence) - CHARGED_BLOCK_SIZE + 1):
            block = sequence[i:i + CHARGED_BLOCK_SIZE]
            charged_count = sum(1 for aa in block if aa in CHARGED_AMINO_ACIDS)
            if charged_count < MIN_CHARGED_PER_BLOCK:
                return False
        
        return True
    
    def _count_max_consecutive(self, sequence: str, amino_acid: str) -> int:
        """
        Count maximum consecutive occurrences of an amino acid.
        
        Args:
            sequence: Protein sequence
            amino_acid: Amino acid to count
            
        Returns:
            Maximum consecutive count
        """
        max_count = 0
        current_count = 0
        
        for aa in sequence:
            if aa == amino_acid:
                current_count += 1
                max_count = max(max_count, current_count)
            else:
                current_count = 0
        
        return max_count


def calculate_statistics(
    detailed_df: pd.DataFrame,
    ddg_threshold: float = DDG_THRESHOLD,
    outlier_threshold: float = OUTLIER_DDG_THRESHOLD
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Convenience function for statistical analysis.
    
    Args:
        detailed_df: DataFrame from parser
        ddg_threshold: Decision threshold
        outlier_threshold: Outlier removal threshold
        
    Returns:
        Tuple of (summary_df, cleaned_detailed_df)
    """
    stats = FoldXStatistics(
        ddg_threshold=ddg_threshold,
        outlier_threshold=outlier_threshold
    )
    return stats.analyze(detailed_df)
