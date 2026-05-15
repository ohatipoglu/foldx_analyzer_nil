# FoldX Genetic Analyzer & Visualizer

Automated analysis tool for FoldX PSSM (Position-Specific Scanning Matrix) output files. This application digitizes the manual workflow of genetic engineers, automating the identification of thermodynamically stable and synthesis-compatible mutation candidates.

## Features

### Core Analysis
- **Automated ΔΔG Calculation**: Computes ΔΔG = Energy_mutant - Energy_WT for all 5 replicates
- **Statistical Analysis**: MEAN, STD, SEM calculations per amino acid
- **Outlier Removal**: Automatic filtering of steric clash artifacts (ΔΔG ≥ 50 kcal/mol)
- **Decision Threshold**: Classifies mutations as "IDEAL CANDIDATE" (ΔΔG < -0.5) or "REJECTED"

### Batch Processing
- Single file, multiple files, or entire folder processing
- Multi-threaded parallel processing (4 workers by default)
- Real-time progress tracking and status updates
- Batch summary Excel export

### Output
- **Multi-sheet Excel files**:
  - `Ozet_Analiz`: Summary statistics with decisions
  - `Hesaplama_Detaylari`: All calculated ΔΔG values
- **Publication-quality plots**: Bar charts with error bars (SEM)
- **Color-coded results**: Green (ideal) vs Red (rejected)

### Modern UI
- Dark/Light theme support
- Drag-and-drop file/folder input
- Real-time colored log console
- Results table with processing status
- Responsive layout

## Installation

### Prerequisites
- Python 3.9 or higher
- pip package manager

### Setup

1. **Clone or download** this project to your local machine.

2. **Navigate** to the project directory:
   ```bash
   cd C:\Projects\PycharmProjects\FoldX_Project_Nil\foldx_analyzer
   ```

3. **Create a virtual environment** (recommended):
   ```bash
   python -m venv venv
   ```

4. **Activate the virtual environment**:
   
   Windows:
   ```bash
   venv\Scripts\activate
   ```
   
   Linux/Mac:
   ```bash
   source venv/bin/activate
   ```

5. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### GUI Mode (Recommended)

1. **Launch the application**:
   ```bash
   python -m foldx_analyzer.main
   ```
   
   Or directly:
   ```bash
   python main.py
   ```

2. **Select input files**:
   - Drag and drop `.fxout` files onto the drop area
   - Click "Select Files" to browse for files
   - Click "Select Folder" to process all `.fxout` files in a folder

3. **Start analysis**:
   - Click "▶ Start Analysis" button
   - Monitor progress in the status bar and log console

4. **View results**:
   - Excel files saved alongside input files
   - Plots saved to `output/plots/` directory
   - Results table shows summary for each processed file

### Command Line (Future Feature)

```bash
python -m foldx_analyzer.cli input.fxout --output-dir ./results
```

## Input File Format

The application expects FoldX PSSM output files (`.fxout`) with the following structure:

| Column | Description |
|--------|-------------|
| Pdb | PDB filename (e.g., `./WT_1_0.pdb`, `./A_1_0.pdb`) |
| Interaction Energy | Calculated interaction energy (kcal/mol) |

### Filename Convention
- Wild Type: `WT_{index}_{run}.pdb` (e.g., `WT_1_0.pdb`)
- Mutant: `{AminoAcid}_{index}_{run}.pdb` (e.g., `A_1_0.pdb`)

Where:
- `index`: Mutation position (1-20, mapping to amino acid order)
- `run`: Replicate ID (0-4 for 5 replicates)

## Amino Acid Mapping

| Index | Amino Acid | Code |
|-------|------------|------|
| 1 | Alanine | A |
| 2 | Cysteine | C |
| 3 | Aspartic Acid | D |
| 4 | Glutamic Acid | E |
| 5 | Phenylalanine | F |
| 6 | Glycine | G |
| 7 | Histidine | H |
| 8 | Isoleucine | I |
| 9 | Lysine | K |
| 10 | Leucine | L |
| 11 | Methionine | M |
| 12 | Asparagine | N |
| 13 | Proline | P |
| 14 | Glutamine | Q |
| 15 | Arginine | R |
| 16 | Serine | S |
| 17 | Threonine | T |
| 18 | Valine | V |
| 19 | Tryptophan | W |
| 20 | Tyrosine | Y |

## Configuration

Edit `utils/config.py` to customize:

```python
# Analysis thresholds
DDG_THRESHOLD = -0.5  # Ideal candidate threshold (kcal/mol)
OUTLIER_DDG_THRESHOLD = 50.0  # Steric clash filter

# Processing
MAX_WORKERS = 4  # Parallel processing threads

# Synthesizability rules (Biomatik guidelines)
MAX_HYDROPHOBIC_RATIO = 50.0  # Maximum hydrophobic %
MAX_CONSECUTIVE_GLYCINES = 4  # Gel formation risk
```

## Project Structure

```
foldx_analyzer/
├── main.py                 # Application entry point
├── ui/
│   ├── main_window.py      # Main GUI window
│   └── widgets.py          # Reusable UI components
├── core/
│   ├── parser.py           # .fxout file parsing
│   ├── statistics.py       # Statistical analysis
│   ├── exporter.py         # Excel export
│   └── visualizer.py       # Plot generation
├── utils/
│   ├── config.py           # Configuration constants
│   └── logger.py           # Logging utilities
├── output/
│   └── plots/              # Generated plots
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## Troubleshooting

### "Excel file is open in another program"
Close the Excel file before re-running the analysis. The application cannot overwrite open files.

### "No valid data in file"
Ensure the `.fxout` file:
- Is tab-separated
- Contains `Pdb` and `Interaction Energy` columns
- Has valid filename format (e.g., `WT_1_0.pdb`)

### GUI doesn't open
- Ensure `customtkinter` is installed: `pip install customtkinter`
- Check Python version: `python --version` (must be 3.9+)

### Plots not generated
- Check `output/plots/` directory exists
- Ensure `matplotlib` is installed: `pip install matplotlib`

## License

This project is provided as-is for academic and research purposes.

## Acknowledgments

- FoldX software: [FoldX Suite](https://foldxsuite.crg.eu/)
- Biomatik Peptide Design Guidelines
- Original manual workflow by genetic engineering team

## Version History

- **2.0.0** (2026): Complete rewrite with modern GUI, batch processing, modular architecture
- **1.0.0**: Original monolithic Tkinter application (`analiz.py`)
