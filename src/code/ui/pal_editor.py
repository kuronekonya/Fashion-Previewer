import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import re
from icon_handler import CHARACTER_MAPPING

class PalEditor:
        def update_compact_palette_editor(app):
            """Update active colors display in compact mode"""
            if not hasattr(app, 'active_colors_frame') or not app.active_colors_frame:
                return
                
            # Clear existing contents correctly
            for widget in app.active_colors_frame.winfo_children():
                widget.destroy()
                
            # Initialize widget tracking
            app._compact_swatch_widgets = {}
                
            # Check if we have a selected palette
            if not hasattr(app, 'last_selected_palette') or not app.last_selected_palette or app.last_selected_palette == "NONE":
                 tk.Label(app.active_colors_frame, text="Choose a pal to see active colors", 
                          fg="gray", bg="white").pack(expand=True)
                 return
    
            # Initialize selected colors set for compact editor
            if not hasattr(app, 'compact_selected_colors'):
                app.compact_selected_colors = set()
            
            # Reset base colors for sliders when recreating editor/switching palette
            if hasattr(app, 'compact_base_colors'):
                # Only clear if we explicitly want to (usually we persist selection? No, reset on redraw usually implies refresh)
                # Actually, let's keep it unless empty to support redraws
                pass
            else:
                app.compact_base_colors = {}
    
            # Find the PaletteLayer or Dummy Layer
            colors = []
            editable_indices = []
            target_layer = None
            target_path = os.path.abspath(app.last_selected_palette)
            target_filename = os.path.basename(target_path)
            
            # Try finding layer by name and type first (Live Editor approach)
            if hasattr(app, 'palette_layers'):
                for layer in app.palette_layers:
                    if getattr(layer, "name", "") == target_filename:
                        if hasattr(app, 'last_selected_palette_type') and app.last_selected_palette_type:
                            if getattr(layer, "palette_type", "") == app.last_selected_palette_type:
                                target_layer = layer
                                break
                        else: 
                             target_layer = layer
                             break
                
                # Fallback to name only
                if not target_layer:
                    for layer in app.palette_layers:
                        if getattr(layer, "name", "") == target_filename:
                            target_layer = layer
                            break
            
            if target_layer:
                app._compact_active_layer = target_layer
                colors = target_layer.colors
                editable_indices = app._get_editable_color_indices(target_layer)
            else:
                app._compact_active_layer = None
                # Fallback: Load from file and use Dummy Layer
                try:
                    with open(app.last_selected_palette, "rb") as f:
                        data = f.read()
                        if len(data) == 768:
                            for i in range(256):
                                colors.append((data[i*3], data[i*3+1], data[i*3+2]))
                            
                            # Prepare Dummy Layer for filtering
                            p_type = "unknown"
                            if hasattr(app, 'last_selected_palette_type') and app.last_selected_palette_type:
                                p_type = app.last_selected_palette_type
                            elif hasattr(app, 'categorize_palette'):
                                p_type = app.categorize_palette(target_filename)
                            
                            # Ensure filename includes character ID for parsing
                            dummy_name = target_filename
                            if hasattr(app, 'current_character') and app.current_character:
                                if app.current_character not in dummy_name:
                                    dummy_name = f"{app.current_character}_{dummy_name}"
                            
                            class DummyLayer:
                                def __init__(app, name, colors, palette_type):
                                    app.name = name
                                    app.colors = colors
                                    app.palette_type = palette_type
                            
                            dummy = DummyLayer(dummy_name, colors, p_type)
                            editable_indices = app._get_editable_color_indices(dummy)
                            
                            if not editable_indices:
                                editable_indices = list(range(256))
                            app._compact_active_layer = dummy
                except Exception as e:
                    pass
                    
            if not colors:
                 tk.Label(app.active_colors_frame, text="Failed to load colors", 
                          fg="red", bg="white").pack(expand=True)
                 return
    
            if not editable_indices:
                 editable_indices = list(range(len(colors)))
                 
            # Filter indices (remove 255 explicitly)
            filtered_indices = [x for x in editable_indices if x != 255]
    
            # --- LAYOUT CONSTRUCTION ---
            
            # Left column: HSV sliders
            left_column = tk.Frame(app.active_colors_frame, bg="white", width=180)
            left_column.pack(side="left", fill="both", padx=5, pady=5)
            left_column.pack_propagate(False)  # Fixed width
            
            tk.Label(left_column, text="HSV Adjustments", font=("Arial", 9, "bold"), bg="white").pack(pady=(0, 5))
            
            def _compact_hsv_slider_changed_proxy(*args):
                if hasattr(app, '_compact_hsv_slider_changed'):
                    app._compact_hsv_slider_changed(*args)
    
            def _compact_hsv_entry_changed_proxy(*args):
                 if hasattr(app, '_compact_hsv_entry_changed'):
                     app._compact_hsv_entry_changed(*args)
    
            # Hue slider
            hue_frame = tk.Frame(left_column, bg="white")
            hue_frame.pack(fill="x", pady=1)
            tk.Label(hue_frame, text="Hue:", width=5, anchor="w", bg="white", font=("Arial", 8)).pack(side="left")
            
            if not hasattr(app, 'compact_hue_var'): app.compact_hue_var = tk.IntVar(value=0)
            hue_slider = tk.Scale(hue_frame, from_=-180, to=180, orient="horizontal", 
                                 resolution=1, bg="white", highlightthickness=0, variable=app.compact_hue_var,
                                 command=_compact_hsv_slider_changed_proxy)
            hue_slider.pack(side="left", fill="x", expand=True)
            app.hue_slider = hue_slider # store ref
            
            hue_entry = tk.Entry(hue_frame, textvariable=app.compact_hue_var, width=5, font=("Arial", 8))
            hue_entry.pack(side="left", padx=1)
            hue_entry.bind('<Return>', lambda e: _compact_hsv_entry_changed_proxy())
            hue_entry.bind('<FocusOut>', lambda e: _compact_hsv_entry_changed_proxy())
            
            # Saturation slider
            sat_frame = tk.Frame(left_column, bg="white")
            sat_frame.pack(fill="x", pady=1)
            tk.Label(sat_frame, text="Sat:", width=5, anchor="w", bg="white", font=("Arial", 8)).pack(side="left")
            
            if not hasattr(app, 'compact_sat_var'): app.compact_sat_var = tk.IntVar(value=0)
            sat_slider = tk.Scale(sat_frame, from_=-100, to=100, orient="horizontal", 
                                 resolution=1, bg="white", highlightthickness=0, variable=app.compact_sat_var,
                                 command=_compact_hsv_slider_changed_proxy)
            sat_slider.pack(side="left", fill="x", expand=True)
            app.sat_slider = sat_slider
            
            sat_entry = tk.Entry(sat_frame, textvariable=app.compact_sat_var, width=5, font=("Arial", 8))
            sat_entry.pack(side="left", padx=1)
            sat_entry.bind('<Return>', lambda e: _compact_hsv_entry_changed_proxy())
            sat_entry.bind('<FocusOut>', lambda e: _compact_hsv_entry_changed_proxy())
            
            # Value slider
            val_frame = tk.Frame(left_column, bg="white")
            val_frame.pack(fill="x", pady=1)
            tk.Label(val_frame, text="Val:", width=5, anchor="w", bg="white", font=("Arial", 8)).pack(side="left")
            
            if not hasattr(app, 'compact_val_var'): app.compact_val_var = tk.IntVar(value=0)
            val_slider = tk.Scale(val_frame, from_=-100, to=100, orient="horizontal", 
                                 resolution=1, bg="white", highlightthickness=0, variable=app.compact_val_var,
                                 command=_compact_hsv_slider_changed_proxy)
            val_slider.pack(side="left", fill="x", expand=True)
            app.val_slider = val_slider
            
            val_entry = tk.Entry(val_frame, textvariable=app.compact_val_var, width=5, font=("Arial", 8))
            val_entry.pack(side="left", padx=1)
            val_entry.bind('<Return>', lambda e: _compact_hsv_entry_changed_proxy())
            val_entry.bind('<FocusOut>', lambda e: _compact_hsv_entry_changed_proxy())
            
            def reset_sliders():
                app.compact_hue_var.set(0)
                app.compact_sat_var.set(0)
                app.compact_val_var.set(0)
                _compact_hsv_slider_changed_proxy()
            
            reset_btn = tk.Button(left_column, text="Reset", command=reset_sliders, 
                                 bg="#f44336", fg="white", font=("Arial", 8, "bold"))
            reset_btn.pack(fill="x", pady=(10, 0))
    
            def toggle_saved_colors():
                if not hasattr(app, 'saved_colors_main_frame'):
                    return
                if str(app.saved_colors_main_frame) in app.paned.panes():
                    app.paned.forget(app.saved_colors_main_frame)
                else:
                    app.paned.add(app.saved_colors_main_frame)
    
            toggle_sc_btn = tk.Button(left_column, text="Toggle Saved Colors", command=toggle_saved_colors,
                                     font=("Arial", 8, "bold"))
            toggle_sc_btn.pack(fill="x", pady=(5, 0))
    
            # Right Column: Active Color Indexes
            right_column = tk.Frame(app.active_colors_frame, bg="white")
            right_column.pack(side="right", fill="both", expand=True, padx=5, pady=5)
            
            tk.Label(right_column, text="Active Color Indexes", font=("Arial", 9, "bold"), bg="white").pack(pady=(0, 5))
    
            # Container for scrollbar and canvas
            container = tk.Frame(right_column, bg="white")
            container.pack(fill="both", expand=True)
    
            # Scrollbar frame on the right
            sb_frame = tk.Frame(container, bg="white", width=20)
            sb_frame.pack(side="right", fill="y")
            
            # Scrollbar widget
            scrollbar = ttk.Scrollbar(sb_frame, orient="vertical")
            scrollbar.pack(side="left", fill="y", expand=True)
            
            # Canvas on the left
            canvas = tk.Canvas(container, bg="white", highlightthickness=0, yscrollcommand=scrollbar.set)
            canvas.pack(side="left", fill="both", expand=True)
            
            scrollbar.config(command=canvas.yview)
            
            content_frame = tk.Frame(canvas, bg="white")
            canvas_window = canvas.create_window((0, 0), window=content_frame, anchor="nw")
            
            def on_configure(event):
                canvas.configure(scrollregion=canvas.bbox("all"))
                canvas.itemconfig(canvas_window, width=event.width)
            canvas.bind("<Configure>", on_configure)
            
            def on_frame_configure(event):
                canvas.configure(scrollregion=canvas.bbox("all"))
            content_frame.bind("<Configure>", on_frame_configure)
            
            def _on_mousewheel(event):
                 canvas.yview_scroll(int(-1*(event.delta/120)), "units")
                
            canvas.bind("<MouseWheel>", _on_mousewheel)
            content_frame.bind("<MouseWheel>", _on_mousewheel)
            
            # Helper to toggle selection
            def toggle_color_selection(idx, swatch_frame):
                if idx in app.compact_selected_colors:
                    app.compact_selected_colors.remove(idx)
                    swatch_frame.config(highlightbackground="black", highlightthickness=1) # Normal
                    
                    if not app.compact_selected_colors:
                        app.compact_base_colors = {}
                        reset_sliders()
                else:
                    if not app.compact_selected_colors:
                        app.compact_base_colors = {}
                        reset_sliders()
                        # Base colors snapshot logic (snapshot ALL visible)
                        for c_idx in filtered_indices:
                            if c_idx < len(colors):
                                app.compact_base_colors[c_idx] = colors[c_idx]
                    
                    app.compact_selected_colors.add(idx)
                    swatch_frame.config(highlightbackground="red", highlightthickness=2) # Selected
    
            # Create swatches grid
            columns = 8 
            swatch_size = 22 # Reduced slightly from 25 to fit 7 items comfortably
            padding = 2
            
            for i, idx in enumerate(filtered_indices):
                if idx < len(colors):
                    r, g, b = colors[idx]
                    hex_col = f"#{r:02x}{g:02x}{b:02x}"
                    
                    # FRAME (No Text)
                    # Use highlightthickness/highlightbackground for selection border
                    is_selected = idx in app.compact_selected_colors
                    border_col = "red" if is_selected else "black"
                    border_width = 2 if is_selected else 1
                    
                    # Use a container frame for the padding/border?
                    # Actually tk.Frame has highlightthickness.
                    swatch = tk.Frame(content_frame, bg=hex_col, width=swatch_size, height=swatch_size, 
                                    relief="flat", highlightthickness=border_width, highlightbackground=border_col)
                                    
                    swatch.grid(row=i//columns, column=i%columns, padx=padding, pady=padding)
                    
                    # Store widget for later updates
                    app._compact_swatch_widgets[idx] = swatch
                    
                    # Bind Events
                    swatch.bind("<MouseWheel>", _on_mousewheel)
                    # Bind click to toggle selection
                    swatch.bind("<Button-1>", lambda e, x=idx, s=swatch: toggle_color_selection(x, s))
                    swatch.bind("<MouseWheel>", _on_mousewheel)
            
            from code.utils.theme_manager import ThemeManager
            ThemeManager.apply_theme(app, app.active_colors_frame)
    
        def open_live_palette_editor(app):
            """Edit ONE active palette layer with an embedded RGB/HEX picker.
            Added: Multi-select mode + Shift-click range selection."""
            app._deselect_frame()
            # Store current UI mode before opening editor
            current_ui_mode = getattr(app, 'live_pal_ui_mode', 'Simple')
            
            # Check if live editor is already open
            if hasattr(app, '_live_editor_window') and app._live_editor_window and app._live_editor_window.winfo_exists():
                app._live_editor_window.lift()
                from code.utils.theme_manager import ThemeManager
                ThemeManager.apply_theme(app, app._live_editor_window)
                app._live_editor_window.focus_force()
                return
                
            # Track palette editing
            if hasattr(app, 'current_character'):
                current_job = app.job_var.get() if hasattr(app, 'job_var') else None
                if current_job:
                    app.statistics.add_character_view(app.current_character, current_job)
                    app._save_statistics()
                
            active_layers = [ly for ly in app.palette_layers if getattr(ly, "active", False)]
            if not active_layers:
                messagebox.showinfo("Live Edit Palette", "No active palette layer. Select Hair or a Fashion item first.")
                return
    
            # Prefer the last selected palette if it's active
            default_idx = 0
            last_pal = getattr(app, 'last_selected_palette', None)
            if last_pal:
                import os
                last_pal_base = os.path.basename(last_pal)
                for i, ly in enumerate(active_layers):
                    if ly.name == last_pal_base:
                        default_idx = i
                        break
            else:
                # Fallback: Prefer an active fashion layer
                for i, ly in enumerate(active_layers):
                    if str(getattr(ly, "palette_type", "")).startswith("fashion_"):
                        default_idx = i
                        break
    
            # Build display names
            names = []
            for ly in active_layers:
                ptype = str(getattr(ly, "palette_type", ""))
                if ptype == "hair":
                    disp = "Hair"
                elif ptype == "3rd_job_base":
                    disp = "3rd Job Base"
                elif ptype.startswith("fashion_"):
                    try:
                        disp = app.get_fashion_type_name(app.current_character, ptype)
                    except Exception:
                        disp = ptype.replace("fashion_", "Fashion ").replace("_"," ").title()
                else:
                    disp = ptype
                names.append(f"{disp} — {ly.name}")
            # Session warning tracker for non-impact edits
            app._live_warned_types = set()
            # Warn up front if default target is Hair or 3rd Job Base
            try:
                default_layer = active_layers[default_idx]
                # Load UI mode from settings if not already set
                if not hasattr(app, 'live_pal_ui_mode'):
                    try:
                        import json
                        import os
                        settings_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "settings.json")
                        if os.path.exists(settings_path):
                            with open(settings_path, 'r', encoding='utf-8') as f:
                                settings = json.load(f)
                                app.live_pal_ui_mode = settings.get('live_pal_editor_ui_mode', 'Simple')
                        else:
                            app.live_pal_ui_mode = 'Simple'
                    except:
                        app.live_pal_ui_mode = 'Simple'
                # Store UI mode before warning dialog
                current_ui_mode = app.live_pal_ui_mode
                if not app._warn_if_nonimpact(getattr(default_layer, "palette_type", "")):
                    # If user clicked "No", bring existing live editor to front if it exists
                    if hasattr(app, '_live_editor_window') and app._live_editor_window and app._live_editor_window.winfo_exists():
                        app._live_editor_window.lift()
                        from code.utils.theme_manager import ThemeManager
                        ThemeManager.apply_theme(app, app._live_editor_window)
                        app._live_editor_window.focus_force()
                    return
                # Restore UI mode after warning dialog
                app.live_pal_ui_mode = current_ui_mode
                app._live_prev_target_name = ""
            except Exception:
                pass
    
    
            # State
            app._live_layers = active_layers
            app._live_target_name = tk.StringVar(value=names[default_idx])
            app._live_prev_target_name = names[default_idx]
            app._current_live_palette_name = names[default_idx]
            app._live_name_to_index = {n:i for i,n in enumerate(names)}
            app._live_selected_index = 0
            app._multi_select = tk.BooleanVar(value=False)
            app._selected_indices = set()
            app._last_clicked_index = None
            
            # Store original colors for all layers to restore when editor closes
            app._live_original_colors = {}
            app._live_saved_layers = set()  # Track which layers were saved
            app._updating_live_selection = False  # Flag to prevent grid recreation during selection updates
            
            # Temporary palette cache to preserve changes during editor session
            app._live_temp_palette_cache = {}  # Cache for temporary changes during session
            
            for i, layer in enumerate(active_layers):
                app._live_original_colors[names[i]] = layer.colors.copy()
                # Initialize temp cache with current colors (which may already have changes)
                app._live_temp_palette_cache[names[i]] = layer.colors.copy()
            
            # Track which job/character each palette type belongs to
            app._live_palette_job_mapping = {}
            # Initialize mapping based on current layers
            for i, layer in enumerate(active_layers):
                if hasattr(layer, "palette_type"):
                    # Extract character number from the name (e.g. chr001)
                    char_match = re.search(r'chr(\d{3})', names[i])
                    if char_match:
                        char_num = char_match.group(1)
                        if char_num in CHARACTER_MAPPING:
                            char_info = CHARACTER_MAPPING[char_num]
                            app._live_palette_job_mapping[names[i]] = {
                                'palette_type': layer.palette_type,
                                'character': char_info['name'],
                                'job': char_info['job']
                            }
    
            app._live_editor_window = tk.Toplevel(app.master)
            app._live_editor_window.title("Live Edit Palette")
            app._live_editor_window.geometry("860x460")  # Wider window to fit gear button
            app._live_editor_window.resizable(False, True)
            
            # Restore the UI mode that was stored earlier
            app.live_pal_ui_mode = current_ui_mode
            
            # Add callback to refresh custom pals when window is closed
            def on_window_close():
                # Restore original colors only for layers that weren't saved
                colors_were_restored = False
                if hasattr(app, '_live_original_colors'):
                    saved_layers = getattr(app, '_live_saved_layers', set())
                    for layer_name, original_colors in app._live_original_colors.items():
                        if layer_name not in saved_layers and layer_name in app._live_name_to_index:
                            layer_idx = app._live_name_to_index[layer_name]
                            if layer_idx < len(app._live_layers):
                                app._live_layers[layer_idx].colors = original_colors.copy()
                                colors_were_restored = True
                    # Clear the original colors storage
                    delattr(app, '_live_original_colors')
                    if hasattr(app, '_live_saved_layers'):
                        delattr(app, '_live_saved_layers')
                    # Clear the temp cache
                    if hasattr(app, '_live_temp_palette_cache'):
                        delattr(app, '_live_temp_palette_cache')
                
                app.refresh_custom_pals(update_ui=True)  # Update UI to refresh custom pals display
                
                # Update the main display to reflect restored palette colors
                if colors_were_restored:
                    # Reload palettes to ensure the restored colors are properly applied
                    app.load_palettes()
                    app._debounced_display_update()
                
                app._live_editor_window.destroy()
                app._live_editor_window = None  # Clear the instance variable
                
                # Re-enable icon editor button when live editor closes
                app._update_icon_editor_button_state()
            
            app._live_editor_window.protocol("WM_DELETE_WINDOW", on_window_close)
            
            from code.utils.theme_manager import ThemeManager
            ThemeManager.apply_theme(app, app._live_editor_window)
    
            # Top bar
            top = tk.Frame(app._live_editor_window); top.pack(fill="x", padx=6, pady=6)
            tk.Label(top, text="Edit which:").pack(side="left")
            om = tk.OptionMenu(top, app._live_target_name, *names, command=app._live_on_target_changed)
            # Apply dark mode styling to OptionMenu if needed
            if getattr(app, 'dark_mode', False):
                om.configure(bg="#1E1E1E", fg="#FFFFFF", activebackground="#333333", activeforeground="#FFFFFF",
                             highlightthickness=0)
                om["menu"].configure(bg="#252525", fg="#FFFFFF", activebackground="#333333", activeforeground="#FFFFFF")
            om.pack(side="left", padx=(4,8))
            tk.Checkbutton(top, text="Multi-select", variable=app._multi_select, command=app._live_multi_toggled).pack(side="left", padx=(8,8))
            tk.Button(top, text="Select All", command=app._live_select_all).pack(side="left", padx=(0,5))
            tk.Button(top, text="Clear Sel", command=app._live_clear_selection).pack(side="left")
            app._sel_count_lbl = tk.Label(top, text="(0 selected)"); app._sel_count_lbl.pack(side="left", padx=(6,0))
            tk.Button(top, text="Save Item .pal", command=app._live_save_item_pal).pack(side="left", padx=(12,8))
            # Gears button for settings
            tk.Button(top, text="⚙", width=3, command=app._open_live_pal_settings_menu).pack(side="right", padx=(0, 5))
            # Divider
            tk.Frame(top, width=2, bg="gray", relief="sunken").pack(side="right", fill="y", padx=5)
            app._live_reset_btn = tk.Menubutton(top, text="Reset Colors", relief="raised")
            app._live_reset_menu = tk.Menu(app._live_reset_btn, tearoff=0)
            app._live_reset_btn.configure(menu=app._live_reset_menu)
            app._live_reset_menu.add_command(label="Selected Index(es)", command=app._live_reset_selected)
            app._live_reset_menu.add_command(label="Whole Pallette", command=app._live_reset_to_original)
            app._live_reset_btn.pack(side="right", padx=(0, 5))
    
            # Body - use grid for better control over proportions
            body = tk.Frame(app._live_editor_window); body.pack(fill="both", expand=True, padx=1, pady=0)
            body.grid_rowconfigure(0, weight=1)  # Allow row to expand
            body.grid_columnconfigure(0, weight=0)  # Left column (grid) - fixed width
            body.grid_columnconfigure(1, weight=1)  # Right column (panel) - expandable
            
            
            # Ensure UI mode is preserved right before building UI
            app.live_pal_ui_mode = current_ui_mode
            
            # Swatches grid (left) - adjust width based on mode
            if app.live_pal_ui_mode == "Simple":
                grid = tk.Frame(body); grid.grid(row=0, column=0, padx=(0,0), pady=0, sticky="nsew")
                # Let the grid expand to fill the allocated column space
            else:
                grid = tk.Frame(body); grid.grid(row=0, column=0, padx=0, pady=0, sticky="nsew")
            
            app._live_swatches = []
            ly = app._live_layers[app._live_name_to_index[app._live_target_name.get()]]
            
            # Check if we're in Simple mode
            if app.live_pal_ui_mode == "Simple":
                app._create_simple_palette_grid(grid, ly)
            else:
                app._create_advanced_palette_grid(grid, ly)
    
            # Picker panel (right) - adjust width based on mode
            if app.live_pal_ui_mode == "Simple":
                panel = tk.Frame(body, width=500)  # No border in Simple mode (120px wider for saved colors)
                panel.grid(row=0, column=1, padx=(4,0), pady=0, sticky="nsew")
            else:
                panel = tk.LabelFrame(body, text="Color Picker", padx=2, pady=1)
                panel.grid(row=0, column=1, padx=(4,0), pady=0, sticky="nsew")
    
            app._picker_idx_var = tk.StringVar(value="0")
            tk.Label(panel, text="Index:").grid(row=0, column=0, sticky="w")
            app._picker_idx_entry = tk.Entry(panel, width=5, textvariable=app._picker_idx_var)
            app._picker_idx_entry.grid(row=0, column=1, sticky="w")
            tk.Button(panel, text="Go", command=app._live_goto_index).grid(row=0, column=2, padx=(6,0))
    
            tk.Label(panel, text="Hex #RRGGBB:").grid(row=1, column=0, sticky="w", pady=(2,0))
            app._picker_hex = tk.Entry(panel, width=10)
            app._picker_hex.grid(row=1, column=1, columnspan=2, sticky="w")
            tk.Button(panel, text="Apply", command=app._live_apply_hex).grid(row=1, column=3, padx=(6,0))
            
            # Colorpicker button
            app._colorpicker_btn = tk.Button(panel, text="🎨 Pick", command=app._toggle_colorpicker)
            app._colorpicker_btn.grid(row=1, column=4, padx=(6,0))
            
            # Gradient button with rainbow colors
            app._gradient_btn = tk.Button(panel, text="🌈", command=app._open_gradient_menu, 
                                         bg="#FF4081", activebackground="#E91E63", width=3, height=1,
                                         font=("Arial", 10, "bold"), relief="raised")
            app._gradient_btn.grid(row=1, column=5, padx=(6,0))
            if not hasattr(app, '_compact_swatch_widgets'): app._compact_swatch_widgets = {}
            app._compact_swatch_widgets['pal_gradient_btn'] = app._gradient_btn
    
            def mk_scale(label, row, varname):
                v = tk.IntVar(value=0)
                setattr(app, varname, v)
                tk.Label(panel, text=label).grid(row=row, column=0, sticky="w", pady=(8,0))
                sc = tk.Scale(panel, from_=0, to=255, orient="horizontal", variable=v,
                              command=lambda *_: app._live_slider_changed())
                sc.grid(row=row, column=1, columnspan=3, sticky="we", pady=(8,0))
            # Configure columns to properly accommodate all widgets including gradient button
            panel.grid_columnconfigure(1, weight=1)  # Make column 1 expandable for hex entry
    
                            
            # HSV controls - minimal spacing
            tk.Label(panel, text="Hue").grid(row=5, column=0, sticky="w", pady=(2,0))
            app._picker_h = tk.Scale(panel, from_=0, to=360, orient="horizontal", command=lambda *_: app._hsv_debounced_change())
            app._picker_h.grid(row=5, column=1, columnspan=5, sticky="we", pady=(1,0))
            tk.Label(panel, text="Sat").grid(row=6, column=0, sticky="w", pady=(1,0))
            app._picker_s = tk.Scale(panel, from_=0, to=100, orient="horizontal", command=lambda *_: app._hsv_debounced_change())
            app._picker_s.grid(row=6, column=1, columnspan=5, sticky="we", pady=(1,0))
            tk.Label(panel, text="Val").grid(row=7, column=0, sticky="w", pady=(1,0))
            app._picker_v = tk.Scale(panel, from_=0, to=100, orient="horizontal", command=lambda *_: app._hsv_debounced_change())
            app._picker_v.grid(row=7, column=1, columnspan=5, sticky="we", pady=(1,0))
            # --- Smooth-drag: mark dragging on press, clear on release ---
            def _start_drag(_e=None):
                app._is_dragging = True
            def _end_drag(_e=None):
                app._is_dragging = False
                try:
                    app._hsv_debounced_change()
                    # Track statistics when slider is released
                    if hasattr(app, 'statistics') and hasattr(app, '_live_selected_index'):
                        app.statistics.track_index_modification(app._live_selected_index)
                except Exception:
                    pass
            for w in (app._picker_h, app._picker_s, app._picker_v):
                try:
                    w.bind("<ButtonPress-1>", _start_drag)
                    w.bind("<ButtonRelease-1>", _end_drag)
                except Exception:
                    pass
    
    
            # HSV numeric entry boxes (right of sliders)
            # H entry
            app._hsv_h_str = tk.StringVar(value="0")
            eH = tk.Entry(panel, textvariable=app._hsv_h_str, width=5)
            eH.grid(row=5, column=6, sticky="w", padx=(6,0))
            # S entry
            app._hsv_s_str = tk.StringVar(value="0")
            eS = tk.Entry(panel, textvariable=app._hsv_s_str, width=5)
            eS.grid(row=6, column=6, sticky="w", padx=(6,0))
            # V entry
            app._hsv_v_str = tk.StringVar(value="0")
            eV = tk.Entry(panel, textvariable=app._hsv_v_str, width=5)
            eV.grid(row=7, column=6, sticky="w", padx=(6,0))
    
            # --- Saved Colors panel (simple MS Paint style) ---
            if not hasattr(app, "_saved_colors"):
                app._saved_colors = [(0,0,0)] * 20
            sc_frame = tk.LabelFrame(panel, text="Saved Colors")
            sc_frame.grid(row=9, column=0, columnspan=7, sticky="we", padx=0, pady=(2,0))
            sc_top = tk.Frame(sc_frame); sc_top.pack(fill="x", padx=2, pady=2)
            
            # Mouse button toggle (right side)
            def toggle_click_mode():
                app.use_right_click = not app.use_right_click
                mouse_btn.config(text="R" if app.use_right_click else "L", 
                               relief="sunken" if app.use_right_click else "raised")
                # Update help text
                if app.use_right_click:
                    help_label.config(text="Left click to apply color | Right click to save color")
                else:
                    help_label.config(text="Left click to save color | Right click to apply color")
                    
            mouse_btn = tk.Button(sc_top, text="R", font=("Arial", 10, "bold"), width=2, 
                                relief="sunken", bg="#d9d9d9", activebackground="#d9d9d9",
                                command=toggle_click_mode)
            mouse_btn.pack(side="right", padx=(4, 0))
            
            # Help text label that updates dynamically
            help_label = tk.Label(sc_frame, text="Left click to apply color | Right click to save color",
                                anchor="w", justify="left", fg="gray40")
            help_label.pack(fill="x", padx=6)
            
            def _sc_save():
                from tkinter import filedialog
                import json
                # Default to exports/colors/json directory for saved colors
                root_dir = getattr(app, "root_dir", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                default_dir = os.path.join(root_dir, "exports", "colors", "json")
    
                os.makedirs(default_dir, exist_ok=True)
                p = filedialog.asksaveasfilename(
                    defaultextension=".json", 
                    filetypes=[("JSON","*.json")], 
                    title="Save Colors",
                    initialdir=default_dir
                )
                
                # Bring live editor to front after file dialog
                app._bring_live_editor_to_front()
                
                if not p: return
                try:
                    # Create directory if it doesn't exist when actually saving
                    os.makedirs(os.path.dirname(p), exist_ok=True)
                    with open(p, "w", encoding="utf-8") as f:
                        json.dump(app._saved_colors, f)
                except Exception: pass
            def _sc_load():
                from tkinter import filedialog
                import json
                p = filedialog.askopenfilename(filetypes=[("JSON","*.json")], title="Load Colors")
                
                # Bring live editor to front after file dialog
                app._bring_live_editor_to_front()
                
                if not p: return
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    if isinstance(data, list) and all(isinstance(t,(list,tuple)) and len(t)==3 for t in data):
                        data = [tuple(int(x) for x in t) for t in data][:20]
                        if len(data) < 20:
                            data += [(0,0,0)]*(20-len(data))
                        app._saved_colors = data
                        _sc_refresh()
                except Exception: pass
            def _sc_clear():
                app._saved_colors = [(0,0,0)] * 20
                _sc_refresh()
            tk.Button(sc_top, text="Save", width=6, command=_sc_save).pack(side="left")
            tk.Button(sc_top, text="Load", width=6, command=_sc_load).pack(side="left", padx=(6,0))
            tk.Button(sc_top, text="Clear", width=6, command=_sc_clear).pack(side="left", padx=(6,0))
    
            sc_grid = tk.Frame(sc_frame); sc_grid.pack(padx=2, pady=(0,2))
            app._sc_btns = []
            def _sc_refresh():
                app._sc_refresh_live = _sc_refresh
                for i, canvas in enumerate(app._sc_btns):
                    r,g,b = app._saved_colors[i]
                    try: 
                        if (r, g, b) == (0, 0, 0) and getattr(app, 'dark_mode', False):
                            hex_color = "#FFFFFF"
                        else:
                            hex_color = f"#{r:02x}{g:02x}{b:02x}"
                        canvas.delete("all")
                        canvas.create_rectangle(0, 0, 30, 30, fill=hex_color, outline="black")
                    except Exception: pass
                if hasattr(app, '_sc_refresh_main') and not getattr(app, '_syncing', False):
                    try:
                        app._syncing = True
                        app._sc_refresh_main()
                        app._syncing = False
                    except Exception:
                        app._syncing = False
            def _sc_put(slot):
                ly = app._live_current_layer() if hasattr(app, "_live_current_layer") else None
                if ly is None: return
                idx = getattr(app, "_live_selected_index", 0)
                try: r,g,b = ly.colors[idx]
                except Exception: r=g=b=0
                app._saved_colors[slot] = (int(r),int(g),int(b))
                _sc_refresh()
            def _sc_pick(slot):
                r,g,b = app._saved_colors[slot]
                ly = app._live_current_layer() if hasattr(app, "_live_current_layer") else None
                if ly is None: return
                idx = getattr(app, "_live_selected_index", 0)
                ly.colors[idx] = (int(r),int(g),int(b))
                try: 
                    # Update swatch based on mode
                    if app.live_pal_ui_mode == "Simple":
                        # Find the display index for this palette index
                        editable_indices = app._get_editable_color_indices()
                        if idx in editable_indices:
                            display_idx = editable_indices.index(idx)
                            if display_idx < len(app._live_swatches) and app._live_swatches[display_idx] is not None:
                                canvas = app._live_swatches[display_idx]
                                hex_color = f"#{r:02x}{g:02x}{b:02x}"
                                canvas.delete("all")
                                canvas.create_rectangle(1, 1, 39, 39, fill=hex_color, outline="black", width=1)
                    else:
                        # Advanced mode: direct index mapping
                        if idx < len(app._live_swatches) and app._live_swatches[idx] is not None:
                            canvas = app._live_swatches[idx]
                            hex_color = f"#{r:02x}{g:02x}{b:02x}"
                            is_dark = getattr(app, 'dark_mode', False)
                            outline_color = "#555555" if is_dark else "black"
                            canvas.delete("all")
                            canvas.create_rectangle(1, 1, 19, 19, fill=hex_color, outline=outline_color, width=1)
                except Exception: pass
                try: app._picker_preview.config(bg=f"#{r:02x}{g:02x}{b:02x}")
                except Exception: pass
                try:
                    app._picker_hex.delete(0,"end"); app._picker_hex.insert(0,f"#{r:02x}{g:02x}{b:02x}")
                except Exception: pass
                if hasattr(app, "_sync_hsv_from_rgb"): app._sync_hsv_from_rgb(int(r),int(g),int(b))
                if hasattr(app, "_debounced_display_update"): app._debounced_display_update()
                
                # Update simple mode preview if in simple mode
                if app.live_pal_ui_mode == "Simple" and hasattr(app, '_update_simple_preview'):
                    app._update_simple_preview()
                
                # Track statistics: saved color applied
                if hasattr(app, 'statistics'):
                    app.statistics.track_index_modification(idx)
            def _handle_click(event, slot):
                """Handle click based on current mode"""
                is_right_click = (event.num == 3) or (event.num == 2) # Support both Win/Linux and Mac
                is_save = is_right_click if getattr(app, 'use_right_click', True) else not is_right_click
                if is_save:
                    _sc_put(slot)
                else:
                    _sc_pick(slot)
                    
            for i in range(20):
                # Create 30x30 pixel buttons using Canvas for exact size control (smaller for live editor)
                canvas = tk.Canvas(sc_grid, width=30, height=30, highlightthickness=1, highlightbackground="#888888")
                canvas.grid(row=i//10, column=i%10, padx=1, pady=1)  # Reduced padding
                
                # Draw the color rectangle
                color = app._saved_colors[i]
                if color == (0, 0, 0) and getattr(app, 'dark_mode', False):
                    hex_color = "#FFFFFF"
                else:
                    hex_color = f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"
                canvas.create_rectangle(0, 0, 30, 30, fill=hex_color, outline="black")
                
                # Bind click events
                canvas.bind("<Button-1>", lambda e, j=i: _handle_click(e, j))
                canvas.bind("<Button-3>", lambda e, j=i: _handle_click(e, j))
                app._sc_btns.append(canvas)
                
            _sc_refresh()
    
            # Close button directly under saved colors
            close_frame = tk.Frame(panel)
            close_frame.grid(row=10, column=0, columnspan=7, sticky="we", pady=(10,0))
            tk.Button(close_frame, text="Close", command=on_window_close, width=12).pack()
    
            def _clamp_int(val, lo, hi, default=0):
                try:
                    n = int(float(val))
                except Exception:
                    n = default
                return max(lo, min(hi, n))
    
            def _apply_hsv_entries(*_):
                H = _clamp_int(app._hsv_h_str.get(), 0, 360, 0)
                S = _clamp_int(app._hsv_s_str.get(), 0, 100, 0)
                V = _clamp_int(app._hsv_v_str.get(), 0, 100, 0)
                if not hasattr(app, "_in_sync"): app._in_sync = False
                if app._in_sync: return
                app._in_sync = True
                try:
                    if not getattr(app, "_is_dragging", False):
                        app._picker_h.set(H)
                        app._picker_s.set(S)
                        app._picker_v.set(V)
                finally:
                    app._in_sync = False
                try:
                    app._hsv_debounced_change()
                except Exception:
                    pass
    
            for w in (eH, eS, eV):
                w.bind("<Return>", lambda _e: _apply_hsv_entries())
                w.bind("<FocusOut>", lambda _e: _apply_hsv_entries())
    
            app._picker_preview = tk.Label(panel, text="            ", relief="sunken")
            app._picker_preview.grid(row=8, column=0, columnspan=4, sticky="we", pady=(2,0))
    
            app._live_select_index(0)  # seed picker
            app._live_window = app._live_editor_window
            app._update_selection_ui()
            
            # Center the live editor window after content is created
            app._live_editor_window.update_idletasks()
            app._center_window_on_parent(app._live_editor_window, app.master)
            
            # Update icon editor button state based on current palette type
            app._update_icon_editor_button_state()
            
            # Apply dark mode theme to the entire live editor window
            from code.utils.theme_manager import ThemeManager
            ThemeManager.apply_theme(app, app._live_editor_window)
    
        def _create_advanced_palette_grid(app, grid, ly):
            """Create the traditional 16x16 palette grid showing all 256 colors"""
            is_dark = getattr(app, 'dark_mode', False)
            for i in range(PALETTE_SIZE):
                r,g,b = ly.colors[i] if isinstance(ly.colors[i], tuple) else (0,0,0)
                # Create canvas-based swatch for better border control
                canvas = tk.Canvas(grid, width=20, height=20, highlightthickness=0, relief="flat", bg="#1E1E1E" if is_dark else "white")
                canvas.grid(row=i//16, column=i%16, padx=1, pady=1)  # Reduced padding
                
                # Draw the color rectangle
                hex_color = f"#{r:02x}{g:02x}{b:02x}"
                outline_color = "#555555" if is_dark else "black"
                canvas.create_rectangle(1, 1, 19, 19, fill=hex_color, outline=outline_color, width=1)
                
                # Left-click with optional Shift
                canvas.bind("<Button-1>", lambda e, i=i: app._live_on_swatch_click(i, e))
                canvas.bind("<Button-3>", lambda e, i=i: app._live_on_swatch_click(i, e))
                app._live_swatches.append(canvas)
    
        def _create_simple_palette_grid(app, grid, ly):
            """Create a simplified palette grid showing only editable colors like the icon editor"""
            # Get editable color indices for the specified layer only
            editable_indices = app._get_editable_color_indices(ly)
            
            if not editable_indices:
                # Fallback to showing all colors if we can't determine editable ones
                app._create_advanced_palette_grid(grid, ly)
                return
            
            # Create a mapping from display position to actual palette index
            app._simple_index_mapping = {}
            
            # Check if we already have a PanedWindow from previous simple mode usage
            existing_paned = None
            existing_main_container = None
            
            for child in grid.winfo_children():
                if isinstance(child, tk.Frame):
                    for subchild in child.winfo_children():
                        if isinstance(subchild, tk.PanedWindow):
                            existing_paned = subchild
                            existing_main_container = child
                            break
                    if existing_paned:
                        break
            
            if existing_paned and existing_main_container:
                # Reuse existing PanedWindow to prevent flash
                paned_window = existing_paned
                main_container = existing_main_container
                
                # Clear only the contents of the paned window, not the paned window itself
                for pane in paned_window.panes():
                    paned_window.forget(pane)
            else:
                # Create new layout for first time
                for child in grid.winfo_children():
                    child.destroy()
                
                # Create main container with resizable paned window
                main_container = tk.Frame(grid)
                main_container.pack(fill="both", expand=True)
                
                # Create PanedWindow for resizable divider between palette and preview
                paned_window = tk.PanedWindow(main_container, orient="vertical", sashwidth=5, sashrelief="raised", 
                                             sashpad=1, bd=1, relief="sunken")
                paned_window.pack(fill="both", expand=True)
            
            # Top part: Palette grid with scrollbar (compact height)
            palette_frame = tk.Frame(paned_window)
            palette_frame.configure(height=90)  # Initial height for palette area
            paned_window.add(palette_frame, minsize=60)  # Minimum size to keep palette visible
            
            # Create scrollable palette area
            palette_canvas_frame = tk.Frame(palette_frame)
            palette_canvas_frame.pack(fill="both", expand=True)
            
            # Create scrollbar for palette
            palette_scrollbar = ttk.Scrollbar(palette_canvas_frame, orient="vertical")
            palette_scrollbar.pack(side="right", fill="y")
            
            # Create canvas for palette
            palette_canvas = tk.Canvas(palette_canvas_frame, yscrollcommand=palette_scrollbar.set)
            palette_canvas.pack(side="left", fill="both", expand=True)
            palette_scrollbar.config(command=palette_canvas.yview)
            
            # Create frame inside canvas for the color squares
            squares_frame = tk.Frame(palette_canvas)
            canvas_window = palette_canvas.create_window((0, 0), window=squares_frame, anchor="nw")
            
            # Make the frame expand to fill canvas width
            def _on_canvas_configure(event):
                palette_canvas.itemconfig(canvas_window, width=event.width)
            palette_canvas.bind("<Configure>", _on_canvas_configure)
            
            # Fixed layout: 8 boxes per row
            cols = 8
            square_size = 40  # 2x larger than advanced mode (20x20)
            padding = 2
            
            for display_idx, palette_idx in enumerate(editable_indices):
                row = display_idx // cols
                col = display_idx % cols
                
                r, g, b = ly.colors[palette_idx] if isinstance(ly.colors[palette_idx], tuple) else (0, 0, 0)
                
                # Create canvas for color square (same size as advanced mode)
                color_canvas = tk.Canvas(squares_frame, width=square_size, height=square_size, 
                                       highlightthickness=0, relief="flat")
                color_canvas.grid(row=row, column=col, padx=padding, pady=padding)
                
                # Draw the color rectangle
                hex_color = f"#{r:02x}{g:02x}{b:02x}"
                color_canvas.create_rectangle(1, 1, square_size-1, square_size-1, fill=hex_color, outline="black", width=1)
                
                # Bind click events - use the actual palette index
                color_canvas.bind("<Button-1>", lambda e, i=palette_idx: app._on_simple_palette_click(i, e))
                
                # Store mapping
                app._simple_index_mapping[display_idx] = palette_idx
                app._live_swatches.append(color_canvas)
            
            # Configure scroll region for palette
            squares_frame.update_idletasks()
            palette_canvas.configure(scrollregion=palette_canvas.bbox("all"))
            
            # Bind mousewheel to palette canvas
            def _on_palette_mousewheel(event):
                try:
                    if palette_canvas.winfo_exists():
                        palette_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
                except tk.TclError:
                    # Canvas has been destroyed, ignore the event
                    pass
            palette_canvas.bind_all("<MouseWheel>", _on_palette_mousewheel)
            
            # Bottom part: Live preview (remaining space) - added to PanedWindow
            preview_frame = tk.Frame(paned_window, bg="white")
            paned_window.add(preview_frame, minsize=100)  # Minimum size to keep preview visible
            
            # Set sash position - only on very first creation
            
            # Set sash position - only for new PanedWindow or when we have stored position to restore
            is_rebuilding = getattr(app, '_is_rebuilding_grid', False)
            has_stored_position = hasattr(app, '_stored_sash_position') and app._stored_sash_position is not None
            is_existing_paned = existing_paned is not None
            
            
            # Only position if it's a new PanedWindow or if we're reusing one and have a stored position
            if (not is_existing_paned) or (is_existing_paned and has_stored_position):
                if not is_existing_paned:
                    app._simple_sash_position_set = True
                
                def set_sash_position():
                    try:
                        
                        # Get the total height of the paned window
                        total_height = paned_window.winfo_height()
                        
                        if total_height > 1:  # Window is configured
                            # Use stored position if available, otherwise use 1/3 from top
                            if hasattr(app, '_stored_sash_position') and app._stored_sash_position is not None:
                                target_position = app._stored_sash_position
                            else:
                                target_position = total_height // 3
                            
                            paned_window.sash_place(0, 0, target_position)
                        else:
                            # Window not yet configured, try again later (but only once more)
                            retry_key = f'_simple_sash_retry_count_{id(paned_window)}'
                            if not hasattr(app, retry_key):
                                setattr(app, retry_key, 1)
                                main_container.after(100, set_sash_position)
                            else:
                                pass  # Already retried, give up
                    except Exception as e:
                        pass  # Error in sash placement
                
                # Schedule the sash positioning after the window is fully rendered
                main_container.after(100, set_sash_position)
            else:
                pass  # Skip sash positioning
            
            # Create preview controls at the top of preview frame
            preview_controls = tk.Frame(preview_frame)
            preview_controls.pack(fill="x", padx=5, pady=5)
            
            # Navigation buttons
            nav_frame = tk.Frame(preview_controls)
            nav_frame.pack(side="left")
            
            app._simple_prev_btn = tk.Button(nav_frame, text="◀", command=app._simple_prev_frame, width=3)
            app._simple_prev_btn.pack(side="left", padx=(0, 2))
            
            app._simple_next_btn = tk.Button(nav_frame, text="▶", command=app._simple_next_frame, width=3)
            app._simple_next_btn.pack(side="left")
            
            # Frame info label
            app._simple_frame_label = tk.Label(preview_controls, text="Frame 1")
            app._simple_frame_label.pack(side="left", padx=(10, 5))
            
            # Helper instruction
            tk.Label(preview_controls, text="(click preview to select index)", font=("Arial", 8)).pack(side="left")
            
            # Zoom controls
            zoom_frame = tk.Frame(preview_controls)
            zoom_frame.pack(side="right")
            
            tk.Label(zoom_frame, text="Zoom:").pack(side="left")
            app._simple_zoom_var = tk.StringVar(value="100%")
            app._simple_zoom_combo = ttk.Combobox(zoom_frame, textvariable=app._simple_zoom_var,
                                                 values=["100%", "200%", "300%", "400%", "500%", "Fit"], state="readonly", width=8)
            app._simple_zoom_combo.pack(side="left", padx=(5, 0))
            app._simple_zoom_combo.bind("<<ComboboxSelected>>", app._simple_on_zoom_change)
            
            # Create canvas for the preview image that fills the available space
            app._simple_preview_canvas = tk.Canvas(preview_frame, bg="white", highlightthickness=1, highlightbackground="gray")
            app._simple_preview_canvas.pack(fill="both", expand=True, padx=5, pady=5)
            
            # Bind resize event to update canvas dimensions for click handling
            app._simple_preview_canvas.bind("<Configure>", app._on_simple_canvas_configure)
            
            # Initialize panning state variables
            app._simple_pan_start_x = 0
            app._simple_pan_start_y = 0
            app._simple_pan_offset_x = 0
            app._simple_pan_offset_y = 0
            app._simple_is_panning = False
            app._simple_click_moved = False
            
            # Bind click event to preview for color selection and panning
            app._simple_preview_canvas.bind("<Button-1>", app._on_simple_preview_click)
            app._simple_preview_canvas.bind("<B1-Motion>", app._on_simple_preview_drag)
            app._simple_preview_canvas.bind("<ButtonRelease-1>", app._on_simple_preview_release)
            
            # Add middle mouse button panning (simpler version using same handlers)
            app._simple_preview_canvas.bind("<Button-2>", app._on_simple_preview_middle_click)
            app._simple_preview_canvas.bind("<B2-Motion>", app._on_simple_preview_drag)
            app._simple_preview_canvas.bind("<ButtonRelease-2>", app._on_simple_preview_release)
            
            # Change cursor to indicate clickability
            app._simple_preview_canvas.bind("<Enter>", lambda e: app._simple_preview_canvas.configure(cursor="hand2"))
            app._simple_preview_canvas.bind("<Leave>", lambda e: app._simple_preview_canvas.configure(cursor=""))
    
            # Bind mousewheel to preview canvas for Zoom
            def _on_simple_preview_mousewheel(event):
                 try:
                     app._cycle_zoom(event.delta, app._simple_zoom_var, lambda: app._simple_zoom_combo.event_generate("<<ComboboxSelected>>"))
                     return "break"
                 except:
                     pass
            app._simple_preview_canvas.bind("<MouseWheel>", _on_simple_preview_mousewheel)
            
            # Store reference to current preview image
            app._simple_current_image = None
            # Initialize to the current frame from the main UI
            app._simple_current_frame = getattr(app, 'current_image_index', 0)
            
            # Update the preview
            app._update_simple_preview()
            
            # Add keyboard bindings for simple mode navigation
            def _on_simple_key(event):
                if event.keysym == "Left":
                    app._simple_prev_frame()
                elif event.keysym == "Right":
                    app._simple_next_frame()
            
            # Bind arrow keys to the live editor window
            if hasattr(app, '_live_editor_window') and app._live_editor_window:
                app._live_editor_window.bind("<Left>", _on_simple_key)
                app._live_editor_window.bind("<Right>", _on_simple_key)
                app._live_editor_window.focus_set()  # Make sure window can receive key events
            
            # Fill remaining positions with None to maintain structure
            while len(app._live_swatches) < PALETTE_SIZE:
                app._live_swatches.append(None)
    
        def _on_simple_palette_click(app, palette_idx, event):
            """Handle palette square clicks - either for selection or colorpicking."""
            if app.colorpicker_active:
                app._colorpick_from_simple_palette(palette_idx)
            else:
                app._live_on_swatch_click(palette_idx, event)
    
        def _rebuild_live_palette_grid(app):
            """Rebuild the palette grid when UI mode changes"""
            if not hasattr(app, '_live_editor_window') or not app._live_editor_window or not app._live_editor_window.winfo_exists():
                return
            
            # Set flag to indicate this is a rebuild, not initial creation
            app._is_rebuilding_grid = True
                
            # Clear current selection and existing swatches
            app._selected_indices.clear()
            app._last_clicked_index = None
            
            # Destroy existing swatches
            for canvas in app._live_swatches:
                try:
                    if canvas is not None:
                        canvas.destroy()
                except:
                    pass
            app._live_swatches.clear()
            
            # Find the grid frame (it's the first Frame child of body)
            grid = None
            for child in app._live_editor_window.winfo_children():
                if isinstance(child, tk.Frame):  # This is the body frame
                    for subchild in child.winfo_children():
                        if isinstance(subchild, tk.Frame) and subchild.grid_info():  # This is the grid frame
                            grid = subchild
                            break
                    if grid:
                        break
            
            if grid:
                # Get current layer
                ly = app._live_current_layer()
                if ly is None:
                    return
                
                # Create grid based on current mode
                if app.live_pal_ui_mode == "Simple":
                    app._create_simple_palette_grid(grid, ly)
                else:
                    app._create_advanced_palette_grid(grid, ly)
                
                # Reset selection to first index
                app._live_select_index(0)
                app._update_selection_ui()
                
                # Update simple mode preview if in simple mode
                if app.live_pal_ui_mode == "Simple" and hasattr(app, '_update_simple_preview'):
                    app._update_simple_preview()
            
            # Clear the rebuild flag
            app._is_rebuilding_grid = False
    
        def _update_simple_palette_colors(app, ly):
            """Update only the colors in simple mode without rebuilding the entire UI"""
            # Set flag to prevent color changes during palette switching
            app._updating_live_selection = True
            
            # Get editable indices for the new layer
            editable_indices = app._get_editable_color_indices(ly)
            
            if not editable_indices:
                return
            
            # Update existing swatches with new colors
            if hasattr(app, '_live_swatches') and app._live_swatches:
                # Clear existing swatches first
                for canvas in app._live_swatches:
                    if canvas is not None:
                        try:
                            canvas.destroy()
                        except:
                            pass
                app._live_swatches.clear()
                
                # Find the existing palette squares frame
                squares_frame = None
                try:
                    if hasattr(app, '_live_editor_window') and app._live_editor_window:
                        def find_squares_frame(widget):
                            # Look for the specific Frame that's inside a Canvas (scrollable palette area)
                            # The palette squares frame is created inside a Canvas for scrolling
                            if isinstance(widget, tk.Canvas):
                                # Check if this canvas has a window (our squares frame)
                                try:
                                    for item in widget.find_all():
                                        item_type = widget.type(item)
                                        if item_type == "window":
                                            # Get the widget from the window item
                                            window_widget = widget.nametowidget(widget.itemcget(item, "window"))
                                            if isinstance(window_widget, tk.Frame):
                                                return window_widget
                                except:
                                    pass
                            
                            # Check children
                            try:
                                for child in widget.winfo_children():
                                    result = find_squares_frame(child)
                                    if result:
                                        return result
                            except:
                                pass
                            return None
                        
                        squares_frame = find_squares_frame(app._live_editor_window)
                except Exception as e:
                    pass  # Error finding squares frame
                
                if squares_frame:
                    
                    # Clear existing squares in the frame
                    child_count = 0
                    for child in squares_frame.winfo_children():
                        try:
                            child.destroy()
                            child_count += 1
                        except:
                            pass
                    
                    # Recreate squares with new colors
                    cols = 8
                    square_size = 40
                    padding = 2
                    
                    created_count = 0
                    for display_idx, palette_idx in enumerate(editable_indices):
                        row = display_idx // cols
                        col = display_idx % cols
                        
                        r, g, b = ly.colors[palette_idx] if isinstance(ly.colors[palette_idx], tuple) else (0, 0, 0)
                        
                        # Create canvas for color square
                        color_canvas = tk.Canvas(squares_frame, width=square_size, height=square_size, 
                                               highlightthickness=0, relief="flat")
                        color_canvas.grid(row=row, column=col, padx=padding, pady=padding)
                        
                        # Draw the color rectangle
                        hex_color = f"#{r:02x}{g:02x}{b:02x}"
                        color_canvas.create_rectangle(1, 1, square_size-1, square_size-1, fill=hex_color, outline="black", width=1)
                        
                        # Bind click events - use the actual palette index
                        color_canvas.bind("<Button-1>", lambda e, i=palette_idx: app._live_on_swatch_click(i, e))
                        
                        # Store mapping
                        if not hasattr(app, '_simple_index_mapping'):
                            app._simple_index_mapping = {}
                        app._simple_index_mapping[display_idx] = palette_idx
                        app._live_swatches.append(color_canvas)
                        created_count += 1
                    
                    
                    # Update the scroll region
                    try:
                        squares_frame.update_idletasks()
                        # Find the parent canvas to update scroll region
                        parent = squares_frame.winfo_parent()
                        if parent:
                            parent_widget = squares_frame.nametowidget(parent)
                            if isinstance(parent_widget, tk.Canvas):
                                parent_widget.configure(scrollregion=parent_widget.bbox("all"))
                    except Exception as e:
                        pass  # Error updating scroll region
                else:
                    app._rebuild_live_palette_grid()
            
                # Fill remaining positions with None to maintain structure
                while len(app._live_swatches) < 256:  # PALETTE_SIZE
                    app._live_swatches.append(None)
    
        def _live_select_index(app, i):
            i = int(i)
            # Don't update if it's the same index (prevents double-click issues)
            if hasattr(app, '_live_selected_index') and app._live_selected_index == i:
                return
                
            # Track index selection
            app.statistics.indexes_selected += 1
            app.statistics.preview_indexes_selected['live_pal'] += 1
            app._save_statistics()
                
            app._live_selected_index = i
            app._picker_idx_var.set(str(i))
            ly = app._live_current_layer()
            if ly is None:
                return
            r,g,b = ly.colors[i] if isinstance(ly.colors[i], tuple) else (0,0,0)
            # Update HEX + preview
            app._picker_hex.delete(0, "end"); app._picker_hex.insert(0, f"#{int(r):02x}{int(g):02x}{int(b):02x}")
            app._picker_preview.config(bg=f"#{int(r):02x}{int(g):02x}{int(b):02x}")
            # Sync HSV sliders from this RGB
            app._sync_hsv_from_rgb(int(r), int(g), int(b))
    
        def _live_goto_index(app):
            try:
                i = int(app._picker_idx_var.get())
            except Exception:
                i = 0
            i = max(0, min(255, i))
            app._live_select_index(i)
    
        def _live_save_item_pal(app, layer=None):
            from tkinter import messagebox
            
            if layer:
                ly = layer
            else:
                ly = app._live_current_layer()
                
            if ly is None:
                return
            colors = ly.colors
            default_name = os.path.splitext(ly.name)[0] + ".pal"
            
            # Set initial directory to exports/custom_pals/fashion
            root_dir = getattr(app, "root_dir", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            initial_dir = os.path.join(root_dir, "exports", "custom_pals", "fashion")
            os.makedirs(initial_dir, exist_ok=True)
            
            path = filedialog.asksaveasfilename(
                title="Save Item .pal", 
                defaultextension=".pal",
                initialfile=default_name, 
                initialdir=initial_dir,
                filetypes=[("VGA 24-bit Palette Files","*.pal")]
            )
            if not path:
                return
                
            try:
                # First save the palette file
                # Ensure we have exactly 256 colors for VGA palette
                vga_colors = list(colors)
                while len(vga_colors) < 256:
                    vga_colors.append((0, 0, 0))  # Fill with black if needed
                
                # Restore colors outside allowed indices from the vanilla palette, and preserve keying colors
                if hasattr(ly, 'palette_type') and ly.palette_type:
                    char_num = app.current_character[3:] if hasattr(app, 'current_character') and app.current_character else None
                    if char_num:
                        allowed_indices = app.get_allowed_indices_for_palette(ly, char_num)
                        if allowed_indices:
                            orig_colors = None
                            if hasattr(app, '_live_original_colors') and app._live_original_colors.get(ly.name):
                                orig_colors = app._live_original_colors[ly.name]
                                
                            for i in range(256):
                                is_outside = i not in allowed_indices and not (ly.palette_type == 'fashion_4' and char_num == '020')
                                
                                if orig_colors and i < len(orig_colors):
                                    orig_color = orig_colors[i]
                                    if is_outside:
                                        # Outside bounds: ALWAYS migrate exactly from vanilla pal
                                        vga_colors[i] = orig_color
                                    else:
                                        # Inside bounds: if the original was a keying color, preserve it for game engine transparency
                                        is_orig_key = False
                                        if getattr(ly, 'palette_type', '') == "hair":
                                            pass
                                        elif getattr(ly, 'palette_type', '').startswith("fashion_"):
                                            from code.core.color_translator import ColorTranslator
                                            is_orig_key = ColorTranslator.is_fashion_palette_keying_color(app, ly, orig_color, i)
                                        else:
                                            is_orig_key = app.is_green_padding(orig_color) or app.is_magenta_transparency(orig_color)
                                        
                                        if is_orig_key:
                                            vga_colors[i] = orig_color
                                elif is_outside:
                                    # Fallback if we don't have the original vanilla palette loaded
                                    vga_colors[i] = (0, 255, 0)
                
                # Write VGA 24-bit format: each color as 3 bytes (R, G, B) in sequence
                non_keyed_count = 0
                with open(path, "wb") as f:
                    for r,g,b in vga_colors[:256]:  # Ensure exactly 256 colors
                        f.write(bytes([r,g,b]))
                        # Count non-keying colors (not magenta)
                        if (r,g,b) != (255,0,255):
                            non_keyed_count += 1
                # Custom saved dialog with Generate XML button
                saved_dialog = tk.Toplevel(app.master)
                saved_dialog.title("Saved")
                saved_dialog.geometry("350x120")
                saved_dialog.resizable(False, False)
                saved_dialog.transient(app.master)
                saved_dialog.grab_set()
                
                saved_dialog.update_idletasks()
                pw, ph = app.master.winfo_width(), app.master.winfo_height()
                px, py = app.master.winfo_x(), app.master.winfo_y()
                dw, dh = 350, 120
                saved_dialog.geometry(f"{dw}x{dh}+{px + (pw - dw)//2}+{py + (ph - dh)//2}")
                
                tk.Label(saved_dialog, text=f"Saved VGA 24-bit palette {os.path.basename(path)}\nfor {getattr(ly, 'name', 'layer')}").pack(pady=15)
                
                btn_frame = tk.Frame(saved_dialog)
                btn_frame.pack(pady=5)
                
                def _open_xml():
                    saved_dialog.destroy()
                    app.open_xml_generator_dialog()
                    
                tk.Button(btn_frame, text="Generate XML", command=_open_xml).pack(side=tk.LEFT, padx=10)
                tk.Button(btn_frame, text="OK", command=saved_dialog.destroy).pack(side=tk.LEFT, padx=10)
                
                from code.utils.theme_manager import ThemeManager
                ThemeManager.apply_theme(app, saved_dialog)
                
                # We do not wait_window so the rest of the stats can track immediately
                
                # Track statistics
                app.statistics.indexes_saved_in_pals += non_keyed_count
                app.statistics.live_palette_files_saved.add(path)
                if hasattr(app, 'current_character') and hasattr(app, 'current_job'):
                    key = f"{app.current_character}_{app.current_job}"
                    if key in app.statistics.character_edits:
                        app.statistics.character_edits[key]['palette_saves'] += 1
                app._save_statistics()
                
                # Mark this layer as saved so we don't restore its original colors when closing
                if hasattr(app, '_live_saved_layers'):
                    layer_name = getattr(ly, 'name', '')
                    app._live_saved_layers.add(layer_name)
                    
                # Update temp cache with saved colors
                if hasattr(app, '_live_temp_palette_cache'):
                    current_name = None
                    # Safely get current name from live editor UI if it exists
                    if hasattr(app, '_live_target_name') and app._live_target_name:
                        try:
                            current_name = app._live_target_name.get()
                        except:
                            pass
                    
                    if current_name:
                        app._live_temp_palette_cache[current_name] = ly.colors.copy()
                    
                # Track palette save in statistics
                if hasattr(app, 'current_character'):
                    current_job = app.job_var.get() if hasattr(app, 'job_var') else None
                    if current_job:
                        app.statistics.live_palette_files_saved.add(path)
                        key = (app.current_character, current_job)
                        if key in app.statistics.character_edits:
                            app.statistics.character_edits[key]['palette_saves'] += 1
                        app._save_statistics()
                
                # Check if this is a hair or 3rd job palette - if so, skip the dialog entirely
                if hasattr(ly, 'palette_type'):
                    palette_type = str(ly.palette_type).lower()
                    if palette_type in ("hair", "3rd_job_base"):
                        # Skip the post-save dialog for hair and 3rd job palettes
                        icon_choice = "no"  # Act as if user clicked "No I'm good"
                    else:
                        icon_choice = app._ask_icon_save_choice(path, ly)
                else:
                    icon_choice = app._ask_icon_save_choice(path, ly)
                # Note: "quicksave" and "saveportrait" are handled within the dialog
                if icon_choice == "openeditor":
                    # Extract character ID and item name from the layer
                    char_match = re.search(r'(?:chr)?(\d{3})', ly.name)
                    if char_match:
                        num = char_match.group(1)
                        char_id = f"chr{num}"  # Normalize to chr format
                        
                        # Get the fashion type from the layer
                        fashion_type = getattr(ly, "palette_type", "")
                        if fashion_type:
                            # Read the newly saved palette
                            try:
                                with open(path, 'rb') as f:
                                    saved_pal_data = f.read()
                                
                                # Convert to RGB tuples
                                saved_palette = []
                                for i in range(0, len(saved_pal_data), 3):
                                    r = saved_pal_data[i]
                                    g = saved_pal_data[i+1]
                                    b = saved_pal_data[i+2]
                                    saved_palette.append((r, g, b))
                                
                                print(f"\\nRead saved palette from: {path}")
                                print(f"Found {len(saved_palette)} colors")
                                
                                # Open the icon palette editor
                                from icon_handler import IconPaletteEditor
                                # Create icon handler and set main window reference
                                from icon_handler import IconHandler
                                icon_handler = IconHandler()
                                icon_handler.main_window = app
                                
                                editor = IconPaletteEditor(
                                    char_id=char_id,
                                    fashion_type=fashion_type,
                                    custom_palette=saved_palette,
                                    palette_path=path,
                                    palette_layers=None,  # Don't pass palette layers to avoid refresh issues
                                    live_editor_window=app._live_editor_window,
                                    is_quicksave_mode=False,  # Editor mode - allow user to name file
                                    icon_handler=icon_handler,
                                    ui_mode=getattr(app, 'live_pal_ui_mode', 'Simple')
                                )
                                # Bring the icon editor to the front after creation
                                editor._bring_to_front()
                            except Exception as e:
                                print(f"CONSOLE ERROR MSG: Error reading saved palette: {e}")
                                messagebox.showerror("Error", f"Failed to open icon editor: {e}")
                
                # Only bring the PAL editor window to the front if we didn't open the icon editor
                # And only if the window actually exists
                if icon_choice != "openeditor":
                    app._bring_live_editor_to_front()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save: {e}")
                # Bring live editor to front even on error
                app._bring_live_editor_to_front()
    
        def _open_live_pal_settings_menu(app):
            """Open settings menu for Live Pal Editor UI mode selection."""
            if not app._live_editor_window or not app._live_editor_window.winfo_exists():
                return
            
            # Create settings menu window
            settings_window = tk.Toplevel(app._live_editor_window)
            settings_window.title("Live Pal Editor Settings")
            settings_window.resizable(False, False)
            settings_window.transient(app._live_editor_window)
            from code.utils.theme_manager import ThemeManager
            ThemeManager.apply_theme(app, settings_window)
            settings_window.grab_set()
            
            # Center the window
            settings_window.update_idletasks()
            width = 300
            height = 150
            x = app._live_editor_window.winfo_x() + (app._live_editor_window.winfo_width() - width) // 2
            y = app._live_editor_window.winfo_y() + (app._live_editor_window.winfo_height() - height) // 2
            settings_window.geometry(f"{width}x{height}+{x}+{y}")
            
            # Main frame
            main_frame = tk.Frame(settings_window, padx=15, pady=15)
            main_frame.pack(fill=tk.BOTH, expand=True)
            
            # Title
            tk.Label(main_frame, text="Palette Display Mode", font=("Arial", 10, "bold")).pack(pady=(0, 10))
            
            # UI mode selection
            ui_mode_var = tk.StringVar(value=app.live_pal_ui_mode)
            
            ttk.Radiobutton(main_frame, text="Simple (Filtered Colors)", variable=ui_mode_var, value="Simple").pack(anchor=tk.W, pady=2)
            ttk.Radiobutton(main_frame, text="Advanced (16x16 Grid - All 256 Colors)", variable=ui_mode_var, value="Advanced").pack(anchor=tk.W, pady=2)
            
            # Buttons
            button_frame = tk.Frame(main_frame)
            button_frame.pack(pady=(15, 0))
            
            def apply_settings():
                new_mode = ui_mode_var.get()
                if new_mode != app.live_pal_ui_mode:
                    app.live_pal_ui_mode = new_mode
                    app._save_live_pal_ui_mode_setting(new_mode)
                    # Close and reopen the Live Pal Editor to apply changes
                    settings_window.destroy()
                    # Store current state
                    current_target = app._live_target_name.get() if hasattr(app, '_live_target_name') else None
                    # Close current editor
                    if app._live_editor_window and app._live_editor_window.winfo_exists():
                        app._live_editor_window.destroy()
                        app._live_editor_window = None
                    # Reopen with new mode
                    app.open_live_palette_editor()
                    # Restore target if possible
                    if current_target and hasattr(app, '_live_target_name'):
                        try:
                            app._live_target_name.set(current_target)
                            app._live_on_target_changed(current_target)
                        except:
                            pass
                else:
                    settings_window.destroy()
            
            def cancel():
                settings_window.destroy()
            
            ttk.Button(button_frame, text="Apply", command=apply_settings).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="Cancel", command=cancel).pack(side=tk.LEFT, padx=5)
    
