"""
Main window for FoldX Analyzer GUI.

Provides the primary application window with:
- File/folder selection area
- Processing controls
- Progress tracking
- Results table
- Log console
"""

import os
import threading
from typing import List, Optional, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk

from core.parser import FoldXParser, FoldXParserError
from core.statistics import FoldXStatistics
from core.exporter import FoldXExporter, ExcelExportError
from core.visualizer import FoldXVisualizer
from utils.config import (
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    DEFAULT_THEME,
    DDG_THRESHOLD,
    MAX_WORKERS,
    PROGRESS_UPDATE_INTERVAL,
    OUTPUT_PLOTS_DIR,
    OUTPUT_EXCELS_DIR,
)
from utils.logger import get_logger, set_ui_callback
from .widgets import LogConsole, FileDropArea, ProgressWidget, ResultTable


class MainWindow(ctk.CTk):
    """
    Main application window for FoldX Analyzer.
    
    Features:
    - Modern dark/light theme support
    - Drag-and-drop file/folder input
    - Multi-threaded batch processing
    - Real-time progress and logging
    - Results table with statistics
    """
    
    def __init__(self):
        """Initialize the main window."""
        super().__init__()
        
        self.logger = get_logger()
        self.files_to_process: List[str] = []
        self.is_processing = False
        self._cancel_flag = False
        
        # Configure window
        self._configure_window()
        
        # Setup UI callback for logging
        set_ui_callback(self._log_message)
        
        # Create UI components
        self._create_ui()
        
        self.logger.info("FoldX Analyzer ready. Select files to begin.")
    
    def _configure_window(self) -> None:
        """Configure main window properties."""
        self.title("FoldX Genetic Analyzer & Visualizer")
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        
        # Set theme
        ctk.set_appearance_mode(DEFAULT_THEME)
        ctk.set_default_color_theme("blue")
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Protocol for window close
        self.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _create_ui(self) -> None:
        """Create all UI components."""
        # Main scrollable container for responsive layout
        self.main_scroll_frame = ctk.CTkScrollableFrame(self)
        self.main_scroll_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.main_scroll_frame.grid_columnconfigure(0, weight=1)
        
        # Header
        self._create_header(self.main_scroll_frame, row=0)

        # File selection area
        self._create_file_area(self.main_scroll_frame, row=1)

        # Results table
        self._create_results_table(self.main_scroll_frame, row=2)

        # Progress and log area
        self._create_progress_log(self.main_scroll_frame, row=3)
    
    def _create_header(self, parent: ctk.CTkFrame, row: int) -> None:
        """Create header section."""
        header_frame = ctk.CTkFrame(parent, fg_color='transparent')
        header_frame.grid(row=row, column=0, sticky="ew", pady=(0, 10))
        header_frame.grid_columnconfigure(0, weight=1)
        
        # Title
        title_label = ctk.CTkLabel(
            header_frame,
            text="FoldX Genetic Analyzer",
            font=ctk.CTkFont(size=20, weight='bold')
        )
        title_label.grid(row=0, column=0, padx=10, sticky='w')
        
        # Subtitle
        subtitle_label = ctk.CTkLabel(
            header_frame,
            text="Automated Protein Mutation Analysis",
            font=ctk.CTkFont(size=12)
        )
        subtitle_label.grid(row=1, column=0, padx=10, sticky='w')
        
        # Control buttons
        button_frame = ctk.CTkFrame(header_frame, fg_color='transparent')
        button_frame.grid(row=0, column=1, rowspan=2, padx=10)
        
        self.btn_start = ctk.CTkButton(
            button_frame,
            text="▶ Start Analysis",
            command=self._start_analysis,
            fg_color='#2ca02c',
            hover_color='#248a24',
            width=150,
            height=35
        )
        self.btn_start.pack(side='left', padx=5)
        
        self.btn_cancel = ctk.CTkButton(
            button_frame,
            text="⏹ Cancel",
            command=self._cancel_analysis,
            fg_color='#d62728',
            hover_color='#b82020',
            width=100,
            height=35,
            state='disabled'
        )
        self.btn_cancel.pack(side='left', padx=5)
        
        self.btn_clear = ctk.CTkButton(
            button_frame,
            text="🗑 Clear",
            command=self._clear_all,
            width=100,
            height=35
        )
        self.btn_clear.pack(side='left', padx=5)
        
        # Biomatik filter options (below buttons)
        options_frame = ctk.CTkFrame(header_frame, fg_color='transparent')
        options_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=(10, 0), sticky='w')
        
        # Checkbox for Biomatik filter
        self.chk_biomatik_var = ctk.BooleanVar(value=False)
        self.chk_biomatik = ctk.CTkCheckBox(
            options_frame,
            text="☑ Biomatik Sentezlenebilirlik Filtresi",
            variable=self.chk_biomatik_var,
            command=self._toggle_sequence_entry,
            width=20
        )
        self.chk_biomatik.pack(side='left', padx=0)
        
        # Sequence entry (initially hidden)
        self.seq_entry_frame = ctk.CTkFrame(options_frame, fg_color='transparent')
        self.seq_entry = ctk.CTkEntry(
            self.seq_entry_frame,
            placeholder_text="Peptid Dizisi (Opsiyonel): Örn: ACDEFGHIKLMNPQRSTVWY",
            width=300,
            height=25
        )
        self.seq_entry.pack(side='left', padx=(10, 0))
        
        # Initially hide the sequence entry
        if not self.chk_biomatik_var.get():
            self.seq_entry_frame.pack_forget()

    def _toggle_sequence_entry(self) -> None:
        """Show/hide sequence entry based on checkbox state."""
        if self.chk_biomatik_var.get():
            self.seq_entry_frame.pack(side='left', padx=(10, 0))
        else:
            self.seq_entry_frame.pack_forget()
    
    def _create_file_area(self, parent: ctk.CTkFrame, row: int) -> None:
        """Create file selection area."""
        file_frame = ctk.CTkFrame(parent)
        file_frame.grid(row=row, column=0, sticky="ew", pady=(0, 10))
        file_frame.grid_columnconfigure(0, weight=1)
        
        # File drop area
        self.drop_area = FileDropArea(
            file_frame,
            on_files_dropped=self._on_files_dropped,
            on_folder_dropped=self._on_folder_dropped,
            height=180
        )
        self.drop_area.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        
        # File count label
        self.file_count_label = ctk.CTkLabel(
            file_frame,
            text="No files selected",
            font=ctk.CTkFont(size=11)
        )
        self.file_count_label.grid(row=1, column=0, padx=10, pady=(0, 10), sticky='w')
    
    def _create_results_table(self, parent: ctk.CTkFrame, row: int) -> None:
        """Create results table."""
        table_frame = ctk.CTkFrame(parent)
        table_frame.grid(row=row, column=0, sticky="nsew", pady=(0, 10))
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(1, weight=1)  # Table container expands

        # Table header
        header_label = ctk.CTkLabel(
            table_frame,
            text="Processing Results",
            font=ctk.CTkFont(size=14, weight='bold')
        )
        header_label.grid(row=0, column=0, padx=10, pady=(10, 5), sticky='w')

        # Create table with scrollbars - fixed minimum height
        table_container = ctk.CTkFrame(table_frame)
        table_container.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")
        
        # Set minimum height for table area
        table_container.configure(height=200)

        # Scrollbars
        y_scrollbar = ctk.CTkScrollbar(table_container, orientation='vertical')
        y_scrollbar.pack(side='right', fill='y')

        x_scrollbar = ctk.CTkScrollbar(table_container, orientation='horizontal')
        x_scrollbar.pack(side='bottom', fill='x')

        # Treeview table
        self.result_table = ResultTable(
            table_container,
            yscrollcommand=y_scrollbar.set,
            xscrollcommand=x_scrollbar.set
        )
        self.result_table.pack(side='left', fill='both', expand=True)
        self.result_table.bind('<Double-1>', self._on_row_double_click)

        y_scrollbar.configure(command=self.result_table.yview)
        x_scrollbar.configure(command=self.result_table.xview)
    
    def _on_row_double_click(self, event) -> None:
        """Handle double click on result table row to open plot."""
        item_id = self.result_table.focus()
        if not item_id:
            return
            
        values = self.result_table.item(item_id, 'values')
        if not values:
            return
            
        filename = values[0]
        base_name = os.path.splitext(filename)[0]
        plot_path = os.path.join(OUTPUT_PLOTS_DIR, f"{base_name}_profile.png")
        
        if os.path.exists(plot_path):
            try:
                if os.name == 'nt':
                    os.startfile(plot_path)
                else:
                    import subprocess
                    subprocess.call(('xdg-open', plot_path))
            except Exception as e:
                self.logger.error(f"Could not open plot: {str(e)}")
        else:
            self.logger.warning(f"Plot not found: {plot_path}")
    
    def _create_progress_log(self, parent: ctk.CTkFrame, row: int) -> None:
        """Create progress and log area."""
        log_frame = ctk.CTkFrame(parent)
        log_frame.grid(row=row, column=0, sticky="nsew", pady=(10, 0))
        log_frame.grid_columnconfigure(0, weight=1)
        log_frame.grid_rowconfigure(2, weight=1)  # Log console expands

        # Progress widget
        self.progress_widget = ProgressWidget(log_frame)
        self.progress_widget.grid(row=0, column=0, padx=10, pady=(0, 5), sticky="ew")

        # Log header
        log_header = ctk.CTkLabel(
            log_frame,
            text="Activity Log",
            font=ctk.CTkFont(size=12, weight='bold')
        )
        log_header.grid(row=1, column=0, padx=10, pady=(5, 0), sticky='w')

        # Log console with minimum height
        self.log_console = LogConsole(log_frame, height=200, max_lines=500)
        self.log_console.grid(row=2, column=0, padx=10, pady=(0, 10), sticky="nsew")
    
    def _on_files_dropped(self, files: List[str]) -> None:
        """Handle dropped files."""
        # Filter for .fxout files
        fxout_files = [f for f in files if f.lower().endswith('.fxout')]
        
        if fxout_files:
            self.files_to_process.extend(fxout_files)
            self._update_file_count()
            self.logger.info(f"Added {len(fxout_files)} file(s) to queue")
        else:
            messagebox.showwarning(
                "Invalid Files",
                "Please select .fxout files only."
            )
    
    def _on_folder_dropped(self, folder_path: str) -> None:
        """Handle dropped folder."""
        # Find all .fxout files in folder
        fxout_files = []
        for filename in os.listdir(folder_path):
            if filename.lower().endswith('.fxout'):
                fxout_files.append(os.path.join(folder_path, filename))
        
        if fxout_files:
            self.files_to_process.extend(fxout_files)
            self._update_file_count()
            self.logger.info(
                f"Found {len(fxout_files)} .fxout files in folder"
            )
        else:
            messagebox.showwarning(
                "No Files Found",
                f"No .fxout files found in:\n{folder_path}"
            )
    
    def _update_file_count(self) -> None:
        """Update file count display."""
        count = len(self.files_to_process)
        if count == 0:
            text = "No files selected"
        elif count == 1:
            text = f"1 file selected: {os.path.basename(self.files_to_process[0])}"
        else:
            text = f"{count} files selected for batch processing"
        
        self.file_count_label.configure(text=text)
    
    def _start_analysis(self) -> None:
        """Start analysis in background thread."""
        if not self.files_to_process:
            messagebox.showwarning(
                "No Files",
                "Please select files or a folder first."
            )
            return
        
        if self.is_processing:
            return

        # Start processing thread
        self.is_processing = True
        self._cancel_flag = False

        # Update UI state
        self.btn_start.configure(state='disabled')
        self.btn_cancel.configure(state='normal')
        self.drop_area.btn_select_files.configure(state='disabled')
        self.drop_area.btn_select_folder.configure(state='disabled')

        # Clear previous results
        self.result_table.clear()

        # Start worker thread
        thread = threading.Thread(target=self._process_files, daemon=True)
        thread.start()
    
    def _cancel_analysis(self) -> None:
        """Cancel ongoing analysis."""
        if self.is_processing:
            self._cancel_flag = True
            self.logger.warning("Cancellation requested...")
    
    def _process_files(self) -> None:
        """Process all queued files (runs in worker thread)."""
        total_files = len(self.files_to_process)
        processed = 0
        results: List[Dict[str, Any]] = []
        
        self.logger.info(f"Starting batch processing of {total_files} file(s)...")
        
        # Use thread pool for parallel processing
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            # Submit all tasks
            future_to_file = {
                executor.submit(self._process_single_file, filepath): filepath
                for filepath in self.files_to_process
            }
            
            # Process completed tasks
            for future in as_completed(future_to_file):
                if self._cancel_flag:
                    break
                
                filepath = future_to_file[future]
                processed += 1
                
                try:
                    result = future.result()
                    results.append(result)
                    
                    # Update progress
                    self._update_progress(
                        processed, total_files,
                        os.path.basename(filepath)
                    )
                    
                except Exception as e:
                    self.logger.error(
                        f"Error processing {filepath}: {str(e)}"
                    )
                    results.append({
                        'filename': os.path.basename(filepath),
                        'status': 'ERROR',
                        'error': str(e)
                    })
        
        # Update UI on main thread
        self.after(0, lambda: self._on_processing_complete(results))
    
    def _process_single_file(self, filepath: str) -> Dict[str, Any]:
        """
        Process a single file through the complete pipeline.
        
        Args:
            filepath: Path to .fxout file
            
        Returns:
            Result dictionary
        """
        result = {
            'filename': os.path.basename(filepath),
            'status': 'PROCESSING',
            'filepath': filepath
        }
        
        try:
            # Step 1: Parse
            self.logger.info(f"Parsing: {os.path.basename(filepath)}")
            parser = FoldXParser()
            detailed_df = parser.parse_file(filepath)
            
            if detailed_df.empty:
                raise FoldXParserError("No valid data in file")
            
            # Step 2: Statistics
            self.logger.info(f"Calculating statistics: {os.path.basename(filepath)}")
            stats = FoldXStatistics(ddg_threshold=DDG_THRESHOLD)
            summary_df, cleaned_df = stats.analyze(detailed_df)
            
            # Step 2b: Optional Biomatik Synthesizability Check
            if self.chk_biomatik_var.get():
                peptide_sequence = self.seq_entry.get().strip()
                if peptide_sequence:
                    self.logger.info("Applying Biomatik synthesizability filters...")
                    summary_df = self._apply_synthesizability_check(
                        summary_df, peptide_sequence
                    )
                else:
                    self.logger.warning(
                        "Biomatik filter enabled but no peptide sequence provided. "
                        "Skipping synthesizability check."
                    )

            # Step 3: Export
            self.logger.info(f"Exporting results: {os.path.basename(filepath)}")
            exporter = FoldXExporter(output_dir=OUTPUT_EXCELS_DIR)
            output_path = exporter.export_analysis(
                summary_df, cleaned_df, filepath
            )
            result['output_path'] = output_path
            
            # Step 4: Visualize
            self.logger.info(f"Generating plot: {os.path.basename(filepath)}")
            visualizer = FoldXVisualizer(output_dir=OUTPUT_PLOTS_DIR)
            visualizer.plot_profile(
                summary_df,
                os.path.splitext(os.path.basename(filepath))[0],
                show_plot=False,  # Never show in batch mode
                save_plot=True
            )
            
            # Calculate statistics for result
            ideal_count = len(summary_df[summary_df['Decision_Status'] == 'IDEAL CANDIDATE'])
            rejected_count = len(summary_df[summary_df['Decision_Status'] == 'REJECTED'])
            best_ddg = summary_df['MEAN_ddG'].min() if not summary_df.empty else None
            
            result['status'] = 'COMPLETE'
            result['ideal_count'] = ideal_count
            result['rejected_count'] = rejected_count
            result['best_ddg'] = best_ddg
            result['total_count'] = len(summary_df)
            
            self.logger.success(
                f"Complete: {os.path.basename(filepath)} "
                f"({ideal_count} ideal candidates)"
            )
            
        except FoldXParserError as e:
            result['status'] = 'ERROR'
            result['error'] = f"Parse error: {str(e)}"
            self.logger.error(f"Parse error for {filepath}: {str(e)}")
            
        except ExcelExportError as e:
            result['status'] = 'ERROR'
            result['error'] = f"Export error: {str(e)}"
            self.logger.error(f"Export error for {filepath}: {str(e)}")
            
        except Exception as e:
            result['status'] = 'ERROR'
            result['error'] = str(e)
            self.logger.error(f"Unexpected error for {filepath}: {str(e)}")
        
        return result
    
    def _update_progress(
        self, current: int, total: int, current_file: str
    ) -> None:
        """Update progress widget (called from worker thread)."""
        self.after(
            0,
            lambda: self.progress_widget.set_progress(
                current, total, f"Processing: {current_file}"
            )
        )
    
    def _on_processing_complete(self, results: List[Dict[str, Any]]) -> None:
        """Handle processing completion (on main thread)."""
        self.is_processing = False

        # Update UI state
        self.btn_start.configure(state='normal')
        self.btn_cancel.configure(state='disabled')
        self.drop_area.btn_select_files.configure(state='normal')
        self.drop_area.btn_select_folder.configure(state='normal')

        # Complete progress
        self.progress_widget.stop("Processing Complete")
        
        # Update results table
        for result in results:
            tag = None
            if result['status'] == 'COMPLETE':
                tag = 'success'
            elif result['status'] == 'ERROR':
                tag = 'error'
            
            self.result_table.add_result(
                filename=result['filename'],
                status=result['status'],
                ideal_count=result.get('ideal_count', 0),
                rejected_count=result.get('rejected_count', 0),
                best_ddg=result.get('best_ddg'),
                tag=tag
            )
        
        # Summary
        complete_count = sum(1 for r in results if r['status'] == 'COMPLETE')
        error_count = sum(1 for r in results if r['status'] == 'ERROR')
        
        self.logger.success(
            f"Batch complete: {complete_count} successful, {error_count} errors"
        )
        
        # Clear processed files
        self.files_to_process.clear()
        self._update_file_count()
        
        # Show completion message
        if error_count == 0:
            messagebox.showinfo(
                "Complete",
                f"Successfully processed {complete_count} file(s)!\n\n"
                f"Excel files and plots saved to output directories."
            )
        else:
            messagebox.showwarning(
                "Complete with Errors",
                f"Processed {complete_count} file(s) successfully.\n"
                f"{error_count} file(s) had errors.\n\n"
                f"Check the log for details."
            )
    
    def _apply_synthesizability_check(
        self,
        summary_df: Any,
        peptide_sequence: str
    ) -> Any:
        """
        Apply Biomatik synthesizability filters to analysis results.
        
        Args:
            summary_df: DataFrame with thermodynamic analysis results
            peptide_sequence: User-provided peptide sequence
            
        Returns:
            Updated DataFrame with synthesizability columns
        """
        from core.synthesizability import (
            SynthesizabilityChecker,
            validate_sequence_input
        )
        import pandas as pd
        
        # Validate sequence
        is_valid, error_msg = validate_sequence_input(peptide_sequence)
        if not is_valid:
            self.logger.error(f"Invalid peptide sequence: {error_msg}")
            return summary_df
        
        checker = SynthesizabilityChecker()
        
        # Initialize new columns
        summary_df = summary_df.copy()
        summary_df['Synthesis_Status'] = 'NOT_CHECKED'
        summary_df['Synthesis_Warnings'] = '-'
        
        ideal_count = 0
        risk_count = 0
        
        # Check each amino acid mutation
        for idx, row in summary_df.iterrows():
            # Only check thermodynamically ideal candidates
            if row['Decision_Status'] != 'IDEAL CANDIDATE':
                continue
            
            # For now, check the full sequence
            # (Position-specific checking would require mutation position mapping)
            result = checker.check_sequence(peptide_sequence, row['AminoAcid'])
            
            if result.passes:
                summary_df.at[idx, 'Synthesis_Status'] = 'PASS'
                summary_df.at[idx, 'Synthesis_Warnings'] = 'All rules passed'
                summary_df.at[idx, 'Decision_Status'] = 'IDEAL & SYNTHESIZABLE'
                ideal_count += 1
            else:
                summary_df.at[idx, 'Synthesis_Status'] = 'FAIL'
                warning_text = checker.get_warning_summary(result)
                summary_df.at[idx, 'Synthesis_Warnings'] = warning_text
                summary_df.at[idx, 'Decision_Status'] = 'IDEAL but SYNTHESIS_RISK'
                risk_count += 1
        
        # Log summary
        self.logger.info(
            f"Biomatik filter: {ideal_count} ideal & synthesizable, "
            f"{risk_count} synthesis risk candidates"
        )
        
        return summary_df

    def _clear_all(self) -> None:
        """Clear all files and results."""
        if self.is_processing:
            messagebox.showwarning(
                "Processing",
                "Cannot clear while processing is in progress."
            )
            return
        
        self.files_to_process.clear()
        self._update_file_count()
        self.result_table.clear()
        self.log_console.clear()
        self.progress_widget.reset()
        self.logger.info("Cleared all data")
    
    def _log_message(self, message: str) -> None:
        """Callback for logger to update UI."""
        # Extract level from message format: [HH:MM:SS] LEVEL: message
        level = 'INFO'
        if 'SUCCESS' in message:
            level = 'SUCCESS'
        elif 'ERROR' in message:
            level = 'ERROR'
        elif 'WARNING' in message:
            level = 'WARNING'
        elif 'DEBUG' in message:
            level = 'DEBUG'
        elif 'CRITICAL' in message:
            level = 'CRITICAL'
        
        # Pass the full formatted message
        self.after(0, lambda: self.log_console.append_message(message, level))
    
    def _on_closing(self) -> None:
        """Handle window close event."""
        if self.is_processing:
            if messagebox.askyesno(
                "Processing",
                "Analysis is in progress. Close anyway?"
            ):
                self._cancel_flag = True
                self.destroy()
        else:
            self.destroy()
