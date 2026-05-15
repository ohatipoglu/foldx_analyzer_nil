"""
Biomatik Synthesizability Checker for Peptide Sequences.

This module implements the Biomatik Peptide Design Guidelines for checking
whether a peptide sequence is suitable for laboratory synthesis.

Rules implemented:
1. Hydrophobic ratio <= 50%
2. At least 1 charged amino acid per 5-residue window
3. No >= 4 consecutive Glycines (gel formation risk)
4. No N-terminal Glutamine (pyroglutamate risk)
"""

from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass

from utils.config import (
    HYDROPHOBIC_AMINO_ACIDS,
    CHARGED_AMINO_ACIDS,
    MAX_CONSECUTIVE_GLYCINES,
    N_TERMINAL_RISK_AA,
    MAX_HYDROPHOBIC_RATIO,
    CHARGED_BLOCK_SIZE,
    MIN_CHARGED_PER_BLOCK,
)


@dataclass
class SynthesisCheckResult:
    """Result of synthesizability check."""
    passes: bool
    warnings: List[str]
    hydrophobic_ratio: float
    charged_ok: bool
    gel_risk: bool
    n_terminal_risk: bool


class SynthesizabilityChecker:
    """
    Checks peptide sequences against Biomatik synthesis guidelines.
    """
    
    def __init__(
        self,
        max_hydrophobic_ratio: float = MAX_HYDROPHOBIC_RATIO,
        max_consecutive_glycines: int = MAX_CONSECUTIVE_GLYCINES,
        charged_block_size: int = CHARGED_BLOCK_SIZE,
        min_charged_per_block: int = MIN_CHARGED_PER_BLOCK
    ):
        """
        Initialize the checker with configurable thresholds.
        
        Args:
            max_hydrophobic_ratio: Maximum allowed hydrophobic percentage
            max_consecutive_glycines: Maximum consecutive G before gel risk
            charged_block_size: Window size for charged AA check
            min_charged_per_block: Minimum charged AAs per window
        """
        self.max_hydrophobic_ratio = max_hydrophobic_ratio
        self.max_consecutive_glycines = max_consecutive_glycines
        self.charged_block_size = charged_block_size
        self.min_charged_per_block = min_charged_per_block
    
    def check_sequence(
        self,
        sequence: str,
        mutation_aa: Optional[str] = None,
        position: Optional[int] = None
    ) -> SynthesisCheckResult:
        """
        Check a peptide sequence against all Biomatik rules.
        
        Args:
            sequence: Full peptide sequence
            mutation_aa: Amino acid being mutated (optional)
            position: Position of mutation in sequence (optional)
            
        Returns:
            SynthesisCheckResult with pass/fail status and warnings
        """
        warnings: List[str] = []
        
        # Validate sequence
        if not sequence:
            return SynthesisCheckResult(
                passes=False,
                warnings=["Empty sequence"],
                hydrophobic_ratio=0.0,
                charged_ok=False,
                gel_risk=False,
                n_terminal_risk=False
            )
        
        # Clean sequence (remove whitespace, convert to uppercase)
        clean_seq = sequence.upper().replace(' ', '').replace('-', '')
        
        # Check for invalid characters
        valid_aa = set('ACDEFGHIKLMNPQRSTVWY')
        invalid_chars = set(clean_seq) - valid_aa
        if invalid_chars:
            warnings.append(f"Invalid characters: {', '.join(invalid_chars)}")
        
        # Rule 1: Hydrophobic ratio
        h_ratio = self._calculate_hydrophobic_ratio(clean_seq)
        hydrophobic_fail = h_ratio > self.max_hydrophobic_ratio
        if hydrophobic_fail:
            warnings.append(
                f"High hydrophobicity: {h_ratio:.1f}% (max: {self.max_hydrophobic_ratio}%)"
            )
        
        # Rule 2: Charged amino acid frequency
        charged_ok = self._check_charged_frequency(clean_seq)
        if not charged_ok:
            warnings.append(
                f"Low charged AA frequency (need >= {self.min_charged_per_block} "
                f"per {self.charged_block_size} residues)"
            )
        
        # Rule 3: Consecutive glycines (gel formation risk)
        max_gly = self._count_max_consecutive(clean_seq, 'G')
        gel_risk = max_gly >= self.max_consecutive_glycines
        if gel_risk:
            warnings.append(
                f"Gel formation risk: {max_gly} consecutive Glycines (max: {self.max_consecutive_glycines - 1})"
            )
        
        # Rule 4: N-terminal Glutamine (pyroglutamate risk)
        n_terminal_risk = len(clean_seq) > 0 and clean_seq[0] in N_TERMINAL_RISK_AA
        if n_terminal_risk:
            warnings.append("N-terminal Glutamine (pyroglutamate formation risk)")
        
        # Determine overall pass/fail
        passes = not (hydrophobic_fail or not charged_ok or gel_risk or n_terminal_risk)
        
        return SynthesisCheckResult(
            passes=passes,
            warnings=warnings,
            hydrophobic_ratio=h_ratio,
            charged_ok=charged_ok,
            gel_risk=gel_risk,
            n_terminal_risk=n_terminal_risk
        )
    
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
        
        hydrophobic_count = sum(
            1 for aa in sequence if aa in HYDROPHOBIC_AMINO_ACIDS
        )
        return (hydrophobic_count / len(sequence)) * 100
    
    def _check_charged_frequency(self, sequence: str) -> bool:
        """
        Check if charged amino acids appear frequently enough.
        
        Rule: At least min_charged_per_block charged AA in every
        charged_block_size consecutive residues.
        
        Args:
            sequence: Protein sequence
            
        Returns:
            True if passes the check
        """
        if len(sequence) < self.charged_block_size:
            return True
        
        for i in range(len(sequence) - self.charged_block_size + 1):
            block = sequence[i:i + self.charged_block_size]
            charged_count = sum(
                1 for aa in block if aa in CHARGED_AMINO_ACIDS
            )
            if charged_count < self.min_charged_per_block:
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
    
    def get_warning_summary(self, result: SynthesisCheckResult) -> str:
        """
        Generate a human-readable warning summary.
        
        Args:
            result: SynthesisCheckResult object
            
        Returns:
            Formatted warning string
        """
        if not result.warnings:
            return "PASS"
        
        return "; ".join(result.warnings)


def check_biomatik_rules(
    sequence: str,
    mutation_aa: Optional[str] = None,
    position: Optional[int] = None
) -> SynthesisCheckResult:
    """
    Convenience function to check Biomatik rules.
    
    Args:
        sequence: Peptide sequence
        mutation_aa: Amino acid being mutated (optional)
        position: Position in sequence (optional)
        
    Returns:
        SynthesisCheckResult
    """
    checker = SynthesizabilityChecker()
    return checker.check_sequence(sequence, mutation_aa, position)


def validate_sequence_input(sequence: str) -> Tuple[bool, str]:
    """
    Validate user-input peptide sequence.
    
    Args:
        sequence: User input sequence
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not sequence or not sequence.strip():
        return False, "Empty sequence"
    
    # Clean and validate
    clean_seq = sequence.upper().replace(' ', '').replace('-', '')
    
    if len(clean_seq) < 5:
        return False, "Sequence too short (min 5 residues)"
    
    valid_aa = set('ACDEFGHIKLMNPQRSTVWY')
    invalid = set(clean_seq) - valid_aa
    
    if invalid:
        return False, f"Invalid amino acids: {', '.join(sorted(invalid))}"
    
    return True, ""
