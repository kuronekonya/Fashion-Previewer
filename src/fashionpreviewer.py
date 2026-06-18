from code.core.color_translator import ColorTranslator
import tkinter as tk
from code.ui.options_menu import CustomPreviewDialog
import colorsys
from tkinter import messagebox, ttk
from PIL import Image
import os
import re
import sys
import time
import json

PALETTE_SIZE = 256

# Fix working directory to the script's location
def fix_working_directory():
    """Change working directory to the script's location to ensure relative paths work"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if os.getcwd() != script_dir:
        os.chdir(script_dir)

# Character mapping based on the provided list
from icon_handler import CHARACTER_MAPPING

DEFAULT_FRAMES = {
    # Values are 0-indexed (user-specified frame - 1)
    "Bunny":   {"1st Job": 0,   "2nd Job": 3,   "3rd Job": 0},
    "Buffalo": {"1st Job": 5,   "2nd Job": 3,   "3rd Job": 0},
    "Sheep":   {"1st Job": 2,   "2nd Job": 3,   "3rd Job": 0},
    "Dragon":  {"1st Job": 3,   "2nd Job": 3,   "3rd Job": 0},
    "Fox":     {"1st Job": 2,   "2nd Job": 106,  "3rd Job": 0},
    "Lion":    {"1st Job": 3,   "2nd Job": 98,   "3rd Job": 0},   # 3rd job also flipped
    "Cat":     {"1st Job": 3,   "2nd Job": 3,   "3rd Job": 0},
    "Raccoon": {"1st Job": 3,   "2nd Job": 91,   "3rd Job": 0},
    "Paula":   {"1st Job": 39,  "2nd Job": 13,   "3rd Job": 32},
}

# Characters/jobs whose default view is flipped
DEFAULT_FLIPPED = {
    "Lion": {"3rd Job"},
}

class PaletteLayer:
    def __init__(self, name, colors, palette_type, active=True, palette_path=""):
        self.name = name
        self.colors = colors  # List of (r,g,b)
        self.palette_type = palette_type  # 'hair', 'gloves', 'fashion', etc.
        self.active = active
        self.palette_path = palette_path

class Statistics:
    """Class to track and manage program statistics"""
    def __init__(self):
        self.live_palette_files_edited = set()  # Track unique files edited
        self.live_palette_files_saved = set()  # Track unique files saved
        self.palettes_previewed = 0  # Track number of palettes previewed in main UI
        
        self.icons_edited = set()  # Track unique icons edited
        self.icons_saved = set()
        self.frames_previewed = 0
        self.frames_skipped = 0  # Track frames skipped with navigation

        self.total_time_spent = 0.0  # Accumulated seconds from previous sessions
        self.session_start_time = time.time()  # Start of current session
        self.character_edits = {}  # Dict to track edits per character/job
        self.exported_frames = 0
        self.exported_backgrounds = 0
        self.exported_palettes = {}  # Dict to track exports by character & type
        self.colors_saved = 0  # Combined from both editors
        
        # New statistics
        self.indexes_changed = 0  # Total number of palette indexes modified
        self.indexes_selected = 0  # Total number of indexes selected
        self.indexes_saved_in_pals = 0  # Number of non-keyed indexes saved in .pal files
        self.colors_saved_in_json = 0  # Number of colors saved in JSON format
        self.preview_indexes_selected = {
            'live_pal': 0,  # Indexes selected in live palette editor
            'live_icon': 0  # Indexes selected in live icon editor
        }
        
        # Index modification tracking (for live palette editor)
        self.unique_indexes_modified = set()  # Set of unique palette indexes that have been modified
        self.total_index_modifications = 0  # Total number of modification events (slider release, gradient apply, color replace)
        
    def add_palette_edit(self, char_id: str, job_type: str):
        """Track a palette edit for a character/job"""
        key = f"{char_id}_{job_type}"
        if key not in self.character_edits:
            self.character_edits[key] = {
                'views': 0,
                'edits': 0,
                'palette_saves': 0,
                'exports': 0
            }
        self.character_edits[key]['edits'] += 1
        
    def add_character_view(self, char_id: str, job_type: str):
        """Track when a character/job is viewed"""
        key = f"{char_id}_{job_type}"
        if key not in self.character_edits:
            self.character_edits[key] = {
                'views': 0,
                'edits': 0,
                'palette_saves': 0,
                'exports': 0
            }
        self.character_edits[key]['views'] += 1
        
    def get_most_edited(self):
        """Get the most edited character & job type"""
        if not self.character_edits:
            return None, None, 0
            
        most_edited = max(self.character_edits.items(), 
                         key=lambda x: x[1]['edits'])
        char_id, job_type = most_edited[0].split('_', 1)
        return char_id, job_type, most_edited[1]['edits']
        
    def get_program_time(self):
        """Get total cumulative time in program in HH:MM:SS format"""
        # Calculate time spent in current session
        current_session_seconds = time.time() - self.session_start_time
        # Add to total accumulated time
        total_seconds = int(self.total_time_spent + current_session_seconds)
        
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    def track_index_modification(self, index_or_indices):
        """Track index modification event (slider release, gradient apply, or color replace)
        
        Args:
            index_or_indices: Single index (int) or collection of indexes (list/set)
        """
        # Normalize to a list
        if isinstance(index_or_indices, int):
            indices = [index_or_indices]
        else:
            indices = list(index_or_indices)
        
        # Add to unique indexes modified
        self.unique_indexes_modified.update(indices)
        
        # Increment total modification events
        self.total_index_modifications += 1
        
    def to_dict(self):
        """Convert statistics to a dictionary for saving"""
        # Update accumulated time with what's passed in current session so far
        now = time.time()
        self.total_time_spent += (now - self.session_start_time)
        self.session_start_time = now # Reset session start to now
        
        return {
            'live_palette_files_edited': list(self.live_palette_files_edited),
            'live_palette_files_saved': list(self.live_palette_files_saved),
            'icons_edited': list(self.icons_edited),
            'icons_saved': list(self.icons_saved),
            'frames_previewed': self.frames_previewed,
            'frames_skipped': self.frames_skipped,
            'total_time_spent': self.total_time_spent,
            'character_edits': self.character_edits,
            'exported_frames': self.exported_frames,
            'exported_backgrounds': self.exported_backgrounds,
            'exported_palettes': self.exported_palettes,
            'colors_saved': self.colors_saved,
            'indexes_changed': self.indexes_changed,
            'indexes_selected': self.indexes_selected,
            'indexes_saved_in_pals': self.indexes_saved_in_pals,
            'colors_saved_in_json': self.colors_saved_in_json,
            'preview_indexes_selected': self.preview_indexes_selected,
            'palettes_previewed': self.palettes_previewed,
            'unique_indexes_modified': list(self.unique_indexes_modified),
            'total_index_modifications': self.total_index_modifications
        }

    @classmethod
    def from_dict(cls, data):
        """Create a Statistics instance from a dictionary"""
        stats = cls()
        stats.live_palette_files_edited = set(data.get('live_palette_files_edited', []))
        stats.live_palette_files_saved = set(data.get('live_palette_files_saved', []))
        stats.icons_edited = set(data.get('icons_edited', []))
        stats.icons_saved = set(data.get('icons_saved', []))
        stats.frames_previewed = data.get('frames_previewed', 0)
        stats.frames_skipped = data.get('frames_skipped', 0)
        
        # Load accumulated time
        stats.total_time_spent = data.get('total_time_spent', 0.0)
        
        # Backward compatibility check for old 'start_time' key
        if 'start_time' in data and 'total_time_spent' not in data:
            old_val = data['start_time']
            # If it's a timestamp (like 1700000000) or 0.0, it's the broken format.
            # If it's a reasonably small number of seconds (e.g. < 1 year), it might be okay.
            if 0 < old_val < 31536000: # Less than 1 year of seconds
                stats.total_time_spent = old_val
            else:
                stats.total_time_spent = 0.0
                
        stats.session_start_time = time.time() # Start fresh session countdown
        
        stats.character_edits = data.get('character_edits', {})
        stats.exported_frames = data.get('exported_frames', 0)
        stats.exported_backgrounds = data.get('exported_backgrounds', 0)
        stats.exported_palettes = data.get('exported_palettes', {})
        stats.colors_saved = data.get('colors_saved', 0)
        stats.indexes_changed = data.get('indexes_changed', 0)
        stats.indexes_selected = data.get('indexes_selected', 0)
        stats.indexes_saved_in_pals = data.get('indexes_saved_in_pals', 0)
        stats.colors_saved_in_json = data.get('colors_saved_in_json', 0)
        stats.preview_indexes_selected = data.get('preview_indexes_selected', {
            'live_pal': 0,
            'live_icon': 0
        })
        stats.palettes_previewed = data.get('palettes_previewed', 0)
        stats.unique_indexes_modified = set(data.get('unique_indexes_modified', []))
        stats.total_index_modifications = data.get('total_index_modifications', 0)
        return stats

class Tooltip:
    """Class to create a tooltip for a widget"""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event=None):
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25

        self.tooltip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")

        label = tk.Label(tw, text=self.text, justify='left',
                       background="#ffffe0", relief='solid', borderwidth=1,
                       font=("Arial", "8", "normal"))
        label.pack(ipadx=1)

    def hide_tooltip(self, event=None):
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None

class StatisticsDialog:
    """Dialog to display program statistics"""
    def __init__(self, parent):
        self.parent = parent
        self.dialog = tk.Toplevel(parent.master)
        self.dialog.title("Program Statistics")
        self.dialog.transient(parent.master)
        self.dialog.grab_set()
        
        # Set fixed window size
        window_width = 650
        window_height = 450
        
        # Center the window
        x = (self.dialog.winfo_screenwidth() - window_width) // 2
        y = (self.dialog.winfo_screenheight() - window_height) // 2
        self.dialog.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.dialog.resizable(False, False)
        
        # Main container with padding
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill="both", expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="Local Statistics", font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 10))
        
        # Create two columns
        columns_frame = ttk.Frame(main_frame)
        columns_frame.pack(fill="both", expand=True)
        
        # Configure equal column widths
        columns_frame.grid_columnconfigure(0, weight=1, uniform="column")
        columns_frame.grid_columnconfigure(1, weight=1, uniform="column")
        
        # General Stats Column
        general_frame = ttk.LabelFrame(columns_frame, text="General Statistics", padding="5")
        general_frame.grid(row=0, column=0, sticky="nsew", padx=2)
        
        general_canvas = tk.Canvas(general_frame, width=150)  # Larger base width
        general_scrollbar = ttk.Scrollbar(general_frame, orient="vertical", command=general_canvas.yview)
        general_content = ttk.Frame(general_canvas)
        
        general_canvas.configure(yscrollcommand=general_scrollbar.set)
        general_scrollbar.pack(side="right", fill="y")
        general_canvas.pack(side="left", fill="both", expand=True)
        
        # Character Stats Column
        character_frame = ttk.LabelFrame(columns_frame, text="Character Statistics", padding="5")
        character_frame.grid(row=0, column=1, sticky="nsew", padx=2)
        
        character_canvas = tk.Canvas(character_frame, width=150)  # Larger base width
        character_scrollbar = ttk.Scrollbar(character_frame, orient="vertical", command=character_canvas.yview)
        character_content = ttk.Frame(character_canvas)
        
        character_canvas.configure(yscrollcommand=character_scrollbar.set)
        character_scrollbar.pack(side="right", fill="y")
        character_canvas.pack(side="left", fill="both", expand=True)
        
        # Populate General Statistics first
        stats = parent.statistics
        self._add_stat(general_content, "Time in Program", stats.get_program_time())
        
        # Files and Icons
        self._add_stat(general_content, "Live Palette Files Edited", len(stats.live_palette_files_edited))
        self._add_stat(general_content, "Live Palette Files Saved", len(stats.live_palette_files_saved))
        self._add_stat(general_content, "Palettes Previewed", stats.palettes_previewed)
        self._add_stat(general_content, "Icons Edited", len(stats.icons_edited))
        self._add_stat(general_content, "Icons Saved", len(stats.icons_saved))
        
        # Frames
        self._add_stat(general_content, "Frames Previewed", stats.frames_previewed)
        self._add_stat(general_content, "Frames Skipped", stats.frames_skipped)
        
        # Palette Indexes
        self._add_stat(general_content, "Indexes Changed", stats.indexes_changed)
        self._add_stat(general_content, "Indexes Selected", stats.indexes_selected)
        self._add_stat(general_content, "Indexes Saved in PALs", stats.indexes_saved_in_pals)
        
        # Index Modification Tracking (New)
        self._add_stat(general_content, "Unique Indexes Modified", len(stats.unique_indexes_modified))
        self._add_stat(general_content, "Total Modification Events", stats.total_index_modifications)
        
        # Colors and Selections
        self._add_stat(general_content, "Colors Saved", stats.colors_saved)
        self._add_stat(general_content, "Colors Saved in JSON", stats.colors_saved_in_json)
        self._add_stat(general_content, "Live Palette Indexes Selected", stats.preview_indexes_selected['live_pal'])
        self._add_stat(general_content, "Live Icon Indexes Selected", stats.preview_indexes_selected['live_icon'])
        
        # Export Statistics (moved from separate column)
        self._add_stat(general_content, "Exported Frames", stats.exported_frames)
        self._add_stat(general_content, "Exported Backgrounds", stats.exported_backgrounds)
        
        # Add palette export stats
        if stats.exported_palettes:
            for char_type, count in stats.exported_palettes.items():
                self._add_stat(general_content, f"Exported {char_type} Palettes", count)
        
        # Populate Character Statistics
        char_id, job_type, edit_count = stats.get_most_edited()
        if char_id and job_type:
            char_name = self._get_character_display_name(char_id)
            self._add_stat(character_content, "Most Edited Character", f"{char_name} ({job_type})")
            self._add_stat(character_content, "Edit Count", edit_count)
        
        # Add character-specific stats
        for key, data in sorted(stats.character_edits.items()):
            char_id, job_type = key.split('_', 1)
            char_name = self._get_character_display_name(char_id)
            frame = ttk.LabelFrame(character_content, text=f"{char_name} - {job_type}")
            frame.pack(fill="x", pady=2)
            self._add_stat(frame, "Views", data['views'])
            self._add_stat(frame, "Edits", data['edits'])
            self._add_stat(frame, "Palette Saves", data['palette_saves'])
            self._add_stat(frame, "Exports", data['exports'])
        
        
        # Create windows for the content frames after content is added
        self.dialog.update_idletasks()  # Update to get proper canvas dimensions
        
        general_canvas.create_window((0, 0), window=general_content, anchor="nw")
        character_canvas.create_window((0, 0), window=character_content, anchor="nw")
        
        # Configure scroll regions after adding content
        general_content.update_idletasks()
        character_content.update_idletasks()
        
        general_canvas.configure(scrollregion=general_canvas.bbox("all"))
        character_canvas.configure(scrollregion=character_canvas.bbox("all"))
        
        # Mouse wheel scrolling
        general_content.bind("<MouseWheel>", lambda e: general_canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
        character_content.bind("<MouseWheel>", lambda e: character_canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
        
        # Button Frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=(10, 0))
        
        def clear_stats():
            from tkinter import messagebox
            if messagebox.askyesno("Warning", "Are you sure you want to clear this?"):
                self.parent.statistics.__init__()
                self.parent._save_statistics()
                self.dialog.destroy()
                self.parent.show_statistics()
                
        clear_button = ttk.Button(button_frame, text="Clear Statistics", command=clear_stats)
        clear_button.pack(side="left", padx=5)

        # Close button
        close_button = ttk.Button(button_frame, text="Close", command=self.dialog.destroy)
        close_button.pack(side="left", padx=5)
        
        from code.utils.theme_manager import ThemeManager
        ThemeManager.apply_theme(self.parent, self.dialog)
        
    def _get_character_display_name(self, char_id):
        """Get the proper display name for a character"""
        from icon_handler import CHARACTER_MAPPING
        if char_id in CHARACTER_MAPPING:
            return CHARACTER_MAPPING[char_id]['name']
        return char_id
    
    def _add_stat(self, parent, label, value):
        """Add a statistic row to the given parent frame"""
        frame = ttk.Frame(parent)
        frame.pack(fill="x", pady=1, padx=2)
        
        # Create a single label that spans the full width
        full_text = f"{label}: {value}"
        label_widget = ttk.Label(frame, text=full_text)
        label_widget.pack(fill="x", expand=True)

class AllModeWarningDialog:
    """Warning dialog for switching to 'All' mode"""
    
    def __init__(self, parent):
        self.parent = parent
        self.result = False
        self.dont_show_again = False
        
        # Create the dialog window
        self.dialog = tk.Toplevel(parent.master)
        self.dialog.title("Warning - All Mode")
        self.dialog.geometry("500x200")
        self.dialog.resizable(False, False)
        
        # Make it modal and bring to front
        self.dialog.transient(parent.master)
        self.dialog.grab_set()
        self.dialog.lift()
        self.dialog.focus_force()
        
        # Center the dialog on the parent window
        self._center_dialog()
        
        self._create_ui()
        
    def _center_dialog(self):
        """Center the dialog on the parent window"""
        self.dialog.update_idletasks()
        
        # Get parent window position and size
        parent_x = self.parent.master.winfo_x()
        parent_y = self.parent.master.winfo_y()
        parent_width = self.parent.master.winfo_width()
        parent_height = self.parent.master.winfo_height()
        
        # Calculate center position
        dialog_width = self.dialog.winfo_reqwidth()
        dialog_height = self.dialog.winfo_reqheight()
        
        x = parent_x + (parent_width // 2) - (dialog_width // 2)
        y = parent_y + (parent_height // 2) - (dialog_height // 2)
        
        self.dialog.geometry(f"+{x}+{y}")
        
    def _create_ui(self):
        """Create the dialog UI"""
        main_frame = tk.Frame(self.dialog)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Warning message
        message = ("Warning: This may be resource-intensive on even newer machines, continue? "
                  "You can always use Custom Preview Options (the gear icon) to change your view "
                  "to more or less frames.")
        
        msg_label = tk.Label(main_frame, text=message, wraplength=460, justify="left", font=("Arial", 10))
        msg_label.pack(pady=(0, 20))
        
        # Button frame
        button_frame = tk.Frame(main_frame)
        button_frame.pack(fill="x", pady=(0, 10))
        
        # Buttons
        ballsy_btn = tk.Button(button_frame, text="Yeah, I'm ballsy!", command=self._on_ballsy, 
                              bg="#4CAF50", fg="white", font=("Arial", 10, "bold"), width=15)
        ballsy_btn.pack(side="left", padx=(0, 10))
        
        good_btn = tk.Button(button_frame, text="No, I'm good", command=self._on_good, 
                            bg="#f44336", fg="white", font=("Arial", 10), width=15)
        good_btn.pack(side="left")
        
        # Don't show again checkbox
        self.dont_show_var = tk.BooleanVar()
        checkbox = tk.Checkbutton(main_frame, text="Don't show warning again", 
                                 variable=self.dont_show_var, font=("Arial", 9))
        checkbox.pack(anchor="w")
        
        # Handle window close event
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_good)
        
    def _on_ballsy(self):
        """User chose to proceed with All mode"""
        self.result = True
        self.dont_show_again = self.dont_show_var.get()
        self.dialog.destroy()
        
    def _on_good(self):
        """User chose not to proceed with All mode"""
        self.result = False
        self.dont_show_again = self.dont_show_var.get()
        self.dialog.destroy()
        
    def show(self):
        """Show the dialog and return the result"""
        self.dialog.wait_window()
        return self.result, self.dont_show_again


class PaletteTool:
    def _warn_if_nonimpact(self, palette_type: str) -> bool:
        """Return True to proceed, False to cancel. Warn only for hair or 3rd job base."""
        try:
            pt = str(palette_type or "").strip().lower()
        except Exception:
            pt = str(palette_type).lower() if palette_type is not None else ""
        if pt in ("hair", "3rd_job_base".lower()):
            # Track acknowledgements per editor session so we don't spam
            if not hasattr(self, "_live_warned_types"):
                self._live_warned_types = set()
            if pt in getattr(self, "_live_warned_types", set()):
                return True
            msg = "⚠️ WARNING: Editing this part will not impact in game fashion, are you sure you want to continue?"
            
            # Create custom dialog with red text
            dialog = tk.Toplevel(self.master)
            dialog.title("Heads up")
            dialog.resizable(False, False)
            dialog.transient(self.master)
            dialog.grab_set()
            
            from code.utils.theme_manager import ThemeManager
            ThemeManager.apply_theme(self, dialog)
            
            # Center the dialog
            dialog.update_idletasks()
            width = 400
            height = 150
            x = (dialog.winfo_screenwidth() - width) // 2
            y = (dialog.winfo_screenheight() - height) // 2
            dialog.geometry(f"{width}x{height}+{x}+{y}")
            
            # Warning message in red
            tk.Label(dialog, text=msg, wraplength=350, justify="center", 
                    fg="red", font=("Arial", 11, "bold")).pack(pady=20)
            
            # Button frame
            button_frame = tk.Frame(dialog)
            button_frame.pack(pady=10)
            
            result = {"ok": False}
            
            def on_yes():
                result["ok"] = True
                dialog.destroy()
            
            def on_no():
                result["ok"] = False
                dialog.destroy()
            
            tk.Button(button_frame, text="Yes", command=on_yes, width=10).pack(side="left", padx=5)
            tk.Button(button_frame, text="No", command=on_no, width=10).pack(side="left", padx=5)
            
            # Wait for dialog to close
            dialog.wait_window()
            ok = result["ok"]
            
            if ok:
                try:
                    self._live_warned_types.add(pt)
                except Exception:
                    pass
            return bool(ok)
        return True
        
    def _get_statistics_path(self):
        """Get the path to the statistics file"""
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), "statistics.json")
    
    def _load_statistics(self):
        """Load statistics from file"""
        try:
            stats_path = self._get_statistics_path()
            with open(stats_path, 'r') as f:
                data = json.load(f)
                self.statistics = Statistics.from_dict(data)
        except (FileNotFoundError, json.JSONDecodeError):
            # Keep default statistics if file doesn't exist or is invalid
            pass
            
    def _save_statistics(self):
        """Save statistics to file"""
        try:
            stats_path = self._get_statistics_path()
            with open(stats_path, 'w') as f:
                json.dump(self.statistics.to_dict(), f, indent=4)
        except Exception as e:
            print(f"CONSOLE ERROR MSG: Error saving statistics: {e}")
    
    def _get_settings_path(self):
        """Get the path to the settings file"""
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")
    
    def _load_settings(self):
        """Load settings from file"""
        try:
            settings_path = self._get_settings_path()
            with open(settings_path, 'r') as f:
                data = json.load(f)
                
                # Load global settings
                global_settings = data.get('global', {})
                self.use_bmp_export = global_settings.get('use_bmp_export', True)
                self.use_portrait_export = global_settings.get('use_portrait_export', True)
                self.cute_bg_option = global_settings.get('cute_bg_option', "both")
                self.palette_format = global_settings.get('palette_format', "png")
                self.show_frame_labels = global_settings.get('show_frame_labels', True)
                self.use_right_click = global_settings.get('use_right_click', True)
                self.live_pal_ui_mode = global_settings.get('live_pal_ui_mode', "Simple")
                self.use_quick_export = global_settings.get('use_quick_export', False)
                self.zoom_level = global_settings.get('zoom_level', "100%")
                self.dont_show_excess_colors_prompt = global_settings.get('dont_show_excess_colors_prompt', False)
                self.show_frame_options = global_settings.get('show_frame_options', True)  # New setting
                self.dark_mode = global_settings.get('dark_mode', False)
                
                # Initialize session-only settings (cleared when program closes)
                self.session_dont_show_excess_colors_prompt = False
                
                # Load background color robustly
                bg_color = global_settings.get('background_color', [255, 0, 255])
                try:
                    if isinstance(bg_color, (list, tuple)) and len(bg_color) >= 3:
                        self.background_color = tuple(int(c) for c in bg_color[:3])
                    elif isinstance(bg_color, str) and bg_color.startswith('#'):
                        self.background_color = (int(bg_color[1:3], 16), int(bg_color[3:5], 16), int(bg_color[5:7], 16))
                    else:
                        self.background_color = (255, 0, 255)
                except:
                    self.background_color = (255, 0, 255)
                
                # Load session state (last used character, frame, preview)
                self.last_character = global_settings.get('last_character', None)
                self.last_job = global_settings.get('last_job', None)
                self.last_frame = global_settings.get('last_frame', 0)
                self.last_preview_mode = global_settings.get('last_preview_mode', "single")
                
                # Store per-character settings for later use
                self.per_character_settings = data.get('per_character', {})
                
                # Scrub per-character palette selections of missing files
                for char_id, char_data in self.per_character_settings.items():
                    pal_sels = char_data.get('palette_selections', {})
                    if not pal_sels:
                        continue
                        
                    if 'hair' in pal_sels:
                        hair_path = pal_sels['hair']
                        if hair_path and hair_path != "NONE" and isinstance(hair_path, str) and not os.path.exists(hair_path):
                            pal_sels['hair'] = "NONE"
                            
                    if 'third_job' in pal_sels:
                        third_job_path = pal_sels['third_job']
                        if third_job_path and third_job_path != "NONE" and isinstance(third_job_path, str) and not os.path.exists(third_job_path):
                            pal_sels['third_job'] = "NONE"
                            
                    if 'fashion' in pal_sels and isinstance(pal_sels['fashion'], dict):
                        for f_key, f_path in pal_sels['fashion'].items():
                            if f_path and f_path != "NONE" and isinstance(f_path, str) and not os.path.exists(f_path):
                                pal_sels['fashion'][f_key] = "NONE"
                
                # Load hidden frames and export frames (standardize keys to lowercase)
                for char_job_raw, settings in self.per_character_settings.items():
                    char_job = str(char_job_raw).strip().lower()
                    if 'hidden_frames' in settings:
                        self.hidden_frames[char_job] = set(settings['hidden_frames'])
                        
                    # Extract character ID (standardize to lowercase)
                    if '_' in char_job:
                        char_id = char_job.split('_')[0].strip().lower()
                        if 'export_frame' in settings and char_id not in self.export_frames:
                            self.export_frames[char_id] = settings['export_frame']
                
        except (FileNotFoundError, json.JSONDecodeError):
            # Use defaults if file doesn't exist or is invalid
            self.per_character_settings = {}
            self.use_quick_export = False
            # Initialize session state defaults
            self.last_character = None
            self.last_job = None
            self.last_frame = 0
            self.last_preview_mode = "single"
    
        except Exception as e:
            print(f"CONSOLE ERROR MSG: Error saving settings: {e}")
    
    def _save_settings(self):
        """Save settings to file"""
        try:
            settings_path = self._get_settings_path()
            
            # Load existing settings to preserve data not tracked in memory
            try:
                with open(settings_path, 'r') as f:
                    data = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                data = {'global': {}, 'per_character': {}}
            
            # Ensure structure exists
            if 'global' not in data: data['global'] = {}
            if 'per_character' not in data: data['per_character'] = {}

            # Update global settings
            # We update individually to preserve unknown global keys
            data['global'].update({
                'use_bmp_export': self.use_bmp_export,
                'use_portrait_export': self.use_portrait_export,
                'cute_bg_option': self.cute_bg_option,
                'palette_format': self.palette_format,
                'show_frame_labels': self.show_frame_labels,
                'use_right_click': self.use_right_click,
                'live_pal_ui_mode': self.live_pal_ui_mode,
                'dark_mode': self.dark_mode,
                'use_quick_export': self.use_quick_export,
                'zoom_level': self.zoom_var.get() if hasattr(self, 'zoom_var') else "100%",
                'background_color': list(self.background_color),
                'dont_show_excess_colors_prompt': getattr(self, 'dont_show_excess_colors_prompt', False),
                'dont_show_all_mode_warning': data['global'].get('dont_show_all_mode_warning', False),
                'dont_show_50_frames_warning': data['global'].get('dont_show_50_frames_warning', False),
                'show_frame_options': getattr(self, 'show_frame_options', True),
                'last_character': self.current_character,
                'last_job': self.current_job,
                'last_frame': self.current_image_index,
                'last_preview_mode': self.preview_var.get() if hasattr(self, 'preview_var') else "single"
            })
            
            # Update per-character settings
            # 1. Merge basic character settings from memory (last_viewed, custom counts)
            if hasattr(self, 'per_character_settings'):
                for char_id, settings in self.per_character_settings.items():
                    if char_id not in data['per_character']:
                        data['per_character'][char_id] = {}
                    data['per_character'][char_id].update(settings)
            
            # 2. Sync runtime hidden frames (Authoritative source)
            if hasattr(self, 'hidden_frames'):
                for char_job_raw, hidden_set in self.hidden_frames.items():
                    char_job = str(char_job_raw).strip().lower()
                    if char_job not in data['per_character']:
                        data['per_character'][char_job] = {}
                    data['per_character'][char_job]['hidden_frames'] = list(hidden_set)
            
            # 3. Sync runtime export frames
            if hasattr(self, 'export_frames'):
                for char_id_raw, frame_idx in self.export_frames.items():
                    char_id = str(char_id_raw).strip().lower()
                    # Apply to all existing job variants for this character in the data
                    # This ensures we don't miss any job variants that exist in the file
                    for char_job in list(data['per_character'].keys()):
                        if char_job.startswith(char_id + '_'):
                            data['per_character'][char_job]['export_frame'] = frame_idx
            
            # Save to file
            with open(settings_path, 'w') as f:
                json.dump(data, f, indent=4)
                
        except Exception as e:
            print(f"CONSOLE ERROR MSG: Error saving settings: {e}")
    
    def _save_per_character_frame_settings(self):
        from code.core.character_loader import CharacterLoader
        return CharacterLoader._save_per_character_frame_settings(self)

    
    def _get_all_mode_warning_preference(self):
        """Get the 'don't show all mode warning' preference from settings"""
        try:
            settings_path = self._get_settings_path()
            if os.path.exists(settings_path):
                with open(settings_path, 'r') as f:
                    settings = json.load(f)
                    return settings.get('global', {}).get('dont_show_all_mode_warning', False)
        except Exception:
            pass
        return False
    
    def _save_all_mode_warning_preference(self, dont_show):
        """Save the 'don't show all mode warning' preference to settings"""
        try:
            settings_path = self._get_settings_path()
            
            # Load existing settings
            try:
                with open(settings_path, 'r') as f:
                    settings = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                settings = {'global': {}, 'per_character': {}}
            
            # Ensure global key exists
            if 'global' not in settings:
                settings['global'] = {}
            
            # Update the preference
            settings['global']['dont_show_all_mode_warning'] = dont_show
            
            # Save settings
            with open(settings_path, 'w') as f:
                json.dump(settings, f, indent=4)
                
        except Exception as e:
            print(f"CONSOLE ERROR MSG: Error saving all mode warning preference: {e}")
    
    def _show_all_mode_warning(self):
        """Show the all mode warning dialog and return user's choice"""
        dialog = AllModeWarningDialog(self)
        result, dont_show_again = dialog.show()
        
        # Save the "don't show again" preference if user checked it
        if dont_show_again:
            self._save_all_mode_warning_preference(True)
        
        return result
    
    def _get_50_frames_warning_preference(self):
        """Get the 'don't show 50+ frames warning' preference from settings"""
        try:
            settings_path = self._get_settings_path()
            if os.path.exists(settings_path):
                with open(settings_path, 'r') as f:
                    settings = json.load(f)
                    return settings.get('global', {}).get('dont_show_50_frames_warning', False)
        except Exception:
            pass
        return False
    
    def _save_50_frames_warning_preference(self, dont_show):
        """Save the 'don't show 50+ frames warning' preference to settings"""
        try:
            settings_path = self._get_settings_path()
            
            # Load existing settings
            try:
                with open(settings_path, 'r') as f:
                    settings = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                settings = {'global': {}, 'per_character': {}}
            
            # Ensure global key exists
            if 'global' not in settings:
                settings['global'] = {}
            
            # Update the preference
            settings['global']['dont_show_50_frames_warning'] = dont_show
            
            # Save settings
            with open(settings_path, 'w') as f:
                json.dump(settings, f, indent=4)
                
        except Exception as e:
            print(f"CONSOLE ERROR MSG: Error saving 50 frames warning preference: {e}")
    
    def _load_character_settings(self, char_id):
        from code.core.character_loader import CharacterLoader
        return CharacterLoader._load_character_settings(self, char_id)

    
    def _save_character_settings(self, char_id):
        from code.core.character_loader import CharacterLoader
        return CharacterLoader._save_character_settings(self, char_id)



    def __init__(self, master):
        # Initialize statistics first
        self.statistics = Statistics()
        self._load_statistics()
        
        self.master = master
        self.master.title("Fashion Previewer v4.2 - A CoraTO & Kyo Collab")
        # And perhaps our last update we'll ever have or need
        # We'll miss you Kyo
        
        # Dictionary to store frame range settings per character/job
        # Format: {char_id: {job: (frame_count, start_frame, end_frame)}}
        self.frame_range_settings = {}

        self.original_image = None
        self.original_palette = [(0, 0, 0)] * PALETTE_SIZE
        self.palette_layers = []
        
        # Character and job selection
        self.current_character = None
        self.current_job = None
        self.current_image_path = None
        self.current_image_index = 0
        
        # Initialize default settings (will be overridden by _load_settings)
        # Custom preview settings
        self.custom_frame_count = 3
        self.custom_start_index = 0
        self.use_bmp_export = True  # False = PNG, True = BMP
        self.use_portrait_export = True  # Portrait mode (100x100)
        self.cute_bg_option = "both"  # Options: "no_cute_bg", "cute_bg", "both"
        self.palette_format = "png"  # Options: "pal", "png"
        self.show_frame_labels = True  # Whether to show frame numbers
        self.use_right_click = True  # True = Right click save (default), False = Left click save
        self.use_frame_choice = False  # Whether to use user-chosen frame for export
        self.chosen_frame = 1  # User's chosen frame for export (1-based)
        self.live_palette_mode = False  # Track if we're in live palette mode
        self.background_color = (255, 0, 255)  # Default background color (magenta)
        self.zoom_level = "100%"  # Track current zoom level
        self.image_flip = False
        self.image_rotation = 0
        self.live_pal_ui_mode = "Simple"  # Default to Simple mode for Live Pal Editor UI
        self._current_preview_mode = "single"  # Track current preview mode for intelligent switching
        self.colorpicker_active = False  # Track colorpicker mode for simple palette editor
        self.dark_mode = False  # Track dark mode state
        
        # UI button visibility settings

        
        # Load settings from file (will override defaults)
        self.hidden_frames = {}
        self.export_frames = {}
        self.loaded_palettes = {}
        self.frame_range_settings = {}
        self._load_settings()
        
        # HSL adjustment settings with defaults
        self._gradient_adjust_hue = True
        self._gradient_adjust_saturation = False
        self._gradient_adjust_value = False
        
        # Get root directory for relative paths
        self.root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Load base images
        script_dir = os.path.dirname(os.path.abspath(__file__))
        getattr(self, "root_dir", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        myshop_base_path = os.path.join(script_dir, "assets", "nonremovable_assets", "myshop_base.bmp")
        try:
            self.myshop_base = Image.open(myshop_base_path)
        except Exception as e:
            self.myshop_base = None
        
        # Available data
        self.available_characters = []
        self.available_jobs = []
        self.character_images = {}  # chr001 -> [list of image paths]
        self.fashion_palettes = {}  # chr001 -> [list of fashion palette paths]
        self.hair_palettes = {}     # chr001 -> [list of hair palette paths]
        self.third_job_palettes = {} # chr001 -> [list of 3rd job base fashion paths]
        self.custom_pals = {}       # chr001 -> [list of custom palette paths]
        
        # UI variables
        self.character_var = tk.StringVar()
        self.job_var = tk.StringVar()
        self.hair_var = tk.StringVar()
        self.third_job_var = tk.StringVar()
        self.zoom_var = tk.StringVar(value=getattr(self, 'zoom_level', "100%"))
        self.fashion_vars = {}  # Track fashion selection variables
        
        # Frame options tracking
        self.selected_frame = None  # Tracks user-clicked frame (None = current/first displayed)
        self.selected_frames = set() # Tracks multiple selected frames
        self.last_frame_click_time = 0  # For double-click detection
        self.last_clicked_frame = None  # For double-click detection
        import time
        self._time_module = time  # Store reference for click timing
        
        # View mode toggle (Big Picture Mode vs Small Preview Mode)
        self.view_mode = "big_picture"  # Options: "big_picture", "small_preview"
        
        # Frame visibility undo history (up to 5 steps)
        self.frame_visibility_history = []  # List of (char_job_key, hidden_frames_snapshot) tuples
        self.max_undo_steps = 5
        
        # Last selected palette for live editor
        self.last_selected_palette = None  # Stores the last clicked palette info
        self.last_selected_palette_type = None  # 'hair', 'fashion', 'third_job'
        
        # Initialization flag to prevent display updates during startup
        self._is_initializing = True
        
        # Load all available data
        self.load_all_data()
        
        # Create UI
        self.create_ui()
        self.apply_theme()
        
        # Try to restore last session state, otherwise auto-load first character
        restored = False
        if hasattr(self, 'last_character') and self.last_character and hasattr(self, 'last_job') and self.last_job:
            # Try to restore the saved character and job
            if self.last_character in self.available_characters:
                if self.last_character in CHARACTER_MAPPING:
                    char_info = CHARACTER_MAPPING[self.last_character]
                    
                    # Directly set the character and job without triggering on_character_change
                    self.current_character = self.last_character
                    self.current_job = char_info['job']
                    self.character_var.set(char_info['name'])
                    self.job_var.set(char_info['job'])
                    
                    # Set restoration flag to prevent saving during restoration
                    self._is_restoring_session = True
                    
                    # Load character settings and data
                    self._load_character_settings(self.last_character)
                    
                    # Populate frame_range_settings for the restored character/job combo
                    # This is needed for custom preview mode to work properly
                    if self.current_character not in self.frame_range_settings:
                        self.frame_range_settings[self.current_character] = {}
                    
                    # Store the custom frame settings for this character/job
                    self.frame_range_settings[self.current_character][char_info['job']] = (
                        self.custom_frame_count,
                        self.custom_start_index,
                        self.custom_start_index + self.custom_frame_count - 1
                    )
                    
                    # Track character view
                    self.statistics.add_character_view(self.last_character, char_info["job"])
                    self._save_statistics()
                    
                    # Update UI sections
                    self.update_third_job_section()
                    self.update_hair_section()
                    self.update_fashion_section()
                    
                    # Load palettes and update display
                    self.load_palettes()
                    self.update_zoom_combo_state()
                    
                    # Restore the last viewed frame if valid
                    if hasattr(self, 'last_frame') and self.last_frame is not None:
                        # Check if character has images loaded
                        if self.current_character in self.character_images:
                            images = self.character_images[self.current_character]
                            if images and 0 <= self.last_frame < len(images):
                                self.current_image_index = self.last_frame
                                # Load the specific frame
                                self.load_image_from_path(images[self.current_image_index])
                    
                    # Update display to show the restored state
                    self.update_image_display()
                    
                    # Update navigation buttons to enable them
                    self.update_navigation_buttons()
                    
                    # Clear restoration flag - now navigation can save settings
                    self._is_restoring_session = False
                    
                    restored = True
        
        # If restoration failed, auto-load first character if available
        if not restored and self.available_characters:
            first_char = self.available_characters[0]
            if first_char in CHARACTER_MAPPING:
                char_info = CHARACTER_MAPPING[first_char]
                self.character_var.set(char_info['name'])
                self.job_var.set(char_info['job'])
                self.on_character_change()
        
        # Initialize zoom combo state based on preview mode (after character is loaded)
        self.update_zoom_combo_state()
        
        # Final navigation button update after all initialization is complete
        if hasattr(self, 'update_navigation_buttons'):
            self.update_navigation_buttons()
        
        # Clear initialization flag - now display updates will work normally
        self._is_initializing = False
        
        # Do a single final display update now that everything is loaded
        if hasattr(self, 'update_image_display'):
            self.update_image_display()
        
        # Set up window close handler to save settings and statistics
        from code.utils.window_behavior import WindowBehavior
        self.master.protocol("WM_DELETE_WINDOW", lambda: WindowBehavior.on_app_close(self))

    # --- Smooth HSV slider: tiny debouncer to prevent jitter ----
    def _hsv_debounced_change(self, *_):
        from code.core.hsv_controls import HSVControls
        return HSVControls._hsv_debounced_change(self, *_)

    
    def _debounced_display_update(self):
        """Debounce main display updates to prevent flickering during live palette editing"""
        # Skip main display updates if live palette editor is open
        if (hasattr(self, '_live_editor_window') and 
            self._live_editor_window and 
            self._live_editor_window.winfo_exists()):
            return
        
        # Skip main display updates if icon palette editor is open
        from icon_handler import IconHandler
        if (IconHandler._icon_editor_instance and 
            IconHandler._icon_editor_instance.window and 
            IconHandler._icon_editor_instance.window.winfo_exists()):
            return
        
        # Cancel any prior scheduled display update
        try:
            if getattr(self, "_display_update_after_id", None):
                try:
                    self.master.after_cancel(self._display_update_after_id)
                except Exception:
                    pass
        except Exception:
            pass
        
        def _update_display():
            try:
                self.update_image_display()
            except Exception as e:
                print(f"Error updating display: {e}")
        
        # Schedule display update with slightly longer delay to reduce flickering
        try:
            self._display_update_after_id = self.master.after(50, _update_display)
        except Exception:
            _update_display()
    
    def _is_keyed_color(self, rgb_color, palette_index=None):
        """Check if an RGB color is a keyed/transparency color that should be avoided"""
        # Only pure green and pure magenta are universally avoided now
        if rgb_color == (0, 255, 0) or rgb_color == (255, 0, 255):
            return True
        return False
    
    def _find_nearest_non_keyed_color(self, target_rgb, adjustment_direction='both'):
        """Find the nearest non-keyed color by adjusting HSV values"""
        if not ColorTranslator._is_keyed_color(target_rgb):
            return target_rgb
            
        import colorsys
        r, g, b = target_rgb
        h, s, v = colorsys.rgb_to_hsv(r/255.0, g/255.0, b/255.0)
        
        if adjustment_direction == 'up':
            v = min(1.0, v + 0.02)
        elif adjustment_direction == 'down':
            v = max(0.0, v - 0.02)
        else:
            if v > 0.5:
                v = max(0.0, v - 0.02)
            else:
                v = min(1.0, v + 0.02)
                
        nr, ng, nb = colorsys.hsv_to_rgb(h, s, v)
        return (int(nr*255), int(ng*255), int(nb*255))
    

    
    def _get_current_or_selected_frame(self):
        from code.core.frame_manager import FrameManager
        return FrameManager._get_current_or_selected_frame(self)


    def _get_selected_frames_list(self):
        from code.core.frame_manager import FrameManager
        return FrameManager._get_selected_frames_list(self)

    
    def _select_frame(self, frame_index, event=None):
        from code.core.frame_manager import FrameManager
        return FrameManager._select_frame(self, frame_index, event)

    
    def _deselect_frame(self, refresh=True):
        from code.core.frame_manager import FrameManager
        return FrameManager._deselect_frame(self, refresh)

    
    def _hide_current_frame(self):
        from code.core.frame_manager import FrameManager
        return FrameManager._hide_current_frame(self)

    
    def _show_previous_frame(self):
        from code.core.frame_manager import FrameManager
        return FrameManager._show_previous_frame(self)

    
    def _show_all_frames(self):
        from code.core.frame_manager import FrameManager
        return FrameManager._show_all_frames(self)

    
    def _set_export_frame(self):
        from code.core.frame_manager import FrameManager
        return FrameManager._set_export_frame(self)

        
    def _show_next_frame(self):
        from code.core.frame_manager import FrameManager
        return FrameManager._show_next_frame(self)

    

    
    def _find_layer_by_pixel_index(self, pixel_idx):
        from code.core.index_loader import IndexLoader
        return IndexLoader._find_layer_by_pixel_index(self, pixel_idx)


    def _identify_layer_from_click(self, frame_idx, event):
        """Identify which layer corresponds to the clicked pixel and update selection"""
        if not hasattr(self, 'current_character') or not self.current_character:
            return
            
        # Removed strict Live Editor checks to allow updating global selection on click

        # Get the item clicked - verify it is an image
        try:
            # Check for overlapping items to handle cases where selection box is on top
            items = self.canvas.find_overlapping(event.x, event.y, event.x, event.y)
            item_id = None
            for item in reversed(items):  # internal tags often last
                if self.canvas.type(item) == "image":
                    item_id = item
                    break
            
            if not item_id:
                # Fallback to closest
                closest = self.canvas.find_closest(event.x, event.y)
                if closest and self.canvas.type(closest[0]) == "image":
                    item_id = closest[0]
            
            if not item_id:
                return
        except:
            return

        # Get Zoom info
        try:
            zoom_str = self.zoom_var.get()
            if zoom_str == "Fit":
                # For Fit mode, we re-calculate scale roughly
                canvas_width = self.canvas.winfo_width()
                canvas_height = self.canvas.winfo_height()
                padding = 10
                
                # Get original image dimensions
                images = self.character_images.get(self.current_character, [])
                if frame_idx >= len(images): return
                path = images[frame_idx]
                
                with Image.open(path) as img:
                    orig_w, orig_h = img.size
                    
                avail_w = canvas_width - (padding * 2)
                avail_h = canvas_height - (padding * 2)
                scale_x = avail_w / orig_w
                scale_y = avail_h / orig_h
                scale = min(scale_x, scale_y, 1.0)
            else:
                scale = float(zoom_str.strip('%')) / 100.0
        except:
            scale = 1.0

        # Map click to original image coordinates
        img_coords = self.canvas.coords(item_id)
        if not img_coords: return
        img_x, img_y = img_coords
        anchor = self.canvas.itemcget(item_id, "anchor")
        
        # Get original image path
        images = self.character_images.get(self.current_character, [])
        if frame_idx >= len(images): return
        path = images[frame_idx]
        
        try:
            with Image.open(path) as img:
                orig_w, orig_h = img.size
                
                # Calculate displayed dimensions
                disp_w = int(orig_w * scale)
                disp_h = int(orig_h * scale)
                
                # Calculate top-left of displayed image
                if anchor == "center":
                    x0 = img_x - disp_w // 2
                    y0 = img_y - disp_h // 2
                elif anchor == "n":
                    x0 = img_x - disp_w // 2
                    y0 = img_y
                else: # "nw"
                    x0, y0 = img_x, img_y
                
                # Relative coordinates
                if scale > 0:
                    rel_x = int((event.x - x0) / scale)
                    rel_y = int((event.y - y0) / scale)
                else:
                    return

                # Check bounds
                if 0 <= rel_x < orig_w and 0 <= rel_y < orig_h:
                    pixel_idx = img.getpixel((rel_x, rel_y))
                    
                    # Identify Layer
                    found_layer = self._find_layer_by_pixel_index(pixel_idx)
                    
                    if found_layer:
                        # Update global selection
                        self.last_selected_palette = found_layer.name
                        
                        # Switch Live Editor Selection if open
                        if (hasattr(self, '_live_editor_window') and self._live_editor_window and 
                            self._live_editor_window.winfo_exists() and hasattr(self, '_live_target_name')):
                            # Only update if different to avoid flickering/loops
                            if self._live_target_name.get() != found_layer.name:
                                self._live_target_name.set(found_layer.name)
                                self._live_on_target_changed()

        except Exception as e:
            # Silently fail if image issues
            pass

    
    def _redraw_frames_with_selection(self):
        from code.core.preview_refresher import PreviewRefresher
        return PreviewRefresher._redraw_frames_with_selection(self)



    def load_all_data(self):
        from code.core.data_loader import DataLoader
        DataLoader.load_all_data(self)

    def refresh_data(self):
        from code.core.preview_refresher import PreviewRefresher
        return PreviewRefresher.refresh_data(self)



    def register_focusable(self, widget, tag=None):
        """Register a widget as focusable and store its tag for quick access"""
        self.focusable_widgets.append(widget)
        if tag:
            if not hasattr(self, 'widget_tags'):
                self.widget_tags = {}
            self.widget_tags[tag] = widget
    
    def navigate_widgets(self, direction):
        """Handle up/down arrow key navigation"""
        current = self.master.focus_get()
        if current in self.focusable_widgets:
            current_idx = self.focusable_widgets.index(current)
            if direction == "up":
                next_idx = (current_idx - 1) % len(self.focusable_widgets)
            else:  # down
                next_idx = (current_idx + 1) % len(self.focusable_widgets)
            self.focusable_widgets[next_idx].focus_set()
    
    def handle_enter(self):
        """Handle Enter key press for selection"""
        current = self.master.focus_get()
        if current:
            if isinstance(current, (tk.Radiobutton, tk.Checkbutton)):
                current.invoke()  # Simulate click
            elif isinstance(current, tk.Button):
                current.invoke()  # Simulate button click
    


    def update_compact_palette_editor(self):
        from code.ui.pal_editor import PalEditor
        return PalEditor.update_compact_palette_editor(self)


    def update_image_display(self):
        """Update the image display with current palette"""
        # Skip display updates during initialization to prevent white flashing
        if getattr(self, '_is_initializing', False):
            return
        
        # Check if canvas exists and is valid
        if not hasattr(self, 'canvas') or not self.canvas.winfo_exists():
            return
            
        if not hasattr(self, 'current_character') or not self.current_character:
            self.canvas.delete("all")
            return
        
        preview_mode = self.preview_var.get()
        old_mode = getattr(self, '_last_preview_mode', None)
        # Only update _last_preview_mode if it's different and not the first time
        if old_mode is not None and old_mode != preview_mode:
            self._last_preview_mode = old_mode  # Keep the previous mode for intelligent switching
        elif old_mode is None:
            self._last_preview_mode = preview_mode  # Initialize on first run
        
        # Handle mode transitions
        if old_mode == "single" and preview_mode == "custom":
            # When switching from single to custom, start at current frame
            self.custom_start_index = self.current_image_index
        
        # Update zoom combo state before displaying (especially important for custom mode)
        self.update_zoom_combo_state()
        
        # Ensure current frame is not hidden when entering Single Mode
        if preview_mode == "single":
            char_job_key = self._get_char_job_key()
            hidden = self.hidden_frames.get(char_job_key, set())
            if self.current_image_index in hidden:
                images = self.character_images.get(self.current_character, [])
                total = len(images)
                if total > 1:
                    next_idx = (self.current_image_index + 1) % total
                    checked = 0
                    while next_idx in hidden and checked < total:
                        next_idx = (next_idx + 1) % total
                        checked += 1
                    if next_idx != self.current_image_index:
                        self.current_image_index = next_idx
                        self.load_image_from_path(images[self.current_image_index])
                        return
        
        if preview_mode == "single":
            self.update_single_frame_display()
        elif preview_mode == "all":
            self.update_all_frames_display()
        elif preview_mode == "custom":
            self.update_custom_frames_display()

    def apply_image_transformations(self, img):
        """Apply flip and rotation to an image"""
        from PIL import Image
        if getattr(self, 'image_flip', False):
            img = img.transpose(Image.FLIP_LEFT_RIGHT)
        rotation = getattr(self, 'image_rotation', 0)
        if rotation == 90:
            img = img.transpose(Image.ROTATE_270) # 90 clockwise = 270 counter-clockwise
        elif rotation == 180:
            img = img.transpose(Image.ROTATE_180)
        elif rotation == 270:
            img = img.transpose(Image.ROTATE_90)  # 270 clockwise = 90 counter-clockwise
        return img

    def update_single_frame_display(self):
        from code.core.preview_refresher import PreviewRefresher
        return PreviewRefresher.update_single_frame_display(self)


    def update_all_frames_display(self):
        from code.core.preview_refresher import PreviewRefresher
        return PreviewRefresher.update_all_frames_display(self)


    def update_custom_frames_display(self):
        from code.core.preview_refresher import PreviewRefresher
        return PreviewRefresher.update_custom_frames_display(self)


    def get_merged_palette(self, export_mode=False):
        """Get the merged palette, respecting keying colors and transparency
        If export_mode is True, keying colors are PRESERVED in the final palette so the game engine handles them."""
        if not self.original_palette:
            return [(0, 0, 0)] * PALETTE_SIZE
        
        result = self.original_palette.copy()
        
        # Check if we have a live editor open and get the current selection
        live_editor_active = (hasattr(self, '_live_editor_window') and 
                            self._live_editor_window and 
                            self._live_editor_window.winfo_exists())
        
        current_live_selection = None
        if live_editor_active and hasattr(self, '_live_target_name'):
            current_live_selection = self._live_target_name.get()
        
        # First, apply 3rd job base fashion to establish the base
        for layer in reversed(self.palette_layers):
            if not layer.active or layer.palette_type != "3rd_job_base":
                continue
            
            # Get allowed indices for this palette type and character
            char_num = self.current_character[3:] if self.current_character else None  # Extract number from chr001
            allowed_indices = self.get_allowed_indices_for_palette(layer, char_num)
            
            for i in range(PALETTE_SIZE):
                color = layer.colors[i]
                
                # Check if this color should be ignored based on palette type
                should_ignore = ColorTranslator.is_fashion_palette_keying_color(self, layer, color, i)
                
                # In export mode, NEVER ignore a keyed color if it was explicitly authored in this layer
                # because the game engine needs it to perform transparency!
                if export_mode and should_ignore:
                    should_ignore = False
                
                # Only apply colors that aren't keying colors AND are in allowed indices
                if (color is not None and not should_ignore and (i in allowed_indices or (getattr(layer, 'palette_type', '') == 'fashion_4' and char_num == '020'))):
                    result[i] = color
                elif layer.palette_type == "hair" and (i in allowed_indices or (getattr(layer, 'palette_type', '') == 'fashion_4' and char_num == '020')) and color is None:
                    # For hair palettes, if a color is None (not defined in palette), 
                    # keep the original color instead of leaving it unchanged
                    # This ensures all hair indices get processed
                    if i < len(self.original_palette):
                        result[i] = self.original_palette[i]
        
        # Then apply other layers (hair and regular fashion)
        for layer in reversed(self.palette_layers):
            if not layer.active or layer.palette_type == "3rd_job_base":
                continue
            
            # Get allowed indices for this palette type and character
            char_num = self.current_character[3:] if self.current_character else None  # Extract number from chr001
            allowed_indices = self.get_allowed_indices_for_palette(layer, char_num)
            
            # Check if this layer matches the current live editor selection
            layer_matches_live_editor = False
            if live_editor_active and current_live_selection:
                # Extract the fashion type from the display name (format: "Hoodie — chr001_w07")
                if " — " in current_live_selection:
                    current_live_selection.split(" — ")[0]
                    selected_char_id = current_live_selection.split(" — ")[1]
                else:
                    selected_char_id = ""
                
                # Get the layer's character ID and palette type
                layer_name = getattr(layer, 'name', '')
                layer_palette_type = getattr(layer, 'palette_type', '')
                
                # Match based on character ID and palette type
                if selected_char_id and layer_name:
                    # Extract character ID from layer name (e.g., "chr001_w07" -> "chr001")
                    char_match = re.search(r'(chr\d{3})', layer_name)
                    if char_match:
                        layer_char_id = char_match.group(1)
                        if layer_char_id == selected_char_id and layer_palette_type:
                            layer_matches_live_editor = True
            
            for i in range(PALETTE_SIZE):
                # Use original colors for layers that don't match the live editor selection
                if live_editor_active and not layer_matches_live_editor and hasattr(self, '_live_original_colors'):
                    layer_name = getattr(layer, 'name', '')
                    if layer_name in self._live_original_colors:
                        color = self._live_original_colors[layer_name][i]
                    else:
                        color = layer.colors[i]
                else:
                    color = layer.colors[i]
                
                # Check if this color should be ignored based on palette type
                should_ignore = False
                
                if layer.palette_type == "hair":
                    # For hair palettes, don't ignore any colors (apply all)
                    should_ignore = False
                    

                elif layer.palette_type.startswith("fashion_"):
                    # For fashion palettes, use fashion-specific keying colors
                    should_ignore = ColorTranslator.is_fashion_palette_keying_color(self, layer, color, i)
                else:
                    # For other palettes, use standard green/magenta keying
                    should_ignore = (self.is_green_padding(color) or 
                                   self.is_magenta_transparency(color))
                
                # In export mode, NEVER ignore a keyed color if it was explicitly authored in this layer
                # because the game engine needs it to perform transparency!
                if export_mode and should_ignore:
                    should_ignore = False
                
                # Only apply colors that aren't keying colors AND are in allowed indices
                if (color is not None and not should_ignore and 
                    (i in allowed_indices or (getattr(layer, 'palette_type', '') == 'fashion_4' and char_num == '020'))):
                    result[i] = color
                elif layer.palette_type == "hair" and (i in allowed_indices or (getattr(layer, 'palette_type', '') == 'fashion_4' and char_num == '020')) and color is None:
                    # For hair palettes, if a color is None (not defined in palette), 
                    # keep the original color instead of leaving it unchanged
                    # This ensures all hair indices get processed
                    if i < len(self.original_palette):
                        result[i] = self.original_palette[i]

        return result

    def get_allowed_indices_for_palette(self, layer, char_num):
        from code.core.index_loader import IndexLoader
        return IndexLoader.get_allowed_indices_for_palette(self, layer, char_num)


    def categorize_palette(self, filename):
        from code.core.color_translator import ColorTranslator
        return ColorTranslator.categorize_palette(self, filename)


    def determine_fashion_type_from_palette_content(self, filename, char_num=None):
        from code.core.color_translator import ColorTranslator
        return ColorTranslator.determine_fashion_type_from_palette_content(self, filename, char_num)




    def convert_rgba_to_rgb_with_green_transparency(self, rgba_img, background_color=None):
        """Convert RGBA image to RGB, making transparent pixels use the specified background color (defaults to green)"""
        if rgba_img.mode != 'RGBA':
            return rgba_img.convert('RGB')
        
        # Use custom background color if provided, otherwise default to green
        if background_color is None:
            background_color = (0, 255, 0)  # Default green
        
        # Create a new RGB image
        rgb_img = Image.new('RGB', rgba_img.size)
        rgba_pixels = rgba_img.load()
        rgb_pixels = rgb_img.load()
        
        for y in range(rgba_img.height):
            for x in range(rgba_img.width):
                r, g, b, a = rgba_pixels[x, y]
                if a == 0:  # Transparent pixel
                    rgb_pixels[x, y] = background_color  # Use custom background color
                else:
                    rgb_pixels[x, y] = (r, g, b)  # Keep original color
        
        return rgb_img













    def is_green_padding(self, color):
        """Check if a color is green padding (0, 255, 0)"""
        return color == (0, 255, 0)

    def is_magenta_transparency(self, color):
        """Check if a color is magenta transparency (255, 0, 255)"""
        return color == (255, 0, 255)


    




    def get_character_palette_ranges(self, char_num, palette_type):
        from code.core.character_loader import CharacterLoader
        return CharacterLoader.get_character_palette_ranges(self, char_num, palette_type)


    def reset_scroll_positions(self):
        """Reset hair and fashion scroll positions to top"""
        if hasattr(self, 'hair_canvas'):
            self.hair_canvas.yview_moveto(0)
        if hasattr(self, 'fashion_canvas'):
            self.fashion_canvas.yview_moveto(0)

    def get_display_image_for_export(self, frame_index=None):
        """Get the current image with palettes applied without updating display"""
        if not self.original_image:
            return None
            
        # Get the current frame index (respects user choice) if not provided
        if frame_index is None:
            frame_index = self.get_current_displayed_frame()
            
        original_img = self.character_images[self.current_character][frame_index]
        

        
        # Get the original palette
        try:
            with open(original_img, 'rb') as f:
                bmp = Image.open(f)
                list(bmp.getpalette())
                bmp.close()
        except Exception:
            return None
            
        # Load original image and get its data
        with Image.open(original_img) as img:
            pixel_data = list(img.get_flattened_data())
            w, h = img.size

        # Create new image with background color
        bg_img = Image.new("RGB", (w, h), self.background_color)
        
        # Create a mask for non-transparent pixels (index 0 is transparent)
        mask_img = Image.new("L", (w, h), 0)  # L mode for single channel
        mask_data = [255 if p != 0 else 0 for p in pixel_data]
        mask_img.putdata(mask_data)
        
        # Create foreground image with current palettes
        fg_img = Image.new("P", (w, h))
        fg_img.putpalette(self._flatten_palette(self.get_merged_palette()))
        fg_img.putdata(pixel_data)
        fg_img = fg_img.convert("RGB")
        
        # Composite foreground onto background using mask
        bg_img.paste(fg_img, (0, 0), mask_img)
        return bg_img
        
    def export_background(self):
        from code.core.exporter import Exporter
        return Exporter.export_background(self)


    def export_background_bmp(self, frame=None, force_portrait=False, silent=False):
        from code.core.exporter import Exporter
        return Exporter.export_background_bmp(self, frame, force_portrait, silent)

            
    def export_transparent_png(self):
        from code.core.exporter import Exporter
        return Exporter.export_transparent_png(self)


    def export_all_frames(self):
        from code.core.exporter import Exporter
        return Exporter.export_all_frames(self)


    def update_bg_color_button(self):
        """Update the background color button appearance"""
        self.bg_color_button.configure(bg=f'#{self.background_color[0]:02x}{self.background_color[1]:02x}{self.background_color[2]:02x}')

    def pick_background_color(self):
        """Open color picker to change background color for preview"""
        from tkinter import colorchooser
        
        # Convert current color to hex to pass to askcolor (prevents tuple errors on some platforms)
        hex_current = f"#{self.background_color[0]:02x}{self.background_color[1]:02x}{self.background_color[2]:02x}"
        # Open color picker dialog
        color = colorchooser.askcolor(title="Choose Background Color", color=hex_current)
        
        if color[1]:  # color[1] contains the hex color, color[0] contains RGB tuple
            # Convert hex to RGB
            hex_color = color[1]
            r = int(hex_color[1:3], 16)
            g = int(hex_color[3:5], 16)
            b = int(hex_color[5:7], 16)
            self.background_color = (r, g, b)
            
            # Update the button color to show current background
            self.bg_color_button.configure(bg=hex_color)
            
            # Update the main preview to reflect new background
            self.update_single_frame_display()
            
            # Save settings to persist background color
            self._save_settings()
            
            # Refresh the display with new background color
            self._debounced_display_update()
    
    def export_pal(self):
        from code.core.exporter import Exporter
        return Exporter.export_pal(self)


    # === Live Edit Palette (Per-Item with Dropdown) ===
    
    # === Live Edit Palette (Per-Item) with Embedded Color Picker ===
    
    def open_live_palette_editor(self):
        from code.ui.pal_editor import PalEditor
        return PalEditor.open_live_palette_editor(self)


    def _create_advanced_palette_grid(self, grid, ly):
        from code.ui.pal_editor import PalEditor
        return PalEditor._create_advanced_palette_grid(self, grid, ly)

    
    def _create_simple_palette_grid(self, grid, ly):
        from code.ui.pal_editor import PalEditor
        return PalEditor._create_simple_palette_grid(self, grid, ly)


    def _get_editable_color_indices(self, layer=None):
        from code.core.index_loader import IndexLoader
        return IndexLoader._get_editable_color_indices(self, layer)


    def _simple_prev_frame(self):
        from code.core.frame_manager import FrameManager
        return FrameManager._simple_prev_frame(self)


    def _simple_next_frame(self):
        from code.core.frame_manager import FrameManager
        return FrameManager._simple_next_frame(self)


    def _simple_on_zoom_change(self, *args):
        """Handle zoom change in simple mode preview"""
        self._update_simple_preview()

    def _on_simple_canvas_configure(self, event):
        """Handle canvas resize to update image display"""
        # Update the preview when canvas size changes
        self._update_simple_preview()

    def _on_simple_preview_middle_click(self, event):
        """Handle middle mouse button click to start panning immediately without index check."""
        self._simple_click_moved = False
        self._simple_pan_start_x = event.x
        self._simple_pan_start_y = event.y
        self._simple_is_panning = True  # Always enable panning for middle click


    def _on_simple_preview_click(self, event):
        """Handle click on simple mode preview to select color index or pick color."""
        # Reset panning state
        self._simple_click_moved = False
        self._simple_pan_start_x = event.x
        self._simple_pan_start_y = event.y
        
        if self.colorpicker_active:
            self._colorpick_from_simple_preview(event)
            return
        
        # Original preview click behavior for color selection
        try:
            if not hasattr(self, 'current_character') or not self.current_character:
                return
            
            if self.current_character not in self.character_images:
                return
            
            images = self.character_images[self.current_character]
            if not images or self._simple_current_frame >= len(images):
                return
            
            # Get click coordinates relative to the canvas
            click_x = event.x
            click_y = event.y
            
            # Get the current zoom and image dimensions
            zoom = self._simple_zoom_var.get()
            # Get actual canvas dimensions dynamically
            canvas_width = self._simple_preview_canvas.winfo_width()
            canvas_height = self._simple_preview_canvas.winfo_height()
            
            # Fallback to reasonable defaults if canvas not yet configured
            if canvas_width <= 1:
                canvas_width = 500
            if canvas_height <= 1:
                canvas_height = 200
            
            # Load the original image to get pixel data
            original_img_path = images[self._simple_current_frame]
            original_img = Image.open(original_img_path).convert("P")
            img_width, img_height = original_img.size
            
            # Calculate the displayed image size based on zoom
            if zoom == "Fit":
                scale_x = canvas_width / img_width
                scale_y = canvas_height / img_height
                scale = min(scale_x, scale_y)
                display_width = int(img_width * scale)
                display_height = int(img_height * scale)
            elif zoom == "200%":
                display_width = img_width * 2
                display_height = img_height * 2
            elif zoom == "300%":
                display_width = img_width * 3
                display_height = img_height * 3
            elif zoom == "400%":
                display_width = img_width * 4
                display_height = img_height * 4
            elif zoom == "500%":
                display_width = img_width * 5
                display_height = img_height * 5
            else:  # 100%
                display_width = img_width
                display_height = img_height
            
            # Calculate the image position (centered in canvas + pan offset)
            image_x = (canvas_width - display_width) / 2 + self._simple_pan_offset_x
            image_y = (canvas_height - display_height) / 2 + self._simple_pan_offset_y
            
            # Check if click is within the image bounds
            if (click_x < image_x or click_x >= image_x + display_width or
                click_y < image_y or click_y >= image_y + display_height):
                # Click outside image - enable panning
                self._simple_is_panning = True
                return
            
            # Convert click coordinates to original image coordinates
            relative_x = click_x - image_x
            relative_y = click_y - image_y
            
            # Scale back to original image coordinates
            if zoom == "Fit":
                original_x = int(relative_x / scale)
                original_y = int(relative_y / scale)
            elif zoom == "200%":
                original_x = int(relative_x / 2)
                original_y = int(relative_y / 2)
            elif zoom == "300%":
                original_x = int(relative_x / 3)
                original_y = int(relative_y / 3)
            elif zoom == "400%":
                original_x = int(relative_x / 4)
                original_y = int(relative_y / 4)
            elif zoom == "500%":
                original_x = int(relative_x / 5)
                original_y = int(relative_y / 5)
            else:  # 100%
                original_x = int(relative_x)
                original_y = int(relative_y)
            
            # Ensure coordinates are within image bounds
            if (0 <= original_x < img_width and 0 <= original_y < img_height):
                # Get the palette index at this pixel
                pixel_index = original_img.getpixel((original_x, original_y))
                
                # Check if this index is in our editable indices for the current layer
                current_layer = self._live_current_layer()
                editable_indices = self._get_editable_color_indices(current_layer)
                if pixel_index in editable_indices:
                    # Select this index in the live editor
                    self._live_select_index(pixel_index)
                    
                    # Update selection UI
                    self._selected_indices.clear()
                    self._selected_indices.add(pixel_index)
                    self._update_selection_ui()
                else:
                    # Click on non-indexed pixel - enable panning
                    self._simple_is_panning = True
                    
        except Exception as e:
            print(f"CONSOLE ERROR MSG: Error handling simple preview click: {e}")

    def _on_simple_preview_drag(self, event):
        """Handle dragging on the simple preview canvas to pan the image."""
        if self._simple_is_panning:
            # Mark that the mouse has moved
            self._simple_click_moved = True
            
            # Calculate the drag delta
            delta_x = event.x - self._simple_pan_start_x
            delta_y = event.y - self._simple_pan_start_y
            
            # Update pan offset
            self._simple_pan_offset_x += delta_x
            self._simple_pan_offset_y += delta_y
            
            # Update start position for next drag event
            self._simple_pan_start_x = event.x
            self._simple_pan_start_y = event.y
            
            # Update the preview with new pan offset
            self._update_simple_preview()
            
            # Change cursor to indicate panning
            self._simple_preview_canvas.configure(cursor="fleur")
    
    def _on_simple_preview_release(self, event):
        """Handle mouse release to end panning."""
        if self._simple_is_panning:
            self._simple_is_panning = False
            # Restore cursor
            self._simple_preview_canvas.configure(cursor="hand2")


    def _update_simple_preview(self):
        from code.core.preview_refresher import PreviewRefresher
        return PreviewRefresher._update_simple_preview(self)


    def _apply_palettes_to_image_path(self, image_path):
        """Apply current active palettes to a specific image file and return the result"""
        try:
            # Load the image
            original_img = Image.open(image_path).convert("P")
            
            # Get the merged palette (same logic as update_single_frame_display)
            merged_palette = self.get_merged_palette()
            
            # Create a new image with the merged palette
            w, h = original_img.size
            display_img = Image.new("P", (w, h))
            
            # Apply the merged palette FIRST
            display_img.putpalette(self._flatten_palette(merged_palette))
            
            # THEN copy the pixel data from original image
            display_img.putdata(original_img.get_flattened_data())
            
            # Replace transparency colors with background color in the merged palette
            display_palette = []
            
            for i, color in enumerate(merged_palette):
                if ColorTranslator.is_universal_keying_color(color) or color == (255, 0, 255):  # Green or magenta
                    display_palette.append(self.background_color)
                else:
                    display_palette.append(color)
            
            # Apply the modified palette to the display image
            display_img.putpalette(self._flatten_palette(display_palette))
            
            # Convert to RGB for display
            rgb_img = display_img.convert("RGB")
            
            return rgb_img
            
        except Exception as e:
            print(f"CONSOLE ERROR MSG: Error applying palettes to image: {e}")
            return None
    
    def _toggle_colorpicker(self):
        from code.core.color_picker import ColorPicker
        return ColorPicker._toggle_colorpicker(self)

    
    def _on_simple_palette_click(self, palette_idx, event):
        from code.ui.pal_editor import PalEditor
        return PalEditor._on_simple_palette_click(self, palette_idx, event)

    
    def _colorpick_from_simple_palette(self, palette_idx):
        from code.core.color_picker import ColorPicker
        return ColorPicker._colorpick_from_simple_palette(self, palette_idx)

    
    def _colorpick_from_simple_preview(self, event):
        from code.core.color_picker import ColorPicker
        return ColorPicker._colorpick_from_simple_preview(self, event)

    
    def _apply_colorpicked_color_simple(self, picked_color):
        from code.core.color_picker import ColorPicker
        return ColorPicker._apply_colorpicked_color_simple(self, picked_color)


    def _rebuild_live_palette_grid(self):
        from code.ui.pal_editor import PalEditor
        return PalEditor._rebuild_live_palette_grid(self)


    def _update_simple_palette_colors(self, ly):
        from code.ui.pal_editor import PalEditor
        return PalEditor._update_simple_palette_colors(self, ly)


    def _live_multi_toggled(self):
        # Collapse to single index if turning off multi-select
        if not self._multi_select.get():
            if self._selected_indices:
                last = sorted(self._selected_indices)[-1]
                self._selected_indices.clear()
                self._live_select_index(last)
        self._update_selection_ui()

    
    def _update_selection_ui(self):
        # Visual highlight for selected tiles and selection count
        # Use simple outline approach to avoid flashing and color corruption
        
        if self.live_pal_ui_mode == "Simple":
            # Simple mode: only update visible editable colors
            editable_indices = self._get_editable_color_indices()
            for display_idx, palette_idx in enumerate(editable_indices):
                if display_idx >= len(self._live_swatches) or self._live_swatches[display_idx] is None:
                    continue
                    
                btn = self._live_swatches[display_idx]
                
                # Check if widget exists
                try:
                    if not btn.winfo_exists():
                        continue
                except Exception:
                    continue
                
                try:
                    if palette_idx in self._selected_indices:
                        # Get the current color to preserve it
                        r, g, b = self._live_layers[self._live_name_to_index[self._live_target_name.get()]].colors[palette_idx]
                        hex_color = f"#{r:02x}{g:02x}{b:02x}"
                        
                        # Always use red border for selected colors
                        border_color = "red"
                        
                        # Redraw with border highlight (40x40 for simple mode)
                        btn.delete("all")
                        # Draw border
                        btn.create_rectangle(0, 0, 40, 40, fill=border_color, outline="")
                        # Draw color rectangle inside
                        btn.create_rectangle(1, 1, 39, 39, fill=hex_color, outline="")
                    else:
                        # Get the current color to preserve it
                        r, g, b = self._live_layers[self._live_name_to_index[self._live_target_name.get()]].colors[palette_idx]
                        hex_color = f"#{r:02x}{g:02x}{b:02x}"
                        
                        # Redraw with normal appearance
                        btn.delete("all")
                        btn.create_rectangle(1, 1, 39, 39, fill=hex_color, outline="black", width=1)
                except Exception:
                    pass
        else:
            # Advanced mode: update all 256 colors
            for i, btn in enumerate(self._live_swatches):
                if btn is None:
                    continue
                    
                # Check if widget exists
                try:
                    if not btn.winfo_exists():
                        continue
                except Exception:
                    continue
                
                try:
                    if i in self._selected_indices:
                        # Get the current color to preserve it
                        r, g, b = self._live_layers[self._live_name_to_index[self._live_target_name.get()]].colors[i]
                        hex_color = f"#{r:02x}{g:02x}{b:02x}"
                        
                        # Always use red border for selected colors
                        border_color = "red"
                        
                        # Redraw with border highlight (keep 20x20 and 19x19 as requested)
                        btn.delete("all")
                        # Draw border
                        btn.create_rectangle(0, 0, 20, 20, fill=border_color, outline="")
                        # Draw color rectangle inside
                        btn.create_rectangle(1, 1, 19, 19, fill=hex_color, outline="")
                    else:
                        # Get the current color to preserve it
                        r, g, b = self._live_layers[self._live_name_to_index[self._live_target_name.get()]].colors[i]
                        hex_color = f"#{r:02x}{g:02x}{b:02x}"
                        
                        # Redraw with normal appearance
                        btn.delete("all")
                        btn.create_rectangle(1, 1, 19, 19, fill=hex_color, outline="black", width=1)
                except Exception:
                    pass
        
        if hasattr(self, "_sel_count_lbl"):
            try:
                self._sel_count_lbl.config(text=f"({len(self._selected_indices)} selected)")
            except Exception:
                pass

    def _live_select_all(self):
        """Select all editable color swatches in the current palette."""
        if hasattr(self, '_live_swatches'):
            # Prevent HSV slider callbacks from applying changes during selection
            self._updating_live_selection = True
            try:
                # Enable multi-select mode to allow relative HSV adjustments
                self._multi_select.set(True)
                
                # Select all editable color indices regardless of UI mode
                editable_indices = self._get_editable_color_indices()
                self._selected_indices = set(editable_indices)
                
                if self._selected_indices:
                    self._last_clicked_index = min(self._selected_indices)
                    # Update sliders to show first selected color
                    self._live_select_index(self._last_clicked_index)
                self._update_selection_ui()
                # Force pending events to process before clearing flag
                if hasattr(self, '_live_editor_window') and self._live_editor_window:
                    self._live_editor_window.update_idletasks()
            finally:
                self._updating_live_selection = False
    
    def _live_clear_selection(self):
        self._selected_indices.clear()
        self._last_clicked_index = None
        self._update_selection_ui()

    def _live_reset_selected(self):
        """Reset only the selected colors back to their original state"""
        if not hasattr(self, '_live_original_colors') or not hasattr(self, '_live_layers'):
            return
            
        if not hasattr(self, '_selected_indices') or not self._selected_indices:
            from tkinter import messagebox
            messagebox.showinfo("Notice", "No colors selected to reset.")
            return
            
        current_name = self._live_target_name.get()
        if current_name not in self._live_original_colors:
            return
            
        # Find the current layer
        current_layer = None
        target_filename = current_name
        if " — " in current_name:
            target_filename = current_name.split(" — ")[-1]
            
        for layer in self._live_layers:
            if hasattr(layer, 'name') and (layer.name == current_name or layer.name == target_filename):
                current_layer = layer
                break
                
        if not current_layer:
            return
            
        # Restore selected original colors to the layer data
        original_colors = self._live_original_colors[current_name]
        for i in self._selected_indices:
            if i < len(current_layer.colors) and i < len(original_colors):
                current_layer.colors[i] = original_colors[i]
                
        # Update temp cache with reset colors
        if hasattr(self, '_live_temp_palette_cache'):
            self._live_temp_palette_cache[current_name] = current_layer.colors.copy()
            
        # Handle reset differently for Simple vs Advanced mode
        if self.live_pal_ui_mode == "Simple":
            self._simple_mode_reset(current_layer)
        else:
            self._advanced_mode_reset(current_layer)

    def _live_reset_to_original(self):
        """Reset the current layer's colors back to their original state"""
        if not hasattr(self, '_live_original_colors') or not hasattr(self, '_live_layers'):
            return
        
        current_name = self._live_target_name.get()
        if current_name not in self._live_original_colors:
            return
        
        # Find the current layer
        current_layer = None
        
        # Extract just the filename from the current_name if it contains a display prefix
        target_filename = current_name
        if " — " in current_name:
            target_filename = current_name.split(" — ")[-1]  # Get the part after the last " — "
        
        for layer in self._live_layers:
            # Try both exact match and filename match
            if hasattr(layer, 'name') and (layer.name == current_name or layer.name == target_filename):
                current_layer = layer
                break
        
        if not current_layer:
            return
        
        # Restore original colors to the layer data
        original_colors = self._live_original_colors[current_name]
        current_layer.colors = original_colors.copy()
        
        # Update temp cache with reset colors
        if hasattr(self, '_live_temp_palette_cache'):
            self._live_temp_palette_cache[current_name] = current_layer.colors.copy()
        
        # Handle reset differently for Simple vs Advanced mode
        if self.live_pal_ui_mode == "Simple":
            self._simple_mode_reset(current_layer)
        else:
            self._advanced_mode_reset(current_layer)
    
    def _simple_mode_reset(self, current_layer):
        """Reset colors specifically for Simple mode using EXACT _live_hsv_changed logic"""
        # Get all editable indices to reset
        editable_indices = self._get_editable_color_indices()
        
        # Reset each editable color using the EXACT same logic as _live_hsv_changed
        for i in editable_indices:
            # Get the original color for this palette index (already restored to current_layer.colors)
            r, g, b = current_layer.colors[i] if isinstance(current_layer.colors[i], tuple) else (0, 0, 0)
            
            # Update swatch based on mode (EXACT copy from _live_hsv_changed)
            if self.live_pal_ui_mode == "Simple":
                # Find the display index for this palette index
                editable_indices_check = self._get_editable_color_indices()
                if i in editable_indices_check:
                    display_idx = editable_indices_check.index(i)
                    
                    if display_idx < len(self._live_swatches) and self._live_swatches[display_idx] is not None:
                        canvas = self._live_swatches[display_idx]
                        hex_color = f"#{r:02x}{g:02x}{b:02x}"
                        
                        try:
                            canvas.delete("all")
                            canvas.create_rectangle(1, 1, 39, 39, fill=hex_color, outline="black", width=1)
                        except Exception as e:
                            print(f"CONSOLE ERROR MSG: Error updating palette swatch {display_idx}: {e}")
        
        # Try forcing a palette refresh
        try:
            self._live_refresh_swatches()
        except Exception as e:
            print(f"CONSOLE ERROR MSG: Error refreshing palette swatches: {e}")
        
        # Reapply selection highlighting after color changes
        if hasattr(self, "_update_selection_ui"):
            try:
                self._update_selection_ui()
            except Exception as e:
                print(f"CONSOLE ERROR MSG: Error updating selection UI: {e}")
        
        # Update color picker
        focus = self._live_selected_index
        if focus < len(current_layer.colors):
            fr, fg, fb = current_layer.colors[focus]
            try:
                self._picker_preview.config(bg=f"#{fr:02x}{fg:02x}{fb:02x}")
                self._picker_hex.delete(0, "end")
                self._picker_hex.insert(0, f"#{fr:02x}{fg:02x}{fb:02x}")
            except Exception as e:
                print(f"CONSOLE ERROR MSG: Error updating color picker: {e}")
        
        # Update main image display (debounced to prevent flickering)
        try:
            self._debounced_display_update()
        except Exception as e:
            print(f"CONSOLE ERROR MSG: Error updating main image display: {e}")
        
        # Update simple mode preview if in simple mode
        if self.live_pal_ui_mode == "Simple" and hasattr(self, '_update_simple_preview'):
            try:
                self._update_simple_preview()
            except Exception as e:
                print(f"CONSOLE ERROR MSG: Error updating simple mode preview: {e}")
    
    def _advanced_mode_reset(self, current_layer):
        """Reset colors specifically for Advanced mode"""
        # Advanced mode: update all 256 colors
        cols = current_layer.colors
        for i in range(256):  # PALETTE_SIZE = 256
            r, g, b = cols[i] if isinstance(cols[i], tuple) else (0, 0, 0)
            try:
                canvas = self._live_swatches[i]
                hex_color = f"#{int(r):02x}{int(g):02x}{int(b):02x}"
                canvas.delete("all")
                canvas.create_rectangle(1, 1, 19, 19, fill=hex_color, outline="black", width=1)
            except Exception as e:
                print(f"CONSOLE ERROR MSG: Error updating advanced mode swatch {i}: {e}")
        
        # Keep selection visuals
        if hasattr(self, "_update_selection_ui"):
            try:
                self._update_selection_ui()
            except Exception as e:
                print(f"CONSOLE ERROR MSG: Error updating selection UI: {e}")
        
        # Update color picker
        focus = self._live_selected_index
        if focus < len(current_layer.colors):
            fr, fg, fb = current_layer.colors[focus]
            try:
                self._picker_preview.config(bg=f"#{fr:02x}{fg:02x}{fb:02x}")
                self._picker_hex.delete(0, "end")
                self._picker_hex.insert(0, f"#{fr:02x}{fg:02x}{fb:02x}")
            except Exception as e:
                print(f"CONSOLE ERROR MSG: Error updating color picker: {e}")
        
        # Update main image display (debounced to prevent flickering)
        try:
            self._debounced_display_update()
        except Exception as e:
            print(f"CONSOLE ERROR MSG: Error updating main image display: {e}")



    def reset_pals(self):
        """Reset all palette selections to their initial state (Reset Pals)"""
        self._deselect_frame(refresh=False)
        if not self.original_image:
            messagebox.showinfo("Reset", "No image loaded")
            return
        
        # Reset hair selection to NONE
        self.hair_var.set("NONE")
        
        # Reset all fashion selections to NONE
        for fashion_type, var in self.fashion_vars.items():
            var.set("NONE")
        
        # Special handling for third job characters (except Paula)
        if hasattr(self, 'current_character') and self.current_character:
            char_id = self.current_character
            if (char_id in CHARACTER_MAPPING and 
                CHARACTER_MAPPING[char_id]["job"] == "3rd Job" and
                char_id not in ["chr025", "chr026", "chr027", "chr100", "chr101", "chr102"]):  # Not Paula
                
                # Set the first third job palette as default (like initial load)
                palette_char_id = self.get_palette_character_id(char_id)
                if palette_char_id in self.third_job_palettes and self.third_job_palettes[palette_char_id]:
                    first_palette = self.third_job_palettes[palette_char_id][0]
                    self.third_job_var.set(first_palette)
                else:
                    self.third_job_var.set("NONE")
            else:
                # For all other characters, set third job to NONE
                self.third_job_var.set("NONE")
        else:
            self.third_job_var.set("NONE")
        
        # Reload palettes with the new selections (this will handle third job auto-loading)
        self.load_palettes()
        
        # Update the image display
        self._debounced_display_update()
        messagebox.showinfo("Reset Pals", "All palette selections have been reset to original.")

    def reset_frames(self):
        from code.core.frame_manager import FrameManager
        return FrameManager.reset_frames(self)


    def _live_on_swatch_click(self, i, event):
        # Prevent clicks during palette switching to avoid cross-palette contamination
        current_time = time.time()
        switch_time = getattr(self, '_palette_switch_time', 0)
        if current_time - switch_time < 0.1:  # 100ms debounce for clicks
            return
        
        # Set flag to prevent any potential grid recreation during selection updates
        self._updating_live_selection = True
        
        # Detect Shift key for range selection (state bit 0x0001 usually indicates Shift)
        shift = bool(getattr(event, "state", 0) & 0x0001)
        if self._multi_select.get():
            if shift and self._last_clicked_index is not None:
                a, b = sorted((self._last_clicked_index, i))
                for j in range(a, b+1):
                    self._selected_indices.add(j)
            else:
                if i in self._selected_indices:
                    self._selected_indices.remove(i)
                else:
                    self._selected_indices.add(i)
            self._last_clicked_index = i
            self._update_selection_ui()
            # Keep picker synced to last clicked
            self._live_select_index(i)
        else:
            # Single-select - clear previous selection and add current one
            self._selected_indices.clear()
            self._selected_indices.add(i)  # Add the selected index for highlighting
            self._last_clicked_index = i
            self._update_selection_ui()
            self._live_select_index(i)
        
        # Clear the flag to allow any potential grid operations again
        self._updating_live_selection = False



    def _hide_selected_frames(self):
        from code.core.frame_manager import FrameManager
        return FrameManager._hide_selected_frames(self)


    def _sync_hsv_from_rgb(self, r, g, b):
        try:
            h, s, v = colorsys.rgb_to_hsv(r/255.0, g/255.0, b/255.0)
            # guard flag to avoid recursive callbacks
            self._in_sync = True
            if not getattr(self, "_is_dragging", False):
                self._picker_h.set(int(round(h*360)))
                self._picker_s.set(int(round(s*100)))
                self._picker_v.set(int(round(v*100)))
        finally:
            self._in_sync = False

    def _sync_rgb_from_hsv(self, h_deg, s_pct, v_pct):
        """Return RGB ints from HSV without touching non-existent RGB widgets."""
        h = (h_deg % 360) / 360.0
        s = max(0, min(100, int(s_pct))) / 100.0
        v = max(0, min(100, int(v_pct))) / 100.0
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        return int(round(r*255)), int(round(g*255)), int(round(b*255))


    def _live_hsv_changed(self):
        if getattr(self, "_in_sync", False):
            return

        ly = self._live_current_layer()
        if ly is None:
            return
        
        # Prevent applying colors during palette switching to avoid color copying between palettes
        if getattr(self, '_updating_live_selection', False):
            return
        
        # Additional protection: Check if we just switched palettes recently (debounce)
        current_time = time.time()
        switch_time = getattr(self, '_palette_switch_time', 0)
        if current_time - switch_time < 0.2:  # 200ms debounce
            return
        
        # Verify we're still on the same palette to prevent cross-contamination
        current_name = self._live_target_name.get()
        if hasattr(self, '_current_live_palette_name') and current_name != self._current_live_palette_name:
            return

        H_new = int(self._picker_h.get())
        S_new = int(self._picker_s.get())
        V_new = int(self._picker_v.get())

        targets = sorted(self._selected_indices) if self._multi_select.get() and self._selected_indices else [self._live_selected_index]
        use_relative = self._multi_select.get() and len(targets) > 1

        if use_relative:
            base_i = self._live_selected_index
            br, bg, bb = ly.colors[base_i] if isinstance(ly.colors[base_i], tuple) else (0, 0, 0)
            bh, bs, bv = colorsys.rgb_to_hsv(br/255.0, bg/255.0, bb/255.0)
            bh = int(round(bh * 360))
            bs = int(round(bs * 100))
            bv = int(round(bv * 100))

            dH = H_new - bh
            EPS = 1  # treat <=1% as zero-ish to avoid stuck scaling
            use_scaleS = bs > EPS
            use_scaleV = bv > EPS
            scaleS = (S_new/100.0) / (bs/100.0) if use_scaleS else None
            scaleV = (V_new/100.0) / (bv/100.0) if use_scaleV else None
            # Clamp additive deltas to prevent extreme changes when base color is near black/gray
            dS = max(-50, min(50, S_new - bs)) if not use_scaleS else 0
            dV = max(-50, min(50, V_new - bv)) if not use_scaleV else 0
        else:
            dH = 0; scaleS = 1.0; scaleV = 1.0; dS = 0; dV = 0

        for i in targets:
            # Check if the original color was a keying color. If so, DO NOT shift it!
            if hasattr(self, '_live_original_colors') and self._live_original_colors.get(ly.name):
                orig_color = self._live_original_colors[ly.name][i]
                is_orig_key = False
                if getattr(ly, 'palette_type', '') == "hair":
                    pass
                elif getattr(ly, 'palette_type', '').startswith("fashion_"):
                    is_orig_key = ColorTranslator.is_fashion_palette_keying_color(self, ly, orig_color, i)
                else:
                    is_orig_key = self.is_green_padding(orig_color) or self.is_magenta_transparency(orig_color)
                
                if is_orig_key:
                    ly.colors[i] = orig_color
                    continue

            r, g, b = ly.colors[i] if isinstance(ly.colors[i], tuple) else (0, 0, 0)
            h, s, v = colorsys.rgb_to_hsv(r/255.0, g/255.0, b/255.0)
            h = int(round(h * 360)); s = int(round(s * 100)); v = int(round(v * 100))

            if use_relative:
                h = (h + dH) % 360
                EPS_TGT = 2
                # Saturation per-swatch: additive if target near zero or scale unavailable; else multiplicative
                if s <= EPS_TGT or scaleS is None:
                    s = max(0, min(100, int(round(s + dS))))
                else:
                    s = max(0, min(100, int(round(s * scaleS))))
                # Value per-swatch: additive if target near zero or scale unavailable; else multiplicative
                if v <= EPS_TGT or scaleV is None:
                    # Additional safety: don't apply extreme negative dV to colors that aren't already dark
                    if dV < -20 and v > 20:  # If trying to apply large negative change to bright color
                        v = max(20, min(100, int(round(v + max(dV, -20)))))  # Limit the darkening
                    else:
                        v = max(0, min(100, int(round(v + dV))))
                else:
                    v = max(0, min(100, int(round(v * scaleV))))
            else:
                h, s, v = H_new % 360, max(0, min(100, S_new)), max(0, min(100, V_new))

            # --- FIX: ensure self.char_num exists ---
            if not hasattr(self, "char_num"):
                import re
                cid = str(getattr(self, "char_id", ""))
                m = re.search(r"(\d+)$", cid)   # e.g. "chr019" -> "019"
                self.char_num = m.group(1) if m else "000"
            # ---------------------------------------

            # Force HSV Nudge if we land on a base keying color
            candidate_color = (int(round(r*255)), int(round(g*255)), int(round(b*255)))
            if candidate_color == (0, 255, 0) or candidate_color == (255, 0, 255):
                candidate_color = ColorTranslator._find_nearest_non_keyed_color(candidate_color)
                
            ly.colors[i] = candidate_color

            rr, gg, bb = colorsys.hsv_to_rgb((h % 360)/360.0, s/100.0, v/100.0)
            rr, gg, bb = int(round(rr*255)), int(round(gg*255)), int(round(bb*255))
            
            # Check if new color would be a keying color
            candidate_color = (rr, gg, bb)
            if (ColorTranslator.is_universal_keying_color(candidate_color) or 
                candidate_color == (255, 0, 255) or  # Magenta
                (hasattr(self, 'is_chr003_keying_color') and ColorTranslator.is_chr003_keying_color(candidate_color)) or  # Sheep
                (hasattr(self, 'is_chr008_keying_color') and ColorTranslator.is_chr008_keying_color(candidate_color)) or  # Raccoon
                (hasattr(self, 'is_chr011_keying_color') and ColorTranslator.is_chr011_keying_color(candidate_color)) or  # Sheep 2nd Job
                (hasattr(self, 'is_chr014_keying_color') and ColorTranslator.is_chr014_keying_color(candidate_color)) or  # Lion 2nd Job
                (hasattr(self, 'is_palette_keying_color') and ColorTranslator.is_palette_keying_color(candidate_color, i, self.char_num))):  # Any other character-specific rules
                candidate_color = ColorTranslator._find_nearest_non_keyed_color(candidate_color)
                rr, gg, bb = candidate_color
            
            ly.colors[i] = (rr, gg, bb)
            
            # Update temp cache with the new color
            if hasattr(self, '_live_temp_palette_cache') and hasattr(self, '_current_live_palette_name'):
                current_name = getattr(self, '_current_live_palette_name', None)
                if current_name and current_name in self._live_temp_palette_cache:
                    self._live_temp_palette_cache[current_name] = ly.colors.copy()
            
            # Update swatch based on mode
            if self.live_pal_ui_mode == "Simple":
                # Find the display index for this palette index
                editable_indices = self._get_editable_color_indices()
                if i in editable_indices:
                    display_idx = editable_indices.index(i)
                    if display_idx < len(self._live_swatches) and self._live_swatches[display_idx] is not None:
                        canvas = self._live_swatches[display_idx]
                        hex_color = f"#{rr:02x}{gg:02x}{bb:02x}"
                        canvas.delete("all")
                        canvas.create_rectangle(1, 1, 39, 39, fill=hex_color, outline="black", width=1)
            else:
                # Advanced mode: direct index mapping
                if i < len(self._live_swatches) and self._live_swatches[i] is not None:
                    canvas = self._live_swatches[i]
                    hex_color = f"#{rr:02x}{gg:02x}{bb:02x}"
                    canvas.delete("all")
                    canvas.create_rectangle(1, 1, 19, 19, fill=hex_color, outline="black", width=1)
        # Reapply selection highlighting after color changes
        if hasattr(self, "_update_selection_ui"):
            self._update_selection_ui()
        focus = self._live_selected_index
        fr, fg, fb = ly.colors[focus]
        self._picker_preview.config(bg=f"#{fr:02x}{fg:02x}{fb:02x}")
        self._picker_hex.delete(0, "end"); self._picker_hex.insert(0, f"#{fr:02x}{fg:02x}{fb:02x}")

        self._debounced_display_update()
        
        # Update simple mode preview if in simple mode
        if self.live_pal_ui_mode == "Simple" and hasattr(self, '_update_simple_preview'):
            self._update_simple_preview()

        self._in_sync = True
        try:
            if not getattr(self, "_is_dragging", False):
                if use_relative:
                    self._picker_h.set(int(H_new % 360))
                    self._picker_s.set(int(max(0, min(100, S_new))))
                    self._picker_v.set(int(max(0, min(100, V_new))))
                else:
                    fh, fs, fv = colorsys.rgb_to_hsv(fr/255.0, fg/255.0, fb/255.0)
                    self._picker_h.set(int(round(fh * 360)))
                    self._picker_s.set(int(round(fs * 100)))
                    self._picker_v.set(int(round(fv * 100)))
        finally:
            self._in_sync = False
        # Sync numeric entry boxes if present
        try:
            self._hsv_h_str.set(str(int(self._picker_h.get())))
            self._hsv_s_str.set(str(int(self._picker_s.get())))
            self._hsv_v_str.set(str(int(self._picker_v.get())))
        except Exception:
            pass




    def _live_refresh_swatches(self):
        from code.core.preview_refresher import PreviewRefresher
        return PreviewRefresher._live_refresh_swatches(self)


    def _live_on_target_changed(self, *_):
        """Called when the item dropdown changes; rebuild swatches for the new layer and reset selection."""
        
        # Ask warning if switching to Hair or 3rd Job Base
        try:
            new_name = self._live_target_name.get()
            idx = self._live_name_to_index.get(new_name, 0)
            ly = self._live_layers[idx]
            
            # Update palette job mapping for the new selection
            if hasattr(ly, "palette_type"):
                char_match = re.search(r'chr(\d{3})', new_name)
                if char_match:
                    char_num = char_match.group(1)
                    if char_num in CHARACTER_MAPPING:
                        char_info = CHARACTER_MAPPING[char_num]
                        self._live_palette_job_mapping[new_name] = {
                            'palette_type': ly.palette_type,
                            'character': char_info['name'],
                            'job': char_info['job']
                        }
            
            # Store UI mode before warning dialog
            current_ui_mode = getattr(self, 'live_pal_ui_mode', 'Simple')
            if not self._warn_if_nonimpact(getattr(ly, "palette_type", "")):
                # Revert selection
                try:
                    self._live_target_name.set(getattr(self, "_live_prev_target_name", new_name))
                except Exception:
                    pass
                # Restore UI mode after warning dialog
                self.live_pal_ui_mode = current_ui_mode
                # Bring live editor window to front after user clicked "No"
                if hasattr(self, '_live_editor_window') and self._live_editor_window and self._live_editor_window.winfo_exists():
                    self._live_editor_window.lift()
                    self._live_editor_window.focus_force()
                return
            # Restore UI mode after warning dialog
            self.live_pal_ui_mode = current_ui_mode
            self._live_prev_target_name = new_name
            
            # Update icon editor button state after switching palette types
            self._update_icon_editor_button_state()
        except Exception:
            pass
        # Save current palette's temporary changes to cache before switching
        if hasattr(self, '_current_live_palette_name') and hasattr(self, '_live_temp_palette_cache'):
            old_name = getattr(self, '_current_live_palette_name', None)
            if old_name and old_name in self._live_name_to_index:
                old_idx = self._live_name_to_index[old_name]
                if old_idx < len(self._live_layers):
                    # Save current state to temp cache
                    self._live_temp_palette_cache[old_name] = self._live_layers[old_idx].colors.copy()
        
        # Clear all selection state to prevent color copying between palettes
        self._selected_indices = set()
        self._last_clicked_index = None
        self._live_selected_index = 0  # Reset to first color
        
        # Track current palette to prevent cross-palette contamination
        self._current_live_palette_name = new_name
        
        # Set flag to prevent color changes during palette switching with timestamp
        self._updating_live_selection = True
        self._palette_switch_time = time.time() if hasattr(time, 'time') else 0
        
        # Restore temporary changes for the newly selected layer from cache
        if hasattr(self, '_live_temp_palette_cache') and new_name in self._live_temp_palette_cache:
            # Restore from temp cache to preserve temporary changes
            ly.colors = self._live_temp_palette_cache[new_name].copy()
        elif hasattr(self, '_live_original_colors') and new_name in self._live_original_colors:
            # Fallback to original colors if not in temp cache (shouldn't happen normally)
            ly.colors = self._live_original_colors[new_name].copy()
            # Also add to temp cache for future switches
            if hasattr(self, '_live_temp_palette_cache'):
                self._live_temp_palette_cache[new_name] = ly.colors.copy()
        
        # Update palette colors for the new layer without rebuilding entire UI
        if self.live_pal_ui_mode == "Simple":
            self._update_simple_palette_colors(ly)
        else:
            # For advanced mode, update existing swatches
            if hasattr(self, '_live_swatches') and self._live_swatches:
                for i, canvas in enumerate(self._live_swatches):
                    if canvas is not None and i < len(ly.colors):
                        r, g, b = ly.colors[i] if isinstance(ly.colors[i], tuple) else (0, 0, 0)
                        hex_color = f"#{r:02x}{g:02x}{b:02x}"
                        try:
                            canvas.delete("all")
                            canvas.create_rectangle(1, 1, 19, 19, fill=hex_color, outline="black", width=1)
                        except:
                            pass
        
        # Update simple mode preview if in simple mode
        if self.live_pal_ui_mode == "Simple" and hasattr(self, '_update_simple_preview'):
            self._update_simple_preview()
        
        # Notify the icon editor if it's open
        self._notify_icon_editor_palette_change()
        # Seed picker with index 0 for the new layer
        self._live_select_index(0)
        
        # Update main canvas display to reflect the new active palette layer
        if hasattr(self, '_debounced_display_update'):
            self._debounced_display_update()
        
        # Clear the updating flag after a short delay to ensure all palette switching is complete
        def clear_protection():
            self._updating_live_selection = False
            # Update the palette name tracking
            self._current_live_palette_name = new_name
        
        # Use a small delay to ensure all UI updates are complete before allowing color changes
        try:
            self.master.after(250, clear_protection)  # 250ms delay
        except:
            # Fallback if master doesn't exist
            clear_protection()
    
    def _notify_icon_editor_palette_change(self):
        from code.ui.icon_editor import IconEditor
        return IconEditor._notify_icon_editor_palette_change(self)


    def _live_current_layer(self):
        if not hasattr(self, "_live_layers") or not self._live_layers:
            return None
        idx = self._live_name_to_index.get(self._live_target_name.get(), 0)
        idx = max(0, min(idx, len(self._live_layers)-1))
        return self._live_layers[idx]

    def _live_select_index(self, i):
        from code.ui.pal_editor import PalEditor
        return PalEditor._live_select_index(self, i)



    def _live_goto_index(self):
        from code.ui.pal_editor import PalEditor
        return PalEditor._live_goto_index(self)


    def _live_apply_hex(self):

        txt = self._picker_hex.get().strip()
        if txt.startswith("#"):
            txt = txt[1:]
        if len(txt) != 6:
            return
        try:
            r = int(txt[0:2], 16); g = int(txt[2:4], 16); b = int(txt[4:6], 16)
        except Exception:
            return
        # Directly apply RGB to the palette
        ly = self._live_current_layer()
        if ly is None:
            return
        
        # Prevent applying colors during palette switching to avoid color copying between palettes
        if getattr(self, '_updating_live_selection', False):
            return
        
        # Additional protection: Check if we just switched palettes recently (debounce)
        current_time = time.time()
        switch_time = getattr(self, '_palette_switch_time', 0)
        if current_time - switch_time < 0.2:  # 200ms debounce
            return
        
        # Verify we're still on the same palette to prevent cross-contamination
        current_name = self._live_target_name.get()
        if hasattr(self, '_current_live_palette_name') and current_name != self._current_live_palette_name:
            return
            
        targets = sorted(self._selected_indices) if self._multi_select.get() and self._selected_indices else [self._live_selected_index]
        for i in targets:
            ly.colors[i] = (r, g, b)
            # Track statistics
            self.statistics.indexes_changed += 1
            self.statistics.colors_saved += 1
            if hasattr(self, 'current_character') and hasattr(self, 'current_job'):
                self.statistics.add_palette_edit(self.current_character, self.current_job)
                self.statistics.live_palette_files_edited.add(ly.name)
            self._save_statistics()
            
            # Update swatch based on mode
            if self.live_pal_ui_mode == "Simple":
                # Find the display index for this palette index
                editable_indices = self._get_editable_color_indices()
                if i in editable_indices:
                    display_idx = editable_indices.index(i)
                    if display_idx < len(self._live_swatches) and self._live_swatches[display_idx] is not None:
                        canvas = self._live_swatches[display_idx]
                        hex_color = f"#{r:02x}{g:02x}{b:02x}"
                        canvas.delete("all")
                        canvas.create_rectangle(1, 1, 39, 39, fill=hex_color, outline="black", width=1)
            else:
                # Advanced mode: direct index mapping
                if i < len(self._live_swatches) and self._live_swatches[i] is not None:
                    canvas = self._live_swatches[i]
                    hex_color = f"#{r:02x}{g:02x}{b:02x}"
                    canvas.delete("all")
                    canvas.create_rectangle(1, 1, 19, 19, fill=hex_color, outline="black", width=1)
        # Reapply selection highlighting after color changes
        if hasattr(self, "_update_selection_ui"):
            self._update_selection_ui()
        self._picker_preview.config(bg=f"#{r:02x}{g:02x}{b:02x}")
        self._debounced_display_update()
        # Sync HSV sliders from this RGB
        self._sync_hsv_from_rgb(r, g, b)
        
        # Update simple mode preview if in simple mode
        if self.live_pal_ui_mode == "Simple" and hasattr(self, '_update_simple_preview'):
            self._update_simple_preview()


    def _live_slider_changed(self):
        # RGB sliders removed in HSV-only mode; keep as no-op to satisfy any callers.
        return


    def _open_gradient_menu(self, parent=None, is_compact=False):
        from code.ui.gradient_menu import GradientMenu
        return GradientMenu._open_gradient_menu(self, parent, is_compact)


    def _apply_gradient_hue(self, target_hue, color_name, variant=None):
        from code.ui.gradient_menu import GradientMenu
        return GradientMenu._apply_gradient_hue(self, target_hue, color_name, variant)

    
    def _update_gradient_settings(self, setting, value):
        from code.ui.gradient_menu import GradientMenu
        return GradientMenu._update_gradient_settings(self, setting, value)

    
    def _reset_gradient_colors(self):
        from code.ui.gradient_menu import GradientMenu
        return GradientMenu._reset_gradient_colors(self)

    
    def _load_vanilla_palette_for_layer(self, char_num, palette_type, layer_name):
        """Load original palette colors for a specific layer (handles both custom and vanilla palettes)."""
        try:
            # First, check if this is a custom palette by looking in custom directories
            root_dir = getattr(self, "root_dir", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
            # Check custom hair directory
            if palette_type == "hair":
                custom_hair_dir = os.path.join(root_dir, "exports", "custom_pals", "hair")
                custom_hair_file = os.path.join(custom_hair_dir, layer_name)
                
                if os.path.exists(custom_hair_file):
                    # This is a custom hair palette, load the original custom file
                    print(f"Loading original custom hair palette: {custom_hair_file}")
                    with open(custom_hair_file, 'rb') as f:
                        pal_data = f.read()
                    
                    colors = []
                    for i in range(0, len(pal_data), 3):
                        if i + 2 < len(pal_data):
                            r, g, b = pal_data[i], pal_data[i+1], pal_data[i+2]
                            colors.append((r, g, b))
                    return colors
            
            # Check custom fashion directories
            elif palette_type.startswith("fashion_"):
                custom_fashion_dir = os.path.join(root_dir, "exports", "custom_pals", "fashion")
                old_custom_fashion_dir = os.path.join(root_dir, "exports", "custom_fashion_pals")
                
                for custom_dir in [custom_fashion_dir, old_custom_fashion_dir]:
                    custom_fashion_file = os.path.join(custom_dir, layer_name)
                    if os.path.exists(custom_fashion_file):
                        # This is a custom fashion palette, load the original custom file
                        print(f"Loading original custom fashion palette: {custom_fashion_file}")
                        with open(custom_fashion_file, 'rb') as f:
                            pal_data = f.read()
                        
                        colors = []
                        for i in range(0, len(pal_data), 3):
                            if i + 2 < len(pal_data):
                                r, g, b = pal_data[i], pal_data[i+1], pal_data[i+2]
                                colors.append((r, g, b))
                        return colors
            
            # If not found in custom directories, try vanilla directories
            script_dir = os.path.dirname(os.path.abspath(__file__))
            vanilla_dir = os.path.join(script_dir, "assets", "nonremovable_assets", "vanilla_pals")
            
            if palette_type == "hair":
                # For vanilla hair palettes, use the exact layer name
                vanilla_file = os.path.join(vanilla_dir, "hair", layer_name)
            elif palette_type.startswith("fashion_"):
                # For vanilla fashion palettes, use the exact layer name
                vanilla_file = os.path.join(vanilla_dir, "fashion", layer_name)
            elif palette_type == "3rd_job_base":
                vanilla_file = os.path.join(vanilla_dir, "3rd_default_fashion", layer_name)
            else:
                return None
            
            if os.path.exists(vanilla_file):
                # Load vanilla palette file
                print(f"Loading original vanilla palette: {vanilla_file}")
                with open(vanilla_file, 'rb') as f:
                    pal_data = f.read()
                
                # Parse palette data
                colors = []
                for i in range(0, len(pal_data), 3):
                    if i + 2 < len(pal_data):
                        r, g, b = pal_data[i], pal_data[i+1], pal_data[i+2]
                        colors.append((r, g, b))
                
                return colors
            else:
                print(f"Original palette file not found: {vanilla_file}")
                return None
                
        except Exception as e:
            print(f"CONSOLE ERROR MSG: Error loading original palette: {e}")
            return None
    

    


    def _live_save_item_pal(self, layer=None):
        from code.ui.pal_editor import PalEditor
        return PalEditor._live_save_item_pal(self, layer)

    
    def _live_open_icon_editor(self):
        from code.ui.icon_editor import IconEditor
        return IconEditor._live_open_icon_editor(self)

    
    def _update_icon_editor_button_state(self):
        from code.ui.icon_editor import IconEditor
        return IconEditor._update_icon_editor_button_state(self)


    def bulk_export_visuals(self):
        from code.core.exporter import Exporter
        return Exporter.bulk_export_visuals(self)


    def _open_icon_editor(self):
        from code.ui.icon_editor import IconEditor
        return IconEditor._open_icon_editor(self)

    
    def _quick_export_icon(self):
        from code.core.exporter import Exporter
        return Exporter._quick_export_icon(self)

    
    def _quick_export_icon_from_dialog(self, path, ly, dialog):
        from code.core.exporter import Exporter
        return Exporter._quick_export_icon_from_dialog(self, path, ly, dialog)

    
    def _quick_export_icon_from_dialog_no_close(self, path, ly):
        from code.core.exporter import Exporter
        return Exporter._quick_export_icon_from_dialog_no_close(self, path, ly)

    
    def _ask_icon_save_choice(self, path, ly):
        from code.core.exporter import Exporter
        return Exporter._ask_icon_save_choice(self, path, ly)


    def open_xml_generator_dialog(self):
        from code.ui.xml_generator import XMLGenerator
        return XMLGenerator.open_xml_generator_dialog(self)

        
    def open_full_creator(self, data):
        """Placeholder for launching fashion_creator.py GUI"""
        try:
            import fashion_creator
            creator = fashion_creator.FashionCreatorApp(self.master, data, previewer_app=self)
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Error", f"Failed to launch fashion creator: {e}")
            print(f"Failed to launch creator: {e}")

    def quick_xml_export(self, data):
        from code.ui.xml_generator import XMLGenerator
        return XMLGenerator.quick_xml_export(self, data)


    
    def _close_dialog(self, dialog, result, choice):
        """Close the dialog and set the result."""
        result["choice"] = choice
        dialog.destroy()

    def refresh_custom_pals(self, update_ui=True):
        from code.core.preview_refresher import PreviewRefresher
        return PreviewRefresher.refresh_custom_pals(self, update_ui)


    def get_custom_pals_paths(self):
        """Get list of custom palette directories to check"""
        root_dir = getattr(self, "root_dir", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        # Use new structure: custom_pals/fashion and custom_pals/hair
        custom_fashion_path = os.path.join(root_dir, "exports", "custom_pals", "fashion")
        custom_hair_path = os.path.join(root_dir, "exports", "custom_pals", "hair")
        # Also check old path for backward compatibility
        old_custom_fashion_path = os.path.join(root_dir, "exports", "custom_fashion_pals")
        
        # Ensure directories exist
        os.makedirs(custom_fashion_path, exist_ok=True)
        os.makedirs(custom_hair_path, exist_ok=True)
        
        paths = [custom_fashion_path, custom_hair_path]
        if os.path.exists(old_custom_fashion_path):
            paths.append(old_custom_fashion_path)
        
        return paths

    def debug_info(self):
        """Show debug information"""
        info = f"Current Character: {self.character_var.get()}\n"
        info += f"Current Job: {self.job_var.get()}\n"
        info += f"Selected Hair: {self.hair_var.get()}\n"
        info += f"Selected 3rd Job Base: {self.third_job_var.get()}\n"
        
        
        # Add preview mode info
        info += f"Preview Mode: {self.preview_var.get()}\n"
        info += f"Zoom Level: {self.zoom_var.get()}\n"
        
        # Add frame info
        if self.preview_var.get() == "custom":
            info += f"Frames Displayed: {getattr(self, 'custom_frame_count', 3)}\n"
            info += f"Starting Frame: {getattr(self, 'custom_start_index', 0) + 1}\n"  # +1 for 1-based display
            if hasattr(self, 'chosen_frame'):
                info += f"Selected Frame for Export: {self.chosen_frame}\n"  # Already 1-based
        elif self.preview_var.get() == "all":
            total_frames = len(self.character_images.get(self.current_character, []))
            info += f"Frames Displayed: {total_frames}\n"
            info += "Starting Frame: 1\n"  # All frames mode always starts at 1
        else:  # single mode
            info += "Frames Displayed: 1\n"
            current_frame = self.current_image_index + 1 if hasattr(self, 'current_image_index') else 1
            info += f"Current Frame: {current_frame}\n"
        
        # Add palette layers info
        # Add custom pals info
        self.current_character
        active_custom_pals = 0
        for layer in self.palette_layers:
            if layer.active and layer.name.startswith("Active"):
                active_custom_pals += 1
        info += f"Active Custom Pals Loaded: {active_custom_pals}\n"
        info += f"Loaded Palette Layers: {len(self.palette_layers)}\n"
        for i, layer in enumerate(self.palette_layers):
            info += f"  {i+1}. {layer.name} ({layer.palette_type}) - {'Active' if layer.active else 'Inactive'}\n"
        
        debug_dialog = tk.Toplevel(self.master)
        debug_dialog.title("Debug Info")
        debug_dialog.geometry("500x600")
        debug_dialog.transient(self.master)
        
        main_frame = tk.Frame(debug_dialog)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        text = tk.Text(main_frame, wrap="word", font=("Courier", 10))
        text.insert("1.0", info)
        text.config(state="disabled")
        text.pack(fill="both", expand=True, pady=(0, 10))
        
        tk.Button(main_frame, text="Close", command=debug_dialog.destroy).pack()
        self._center_window_on_parent(debug_dialog)
        
        from code.utils.theme_manager import ThemeManager
        ThemeManager.apply_theme(self, debug_dialog)
        debug_dialog.grab_set()

    def show_current_display_info(self):
        """Show current display information"""
        try:
            # Create dialog window
            info_dialog = tk.Toplevel(self.master)
            info_dialog.title("Current Display Info")
            info_dialog.geometry("500x600")
            
            info_dialog.transient(self.master)
            info_dialog.resizable(False, False)
            
            # Main frame with padding
            main_frame = tk.Frame(info_dialog)
            main_frame.pack(fill="both", expand=True, padx=30, pady=20)
            
            char_name = self.character_var.get() if hasattr(self, 'character_var') else "Unknown"
            job_name = self.job_var.get() if hasattr(self, 'job_var') else "Unknown"
            
            info = f"Character: {char_name}\n"
            info += f"Job: {job_name}\n"
            
            hair_pal = "None"
            fashion_pals = []
            third_job_base = "None"
            
            if hasattr(self, 'palette_layers'):
                for layer in self.palette_layers:
                    if getattr(layer, 'active', False):
                        layer_name = getattr(layer, 'name', 'Unknown')
                        if getattr(layer, 'palette_type', '') == "hair":
                            hair_pal = os.path.basename(layer_name)
                        elif getattr(layer, 'palette_type', '').startswith("fashion_"):
                            label = layer.palette_type.capitalize().replace('_', ' ')
                            name = os.path.basename(layer_name)
                            fashion_pals.append(f"{label} : {name}")
                        elif getattr(layer, 'palette_type', '') == "3rd_job_base":
                            third_job_base = os.path.basename(layer_name)
                        
            info += f"Hair palette: {hair_pal}\n"
            for fp in sorted(fashion_pals):
                info += f"{fp}\n"
                
            if third_job_base != "None":
                info += f"Third job base: {third_job_base}\n"
                
            current_frame = 1
            total_frames = 0
            try:
                current_frame = self.get_current_displayed_frame() + 1
                if hasattr(self, 'current_character') and getattr(self, 'current_character', None):
                    total_frames = len(self.character_images.get(self.current_character, []))
            except Exception as e:
                print(f"Error getting frame info: {e}")
                
            info += f"Frame: {current_frame} / {total_frames}\n"
            
            info_label = tk.Label(main_frame, text=info, justify="left", font=("Arial", 11))
            info_label.pack(pady=(0, 20))
            
            # Close button
            close_btn = tk.Button(main_frame, text="Close", 
                                 command=info_dialog.destroy, font=("Arial", 10), width=10)
            close_btn.pack()
            
            # Center the dialog
            info_dialog.update_idletasks()
            self._center_window_on_parent(info_dialog)
            
            # Grab set AFTER successful build to prevent freezing on error
            info_dialog.grab_set()
            
            # Bring to front
            info_dialog.lift()
            from code.utils.theme_manager import ThemeManager
            ThemeManager.apply_theme(self, info_dialog)
            info_dialog.focus_force()
        except Exception as e:
            print(f"Error showing display info: {e}")
            if 'info_dialog' in locals():
                info_dialog.destroy()
            from tkinter import messagebox
            messagebox.showerror("Error", f"Could not show display info: {e}")

    def show_credits(self):
        """Show credits dialog"""
        # Create credits dialog window
        credits_dialog = tk.Toplevel(self.master)
        credits_dialog.title("Credits & Acknowledgements")
        credits_dialog.geometry("600x500")
        
        credits_dialog.transient(self.master)
        credits_dialog.grab_set()
        credits_dialog.resizable(False, False)
        
        # Main frame with padding
        main_frame = tk.Frame(credits_dialog)
        main_frame.pack(fill="both", expand=True, padx=30, pady=20)
        
        # Credits message
        credits_text = ("This program has been brought to you by the wonderful staff of CoraTO: "
                       "Dino, Yuki, and Mewsie, and the initial foundation for the project as well as "
                       "additional research provided by KusanagiKyo.\n\n"
                       "Thank you all, truly, for your hard work and dedication to this community, "
                       "to providing this awesome, free tool for everyone!")
        
        credits_label = tk.Label(main_frame, text=credits_text, wraplength=400, justify="center", 
                                font=("Arial", 11))
        credits_label.pack(pady=(0, 20))
        
        # Thank you button
        thank_you_btn = tk.Button(main_frame, text="Thank you guys :)", 
                                 command=credits_dialog.destroy, font=("Arial", 10))
        thank_you_btn.pack()
        
        # Center the dialog
        credits_dialog.update_idletasks()
        dialog_width = credits_dialog.winfo_width()
        dialog_height = credits_dialog.winfo_height()
        
        parent_x = self.master.winfo_x()
        parent_y = self.master.winfo_y()
        parent_width = self.master.winfo_width()
        parent_height = self.master.winfo_height()
        
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2
        
        credits_dialog.geometry(f"+{x}+{y}")
        
        from code.utils.theme_manager import ThemeManager
        ThemeManager.apply_theme(self, credits_dialog)
    
    def show_statistics(self):
        self._deselect_frame()
        """Show statistics dialog"""
        StatisticsDialog(self)
    
    def _center_window(self):
        """Center the main window on the screen."""
        # Update the window to get accurate dimensions
        self.master.update_idletasks()
        
        # Get window dimensions
        window_width = self.master.winfo_width()
        window_height = self.master.winfo_height()
        
        # Get screen dimensions
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()
        
        # Calculate center position
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        # Set the window position
        self.master.geometry(f"{window_width}x{window_height}+{x}+{y}")
    
    def _bring_live_editor_to_front(self):
        """Bring the live palette editor window to the front with multiple methods for reliability across platforms."""
        try:
            if hasattr(self, '_live_editor_window') and self._live_editor_window and self._live_editor_window.winfo_exists():
                import platform
                system = platform.system().lower()
                
                # Common methods that work on both platforms
                self._live_editor_window.deiconify()  # Ensure window is not minimized
                self._live_editor_window.lift()  # Bring to front in stacking order
                
                if system == "windows":
                    # Windows-specific focus handling
                    self._live_editor_window.focus_force()  # Force keyboard focus
                    self._live_editor_window.attributes('-topmost', True)  # Temporarily make topmost
                    self._live_editor_window.after(100, lambda: self._live_editor_window.attributes('-topmost', False))  # Remove topmost after 100ms
                    
                    # Additional Windows focus methods
                    try:
                        self._live_editor_window.wm_attributes('-topmost', 1)
                        self._live_editor_window.after(10, lambda: self._live_editor_window.wm_attributes('-topmost', 0))
                    except:
                        pass
                        
                elif system == "linux":
                    # Linux-specific focus handling
                    self._live_editor_window.focus_set()  # Set focus (gentler than focus_force)
                    self._live_editor_window.tkraise()  # Raise window in stacking order
                    
                    # Try to activate the window (X11 specific)
                    try:
                        self._live_editor_window.wm_attributes('-topmost', True)
                        self._live_editor_window.after(50, lambda: self._live_editor_window.wm_attributes('-topmost', False))
                    except:
                        pass
                        
                    # Additional method for some Linux window managers
                    try:
                        self._live_editor_window.focus()
                    except:
                        pass
                        
                else:
                    # Fallback for other systems (macOS, etc.)
                    self._live_editor_window.focus_set()
                    self._live_editor_window.tkraise()
                
        except Exception as e:
            pass
    
    def _open_live_pal_settings_menu(self):
        from code.ui.pal_editor import PalEditor
        return PalEditor._open_live_pal_settings_menu(self)

    
    def _save_live_pal_ui_mode_setting(self, ui_mode):
        """Save Live Pal Editor UI mode setting to settings.json"""
        try:
            import json
            import os
            settings_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")
            
            # Load existing settings
            settings = {}
            if os.path.exists(settings_path):
                try:
                    with open(settings_path, 'r', encoding='utf-8') as f:
                        settings = json.load(f)
                except:
                    settings = {}
            
            # Update live pal editor UI mode
            settings['live_pal_editor_ui_mode'] = ui_mode
            
            # Save back
            with open(settings_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4)
        except Exception as e:
            print(f"Error saving Live Pal UI mode setting: {e}")
    
    
    def _center_window_on_parent(self, window, parent=None, width=None, height=None):
        """Center a window on its parent window or screen if no parent."""
        if parent is None:
            parent = self.master
        
        # Use provided dimensions or get from window
        if width is None or height is None:
            window.update_idletasks()
            window_width = window.winfo_width() if width is None else width
            window_height = window.winfo_height() if height is None else height
        else:
            window_width = width
            window_height = height
        
        if parent and parent.winfo_exists():
            # Center on parent window
            parent_x = parent.winfo_x()
            parent_y = parent.winfo_y()
            parent_width = parent.winfo_width()
            parent_height = parent.winfo_height()
            
            # Calculate center position relative to parent
            x = parent_x + (parent_width - window_width) // 2
            y = parent_y + (parent_height - window_height) // 2
        else:
            # Center on screen if no parent
            screen_width = window.winfo_screenwidth()
            screen_height = window.winfo_screenheight()
            x = (screen_width - window_width) // 2
            y = (screen_height - window_height) // 2
        
        # Set the window geometry with position
        window.geometry(f"{window_width}x{window_height}+{x}+{y}")
    
    def toggle_view_mode(self):
        from code.ui.main_previewer import MainPreviewer
        return MainPreviewer.toggle_view_mode(self)

    
    def _get_char_job_key(self):
        from code.core.character_loader import CharacterLoader
        return CharacterLoader._get_char_job_key(self)

    
    def _save_frame_visibility_state(self):
        """Save current frame visibility state to undo history"""
        char_job_key = self._get_char_job_key()
        if not char_job_key:
            return
        
        # Get current hidden frames for this character/job
        hidden = self.hidden_frames.get(char_job_key, set()).copy()
        flip = getattr(self, 'image_flip', False)
        rot = getattr(self, 'image_rotation', 0)
        
        # Add to history
        self.frame_visibility_history.append((char_job_key, hidden, flip, rot))
        
        # Limit history to max_undo_steps
        if len(self.frame_visibility_history) > self.max_undo_steps:
            self.frame_visibility_history.pop(0)
    
    def undo_frame_visibility(self):
        from code.core.frame_manager import FrameManager
        return FrameManager.undo_frame_visibility(self)

    
    def toggle_all_frames_visibility(self):
        from code.core.frame_manager import FrameManager
        return FrameManager.toggle_all_frames_visibility(self)

    
    def toggle_selected_frames_visibility(self):
        from code.core.frame_manager import FrameManager
        return FrameManager.toggle_selected_frames_visibility(self)

    
    def quick_export(self):
        from code.core.exporter import Exporter
        return Exporter.quick_export(self)

    
    def on_palette_selection_change(self, palette_type, palette_path):
        """Track palette selection for live editor"""
        # Always update even if redundant to ensure it's considered the 'last' selection
        self.last_selected_palette = palette_path
        self.last_selected_palette_type = palette_type
        
        # Update compact palette editor if in small preview mode
        if getattr(self, 'view_mode', '') == "small_preview":
            self.update_compact_palette_editor()
    

    def _compact_hsv_slider_changed(self, *args):
        """Handle HSV slider changes in compact editor with live preview"""
        # Apply HSV changes live (like the live palette editor)
        if not hasattr(self, 'compact_selected_colors') or not self.compact_selected_colors:
            return
        
        # Get HSV values
        hue_shift = self.compact_hue_var.get() if hasattr(self, 'compact_hue_var') else 0
        sat_shift = self.compact_sat_var.get() if hasattr(self, 'compact_sat_var') else 0
        val_shift = self.compact_val_var.get() if hasattr(self, 'compact_val_var') else 0
        
        # Find the matching palette layer
        if not hasattr(self, 'last_selected_palette') or not self.last_selected_palette:
            return
            
        matching_layer = None
        palette_name = self.last_selected_palette
        palette_type = getattr(self, 'last_selected_palette_type', '')
        
        if hasattr(self, 'palette_layers'):
            # PASS 1: Priority - Exact Name Match
            target_name = os.path.basename(palette_name)
            for layer in self.palette_layers:
                layer_name = getattr(layer, 'name', '')
                if layer_name == target_name:
                    matching_layer = layer
                    break
            
            # PASS 2: Fallback - Type Match
            if not matching_layer:
                for layer in self.palette_layers:
                    layer_type = getattr(layer, 'palette_type', '')
                    
                    if (palette_type == 'hair' and layer_type == 'hair') or \
                       (palette_type == 'third_job' and layer_type.startswith('3rd_job')) or \
                       (palette_type == 'fashion' and layer_type.startswith('fashion')):
                        matching_layer = layer
                        break
        
        if not matching_layer:
            return
            
        # Ensure we have base colors to work from
        if not hasattr(self, 'compact_base_colors') or not self.compact_base_colors:
             # If missing base colors, snapshot them now (fallback)
             self.compact_base_colors = {}
             for i in self.compact_selected_colors:
                 if i < len(matching_layer.colors):
                     self.compact_base_colors[i] = list(matching_layer.colors[i])
        
        # Apply HSV to selected colors based on BASE colors
        import colorsys
        for idx in self.compact_selected_colors:
            if idx >= len(matching_layer.colors):
                continue
                
            # Use base color for calculation if available, otherwise current
            original_color = self.compact_base_colors.get(idx, matching_layer.colors[idx])
            
            if original_color is None:
                continue
            
            # Convert RGB to HSV
            if hue_shift == 0 and sat_shift == 0 and val_shift == 0:
                new_color = tuple(original_color)
            else:
                r, g, b = original_color[0] / 255.0, original_color[1] / 255.0, original_color[2] / 255.0
                h, s, v = colorsys.rgb_to_hsv(r, g, b)
                
                # Apply shifts
                h = (h * 360 + hue_shift) % 360 / 360  # Hue wraps around
                s = max(0, min(1, s + sat_shift / 100))  # Saturation clamped 0-1
                v = max(0, min(1, v + val_shift / 100))  # Value clamped 0-1
                
                # Convert back to RGB
                r, g, b = colorsys.hsv_to_rgb(h, s, v)
                new_color = (int(r * 255), int(g * 255), int(b * 255))
            
            if new_color == (0, 255, 0) or new_color == (255, 0, 255):
                new_color = ColorTranslator._find_nearest_non_keyed_color(new_color)
            
            # Update the layer color
            matching_layer.colors[idx] = new_color
            
            # Update the specific color swatch in the UI
            if hasattr(self, 'compact_color_widgets') and idx in self.compact_color_widgets:
                try:
                    c_frame, c_label = self.compact_color_widgets[idx]
                    hex_color = f"#{new_color[0]:02x}{new_color[1]:02x}{new_color[2]:02x}"
                    c_frame.config(bg=hex_color)
                    c_label.config(bg=hex_color)
                except Exception:
                    pass
        
        # Update the display
        self._debounced_display_update()
    
    def _compact_hsv_entry_changed(self):
        """Handle HSV entry changes with validation"""
        # Clamp values to valid ranges
        try:
            hue = max(-180, min(180, self.compact_hue_var.get()))
            self.compact_hue_var.set(hue)
        except:
            self.compact_hue_var.set(0)
        
        try:
            sat = max(-100, min(100, self.compact_sat_var.get()))
            self.compact_sat_var.set(sat)
        except:
            self.compact_sat_var.set(0)
        
        try:
            val = max(-100, min(100, self.compact_val_var.get()))
            self.compact_val_var.set(val)
        except:
            self.compact_val_var.set(0)
        
        # Trigger slider changed
        self._compact_hsv_slider_changed()
    
    def export_background_compact(self):
        from code.core.exporter import Exporter
        return Exporter.export_background_compact(self)

    
    def export_pal_compact(self):
        from code.core.exporter import Exporter
        return Exporter.export_pal_compact(self)


    
    def apply_gradient_compact(self):
        from code.ui.gradient_menu import GradientMenu
        return GradientMenu.apply_gradient_compact(self)


    def _update_compact_swatch_highlights(self):
        """Update only the selection highlights in compact mode without rebuilding UI"""
        if not hasattr(self, '_compact_swatch_widgets'):
            return
            
        for idx, swatch in self._compact_swatch_widgets.items():
            if idx in self.compact_selected_colors:
                swatch.config(highlightbackground="red", highlightthickness=2)
            else:
                swatch.config(highlightbackground="black", highlightthickness=1)

    def _select_all_compact(self):
        """Select all editable color swatches in compact mode."""
        if not hasattr(self, 'compact_selected_colors'):
            self.compact_selected_colors = set()
            
        current_layer = getattr(self, '_compact_active_layer', None)
        if not current_layer:
            return
            
        editable_indices = self._get_editable_color_indices(current_layer)
        if not editable_indices:
            return
            
        # Snapshot base colors if this is the first selection
        if not self.compact_selected_colors:
            self.compact_base_colors = {}
            colors = getattr(current_layer, 'colors', [])
            for idx in editable_indices:
                if idx < len(colors):
                    self.compact_base_colors[idx] = colors[idx]
        
        # Add all to selection
        for idx in editable_indices:
            self.compact_selected_colors.add(idx)
            
        # Ensure multi-select is ON if we selected multiple
        if len(editable_indices) > 1:
            self.compact_multiselect_var.set(True)
            
        # Refresh the UI highlights (no rebuild)
        self._update_compact_swatch_highlights()

    def _clear_selection_compact(self):
        """Clear all selected colors in compact mode."""
        if hasattr(self, 'compact_selected_colors'):
            self.compact_selected_colors.clear()
            self.compact_base_colors = {}
            
        # Refresh the UI highlights (no rebuild)
        self._update_compact_swatch_highlights()
            
        # Reset sliders if they exist
        if hasattr(self, 'hue_slider'): # Refers to compact sliders stored in update_compact_palette_editor
            self.compact_hue_var.set(0)
            self.compact_sat_var.set(0)
            self.compact_val_var.set(0)
            # Trigger update
            if hasattr(self, '_compact_hsv_slider_changed'):
                self._compact_hsv_slider_changed()

    
    def _cycle_zoom(self, delta, var, update_func=None):
        """Cycle zoom level based on scroll direction with reduced sensitivity"""
        # Add accumulator if not present
        if not hasattr(self, '_zoom_accumulator'):
            self._zoom_accumulator = 0
            
        # Accumulate delta
        self._zoom_accumulator += delta
        
        # Sensitivity threshold (120 is one standard notch on Windows)
        # Using 120 ensures that at least one full notch is required to change zoom
        threshold = 120
        
        if abs(self._zoom_accumulator) < threshold:
            return
            
        values = ["100%", "200%", "300%", "400%", "500%", "Fit"]
        try:
            current = var.get()
            if current in values:
                curr_idx = values.index(current)
            else:
                 curr_idx = 0
            
            # Determine direction based on accumulated delta
            direction = 1 if self._zoom_accumulator > 0 else -1
            
            # Reset accumulator after a zoom change
            self._zoom_accumulator = 0
            
            new_idx = max(0, min(len(values)-1, curr_idx + direction))
            
            if new_idx != curr_idx:
                var.set(values[new_idx])
                if update_func:
                    update_func()
        except Exception:
            pass

    def on_frame_click(self, event, frame_index):
        from code.core.frame_manager import FrameManager
        return FrameManager.on_frame_click(self, event, frame_index)

    
    def _select_color_from_frame_click(self, event, frame_index):
        from code.core.color_picker import ColorPicker
        return ColorPicker._select_color_from_frame_click(self, event, frame_index)

    
    def start_resize_active_colors(self, event):
        """Start resizing the active colors section"""
        self._resize_last_y = event.y_root
        self._is_resizing = True
    
    def resize_active_colors(self, event):
        """Resize the active colors section"""
        if not hasattr(self, '_is_resizing') or not self._is_resizing:
            return
        
        # Calculate the incremental change from last position
        # Dragging UP (decreasing y_root) = negative delta = increase height
        # Dragging DOWN (increasing y_root) = positive delta = decrease height
        delta_y = event.y_root - self._resize_last_y
        self._resize_last_y = event.y_root  # Update for next iteration
        
        # Get maximum height (default to 250 if not set)
        max_height = getattr(self, 'active_colors_max_height', 250)
        
        # Update active colors height incrementally (subtract delta for intuitive behavior)
        # Constrained to prevent overlaying main buttons
        new_height = max(50, min(max_height, self.active_colors_height - delta_y))  # Min 50px, max from setting
        
        # Only update if height actually changed
        if new_height != self.active_colors_height:
            self.active_colors_height = new_height
            self.active_colors_frame.config(height=new_height)
            
            # Force the compact control bar to stay visible and update layout
            if hasattr(self, 'compact_control_bar') and self.compact_control_bar.winfo_ismapped():
                self.compact_control_bar.update_idletasks()
    
    def end_resize_active_colors(self, event):
        """End resizing the active colors section"""
        self._is_resizing = False
        if hasattr(self, '_resize_last_y'):
            del self._resize_last_y




    def _show_frame_context_menu(self, event, frame_idx):
        from code.core.frame_manager import FrameManager
        return FrameManager._show_frame_context_menu(self, event, frame_idx)

        
    def _select_frame_context(self, frame_idx):
        from code.core.frame_manager import FrameManager
        return FrameManager._select_frame_context(self, frame_idx)

            
    def _switch_to_single_preview(self, frame_idx):
        from code.core.frame_manager import FrameManager
        return FrameManager._switch_to_single_preview(self, frame_idx)

            

    def create_ui(self):
        from code.ui.main_previewer import MainPreviewer
        return MainPreviewer.create_ui(self)

    def _hide_frame_context(self, frame_idx):
        from code.core.frame_manager import FrameManager
        return FrameManager._hide_frame_context(self, frame_idx)


    def on_character_change(self):
        """Handle character selection change"""
        character_name = self.character_var.get()
        if not character_name:
            return
            
        # Try to remember the previously selected job
        previous_job = self.job_var.get() if hasattr(self, 'job_var') else None
        
        char_id = None
        
        # First try to find a character ID that matches both the name and the previous job
        if previous_job:
            if character_name == "Paula":
                if previous_job == "1st Job":
                    if "chr025" in self.available_characters: char_id = "chr025"
                    elif "chr100" in self.available_characters: char_id = "chr100"
                elif previous_job == "2nd Job":
                    if "chr026" in self.available_characters: char_id = "chr026"
                    elif "chr101" in self.available_characters: char_id = "chr101"
                elif previous_job == "3rd Job":
                    if "chr027" in self.available_characters: char_id = "chr027"
                    elif "chr102" in self.available_characters: char_id = "chr102"
            else:
                for char_id_key in self.available_characters:
                    if char_id_key in CHARACTER_MAPPING:
                        char_info = CHARACTER_MAPPING[char_id_key]
                        if char_info['name'] == character_name and char_info['job'] == previous_job:
                            char_id = char_id_key
                            break

        # If not found or no previous job, fallback to the first character ID for this name
        if not char_id:
            for char_id_key in self.available_characters:
                if char_id_key in CHARACTER_MAPPING:
                    char_info = CHARACTER_MAPPING[char_id_key]
                    if char_info['name'] == character_name:
                        char_id = char_id_key
                        break
                else:
                    if char_id_key == character_name:
                        char_id = char_id_key
                        break
                    
        # Reset custom frame settings when changing character
        if hasattr(self, 'current_character') and self.current_character != char_id:
            # Save per-character settings before switching
            if self.current_character:
                self._save_character_settings(self.current_character)
            
            # Store current settings before changing
            if self.preview_var.get() == "custom" and hasattr(self, 'custom_frame_count'):
                current_job = self.job_var.get() if hasattr(self, 'job_var') else None
                if self.current_character not in self.frame_range_settings:
                    self.frame_range_settings[self.current_character] = {}
                self.frame_range_settings[self.current_character][current_job] = (
                    self.custom_frame_count,
                    getattr(self, 'custom_start_frame', 0),
                    getattr(self, 'custom_end_frame', len(self.character_images.get(self.current_character, [])) - 1)
                )
        
        if char_id and char_id in CHARACTER_MAPPING:
            char_info = CHARACTER_MAPPING[char_id]
            self.current_character = char_id
            self.current_job = char_info["job"]
            self.job_var.set(self.current_job)
            
            # Load per-character settings for this character
            self._load_character_settings(char_id)
            
            # Track character view
            self.statistics.add_character_view(char_id, char_info["job"])
            self._save_statistics()
            
            # Clear current image display first (only if canvas exists)
            if hasattr(self, 'canvas') and self.canvas.winfo_exists():
                self.canvas.delete("all")
            self.original_image = None
            self.current_image_path = None
            
            # Clear fashion variables before updating UI
            self.fashion_vars.clear()
            
            # Reset palette selections
            self.hair_var.set("NONE")
            self.third_job_var.set("NONE")
            
            # Reset palette selection tracking for compact editor
            self.last_selected_palette = None
            self.last_selected_palette_type = None
            if hasattr(self, 'update_compact_palette_editor'):
                self.update_compact_palette_editor()
            
            # Clear palette layers
            self.palette_layers = []
            
            # Update all UI sections
            self.update_third_job_section()
            self.update_hair_section()
            self.update_fashion_section()
            
            # Reset scroll positions
            self.reset_scroll_positions()
            
            # Load palettes and update display immediately for all characters
            self.load_palettes()
            # Update zoom combo state based on new character's frame count
            self.update_zoom_combo_state()
            self.update_image_display()
            
            # Load image for this character, respecting the restored frame index
            if char_id in self.character_images and self.character_images[char_id]:
                # Bounds check the restored index against available images
                max_idx = len(self.character_images[char_id]) - 1
                if self.current_image_index > max_idx:
                    self.current_image_index = 0
                if self.current_image_index < 0:
                    self.current_image_index = 0
                
                self.load_character_image()
                self.update_navigation_buttons()
            
            # Ensure zoom state is updated after character change
            self.update_zoom_combo_state()

    def prev_image(self):
        """Navigate to previous image"""
        preview_mode = self.preview_var.get()
        
        # Don't allow navigation in "all" mode
        if preview_mode == "all":
            return
        
        if preview_mode == "custom":
            self.prev_custom_frames()
        else:
            if not hasattr(self, 'current_character') or not self.current_character:
                return
                
            char_id = self.current_character
            if char_id not in self.character_images:
                return
                
            images = self.character_images[char_id]
            if len(images) <= 1:
                return
                
            # Wrap around to the last image when at the beginning
            # Navigation with hidden frame skipping
            char_job_key = self._get_char_job_key()
            hidden = self.hidden_frames.get(char_job_key, set())
            
            search_idx = self.current_image_index
            total = len(images)
            checked = 0
            
            # Use minimal loop logic
            while checked < total:
                # Move to prev
                if search_idx > 0:
                    search_idx -= 1
                else:
                    search_idx = total - 1
                
                if search_idx not in hidden:
                    self.current_image_index = search_idx
                    break
                checked += 1
                
            self.load_image_from_path(images[self.current_image_index])
            self.update_navigation_buttons()
            
            # Save current frame position
            if hasattr(self, 'current_character') and self.current_character:
                self._save_character_settings(self.current_character)
            else:
                self._save_settings()

    def prev_custom_frames(self):
        from code.core.frame_manager import FrameManager
        return FrameManager.prev_custom_frames(self)


    def next_image(self):
        """Navigate to next image"""
        preview_mode = self.preview_var.get()
        
        # Don't allow navigation in "all" mode
        if preview_mode == "all":
            return
        
        if preview_mode == "custom":
            self.next_custom_frames()
            # Track frame navigation
            self.statistics.frames_skipped += 1
            self._save_statistics()
        else:
            if not hasattr(self, 'current_character') or not self.current_character:
                return
                
            char_id = self.current_character
            if char_id not in self.character_images:
                return
                
            images = self.character_images[char_id]
            if len(images) <= 1:
                return
                
            # Wrap around to the first image when at the end
            # Navigation with hidden frame skipping
            char_job_key = self._get_char_job_key()
            hidden = self.hidden_frames.get(char_job_key, set())
            
            search_idx = self.current_image_index
            total = len(images)
            checked = 0
            
            # Use minimal loop logic
            while checked < total:
                # Move to next
                search_idx = (search_idx + 1) % total
                
                if search_idx not in hidden:
                    self.current_image_index = search_idx
                    break
                checked += 1

            self.load_image_from_path(images[self.current_image_index])
            self.update_navigation_buttons()
            # Track frame navigation
            self.statistics.frames_skipped += 1
            self._save_statistics()
            
            # Save current frame position
            if hasattr(self, 'current_character') and self.current_character:
                self._save_character_settings(self.current_character)
            else:
                self._save_settings()

    def next_custom_frames(self):
        from code.core.frame_manager import FrameManager
        return FrameManager.next_custom_frames(self)


    def update_navigation_buttons(self):
        """Update the state of image navigation buttons"""
        preview_mode = self.preview_var.get()
        
        # Disable navigation buttons in "all" mode
        if preview_mode == "all":
            self.prev_btn.config(state="disabled")
            self.next_btn.config(state="disabled")
            return
        
        if not hasattr(self, 'current_character') or not self.current_character:
            self.prev_btn.config(state="disabled")
            self.next_btn.config(state="disabled")
            return
            
        char_id = self.current_character
        if char_id not in self.character_images:
            self.prev_btn.config(state="disabled")
            self.next_btn.config(state="disabled")
            return
            
        images = self.character_images[char_id]
        
        if preview_mode == "custom":
            # For custom mode, always enable navigation if we have frames
            if len(images) > 0:
                self.prev_btn.config(state="normal")
                self.next_btn.config(state="normal")
            else:
                self.prev_btn.config(state="disabled")
                self.next_btn.config(state="disabled")
        else:
            # For single mode, enable if we have more than one image
            if len(images) > 1:
                # Always enable navigation buttons since we have wrap-around
                self.prev_btn.config(state="normal")
                self.next_btn.config(state="normal")
            else:
                self.prev_btn.config(state="disabled")
                self.next_btn.config(state="disabled")

    def on_job_change(self):
        """Handle job selection change"""
        character_name = self.character_var.get()
        job_name = self.job_var.get()
        
        if not character_name or not job_name:
            return
            
        # Find the character ID for this character name and job
        char_id = None
        
        # Store current frame settings before job change
        if hasattr(self, 'current_character') and self.preview_var.get() == "custom" and hasattr(self, 'custom_frame_count'):
            old_job = getattr(self, 'current_job', None)
            if old_job and old_job != job_name:
                if self.current_character not in self.frame_range_settings:
                    self.frame_range_settings[self.current_character] = {}
                self.frame_range_settings[self.current_character][old_job] = (
                    self.custom_frame_count,
                    getattr(self, 'custom_start_frame', 0),
                    getattr(self, 'custom_end_frame', len(self.character_images.get(self.current_character, [])) - 1)
                )
        
        # For Paula, map job to correct character IDs
        if character_name == "Paula":
            if job_name == "1st Job":
                # Use chr025 for images, chr100 for palettes
                if "chr025" in self.available_characters:
                    char_id = "chr025"
                elif "chr100" in self.available_characters:
                    char_id = "chr100"
            elif job_name == "2nd Job":
                # Use chr026 for images, chr101 for palettes
                if "chr026" in self.available_characters:
                    char_id = "chr026"
                elif "chr101" in self.available_characters:
                    char_id = "chr101"
            elif job_name == "3rd Job":
                # Use chr027 for images, chr102 for palettes
                if "chr027" in self.available_characters:
                    char_id = "chr027"
                elif "chr102" in self.available_characters:
                    char_id = "chr102"
        else:
            # For other characters, use the original logic
            for char_id_key in self.available_characters:
                if char_id_key in CHARACTER_MAPPING:
                    char_info = CHARACTER_MAPPING[char_id_key]
                    if char_info['name'] == character_name and char_info['job'] == job_name:
                        char_id = char_id_key
                        break
        
        if char_id and char_id in CHARACTER_MAPPING:
            # Save current settings before switching to a new job/character
            if hasattr(self, 'current_character') and self.current_character:
                self._save_character_settings(self.current_character)
                
            self.current_character = char_id
            self.current_job = job_name
            
            # Load per-character settings for this character
            self._load_character_settings(char_id)
            
            # Clear current image display first
            self.canvas.delete("all")
            self.original_image = None
            self.current_image_path = None
            
            # Clear fashion variables before updating UI
            self.fashion_vars.clear()
            
            # Reset palette selections
            self.hair_var.set("NONE")
            self.third_job_var.set("NONE")
            
            # Reset palette selection tracking for compact editor
            self.last_selected_palette = None
            self.last_selected_palette_type = None
            if hasattr(self, 'update_compact_palette_editor'):
                self.update_compact_palette_editor()
            
            # Clear palette layers
            self.palette_layers = []
            
            # Update all UI sections
            self.update_third_job_section()
            self.update_hair_section()
            self.update_fashion_section()
            
            # Reset scroll positions
            self.reset_scroll_positions()
            
            # Load palettes and update display immediately for 3rd job characters
            self.load_palettes()
            # Update zoom combo state based on new character's frame count
            self.update_zoom_combo_state()
            self.update_image_display()
            
            # Load image for this character, respecting the restored frame index
            if char_id in self.character_images and self.character_images[char_id]:
                # Bounds check the restored index against available images
                max_idx = len(self.character_images[char_id]) - 1
                if self.current_image_index > max_idx:
                    self.current_image_index = 0
                if self.current_image_index < 0:
                    self.current_image_index = 0
                
                self.load_character_image()
            
            # Update navigation buttons after job change (always, not just when loading image)
            self.update_navigation_buttons()
            
            # Ensure zoom state is updated after job change
            self.update_zoom_combo_state()

    def update_third_job_section(self):
        """Update the 3rd Job Base Fashion section"""
        # Clear existing widgets
        for widget in self.third_job_frame.winfo_children():
            widget.destroy()
        
        # Hide the third job frame initially
        self.third_job_frame.pack_forget()
        
        if not hasattr(self, 'current_character') or not self.current_character:
            # Reset fashion frame to normal height when no third job
            self._adjust_layout_for_third_job(False)
            return
        
        char_id = self.current_character
        if char_id not in CHARACTER_MAPPING:
            return
        
        char_info = CHARACTER_MAPPING[char_id]
        
        # For 1st and 2nd jobs, hide the 3rd job section entirely
        if char_info["job"] in ["1st Job", "2nd Job"]:
            # Reset fashion frame to normal height when no third job
            self._adjust_layout_for_third_job(False)
            return
        else:
            # Show the 3rd job frame for 3rd jobs - pack it below the PanedWindow
            self.third_job_frame.pack(fill="x", pady=(5, 0))
            # Adjust layout to accommodate third job frame
            self._adjust_layout_for_third_job(True)
        
        # Special handling for Paula characters - they don't have 3rd job base fashion
        if char_id in ["chr025", "chr026", "chr027"]:
            lbl = tk.Label(self.third_job_frame, text="Silly, Paula doesn't have multiple 3rd jobs!", 
                    fg="red", font=("Arial", 9, "bold"))
            lbl.pack(anchor="w", padx=5, pady=5)
            self.apply_theme(self.third_job_frame)
            lbl.configure(fg="red")
            return
        
        # Check if this character has 3rd job base fashion palettes
        palette_char_id = self.get_palette_character_id(char_id)
        if palette_char_id in self.third_job_palettes:
            palettes = self.third_job_palettes[palette_char_id]
            
            grid_frame = tk.Frame(self.third_job_frame)
            grid_frame.pack(fill="x", padx=(0, 0))
            
            columns = 3 if char_info["name"] == "Dragon" else 2
            for c in range(columns):
                grid_frame.grid_columnconfigure(c, weight=1, uniform="col")

            # Add palette options (no NONE option for 3rd jobs)
            for i, palette_path in enumerate(palettes):
                palette_name = os.path.basename(palette_path)
                rb = tk.Radiobutton(grid_frame, text=palette_name, variable=self.third_job_var,
                              value=palette_path, command=self.on_third_job_change)
                row = i // columns
                col = i % columns
                rb.grid(row=row, column=col, sticky="w", padx=2, pady=0)
            
            # Restore saved selection if available
            saved_pal = self.loaded_palettes.get('third_job')
            if saved_pal and saved_pal in palettes:
                self.third_job_var.set(saved_pal)
            elif palettes:
                self.third_job_var.set(palettes[0])
            else:
                self.third_job_var.set("NONE")
                
            self.apply_theme(self.third_job_frame)

    def _adjust_layout_for_third_job(self, has_third_job):
        """Adjust the layout to accommodate the third job frame"""
        if has_third_job:
            # Reduce fashion frame height to make room for third job frame
            self.fashion_frame.configure(height=240)
            self.fashion_canvas.configure(height=240)
            # Keep the same minimum window size - just adjust the internal layout
            self.master.minsize(1050, 650)
        else:
            # Restore normal fashion frame height
            self.fashion_frame.configure(height=360)
            self.fashion_canvas.configure(height=360)
            # Keep the same minimum window size
            self.master.minsize(1050, 650)

    def get_palette_character_id(self, char_id):
        """Get the character ID to use for palettes (handles Paula mapping)"""
        if char_id == "chr025":
            return "chr100"  # Paula 1st Job: chr025 images -> chr100 palettes
        elif char_id == "chr026":
            return "chr101"  # Paula 2nd Job: chr026 images -> chr101 palettes
        elif char_id == "chr027":
            return "chr102"  # Paula 3rd Job: chr027 images -> chr102 palettes
        else:
            return char_id  # For other characters, use the same ID

    def get_fashion_type_name(self, char_id, fashion_type):
        """Get the proper name for a fashion type based on character"""
        # Map Paula's display IDs to their palette IDs
        if char_id == "chr025":
            char_id = "chr100"  # Paula 1st Job
        elif char_id == "chr026":
            char_id = "chr101"  # Paula 2nd Job
        elif char_id == "chr027":
            char_id = "chr102"  # Paula 3rd Job
            
        char_num = char_id[3:] if char_id.startswith("chr") else char_id
        
        # Fashion type mappings for different characters
        fashion_names = {
            "001": {  # chr001
                "fashion_1": "Hoodie",
                "fashion_2": "Gloves", 
                "fashion_3": "Skort",
                "fashion_4": "Backpack",
                "fashion_5": "Shoes"
            },
            "002": {  # chr002
                "fashion_1": "Airshoes",
                "fashion_2": "Turtle Vest",
                "fashion_3": "Sash Belt", 
                "fashion_4": "Warmups",
                "fashion_5": "Wraps",
                "fashion_6": "Hood Tie"
            },
            "004": {  # chr004
                "fashion_1": "Robe",
                "fashion_2": "Shirt",
                "fashion_3": "Jeans",
                "fashion_4": "Monk Shoes", 
                "fashion_5": "Cane"
            },
            "005": {  # chr005
                "fashion_1": "Coat",
                "fashion_2": "Heels",
                "fashion_3": "Slit Skirt",
                "fashion_4": "Tank",
                "fashion_5": "Tote"
            },
            "006": {  # chr006
                "fashion_1": "Jacket",
                "fashion_2": "Shorts",
                "fashion_3": "Trainers",
                "fashion_4": "Open Glove",
                "fashion_5": "T-neck"
            },
            "007": {  # chr007
                "fashion_1": "Ribbon",
                "fashion_2": "Belt",
                "fashion_3": "Halter",
                "fashion_4": "Heels",
                "fashion_5": "Paws",
                "fashion_6": "Skirt"
            },
            "008": {  # chr008
                "fashion_1": "Blazer",
                "fashion_2": "Slacks",
                "fashion_3": "Dress Shoes"
            },
            "009": {  # chr009
                "fashion_1": "Robe",
                "fashion_2": "Boxing Glove",
                "fashion_3": "Shorts",
                "fashion_4": "Gloves",
                "fashion_5": "Boxing Shoes",
                "fashion_6": "Stocking"
            },
            "010": {  # chr010
                "fashion_1": "Fur Collar",
                "fashion_2": "Tunic",
                "fashion_3": "Bolero",
                "fashion_4": "Gauntlet",
                "fashion_5": "Leather Shoes"
            },
            "012": {  # chr012
                "fashion_1": "Shawl",
                "fashion_2": "Beads Necklace",
                "fashion_3": "Robe",
                "fashion_4": "Wrap Skirt",
                "fashion_5": "Ankle Boots"
            },
            "013": {  # chr013
                "fashion_1": "Sports Suit",
                "fashion_2": "Tube Top",
                "fashion_3": "Elbow Wrap",
                "fashion_4": "Mittens",
                "fashion_5": "Walkers"
            },
            "014": {  # chr014
                "fashion_1": "Turtleneck",
                "fashion_2": "Coil Coat",
                "fashion_3": "Utility Belt",
                "fashion_4": "Glove",
                "fashion_5": "Boots"
            },
            "015": {  # chr015
                "fashion_1": "Hippie Shirt",
                "fashion_2": "Studded Belt",
                "fashion_3": "Checkered Skirt",
                "fashion_4": "Checkered Stockings",
                "fashion_5": "Heel Boots"
            },
            "016": {  # chr016
                "fashion_1": "Dress Shirt",
                "fashion_2": "Checkered Suit",
                "fashion_3": "Dress Shoes"
            },
            "100": {  # chr100 (Paula 1st Job)
                "fashion_1": "Stadium Jacket",
                "fashion_2": "Sleeveless Dress",
                "fashion_3": "Knee Socks",
                "fashion_4": "School Loafers",
                "fashion_5": "Ribbon Chou",
                "fashion_6": "Cutie Satchel",
                "fashion_7": "Extra"
            },
            "101": {  # chr101 (Paula 2nd Job)
                "fashion_1": "Pocket One-piece",
                "fashion_2": "Animal Pocket Belt",
                "fashion_3": "Knee-high Boots",
                "fashion_4": "Ribbons",
                "fashion_5": "Arm Cover",
                "fashion_6": "Whip"
            },
            "102": {  # chr102 (Paula 3rd Job)
                "fashion_1": "Blouse",
                "fashion_2": "Trench Dress",
                "fashion_3": "Frilly Socks",
                "fashion_4": "Cutie Buckle Boots",
                "fashion_5": "Ribbon Rubber",
                "fashion_6": "Ribbon Brooch",
                "fashion_7": "Mini Pocket Belt",
                "fashion_8": "Leather Buckle Gloves"
            },
            "003": {  # chr003
                "fashion_1": "Blouse",
                "fashion_2": "Bow",
                "fashion_3": "Frill Dress",
                "fashion_4": "Flats",
                "fashion_5": "Socks",
                "fashion_6": "Spellbook"
            },
            "020": {  # chr020
                "fashion_1": "Wrap",
                "fashion_2": "Hooded Robe",
                "fashion_3": "Overcoat",
                "fashion_4": "Robe",
                "fashion_5": "Leather Boots"
            },
            "017": {  # chr017
                "fashion_1": "Tube Top",
                "fashion_2": "Bolero Jacket",
                "fashion_3": "Gauntlets",
                "fashion_4": "Chord Skirt",
                "fashion_5": "Steel Boots"
            },
            "018": {  # chr018
                "fashion_1": "Asymmetrical Tee",
                "fashion_2": "Protector",
                "fashion_3": "Kilt",
                "fashion_4": "Steel Armlets",
                "fashion_5": "Ankle Shoes"
            },
            "011": {  # chr011
                "fashion_1": "Checkered Dress",
                "fashion_2": "Ribbon",
                "fashion_3": "Minisack",
                "fashion_4": "Gloves",
                "fashion_5": "Ribbon Boots"
            },
            "019": {  # chr019
                "fashion_1": "Flower Ribbon",
                "fashion_2": "Puffy Blouse",
                "fashion_3": "Flower Brooch",
                "fashion_4": "Layered Dress",
                "fashion_5": "Flower Shoes"
            },
            "021": {  # chr021
                "fashion_1": "Zip-up Coat",
                "fashion_2": "Leather Shorts",
                "fashion_3": "Leather Wristlets",
                "fashion_4": "Buckle Boots",
                "fashion_5": "Unknown"
            },
            "022": {  # chr022
                "fashion_1": "Zip-up Jacket",
                "fashion_2": "Long Jacket",
                "fashion_3": "Shorts",
                "fashion_4": "Long Boots",
                "fashion_5": "Unknown"
            },
            "023": {  # chr023
                "fashion_1": "Double Coat",
                "fashion_2": "Shirring Skirt",
                "fashion_3": "Buckle Shoes",
                "fashion_4": "Blouse"
            },
            "024": {  # chr024 (Raccoon 3rd Job)
                "fashion_1": "Dress Shirt",
                "fashion_2": "Opera Cape",
                "fashion_3": "Frock Coat",
                "fashion_4": "Dress Pants",
                "fashion_5": "Formal Shoes"
            },
            "025": {  # chr025 (Paula 1st Job)
                "fashion_1": "Stadium Jacket",
                "fashion_2": "Sleeveless Dress",
                "fashion_3": "Knee Socks",
                "fashion_4": "School Loafers",
                "fashion_5": "Ribbon Chou",
                "fashion_6": "Cutie Satchel",
                "fashion_7": "Extra"
            },
            "026": {  # chr026 (Paula 2nd Job)
                "fashion_1": "Pocket One-piece",
                "fashion_2": "Animal Pocket Belt",
                "fashion_3": "Knee-high Boots",
                "fashion_4": "Ribbons",
                "fashion_5": "Arm Cover",
                "fashion_6": "Whip"
            },
            "027": {  # chr027 (Paula 3rd Job)
                "fashion_1": "Blouse",
                "fashion_2": "Trench Dress",
                "fashion_3": "Frilly Socks",
                "fashion_4": "Cutie Buckle Boots",
                "fashion_5": "Ribbon Rubber",
                "fashion_6": "Ribbon Brooch",
                "fashion_7": "Mini Pocket Belt",
                "fashion_8": "Leather Buckle Gloves",
                "fashion_9": "Special"
            }
        }
        
        if char_num in fashion_names and fashion_type in fashion_names[char_num]:
            return fashion_names[char_num][fashion_type]
        else:
            return fashion_type  # Return original if no mapping found

    def update_hair_section(self):
        """Update the Hair section"""
        # Clear existing widgets
        for widget in self.hair_scrollable_frame.winfo_children():
            widget.destroy()
        
        # Clear any existing "NONE" option
        for widget in self.hair_frame.winfo_children():
            if isinstance(widget, tk.Radiobutton) and widget.cget("text") == "NONE":
                widget.destroy()
        
        # Add "NONE" option outside the scrollable area
        rb = tk.Radiobutton(self.hair_frame, text="NONE", variable=self.hair_var,
                      value="NONE", command=self.on_hair_change)
        rb.configure(pady=0, bd=0, highlightthickness=0)  # Remove all padding and borders
        rb.pack(anchor="w", padx=3, pady=1, before=self.hair_canvas)
        
        if not hasattr(self, 'current_character') or not self.current_character:
            return
            
        char_id = self.current_character
        palette_char_id = self.get_palette_character_id(char_id)
        
        # Add hair palette options
        if palette_char_id in self.hair_palettes:
            # Grid container for 3-column layout
            grid_frame = tk.Frame(self.hair_scrollable_frame)
            grid_frame.pack(fill="x", padx=(0, 0))
            grid_frame.grid_columnconfigure(0, weight=1, uniform="col")
            grid_frame.grid_columnconfigure(1, weight=1, uniform="col")
            grid_frame.grid_columnconfigure(2, weight=1, uniform="col")
            
            for i, palette_path in enumerate(sorted(self.hair_palettes[palette_char_id])):
                palette_name = os.path.basename(palette_path)
                # Check if this is a custom palette
                root_dir = getattr(self, "root_dir", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                custom_hair_pals_path = os.path.join(root_dir, "exports", "custom_pals", "hair")
                custom_fashion_pals_path = os.path.join(root_dir, "exports", "custom_pals", "fashion")
                old_custom_fashion_pals_path = os.path.join(root_dir, "exports", "custom_fashion_pals")
                is_custom_hair = os.path.abspath(palette_path).startswith(os.path.abspath(custom_hair_pals_path))
                is_custom_fashion = os.path.abspath(palette_path).startswith(os.path.abspath(custom_fashion_pals_path))
                is_old_custom_fashion = os.path.abspath(palette_path).startswith(os.path.abspath(old_custom_fashion_pals_path))
                is_custom = is_custom_hair or is_custom_fashion or is_old_custom_fashion
                display_name = f"{palette_name} (C)" if is_custom else palette_name
                
                rb = tk.Radiobutton(grid_frame, text=display_name, variable=self.hair_var,
                              value=palette_path, command=self.on_hair_change)
                rb.configure(pady=2)
                row = i // 3
                col = i % 3
                rb.grid(row=row, column=col, sticky="w", padx=3, pady=1)
                self.register_focusable(rb, f"hair_{palette_path}")
        
        # Restore saved selection if available
        saved_pal = self.loaded_palettes.get('hair', "NONE")
        self.hair_var.set(saved_pal)
        
        # Apply theme so radio buttons respect dark mode
        self.apply_theme(self.hair_frame)

    def update_fashion_section(self):
        """Update the Fashion section"""
        # Clear existing widgets
        for widget in self.fashion_scrollable_frame.winfo_children():
            widget.destroy()
        
        if not hasattr(self, 'current_character') or not self.current_character:
            return
            
        char_id = self.current_character
        palette_char_id = self.get_palette_character_id(char_id)
        
        # Add fashion palette options
        if palette_char_id in self.fashion_palettes:
            # Group palettes by their actual palette type based on hardcoded ranges
            fashion_groups = {}
            
            # Sort fashion palettes by their actual palette type (based on index ranges)
            def sort_fashion_key(palette_path):
                palette_name = os.path.basename(palette_path)
                # First, categorize the palette to get its actual type
                palette_type = self.categorize_palette(palette_name)
                
                # Extract the character number and fashion number for sorting
                char_match = re.match(r'^chr(\d{3})_w(\d+)\.pal$', palette_name.lower())  # Keep the capture group for fashion number
                char_match.group(1) if char_match else "000"
                fashion_num = int(char_match.group(2)) if char_match else 0
                
                # Sort by palette type first, then by fashion number
                # Normal sorting for all characters
                if True:
                    # Normal sorting for other characters
                    if palette_type == "fashion_1":
                        return (1, fashion_num)
                    elif palette_type == "fashion_2":
                        return (2, fashion_num)
                    elif palette_type == "fashion_3":
                        return (3, fashion_num)
                    elif palette_type == "fashion_4":
                        return (4, fashion_num)
                    elif palette_type == "fashion_5":
                        return (5, fashion_num)
                    elif palette_type == "fashion_6":
                        return (6, fashion_num)
                    else:
                        return (99, fashion_num)  # Unknown types go last
            
            for palette_path in sorted(self.fashion_palettes[palette_char_id], key=sort_fashion_key):
                palette_name = os.path.basename(palette_path)
                palette_type = self.categorize_palette(palette_name)
                if palette_type not in fashion_groups:
                    fashion_groups[palette_type] = []
                fashion_groups[palette_type].append((palette_name, palette_path))
            
            # Create radio buttons for each fashion type
            for fashion_type, palettes in fashion_groups.items():
                if fashion_type.startswith("fashion_"):
                    # Create a frame for this fashion type
                    type_frame = tk.Frame(self.fashion_scrollable_frame)
                    type_frame.pack(fill="x", pady=0)
                    
                    # Get proper fashion type name
                    fashion_name = self.get_fashion_type_name(char_id, fashion_type)
                    
                    # Label for fashion type
                    tk.Label(type_frame, text=f"{fashion_name}:", font=("Arial", 9, "bold")).pack(anchor="w", pady=(1,0))
                    
                    # Radio buttons for this type - 3-column grid
                    var = tk.StringVar()
                    self.fashion_vars[fashion_type] = var
                    
                    # Grid container for 3-column layout
                    grid_frame = tk.Frame(type_frame)
                    grid_frame.pack(fill="x", padx=(10, 0))
                    columns = 3
                    for c in range(columns):
                        grid_frame.grid_columnconfigure(c, weight=1, uniform="col")

                    # All items: NONE first, then palettes
                    all_items = [("NONE", "NONE")] + list(palettes)
                    
                    root_dir = getattr(self, "root_dir",
                                      os.environ.get("FASHION_PREVIEWER_ROOT",
                                                   os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
                    custom_pals_path = os.path.join(root_dir, "exports", "custom_pals", "fashion")
                    old_custom_pals_path = os.path.join(root_dir, "exports", "custom_fashion_pals")

                    for col_idx, (palette_name, palette_path) in enumerate(all_items):
                        row_idx = col_idx // columns
                        col = col_idx % columns
                        if palette_path == "NONE":
                            display_name = "NONE"
                        else:
                            is_custom = (os.path.abspath(palette_path).startswith(os.path.abspath(custom_pals_path)) or
                                       os.path.abspath(palette_path).startswith(os.path.abspath(old_custom_pals_path)))
                            display_name = f"{palette_name} (C)" if is_custom else palette_name
                        
                        rb = tk.Radiobutton(grid_frame, text=display_name, variable=var,
                                          value=palette_path, command=lambda ft=fashion_type: self.on_fashion_change(ft),
                                          anchor="w", justify="left")
                        rb.configure(pady=1)
                        rb.grid(row=row_idx, column=col, sticky="w", padx=(0, 4), pady=0)
                        if palette_path != "NONE":
                            self.register_focusable(rb, f"fashion_{fashion_type}_{palette_path}")
                    
                    # Restore saved selection if available
                    saved_pal = self.loaded_palettes.get('fashion', {}).get(fashion_type, "NONE")
                    var.set(saved_pal)

            # Apply theme so radio buttons respect dark mode
            self.apply_theme(self.fashion_scrollable_frame)


    def on_third_job_change(self):
        """Handle 3rd job base fashion selection change"""
        self._deselect_frame(refresh=False)
        # Safety check: if current character is Paula, don't process 3rd job changes
        if hasattr(self, 'current_character') and self.current_character in ["chr025", "chr026", "chr027"]:
            return
        
        if hasattr(self, 'current_character') and self.current_character:
            self._save_character_settings(self.current_character)
            
        self.load_palettes()
        
        # Track palette selection for compact editor (after loading palettes)
        if hasattr(self, 'on_palette_selection_change'):
            selected_pal = self.third_job_var.get()
            if selected_pal != "NONE":
                self.on_palette_selection_change('third_job', selected_pal)
                
        self._debounced_display_update()

    def on_hair_change(self):
        """Handle hair selection change"""
        self._deselect_frame(refresh=False)
        # No warning on selection - warnings only appear when trying to edit
        
        if hasattr(self, 'current_character') and self.current_character:
            self._save_character_settings(self.current_character)
            
        self.load_palettes()
        
        # Track palette selection for compact editor (after loading palettes)
        if hasattr(self, 'on_palette_selection_change'):
            selected_pal = self.hair_var.get()
            if selected_pal != "NONE":
                self.on_palette_selection_change('hair', selected_pal)
                
        self._debounced_display_update()

    def on_fashion_change(self, changed_fashion_type=None):
        """Handle fashion selection change"""
        self._deselect_frame(refresh=False)
        
        if hasattr(self, 'current_character') and self.current_character:
            self._save_character_settings(self.current_character)
            
        self.load_palettes()
        
        # Track palette selection for compact editor (after loading palettes)
        if hasattr(self, 'on_palette_selection_change'):
            if changed_fashion_type and changed_fashion_type in self.fashion_vars:
                # Update specific fashion type that changed
                selected_pal = self.fashion_vars[changed_fashion_type].get()
                if selected_pal != "NONE":
                    self.on_palette_selection_change(changed_fashion_type, selected_pal)
            else:
                # Fallback: Get the last selected fashion palette
                for fashion_type, var in self.fashion_vars.items():
                    selected_pal = var.get()
                    if selected_pal != "NONE":
                        self.on_palette_selection_change(fashion_type, selected_pal)
                        break  # Just track the first one changed
        
        self._debounced_display_update()

    def load_palettes(self):
        """Load selected palettes"""
        # Store current UI mode before loading palettes
        current_ui_mode = getattr(self, 'live_pal_ui_mode', 'Simple')
        self.palette_layers = []
        
        # Load 3rd job base fashion palette (second from bottom layer)
        third_job_path = self.third_job_var.get()
        if third_job_path and third_job_path != "NONE":
            # Safety check: don't load 3rd job palettes for Paula characters
            if hasattr(self, 'current_character') and self.current_character in ["chr025", "chr026", "chr027"]:
                pass  # Don't return, continue to load other palettes
            else:
                layer = self.load_palette_file(third_job_path)
                if layer:
                    layer.palette_type = "3rd_job_base"
                    layer.active = True  # Ensure the layer is active
                    self.palette_layers.append(layer)
                    # Ensure UI mode is preserved when loading 3rd job base fashion
                    self.live_pal_ui_mode = current_ui_mode
        elif hasattr(self, 'current_character') and self.current_character:
            # For 3rd job characters (except Paula), automatically load the first available 3rd job palette
            char_id = self.current_character
            if char_id in CHARACTER_MAPPING and CHARACTER_MAPPING[char_id]["job"] == "3rd Job":
                if char_id not in ["chr025", "chr026", "chr027"]:  # Not Paula
                    palette_char_id = self.get_palette_character_id(char_id)
                    if palette_char_id in self.third_job_palettes and self.third_job_palettes[palette_char_id]:
                        first_palette = self.third_job_palettes[palette_char_id][0]
                        layer = self.load_palette_file(first_palette)
                        if layer:
                            layer.palette_type = "3rd_job_base"
                            layer.active = True  # Ensure the layer is active
                            self.palette_layers.append(layer)
                            # Update the variable to reflect the loaded palette
                            self.third_job_var.set(first_palette)

        # Restore UI mode after loading palettes
        self.live_pal_ui_mode = current_ui_mode
        
        # Load hair palette (bottom layer - processed first)
        hair_path = self.hair_var.get()
        if hair_path and hair_path != "NONE":
            layer = self.load_palette_file(hair_path)
            if layer:
                layer.palette_type = "hair"
                layer.active = True  # Ensure the layer is active
                self.palette_layers.append(layer)
            else:
                pass  # Failed to load hair palette
        else:
            pass  # No hair palette selected
        
        # Load selected fashion palettes (top layer - processed last)
        if hasattr(self, 'current_character') and self.current_character:
            char_id = self.current_character
            # Use the palette character ID for fashion palettes (handles Paula mapping)
            palette_char_id = self.get_palette_character_id(char_id)
            if palette_char_id in self.fashion_palettes:
                for fashion_type, var in self.fashion_vars.items():
                    selected_path = var.get()
                    if selected_path and selected_path != "NONE":
                        layer = self.load_palette_file(selected_path)
                        if layer:
                            layer.palette_type = fashion_type
                            layer.active = True  # Ensure the layer is active
                            self.palette_layers.append(layer)
                        else:
                            pass  # Failed to load palette
                    else:
                        pass  # No fashion selected
            else:
                pass  # No fashion palettes found

    def load_palette_file(self, file_path):
        """Load a palette file and return PaletteLayer object"""
        try:
            with open(file_path, "rb") as f:
                data = f.read()
                
            if len(data) != PALETTE_SIZE * 3:
                raise ValueError(f"Palette file size incorrect: {len(data)} bytes")
            
            colors = []
            for i in range(PALETTE_SIZE):
                r = data[i*3]
                g = data[i*3+1]
                b = data[i*3+2]
                colors.append((r, g, b))
            
            filename = os.path.basename(file_path)
            palette_type = self.categorize_palette(filename)
            
            # Track palette preview
            self.statistics.palettes_previewed += 1
            self._save_statistics()
            
            return PaletteLayer(filename, colors, palette_type, True, file_path)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load palette {file_path}: {e}")
            return None

    def _flatten_palette(self, palette):
        """Safely flatten a palette into exactly 768 integers for Pillow's putpalette.
        This prevents C-extension crashes when palettes have incorrect lengths or types."""
        flat = []
        for c in palette:
            if isinstance(c, (list, tuple)) and len(c) >= 3:
                try:
                    flat.extend([int(c[0]), int(c[1]), int(c[2])])
                except (ValueError, TypeError):
                    flat.extend([0, 0, 0])
            else:
                flat.extend([0, 0, 0])
        
        flat = flat[:768]
        while len(flat) < 768:
            flat.append(0)
        return flat

    def load_character_image(self):
        """Load the current character's image based on current_image_index"""
        if not hasattr(self, 'current_character') or not self.current_character:
            return
            
        char_id = self.current_character
        if char_id not in self.character_images or not self.character_images[char_id]:
            return
            
        images = self.character_images[char_id]
        if 0 <= self.current_image_index < len(images):
            self.load_image_from_path(images[self.current_image_index])

    def load_image_from_path(self, path):
        """Load image from a specific path"""
        # Track frame preview (but don't save during startup restoration)
        self.statistics.frames_previewed += 1
        if not getattr(self, '_is_restoring_session', False):
            self._save_statistics()
        try:
            img = Image.open(path)
            
            # Handle different image modes
            if img.mode == 'P':
                # Already palette mode
                self.original_image = img.copy()
                raw_palette = img.getpalette()
                self.original_palette = [
                    (raw_palette[i*3], raw_palette[i*3+1], raw_palette[i*3+2])
                    for i in range(PALETTE_SIZE)
                ]
            elif img.mode in ['RGB', 'RGBA']:
                # Convert to palette mode more carefully to preserve transparency
                if img.mode == 'RGBA':
                    # Handle alpha channel properly - use green background instead of white
                    background = Image.new('RGB', img.size, (0, 255, 0))  # Green background
                    img = Image.alpha_composite(background.convert('RGBA'), img).convert('RGB')
                
                # Use quantization without dithering to preserve keying colors
                img_palette = img.quantize(colors=256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
                raw_palette = img_palette.getpalette()
                if raw_palette:
                    self.original_palette = [
                        (raw_palette[i*3], raw_palette[i*3+1], raw_palette[i*3+2])
                        for i in range(min(len(raw_palette)//3, PALETTE_SIZE))
                    ]
                    while len(self.original_palette) < PALETTE_SIZE:
                        self.original_palette.append((0, 255, 0))  # Fill with green instead of black
                else:
                    self.original_palette = [(0, 255, 0)] * PALETTE_SIZE  # Use green instead of black
                
                self.original_image = img_palette
            else:
                messagebox.showerror("Error", f"Unsupported image mode: {img.mode}")
                return
            
            self.current_image_path = path
            # Update zoom combo state after image is loaded
            self.update_zoom_combo_state()
            self.update_image_display()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load image: {e}")

    def on_preview_mode_change(self):
        """Handle preview mode change (single vs all frames)"""
        # Sync view with selection if available
        if self.preview_var.get() == "single" and hasattr(self, 'selected_frame') and self.selected_frame is not None:
            self.current_image_index = self.selected_frame
            
        # Track mode changes for intelligent custom defaults
        new_mode = self.preview_var.get()
        old_mode = getattr(self, '_current_preview_mode', 'single')
        
        # Check if switching to "all" mode and show warning if needed
        if new_mode == "all" and old_mode != "all":
            if not self._get_all_mode_warning_preference():
                # Show warning dialogue
                result = self._show_all_mode_warning()
                if not result:
                    # User chose not to proceed, revert to previous mode
                    self.preview_var.set(old_mode)
                    return
        
        # If switching to custom mode, set intelligent defaults based on previous mode
        if new_mode == "custom" and old_mode != "custom":
            # Check if there are stored settings for this character/job
            current_job = self.job_var.get() if hasattr(self, 'job_var') else None
            char_settings = self.frame_range_settings.get(self.current_character, {}) if hasattr(self, 'current_character') else {}
            job_settings = char_settings.get(current_job, None)
            
            if not job_settings:
                # No stored custom settings, use intelligent defaults based on previous mode
                if old_mode == "single":
                    self.custom_frame_count = 1
                elif old_mode == "all" and hasattr(self, 'current_character') and self.current_character in self.character_images:
                    self.custom_frame_count = len(self.character_images[self.current_character])
                # If switching from custom to custom (shouldn't happen), keep existing
        
        # Update current mode tracking
        self._current_preview_mode = new_mode
        
        # Track frames based on mode
        if hasattr(self, 'current_character') and self.current_character in self.character_images:
            if new_mode == "all":
                self.statistics.frames_previewed += len(self.character_images[self.current_character])
            elif new_mode == "custom" and hasattr(self, 'custom_frame_count'):
                self.statistics.frames_previewed += self.custom_frame_count
            elif new_mode == "single":
                self.statistics.frames_previewed += 1
            self._save_statistics()
        
        self.update_zoom_combo_state()
        self.update_image_display()
        
        # Update navigation buttons after preview mode change
        self.update_navigation_buttons()
        
        # Return focus to canvas to ensure keyboard shortcuts function
        if hasattr(self, 'canvas') and self.canvas.winfo_exists():
            self.canvas.focus_set()
        
        # Add a delayed update to ensure zoom state is set correctly after UI updates
        self.master.after(100, self.update_zoom_combo_state)

    def get_current_displayed_frame(self):
        from code.core.frame_manager import FrameManager
        return FrameManager.get_current_displayed_frame(self)


    def open_custom_settings(self):
        """Open custom preview settings dialog"""
        self._deselect_frame()
        if not hasattr(self, 'current_character') or not self.current_character:
            messagebox.showinfo("Notice", "Please select a character first.")
            return
        
        if self.current_character not in self.character_images:
            messagebox.showinfo("Notice", "No images found for this character.")
            return
        
        max_frames = len(self.character_images[self.current_character])
        
        # Get current job
        current_job = self.job_var.get() if hasattr(self, 'job_var') else None
        
        # Get the currently displayed frame
        current_frame = self.get_current_displayed_frame()
        current_mode = self.preview_var.get()
        
        # Special handling for "all" mode - always show full range
        if current_mode == "all":
            dialog = CustomPreviewDialog(self, max_frames, 
                                       start_frame=0, end_frame=max_frames-1, num_frames=max_frames,
                                       use_bmp=self.use_bmp_export,
                                       show_labels=self.show_frame_labels,
                                       initial_frame=current_frame)
        else:
            # Get stored settings for this character/job combination
            char_settings = self.frame_range_settings.get(self.current_character, {})
            job_settings = char_settings.get(current_job, None)
            
            if job_settings:
                frame_count, start_frame, end_frame = job_settings
                dialog = CustomPreviewDialog(self, max_frames, start_frame, end_frame, frame_count, 
                                           self.use_bmp_export, self.show_frame_labels,
                                           initial_frame=current_frame)
            else:
                # Always use the current custom frame count when in custom mode, don't flash to 3
                default_frames = getattr(self, 'custom_frame_count', 3)
                
                dialog = CustomPreviewDialog(self, max_frames, num_frames=default_frames,
                                           use_bmp=self.use_bmp_export,
                                           show_labels=self.show_frame_labels,
                                           initial_frame=current_frame)
            
        self.master.wait_window(dialog.dialog)
        
        if dialog.result is not None:
            if len(dialog.result) == 12:
                frame_count, start_frame, end_frame, use_bmp, show_labels, use_portrait, use_choice, chosen_frame, palette_format, cute_bg, live_pal_ui, show_excess_prompt = dialog.result
                self.live_pal_ui_mode = live_pal_ui
                self.dont_show_excess_colors_prompt = not show_excess_prompt  # Invert for storage
            elif len(dialog.result) >= 11:
                frame_count, start_frame, end_frame, use_bmp, show_labels, use_portrait, use_choice, chosen_frame, palette_format, cute_bg, live_pal_ui = dialog.result
                self.live_pal_ui_mode = live_pal_ui
            else:
                frame_count, start_frame, end_frame, use_bmp, show_labels, use_portrait, use_choice, chosen_frame, palette_format, cute_bg = dialog.result
            
            self.custom_frame_count = frame_count
            self.use_bmp_export = use_bmp
            self.use_portrait_export = use_portrait
            self.show_frame_labels = show_labels
            self.custom_start_frame = start_frame
            self.custom_end_frame = end_frame
            self.cute_bg_option = cute_bg
            
            # If user chose a specific frame, set it as the start index
            if use_choice and chosen_frame is not None:
                self.custom_start_index = chosen_frame - 1  # Convert 1-based to 0-based for internal use
            else:
                self.custom_start_index = start_frame
            self.update_image_display()  # Refresh display to show/hide labels
            self.update_export_button_text()
            
            # Store settings for this character/job combination
            if self.current_character not in self.frame_range_settings:
                self.frame_range_settings[self.current_character] = {}
            self.frame_range_settings[self.current_character][current_job] = (frame_count, start_frame, end_frame)
            # Reset custom start index if it would exceed bounds
            if self.custom_start_index + self.custom_frame_count > max_frames:
                self.custom_start_index = max(0, max_frames - self.custom_frame_count)
            # Update zoom combo state based on new frame count
            self.update_zoom_combo_state()
            self.update_image_display()

    def get_custom_frame_range(self):
        from code.core.frame_manager import FrameManager
        return FrameManager.get_custom_frame_range(self)


    def on_zoom_change(self):
        """Handle zoom level change"""
        # Force canvas update before recalculating layout
        if hasattr(self, 'canvas') and self.canvas.winfo_exists():
            self.canvas.update_idletasks()
        self._debounced_display_update()

    def update_export_button_text(self):
        """Update the export button text based on the selected format"""
        if hasattr(self, 'export_button'):
            if self.use_bmp_export:
                self.export_button.config(text="Export Background BMP")
                self.export_button.config(command=self.export_background_bmp)
            else:
                self.export_button.config(text="Export Transparent PNG")
                self.export_button.config(command=self.export_transparent_png)

    def update_zoom_combo_state(self):
        """Update zoom combo state based on current preview mode"""
        self.preview_var.get()
        
        if hasattr(self, 'current_character') and self.current_character:
            char_id = self.current_character
            if char_id in self.character_images:
                # Enable zoom for all modes when images are loaded
                self.zoom_combo.config(state="readonly")
            else:
                # No images loaded, disable zoom
                self.zoom_combo.config(state="disabled")
        else:
            # No character selected, disable zoom
            self.zoom_combo.config(state="disabled")
        
        # Force update the UI
        self.zoom_combo.update()
        
        # Schedule another update after a short delay to ensure UI state is applied
        self.master.after(50, self._force_zoom_state_update)

    def _force_zoom_state_update(self):
        """Force update zoom combo state after a delay"""
        preview_mode = self.preview_var.get()
        if preview_mode == "custom":
            if hasattr(self, 'current_character') and self.current_character:
                char_id = self.current_character
                if char_id in self.character_images:
                    # Enable zoom for all frame counts
                    self.zoom_combo.config(state="readonly")


    def apply_theme(self, widget=None):
        from code.utils.theme_manager import ThemeManager
        return ThemeManager.apply_theme(self, widget)

    def on_canvas_configure(self, event):
        # Configure scroll region for single frame mode and custom preview mode (up to 50 frames)
        preview_mode = self.preview_var.get()
        
        if preview_mode == "single" and self.original_image:
            w, h = self.original_image.size
            
            # Apply zoom based on current zoom setting
            zoom_level = self.zoom_var.get()
            display_w, display_h = w, h
            
            if zoom_level == "200%":
                display_w = int(w * 2)
                display_h = int(h * 2)
            elif zoom_level == "300%":
                display_w = int(w * 3)
                display_h = int(h * 3)
            elif zoom_level == "400%":
                display_w = int(w * 4)
                display_h = int(h * 4)
            elif zoom_level == "500%":
                display_w = int(w * 5)
                display_h = int(h * 5)
            elif zoom_level == "Fit":
                canvas_width = self.canvas.winfo_width()
                canvas_height = self.canvas.winfo_height()
                if canvas_width > 1 and canvas_height > 1:
                    scale_x = canvas_width / w
                    scale_y = canvas_height / h
                    scale = min(scale_x, scale_y)
                    display_w = int(w * scale)
                    display_h = int(h * scale)
            
            # Configure scroll region to show full content with proper bounds
            self.canvas.config(scrollregion=(0, 0, display_w, display_h))
        elif preview_mode == "custom" and hasattr(self, 'current_character') and self.current_character:
            # For custom mode, only configure scroll region if we have 100 or fewer frames being displayed
            char_id = self.current_character
            if char_id in self.character_images:
                frames_to_display = getattr(self, 'custom_frame_count', 3)
                if frames_to_display <= 100:
                    # Let the custom frames display function handle the scroll region
                    # This will be called when update_custom_frames_display runs
                    pass


    def toggle_flip(self):
        """Toggle image flip"""
        if hasattr(self, '_save_frame_visibility_state'):
            self._save_frame_visibility_state()
        self.image_flip = not getattr(self, 'image_flip', False)
        self._debounced_display_update()
        
    def rotate_preview(self):
        """Rotate the image 90 degrees"""
        if hasattr(self, '_save_frame_visibility_state'):
            self._save_frame_visibility_state()
        self.image_rotation = (getattr(self, 'image_rotation', 0) - 90) % 360
        self._debounced_display_update()
        
    def open_fashion_creator(self):
        """Open the Fashion Creator / XML Generator"""
        try:
            from fashion_creator import FashionCreatorApp
            # Ensure it only opens one instance if desired, or let it open multiple
            if not hasattr(self, 'fashion_creator_window') or not self.fashion_creator_window.winfo_exists():
                self.fashion_creator_window = FashionCreatorApp(master=self.master, previewer_app=self)
            else:
                self.fashion_creator_window.lift()
                self.fashion_creator_window.focus_force()
        except Exception as e:
            import tkinter.messagebox as messagebox
            messagebox.showerror("Error", f"Failed to launch fashion creator: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = PaletteTool(root)
    app.statistics = Statistics()  # Initialize statistics
    app._load_statistics()  # Load saved statistics
    root.mainloop()

