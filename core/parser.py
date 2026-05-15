"""
FoldX .fxout file parser module.

Handles reading and parsing FoldX PSSM output files, extracting mutation
information, pairing Wild Type and Mutant structures, and calculating
ΔΔG (Delta Delta G) values.
"""

import os
from typing import Optional, Tuple
import pandas as pd
import numpy as np

from utils.config import (
    AMINO_ACIDS,
    INDEX_TO_AMINO_ACID,
    PDB_MUTATION_PATTERN,
    WT_PATTERN,
)
from utils.logger import get_logger

logger = get_logger()


class FoldXParserError(Exception):
    """Exception raised for parsing errors."""
    pass


class FoldXParser:
    """
    Parser for FoldX .fxout files.
    
    This class handles the complete parsing pipeline:
    1. Reading the raw .fxout file
    2. Extracting mutation indices and run IDs from filenames
    3. Separating Wild Type and Mutant structures
    4. Pairing Mutant with corresponding WT by index and run ID
    5. Calculating ΔΔG = Energy_Mutant - Energy_WT
    """
    
    def __init__(self):
        self.logger = get_logger()
    
    def parse_file(self, filepath: str) -> pd.DataFrame:
        """
        Parse a single .fxout file and return processed DataFrame.
        
        Args:
            filepath: Path to the .fxout file
            
        Returns:
            DataFrame with columns: AminoAcid, Mut_Index, Run_ID, 
                                   Mutant_Energy, WT_Energy, ddG
            
        Raises:
            FoldXParserError: If file cannot be parsed
        """
        self.logger.info(f"Parsing file: {os.path.basename(filepath)}")
        
        try:
            # Read raw data
            raw_df = self._read_raw_file(filepath)
            
            # Validate data
            if raw_df.empty:
                raise FoldXParserError("Empty file or no valid data found")
            
            # Extract metadata from PDB filenames
            raw_df = self._extract_metadata(raw_df)
            
            # Separate WT and Mutant structures
            wt_df, mut_df = self._separate_wt_mutant(raw_df)
            
            # Pair and calculate ΔΔG
            merged_df = self._pair_and_calculate_ddg(wt_df, mut_df)
            
            self.logger.info(
                f"Successfully parsed {len(merged_df)} valid iterations"
            )
            
            return merged_df
            
        except FileNotFoundError:
            raise FoldXParserError(f"File not found: {filepath}")
        except pd.errors.EmptyDataError:
            raise FoldXParserError(f"Empty file: {filepath}")
        except Exception as e:
            raise FoldXParserError(f"Error parsing {filepath}: {str(e)}")
    
    def _read_raw_file(self, filepath: str) -> pd.DataFrame:
        """
        Read the raw .fxout file into a DataFrame.
        
        Args:
            filepath: Path to the .fxout file
            
        Returns:
            Raw DataFrame with all columns from the file
        """
        # Read tab-separated file, handling potential whitespace
        df = pd.read_csv(
            filepath,
            sep='\t',
            skipinitialspace=True,
            encoding='utf-8',
            on_bad_lines='skip'
        )
        
        # Strip whitespace from column names
        df.columns = df.columns.str.strip()
        
        self.logger.debug(f"Loaded {len(df)} rows from file")
        
        return df
    
    def _extract_metadata(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Extract mutation index, run ID, and amino acid from PDB filenames.
        
        Args:
            df: Raw DataFrame with 'Pdb' column
            
        Returns:
            DataFrame with added Mut_Index, Run_ID, and AminoAcid columns
        """
        # Extract mutation index and run ID using regex
        extracted = df['Pdb'].str.extract(PDB_MUTATION_PATTERN)
        
        # Convert to numeric, handling potential NaN values
        df['Mut_Index'] = pd.to_numeric(extracted[0], errors='coerce')
        df['Run_ID'] = pd.to_numeric(extracted[1], errors='coerce')
        
        # Map mutation index to amino acid letter
        df['AminoAcid'] = df['Mut_Index'].apply(
            lambda x: self._index_to_amino_acid(x)
        )
        
        # Identify Wild Type structures
        df['Is_WT'] = df['Pdb'].apply(
            lambda x: bool(WT_PATTERN.match(str(x)))
        )
        
        valid_count = df['Mut_Index'].notna().sum()
        self.logger.debug(f"Extracted metadata for {valid_count} valid entries")
        
        return df
    
    def _index_to_amino_acid(self, index: float) -> str:
        """
        Convert numeric mutation index to amino acid letter.
        
        Args:
            index: Numeric index (1-20) from FoldX filename
            
        Returns:
            Single-letter amino acid code or 'Unknown'
        """
        if pd.isna(index):
            return 'Unknown'
        
        int_index = int(index)
        if 1 <= int_index <= 20:
            return INDEX_TO_AMINO_ACID[int_index]
        
        return 'Unknown'
    
    def _separate_wt_mutant(
        self, df: pd.DataFrame
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Separate Wild Type and Mutant structures into separate DataFrames.
        
        Args:
            df: DataFrame with 'Is_WT' column
            
        Returns:
            Tuple of (wt_df, mut_df) with relevant columns
        """
        # Extract WT energies
        wt_df = df[df['Is_WT']][[
            'Mut_Index', 'Run_ID', 'Interaction Energy'
        ]].copy()
        wt_df = wt_df.rename(columns={'Interaction Energy': 'WT_Energy'})
        
        # Extract Mutant energies
        mut_df = df[~df['Is_WT']][[
            'Mut_Index', 'Run_ID', 'AminoAcid', 'Interaction Energy'
        ]].copy()
        mut_df = mut_df.rename(columns={'Interaction Energy': 'Mutant_Energy'})
        
        self.logger.debug(
            f"Separated into {len(wt_df)} WT and {len(mut_df)} Mutant entries"
        )
        
        return wt_df, mut_df
    
    def _pair_and_calculate_ddg(
        self, wt_df: pd.DataFrame, mut_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Pair Mutant with corresponding WT and calculate ΔΔG.
        
        Args:
            wt_df: Wild Type DataFrame with WT_Energy
            mut_df: Mutant DataFrame with Mutant_Energy
            
        Returns:
            DataFrame with paired data and calculated ddG
        """
        # Merge on Mut_Index and Run_ID to pair Mutant with WT
        merged_df = pd.merge(
            mut_df, wt_df,
            on=['Mut_Index', 'Run_ID'],
            how='inner'
        )
        
        # Calculate ΔΔG = Mutant_Energy - WT_Energy
        merged_df['ddG'] = merged_df['Mutant_Energy'] - merged_df['WT_Energy']
        
        # Select and order final columns
        columns = [
            'AminoAcid', 'Mut_Index', 'Run_ID',
            'Mutant_Energy', 'WT_Energy', 'ddG'
        ]
        result_df = merged_df[columns].copy()
        
        # Log pairing statistics
        unpaired = len(mut_df) - len(result_df)
        if unpaired > 0:
            self.logger.warning(
                f"{unpaired} mutant entries could not be paired with WT"
            )
        
        return result_df


def parse_fxout_file(filepath: str) -> pd.DataFrame:
    """
    Convenience function to parse a single .fxout file.
    
    Args:
        filepath: Path to the .fxout file
        
    Returns:
        DataFrame with parsed and calculated data
    """
    parser = FoldXParser()
    return parser.parse_file(filepath)


def validate_fxout_file(filepath: str) -> Tuple[bool, Optional[str]]:
    """
    Validate that a file is a valid FoldX .fxout file.
    
    Args:
        filepath: Path to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not os.path.exists(filepath):
        return False, f"File does not exist: {filepath}"
    
    if not filepath.lower().endswith('.fxout'):
        return False, "File does not have .fxout extension"
    
    try:
        # Try to read first few lines to validate format
        with open(filepath, 'r', encoding='utf-8') as f:
            first_line = f.readline()
            # Check for expected column headers
            if 'Pdb' not in first_line or 'Interaction' not in first_line:
                return False, "File does not appear to be a valid FoldX output"
        
        return True, None
        
    except Exception as e:
        return False, f"Error reading file: {str(e)}"
