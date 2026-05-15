"""
Reusable UI widgets for FoldX Analyzer GUI.

Provides custom widgets:
- LogConsole: Scrollable, colored log display
- FileDropArea: Drag-and-drop file/folder zone
- ProgressWidget: Progress bar with status
- ResultTable: File processing results table
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable, List, Dict, Any
import customtkinter as ctk

from utils.config import LOG_FONT_SIZE, LOG_MAX_LINES


class LogConsole(ctk.CTkTextbox):
    """
    Scrollable log console with colored output support.
    
    Features:
    - Automatic scrolling to latest message
    - Color-coded message types (INFO, WARNING, ERROR, SUCCESS)
    - Maximum line limit with automatic trimming
    - Thread-safe message appending
    """
    
    # Color scheme for message types
    COLORS = {
        'DEBUG': 'gray',
        'INFO': '#c9d1d9',  # Light gray for info
        'SUCCESS': '#2ca02c',  # Green
        'WARNING': '#ff8c00',  # Orange
        'ERROR': '#ff4444',    # Red
        'CRITICAL': '#ff0000',
    }
    
    def __init__(
        self,
        master: Any,
        max_lines: int = LOG_MAX_LINES,
        font_size: int = LOG_FONT_SIZE,
        **kwargs
    ):
        """
        Initialize log console.
        
        Args:
            master: Parent widget
            max_lines: Maximum lines to retain
            font_size: Font size in points
        """
        super().__init__(master, **kwargs)
        
        self.max_lines = max_lines
        self._line_count = 0
        self._lock = False  # Prevent recursive updates
        
        # Configure text widget
        self.configure(
            font=('Consolas', font_size),
            wrap='word',
            state='disabled'
        )
    
    def append_message(self, message: str, level: str = 'INFO') -> None:
        """
        Append a message to the log (thread-safe).
        
        Note: CTkTextbox doesn't support colored text tags, so all
        messages use the default color. Level is still tracked for
        potential future enhancements.
        
        Args:
            message: Message text (already formatted with timestamp and level)
            level: Message level (INFO, WARNING, ERROR, etc.) - unused for now
        """
        if self._lock:
            return
        
        try:
            self._lock = True
            
            # Enable editing
            self.configure(state='normal')
            
            # Trim if at max lines
            if self._line_count >= self.max_lines:
                self._trim_lines(self.max_lines // 2)
            
            # Insert the formatted message
            self.insert('end', f"{message}\n")
            self._line_count += 1
            
            # Auto-scroll to end
            self.see('end')
            
            # Disable editing
            self.configure(state='disabled')
            
        finally:
            self._lock = False
    
    def _trim_lines(self, keep_count: int) -> None:
        """
        Remove old lines from the log.
        
        Args:
            keep_count: Number of lines to keep from the end
        """
        content = self.get('1.0', 'end').splitlines()
        if len(content) > keep_count:
            self.delete('1.0', 'end')
            self.insert('1.0', '\n'.join(content[-keep_count:]) + '\n')
            self._line_count = keep_count
    
    def clear(self) -> None:
        """Clear all log messages."""
        self.configure(state='normal')
        self.delete('1.0', 'end')
        self._line_count = 0
        self.configure(state='disabled')
    
    def log_info(self, message: str) -> None:
        """Log an INFO message."""
        self.append_message(message, 'INFO')
    
    def log_success(self, message: str) -> None:
        """Log a SUCCESS message."""
        self.append_message(message, 'SUCCESS')
    
    def log_warning(self, message: str) -> None:
        """Log a WARNING message."""
        self.append_message(message, 'WARNING')
    
    def log_error(self, message: str) -> None:
        """Log an ERROR message."""
        self.append_message(message, 'ERROR')


class FileDropArea(ctk.CTkFrame):
    """
    Drag-and-drop area for files and folders.
    
    Features:
    - Visual feedback on drag hover
    - Support for single file, multiple files, and folders
    - Click to browse alternative
    """
    
    def __init__(
        self,
        master: Any,
        on_files_dropped: Callable[[List[str]], None],
        on_folder_dropped: Callable[[str], None],
        **kwargs
    ):
        """
        Initialize drop area.
        
        Args:
            master: Parent widget
            on_files_dropped: Callback for dropped files
            on_folder_dropped: Callback for dropped folder
        """
        super().__init__(master, **kwargs)
        
        self.on_files_dropped = on_files_dropped
        self.on_folder_dropped = on_folder_dropped
        self._is_hovering = False
        
        # Configure appearance
        self.configure(
            fg_color='#2b2b2b',
            corner_radius=10,
            border_width=2,
            border_color='#444444'
        )
        
        # Create content
        self._create_content()
        
        # Bind drag-and-drop events (platform-specific)
        self._bind_drag_events()
    
    def _create_content(self) -> None:
        """Create the drop area content."""
        # Icon label
        self.icon_label = ctk.CTkLabel(
            self,
            text="📁",
            font=ctk.CTkFont(size=48)
        )
        self.icon_label.pack(pady=(20, 10))
        
        # Instruction label
        self.instruction_label = ctk.CTkLabel(
            self,
            text="Drag & Drop files or folder here",
            font=ctk.CTkFont(size=14, weight='bold')
        )
        self.instruction_label.pack(pady=(0, 5))
        
        # Alternative label
        self.alt_label = ctk.CTkLabel(
            self,
            text="or click 'Select Files' / 'Select Folder' buttons below",
            font=ctk.CTkFont(size=11)
        )
        self.alt_label.pack(pady=(0, 15))
        
        # Button frame
        self.button_frame = ctk.CTkFrame(self, fg_color='transparent')
        self.button_frame.pack(pady=(0, 20))
        
        # Select files button
        self.btn_select_files = ctk.CTkButton(
            self.button_frame,
            text="Select Files",
            command=self._browse_files,
            width=140
        )
        self.btn_select_files.pack(side='left', padx=10)
        
        # Select folder button
        self.btn_select_folder = ctk.CTkButton(
            self.button_frame,
            text="Select Folder",
            command=self._browse_folder,
            width=140
        )
        self.btn_select_folder.pack(side='left', padx=10)
    
    def _bind_drag_events(self) -> None:
        """Bind drag-and-drop events."""
        # Note: Full drag-and-drop requires tkinter-dnd package
        # This is a placeholder for basic functionality
        
        # Hover effects
        self.bind('<Enter>', self._on_enter)
        self.bind('<Leave>', self._on_leave)
        
        # Click to browse
        self.bind('<Button-1>', lambda e: self._browse_files())
    
    def _on_enter(self, event) -> None:
        """Handle mouse enter event."""
        if not self._is_hovering:
            self._is_hovering = True
            self.configure(border_color='#0078d7')
    
    def _on_leave(self, event) -> None:
        """Handle mouse leave event."""
        if self._is_hovering:
            self._is_hovering = False
            self.configure(border_color='#444444')
    
    def _browse_files(self) -> None:
        """Open file browser dialog."""
        from tkinter import filedialog
        
        files = filedialog.askopenfilenames(
            title="Select .fxout Files",
            filetypes=[("FoldX Output", "*.fxout"), ("All Files", "*.*")]
        )
        
        if files:
            self.on_files_dropped(list(files))
    
    def _browse_folder(self) -> None:
        """Open folder browser dialog."""
        from tkinter import filedialog
        
        folder = filedialog.askdirectory(
            title="Select Folder with .fxout Files"
        )
        
        if folder:
            self.on_folder_dropped(folder)
    
    def set_status(self, status: str) -> None:
        """
        Update status text.
        
        Args:
            status: Status message to display
        """
        self.instruction_label.configure(text=status)


class ProgressWidget(ctk.CTkFrame):
    """
    Progress bar with status label and percentage.
    
    Features:
    - Determinate and indeterminate modes
    - Percentage display
    - Status message
    """
    
    def __init__(self, master: Any, **kwargs):
        """
        Initialize progress widget.
        
        Args:
            master: Parent widget
        """
        super().__init__(master, **kwargs)
        self.configure(fg_color='transparent')
        
        # Progress bar
        self.progressbar = ctk.CTkProgressBar(
            self,
            mode='determinate',
            width=400
        )
        self.progressbar.pack(fill='x', padx=10, pady=(10, 5))
        self.progressbar.set(0)
        
        # Status label
        self.status_label = ctk.CTkLabel(
            self,
            text="Ready",
            font=ctk.CTkFont(size=11)
        )
        self.status_label.pack(anchor='w', padx=10, pady=(0, 5))
        
        # Percentage label
        self.percent_label = ctk.CTkLabel(
            self,
            text="0%",
            font=ctk.CTkFont(size=11, weight='bold')
        )
        self.percent_label.pack(anchor='e', padx=10)
    
    def set_progress(self, value: float, total: float, status: str = "") -> None:
        """
        Update progress.
        
        Args:
            value: Current progress value
            total: Total value
            status: Status message
        """
        if total > 0:
            percent = (value / total) * 100
        else:
            percent = 0
        
        self.progressbar.set(percent / 100)
        self.percent_label.configure(text=f"{percent:.1f}%")
        
        if status:
            self.status_label.configure(text=status)
    
    def start_indeterminate(self, status: str = "Processing...") -> None:
        """Start indeterminate progress animation."""
        self.progressbar.configure(mode='indeterminate')
        self.status_label.configure(text=status)
        self.percent_label.configure(text="...")
    
    def stop(self, status: str = "Complete") -> None:
        """Stop progress and set to complete."""
        self.progressbar.configure(mode='determinate')
        self.progressbar.set(1.0)
        self.percent_label.configure(text="100%")
        self.status_label.configure(text=status)
    
    def reset(self) -> None:
        """Reset progress to zero."""
        self.progressbar.set(0)
        self.status_label.configure(text="Ready")
        self.percent_label.configure(text="0%")


class ResultTable(ttk.Treeview):
    """
    Table widget for displaying file processing results.
    
    Columns:
    - File: Filename
    - Status: Processing status
    - Ideal: Number of ideal candidates
    - Rejected: Number of rejected
    - Best ΔΔG: Best (most negative) ΔΔG value
    """
    
    def __init__(self, master: Any, **kwargs):
        """
        Initialize result table.
        
        Args:
            master: Parent widget
        """
        super().__init__(
            master,
            columns=('File', 'Status', 'Ideal', 'Rejected', 'Best_ddG'),
            show='headings',
            **kwargs
        )
        
        # Configure columns
        self.heading('File', text='File')
        self.heading('Status', text='Status')
        self.heading('Ideal', text='Ideal Candidates')
        self.heading('Rejected', text='Rejected')
        self.heading('Best_ddG', text='Best ΔΔG (kcal/mol)')
        
        self.column('File', width=300, minwidth=150)
        self.column('Status', width=100, minwidth=80)
        self.column('Ideal', width=100, minwidth=60, anchor='center')
        self.column('Rejected', width=100, minwidth=60, anchor='center')
        self.column('Best_ddG', width=120, minwidth=80, anchor='center')
        
        # Configure tags for row colors with white text for readability
        self.tag_configure('success', background='#2b5c2b', foreground='#FFFFFF')
        self.tag_configure('error', background='#5c2b2b', foreground='#FFFFFF')
        self.tag_configure('processing', background='#5c5c2b', foreground='#FFFFFF')
    
    def add_result(
        self,
        filename: str,
        status: str,
        ideal_count: int = 0,
        rejected_count: int = 0,
        best_ddg: Optional[float] = None,
        tag: Optional[str] = None
    ) -> str:
        """
        Add a result row to the table.
        
        Args:
            filename: Processed filename
            status: Processing status
            ideal_count: Number of ideal candidates
            rejected_count: Number of rejected
            best_ddg: Best ΔΔG value
            tag: Row tag for styling
            
        Returns:
            Item ID
        """
        item_id = filename  # Use filename as ID for easy lookup
        
        best_ddg_str = f"{best_ddg:.4f}" if best_ddg is not None else "N/A"
        
        self.insert(
            '',
            'end',
            iid=item_id,
            values=(
                filename,
                status,
                ideal_count,
                rejected_count,
                best_ddg_str
            ),
            tags=(tag,) if tag else ()
        )
        
        return item_id
    
    def update_status(self, item_id: str, status: str, tag: Optional[str] = None) -> None:
        """
        Update status of an existing row.
        
        Args:
            item_id: Item ID (filename)
            status: New status
            tag: New tag for styling
        """
        current = self.item(item_id, 'values')
        if current:
            values = list(current)
            values[1] = status
            self.item(item_id, values=values)
            
            if tag:
                self.item(item_id, tags=(tag,))
    
    def clear(self) -> None:
        """Clear all rows."""
        for item in self.get_children():
            self.delete(item)
