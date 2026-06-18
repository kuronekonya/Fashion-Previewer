from fashionpreviewer import Tooltip
from icon_handler import CHARACTER_MAPPING
import re
import tkinter as tk
from tkinter import ttk
class MainPreviewer:
        def toggle_view_mode(app):
            """Toggle between Big Picture Mode and Small Preview Mode"""
            if app.view_mode == "big_picture":
                # Switch to Small Preview Mode
                app.view_mode = "small_preview"
                app.view_mode_button.config(text="Small Preview Mode")
                
                # Calculate new height based on active colors section
                # Start with 1/2 of current height, then subtract active colors height
                if hasattr(app, 'scroll_frame'):
                    current_height = app.scroll_frame.winfo_height()
                    if current_height > 0:
                        # Use 1/2 height minus the active colors section height
                        base_height = int(current_height * 1 / 2)
                        active_colors_h = getattr(app, 'active_colors_height', 100)
                        new_height = max(200, base_height - active_colors_h)  # Minimum 200px
                        app.scroll_frame.config(height=new_height)
                        
                        # Store the original height for restoration
                        app.original_scroll_height = current_height
                
                # Show the compact control bar
                app.compact_control_bar.pack(side="bottom", fill="x", pady=(5, 0))
                
                # Automatically show Saved Colors grid in Small Preview mode
                if hasattr(app, 'saved_colors_main_frame'):
                    app.paned.add(app.saved_colors_main_frame)
                
                # Ensure main button frame is always visible and on top
                if hasattr(app, 'main_button_frame'):
                    app.main_button_frame.lift()  # Raise to top of stacking order
                    app.main_button_frame.update_idletasks()  # Force update
                
            else:
                # Switch to Big Picture Mode
                app.view_mode = "big_picture"
                app.view_mode_button.config(text="Big Picture Mode")
                
                # Restore scroll frame to full height
                if hasattr(app, 'scroll_frame'):
                    app.scroll_frame.config(height=0)  # Let it expand naturally
                
                # Hide the compact control bar
                app.compact_control_bar.pack_forget()
                
                # Automatically hide Saved Colors grid in Big Picture mode
                if hasattr(app, 'saved_colors_main_frame'):
                    app.paned.forget(app.saved_colors_main_frame)
            
            # Update the display
            if hasattr(app, 'load_character_image'):
                app.load_character_image()
    

        def create_ui(app):
            """Create the main UI"""
            # List to store focusable widgets in order
            app.focusable_widgets = []
            app.widget_tags = {}
            
            
            # Bind keyboard shortcuts
            app.master.bind("b", lambda e: app.pick_background_color())
            app.master.bind("e", lambda e: app.export_background_bmp())
            app.master.bind("E", lambda e: app.export_all_frames())  # Shift+E
            app.master.bind("p", lambda e: app.open_live_palette_editor())
            app.master.bind("P", lambda e: app.export_pal())  # Shift+P
            app.master.bind("r", lambda e: app.reset_pals())
            app.master.bind("d", lambda e: app.debug_info())
            app.master.bind("v", lambda e: app.toggle_view_mode())
            app.master.bind("o", lambda e: app.open_custom_settings())
            
            
            # Set window size and make it resizable
            app.master.title("Fashion Previewer")
            app.master.geometry("1050x650")  # Original size was 900x650
            app.master.minsize(1050, 650)  # Original minimum size was 900x650
            app.master.resizable(True, True)
            
            # Center the window on screen
            app._center_window()
            
            # Main frame
            main_frame = tk.Frame(app.master)
            main_frame.pack(fill="both", expand=True, padx=10, pady=10)
            
            # Top section - Character and Job selection
            top_frame = tk.Frame(main_frame)
            top_frame.pack(fill="x", pady=(0, 10))
            
            # Character selection
            tk.Label(top_frame, text="Character:").pack(side="left")
            
            # Create unique character names (without job info)
            character_names = []
            # Sort characters numerically by their number
            def sort_char_key(char_id):
                # Extract the number from chr### format
                match = re.match(r'chr(\d+)', char_id)
                if match:
                    return int(match.group(1))
                return 0
            
            for char_id in sorted(app.available_characters, key=sort_char_key):
                if char_id in CHARACTER_MAPPING:
                    char_info = CHARACTER_MAPPING[char_id]
                    if char_info['name'] not in character_names:
                        character_names.append(char_info['name'])
                else:
                    if char_id not in character_names:
                        character_names.append(char_id)
            
            app.character_combo = ttk.Combobox(top_frame, textvariable=app.character_var, 
                                              values=character_names, state="readonly", width=15)
            app.character_combo.pack(side="left", padx=(5, 10))
            app.character_combo.bind("<<ComboboxSelected>>", lambda e: app.on_character_change())
            
            # Job selection
            tk.Label(top_frame, text="Job:").pack(side="left")
            app.job_combo = ttk.Combobox(top_frame, textvariable=app.job_var, 
                                        values=app.available_jobs, state="readonly", width=15)
            app.job_combo.pack(side="left", padx=(5, 10))
            app.job_combo.bind("<<ComboboxSelected>>", lambda e: app.on_job_change())
            
            # Zoom selection
            tk.Label(top_frame, text="Zoom:").pack(side="left")
    
            # Refresh assets (placed between Zoom and Preview)
    
            app.zoom_combo = ttk.Combobox(top_frame, textvariable=app.zoom_var, 
                                         values=["100%", "200%", "300%", "400%", "500%", "Fit"], state="readonly", width=10)
            app.zoom_combo.pack(side="left", padx=(5, 10))
            app.zoom_combo.bind("<<ComboboxSelected>>", lambda e: app.on_zoom_change())
            
    
            
            # Create a spacer frame to push preview section to the right
            spacer_frame = tk.Frame(top_frame)
            spacer_frame.pack(side="left", fill="x", expand=True)
            
            # Preview mode selection (right side)
            preview_frame = tk.Frame(top_frame)
            preview_frame.pack(side="right", padx=(0, 10))
            
            tk.Label(preview_frame, text="Preview:").pack(side="left")
            # Use saved preview mode from settings
            initial_preview_mode = getattr(app, 'last_preview_mode', 'single')
            app.preview_var = tk.StringVar(value=initial_preview_mode)
            tk.Radiobutton(preview_frame, text="Single", variable=app.preview_var, 
                          value="single", command=app.on_preview_mode_change).pack(side="left", padx=(5, 0))
            tk.Radiobutton(preview_frame, text="All", variable=app.preview_var, 
                          value="all", command=app.on_preview_mode_change).pack(side="left", padx=(5, 0))
            
            # Custom preview option with gear button
            custom_frame = tk.Frame(preview_frame)
            custom_frame.pack(side="left", padx=(5, 0))
            
            app.custom_var = tk.StringVar(value="custom")
            custom_radio = tk.Radiobutton(custom_frame, text="Custom", variable=app.preview_var, 
                                         value="custom", command=app.on_preview_mode_change)
            custom_radio.pack(side="left")
            
            # Dark Mode toggle button
            from code.utils.theme_manager import ThemeManager
            app.dark_mode_button = tk.Button(custom_frame, text="🌙", font=("Arial", 10), 
                                            command=lambda: ThemeManager.toggle_dark_mode(app), width=2, height=1)
            app.dark_mode_button.pack(side="left", padx=(2, 2))
            
            # Gear button for custom settings
            app.gear_button = tk.Button(custom_frame, text="⚙", font=("Arial", 10), 
                                       command=app.open_custom_settings, width=2, height=1)
            app.gear_button.pack(side="left", padx=(0, 0))
            
            # Main content area with image on left, controls on right
            content_frame = tk.Frame(main_frame)
            content_frame.pack(fill="both", expand=True, pady=(0, 10))
            
            # Image display area (left side)
            img_frame = tk.Frame(content_frame)
            img_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))
            
            # Scrollable canvas for image with both vertical and horizontal scrollbars
            # Create frame for scrollbars with border to ensure clipping
            app.scroll_frame = tk.Frame(img_frame, relief="solid", bd=1)
            app.scroll_frame.pack(fill="both", expand=True)
            
            # Vertical and Horizontal scrollbars
            app.v_scroll = tk.Scrollbar(app.scroll_frame, orient="vertical")
            app.v_scroll.pack(side="right", fill="y")
            
            app.h_scroll = tk.Scrollbar(app.scroll_frame, orient="horizontal")
            app.h_scroll.pack(side="bottom", fill="x")
            
            # Canvas with both scrollbars
            app.canvas = tk.Canvas(app.scroll_frame, 
                               yscrollcommand=app.v_scroll.set,
                               xscrollcommand=app.h_scroll.set,
                               highlightthickness=0,
                               bg="white")
            app.canvas.pack(side="left", fill="both", expand=True)
            
            # Configure scrollbars
            app.v_scroll.config(command=app.canvas.yview)
            app.h_scroll.config(command=app.canvas.xview)
            app.canvas.bind("<Configure>", app.on_canvas_configure)
            
            # Initialize panning state variables for main canvas
            app.canvas_pan_start_x = 0
            app.canvas_pan_start_y = 0
            app.canvas_is_panning = False
            
            # Add mouse wheel support
            def _on_mousewheel(event):
                # Check if we are in "All Preview" mode
                if app.preview_var.get() == "all":
                    # Scroll the canvas instead of zooming
                    app.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
                else:
                    # Use mousewheel for Zoom (standard behavior for single/custom)
                    app._cycle_zoom(event.delta, app.zoom_var, lambda: app.zoom_combo.event_generate("<<ComboboxSelected>>"))
                return "break"
            app.canvas.bind("<MouseWheel>", _on_mousewheel)  # Windows
            app.canvas.bind("<Button-4>", lambda e: _on_mousewheel(e))  # Linux
            app.canvas.bind("<Button-5>", lambda e: _on_mousewheel(e))   # Linux
            
            # Add middle mouse button panning
            def _on_canvas_pan_start(event):
                app.canvas_is_panning = True
                app.canvas_pan_start_x = event.x
                app.canvas_pan_start_y = event.y
                app.canvas.config(cursor="fleur")
            
            def _on_canvas_pan_drag(event):
                if app.canvas_is_panning:
                    delta_x = event.x - app.canvas_pan_start_x
                    delta_y = event.y - app.canvas_pan_start_y
                    
                    if delta_x != 0:
                        app.canvas.xview_scroll(-delta_x // 10, "units")
                    if delta_y != 0:
                        app.canvas.yview_scroll(-delta_y // 10, "units")
                        
                    app.canvas_pan_start_x = event.x
                    app.canvas_pan_start_y = event.y
            
            def _on_canvas_pan_release(event):
                app.canvas_is_panning = False
                app.canvas.config(cursor="")
            
            app.canvas.bind("<Button-2>", _on_canvas_pan_start)  # Middle mouse button
            app.canvas.bind("<B2-Motion>", _on_canvas_pan_drag)
            app.canvas.bind("<ButtonRelease-2>", _on_canvas_pan_release)
            
            app.img_id = None
            app.tk_image = None
            
            # Compact control bar for Small Preview Mode (hidden by default)
            # Set maximum height to prevent overlaying main buttons
            app.compact_control_bar = tk.Frame(img_frame, relief="raised", bd=2)
            app.compact_control_bar_max_height = 350  # Maximum total height for compact bar
            # Don't pack it yet - it will be shown/hidden by toggle_view_mode
            
            # Top row: Frame navigation and visibility controls (horizontal)
            frame_tools_row = tk.Frame(app.compact_control_bar)
            frame_tools_row.pack(side="top", fill="x", padx=5, pady=(5, 2))
            
            # Frame navigation arrows
            tk.Button(frame_tools_row, text="◀", command=app.prev_image, width=3).pack(side="left", padx=2)
            tk.Button(frame_tools_row, text="▶", command=app.next_image, width=3).pack(side="left", padx=2)
            
            # Toggle all frames visibility button
            app.toggle_all_frames_button = tk.Button(frame_tools_row, text="👁", 
                                                       command=app.toggle_all_frames_visibility, width=3)
            app.toggle_all_frames_button.pack(side="left", padx=2)
            Tooltip(app.toggle_all_frames_button, "Toggle All Frames' Visibility")
    
            # Undo button for frame visibility
            
            # Flip and Rotate buttons
            tk.Button(frame_tools_row, text="Flip", command=lambda: app.toggle_flip(), width=4).pack(side="left", padx=2)
            tk.Button(frame_tools_row, text="Rot", command=lambda: app.rotate_preview(), width=3).pack(side="left", padx=2)
            
            app.undo_frame_visibility_button = tk.Button(frame_tools_row, text="↶", command=app.undo_frame_visibility, width=3)
            app.undo_frame_visibility_button.pack(side="left", padx=2)
            Tooltip(app.undo_frame_visibility_button, "Undo Frame Visibility")
            
            # Right side buttons (reversed order: Multi, Gradient, Export)
            # Export dropdown menu button
            export_menu_btn = tk.Menubutton(frame_tools_row, text="Export", relief="raised", width=8)
            export_menu_btn.pack(side="right", padx=2)
            export_menu = tk.Menu(export_menu_btn, tearoff=0)
            export_menu_btn.config(menu=export_menu)
            export_menu.add_command(label="Background", command=app.export_background_compact)
            export_menu.add_command(label="Pal", command=app.export_pal_compact)
            export_menu.add_command(label="Generate XML", command=app.open_xml_generator_dialog)
            
            # Gradient button (colored)
            app.gradient_btn_compact = tk.Button(frame_tools_row, text="Gradient", command=app.apply_gradient_compact, 
                     width=8, bg="#9C27B0", fg="white", font=("Arial", 8, "bold"))
            app.gradient_btn_compact.pack(side="right", padx=2)
            if not hasattr(app, '_compact_swatch_widgets'): app._compact_swatch_widgets = {}
            app._compact_swatch_widgets['main_gradient_btn'] = app.gradient_btn_compact
            
            # Multiselect checkbox and Selection buttons
            app.compact_multiselect_var = tk.BooleanVar(value=False)
            tk.Checkbutton(frame_tools_row, text="Multi", variable=app.compact_multiselect_var, 
                          font=("Arial", 8)).pack(side="right", padx=2)
            
            # Select All / Clear Selection buttons
            tk.Button(frame_tools_row, text="None", command=app._clear_selection_compact,
                      width=4, font=("Arial", 8)).pack(side="right", padx=1)
            tk.Button(frame_tools_row, text="All", command=app._select_all_compact,
                      width=4, font=("Arial", 8)).pack(side="right", padx=1)
            
            # Resizable active colors section (bottom)
            # Container for resize handle and active colors
            active_colors_container = tk.Frame(app.compact_control_bar)
            active_colors_container.pack(side="top", fill="x", expand=False, padx=5, pady=(2, 5))
            
            # Resize handle at the top (outside the active colors frame)
            resize_handle = tk.Frame(active_colors_container, bg="gray", height=5, cursor="sb_v_double_arrow")
            resize_handle.pack(side="top", fill="x")
            resize_handle.bind("<Button-1>", app.start_resize_active_colors)
            resize_handle.bind("<B1-Motion>", app.resize_active_colors)
            resize_handle.bind("<ButtonRelease-1>", app.end_resize_active_colors)
            
            # Active colors frame (below the resize handle)
            app.active_colors_frame = tk.Frame(active_colors_container, relief="sunken", bd=1)
            app.active_colors_frame.pack(side="top", fill="x", expand=False)
            
            # Active colors height control (constrained to prevent overlaying main buttons)
            # Maximum height is 250px to ensure main buttons always visible
            app.active_colors_height = 180  # Default height
            app.active_colors_max_height = 205  # Maximum allowed height (increased from 180)
            
            # Set initial height
            app.active_colors_frame.config(height=app.active_colors_height)
            app.active_colors_frame.pack_propagate(False)  # Prevent children from resizing the frame
            
            # Placeholder label
            app.palette_editor_placeholder = tk.Label(app.active_colors_frame, 
                                                        text="Choose a pal to see active colors", 
                                                        fg="gray")
            app.palette_editor_placeholder.pack(expand=True)
            
            # Pack the compact control bar at the bottom of img_frame (initially hidden)
            # It will be shown/hidden by view mode toggle
            # IMPORTANT: Pack with before= to ensure it doesn't overlay main buttons
            app.compact_control_bar.pack(side="bottom", fill="x")
            app.compact_control_bar.pack_forget()  # Hide it initially
            
            
            
            # Control panel (right side)
            control_frame = tk.Frame(content_frame)
            control_frame.pack(side="right", fill="y", padx=(10, 0))
            
            # Create PanedWindow for resizable sections (hair and fashion only)
            app.paned = tk.PanedWindow(control_frame, orient="vertical", sashwidth=4, sashrelief="raised")
            app.paned.pack(fill="both", expand=True)
            # Set initial sash position
            app.paned.after_idle(lambda: app.paned.sash_place(0, 0, 120))
            
            # 3rd Job Base Fashion section (only for 3rd jobs) - static section below PanedWindow
            app.third_job_frame = tk.LabelFrame(control_frame, text="3rd Job Base Fashion")
            # Initially hidden, will be shown when needed
            app.third_job_frame.configure(width=450)
            
            # Hair section
            app.hair_frame = tk.LabelFrame(app.paned, text="Hair")
            app.hair_frame.configure(width=450)
            app.paned.add(app.hair_frame)
    
            
            # Create scrollable frame for hair palettes - force very small height
            app.hair_canvas = tk.Canvas(app.hair_frame, height=10)
            app.hair_scrollbar = tk.Scrollbar(app.hair_frame, orient="vertical", command=app.hair_canvas.yview)
            app.hair_scrollable_frame = tk.Frame(app.hair_canvas)
            
            # Configure hair canvas
            app.hair_canvas.configure(yscrollcommand=app.hair_scrollbar.set)
            
            # Update scroll region when frame size changes
            def update_hair_scroll_region(event):
                app.hair_canvas.configure(scrollregion=app.hair_canvas.bbox("all"))
            app.hair_scrollable_frame.bind("<Configure>", update_hair_scroll_region)
            
            # Create window in canvas
            app.hair_canvas.create_window((0, 0), window=app.hair_scrollable_frame, anchor="nw")
            
            # Add mouse wheel support for hair palette
            def _on_hair_mousewheel(event):
                if event.state & 0x4:  # Check if Control is pressed
                    return  # Don't scroll if Control is pressed
                # Get the scrollbar position info
                first, last = app.hair_scrollbar.get()
                if first != 0.0 or last != 1.0:  # Only scroll if scrollbar is active
                    app.hair_canvas.yview_scroll(-1 * (event.delta // 120), "units")
            # Bind scroll events to both canvas and frame to ensure it works everywhere in the hair section
            app.hair_canvas.bind("<MouseWheel>", _on_hair_mousewheel)
            app.hair_scrollable_frame.bind("<MouseWheel>", _on_hair_mousewheel)
            def _on_hair_linux_scroll(direction):
                first, last = app.hair_scrollbar.get()
                if first != 0.0 or last != 1.0:  # Only scroll if scrollbar is active
                    app.hair_canvas.yview_scroll(direction, "units")
            # Bind Linux scroll events to both canvas and frame
            for widget in (app.hair_canvas, app.hair_scrollable_frame):
                widget.bind("<Button-4>", lambda e: _on_hair_linux_scroll(-1))
                widget.bind("<Button-5>", lambda e: _on_hair_linux_scroll(1))
            
            # Pack hair canvas and scrollbar
            app.hair_canvas.pack(side="left", fill="both", expand=True)
            app.hair_scrollbar.pack(side="right", fill="y")
            
            # Fashion section with scrollbar
            app.fashion_frame = tk.LabelFrame(app.paned, text="Fashion")
            app.fashion_frame.configure(height=180, width=450)
            app.paned.add(app.fashion_frame)
            
            # Create scrollable frame for fashion palettes - reduced height
            app.fashion_canvas = tk.Canvas(app.fashion_frame, height=180, width=450)
            app.fashion_scrollbar = tk.Scrollbar(app.fashion_frame, orient="vertical", command=app.fashion_canvas.yview)
            app.fashion_scrollable_frame = tk.Frame(app.fashion_canvas)
            
            def update_scroll_region(event):
                app.fashion_canvas.configure(scrollregion=app.fashion_canvas.bbox("all"))
            
            app.fashion_scrollable_frame.bind("<Configure>", update_scroll_region)
            
            app.fashion_canvas.create_window((0, 0), window=app.fashion_scrollable_frame, anchor="nw")
            app.fashion_canvas.configure(yscrollcommand=app.fashion_scrollbar.set)
            
            # Add mouse wheel support for fashion palette
            def _on_fashion_mousewheel(event):
                if event.state & 0x4:  # Check if Control is pressed
                    return  # Don't scroll if Control is pressed
                # Get the scrollbar position info
                first, last = app.fashion_scrollbar.get()
                if first != 0.0 or last != 1.0:  # Only scroll if scrollbar is active
                    app.fashion_canvas.yview_scroll(-1 * (event.delta // 120), "units")
            # Bind scroll events to both canvas and frame to ensure it works everywhere in the fashion section
            app.fashion_canvas.bind("<MouseWheel>", _on_fashion_mousewheel)
            app.fashion_scrollable_frame.bind("<MouseWheel>", _on_fashion_mousewheel)
            def _on_fashion_linux_scroll(direction):
                first, last = app.fashion_scrollbar.get()
                if first != 0.0 or last != 1.0:  # Only scroll if scrollbar is active
                    app.fashion_canvas.yview_scroll(direction, "units")
            # Bind Linux scroll events to both canvas and frame
            for widget in (app.fashion_canvas, app.fashion_scrollable_frame):
                widget.bind("<Button-4>", lambda e: _on_fashion_linux_scroll(-1))
                widget.bind("<Button-5>", lambda e: _on_fashion_linux_scroll(1))
            
            app.fashion_canvas.pack(side="left", fill="both", expand=True)
            app.fashion_scrollbar.pack(side="right", fill="y")
    
            # Saved Colors section
            app.saved_colors_main_frame = tk.LabelFrame(app.paned, text="Saved Colors")
            app.saved_colors_main_frame.configure(height=180, width=450)
            # NOT adding to paned window by default, it should only show when toggled
            
            # Ensure _saved_colors exists
            if not hasattr(app, "_saved_colors"):
                app._saved_colors = [(0,0,0)] * 20
                
            sc_top = tk.Frame(app.saved_colors_main_frame)
            sc_top.pack(fill="x", padx=2, pady=2)
            
            tk.Label(app.saved_colors_main_frame, text="Left click to apply color\nRight click to save color",
                    anchor="w", justify="left", fg="gray40", font=("Arial", 8)).pack(fill="x", padx=6)
                    
            def _sc_load_main():
                from tkinter import filedialog
                import json
                import os
                
                root_dir = getattr(app, "root_dir", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                default_dir = os.path.join(root_dir, "exports", "colors", "json")
                os.makedirs(default_dir, exist_ok=True)
                
                p = filedialog.askopenfilename(filetypes=[("JSON","*.json")], title="Load Colors", initialdir=default_dir)
                if not p: return
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    if isinstance(data, list) and all(isinstance(t,(list,tuple)) and len(t)==3 for t in data):
                        data = [tuple(int(x) for x in t) for t in data][:20]
                        if len(data) < 20: data += [(0,0,0)]*(20-len(data))
                        app._saved_colors = data
                        app._sc_refresh_main()
                except Exception: pass
                
            def _sc_clear_main():
                app._saved_colors = [(0,0,0)] * 20
                app._sc_refresh_main()
                
            tk.Button(sc_top, text="Load", width=6, command=_sc_load_main).pack(side="left")
            tk.Button(sc_top, text="Clear", width=6, command=_sc_clear_main).pack(side="left", padx=(6,0))
            
            sc_grid = tk.Frame(app.saved_colors_main_frame)
            sc_grid.pack(padx=2, pady=(0,2))
            app._sc_main_btns = []
            
            def _sc_put_main(slot):
                # Save selected color from compact editor
                if not hasattr(app, 'compact_selected_colors') or not app.compact_selected_colors:
                    return
                current_layer = getattr(app, '_compact_active_layer', None)
                if not current_layer or not hasattr(current_layer, 'colors'):
                    return
                # Get the first selected color
                idx = list(app.compact_selected_colors)[0]
                if idx < len(current_layer.colors):
                    color = current_layer.colors[idx]
                    app._saved_colors[slot] = (int(color[0]), int(color[1]), int(color[2]))
                    app._sc_refresh_main()
                    
            def _sc_pick_main(slot):
                # Apply color to selected slots in compact editor
                if not hasattr(app, 'compact_selected_colors') or not app.compact_selected_colors:
                    return
                current_layer = getattr(app, '_compact_active_layer', None)
                if not current_layer or not hasattr(current_layer, 'colors'):
                    return
                
                r, g, b = app._saved_colors[slot]
                if (r,g,b) == (0,0,0): return  # Ignore empty slots
                
                # Update all selected colors
                for idx in app.compact_selected_colors:
                    if idx < len(current_layer.colors):
                        current_layer.colors[idx] = [int(r), int(g), int(b), 255]
                
                # Refresh compact editor UI
                if hasattr(app, '_update_compact_swatch_colors'):
                    app._update_compact_swatch_colors()
                elif hasattr(app, '_update_compact_palette_editor_from_layer'):
                    app._update_compact_palette_editor_from_layer(current_layer)
                    
                if hasattr(app, 'update_image_display'):
                    app.update_image_display()
                    
            def _handle_click_main(event, slot, is_right_click):
                is_save = is_right_click if getattr(app, 'use_right_click', True) else not is_right_click
                if is_save:
                    _sc_put_main(slot)
                else:
                    _sc_pick_main(slot)
                    
            app._sc_refresh_main = lambda: None # Will define below
            
            for i in range(20):
                canvas = tk.Canvas(sc_grid, width=24, height=24, highlightthickness=1, highlightbackground="#888888")
                canvas.grid(row=i//10, column=i%10, padx=1, pady=1)
                canvas.bind("<Button-1>", lambda e, j=i: _handle_click_main(e, j, False))
                canvas.bind("<Button-3>", lambda e, j=i: _handle_click_main(e, j, True))
                app._sc_main_btns.append(canvas)
                
            def real_refresh_main():
                if getattr(app, '_syncing', False): return
                if not hasattr(app, '_sc_main_btns'): return
                for i, canvas in enumerate(app._sc_main_btns):
                    color = app._saved_colors[i]
                    if color == (0, 0, 0) and getattr(app, 'dark_mode', False):
                        hex_color = "#FFFFFF"
                    else:
                        hex_color = f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"
                    canvas.delete("all")
                    canvas.create_rectangle(0, 0, 24, 24, fill=hex_color, outline="black")
                if hasattr(app, '_sc_refresh_live') and not getattr(app, '_syncing', False):
                    try:
                        app._syncing = True
                        app._sc_refresh_live()
                        app._syncing = False
                    except Exception:
                        app._syncing = False
            app._sc_refresh_main = real_refresh_main
            app._sc_refresh_main()
    
            # Control buttons at the bottom (fixed height and minimum width to prevent squishing)
            # Store reference for visibility management in Small Preview Mode
            app.main_button_frame = tk.Frame(main_frame, height=60)
            app.main_button_frame.pack(fill="x", pady=(10, 0))
            app.main_button_frame.pack_propagate(False)  # Prevent children from resizing the frame
            
            # Set minimum width to prevent button squishing
            app.main_button_frame.configure(width=850)
            app.main_button_frame.grid_propagate(False)  # Additional protection against resizing
            
            # Alias for backward compatibility
            button_frame = app.main_button_frame
    
            # Navigation buttons
            nav_frame = tk.Frame(button_frame)
            nav_frame.pack(side="left", padx=(0, 5))
            
            app.prev_btn = tk.Button(nav_frame, text="◀", command=app.prev_image, width=3)
            app.prev_btn.pack(side="left", padx=(0, 2))
            
            app.next_btn = tk.Button(nav_frame, text="▶", command=app.next_image, width=3)
            app.next_btn.pack(side="left")
            
            # Flip and Rotate buttons - ALWAYS visible on main previewer
            flip_frame = tk.Frame(button_frame)
            flip_frame.pack(side="left", padx=(0, 5))
            
            app.flip_btn = tk.Button(flip_frame, text="Flip", command=app.toggle_flip, width=4)
            app.flip_btn.pack(side="left", padx=(0, 2))
            Tooltip(app.flip_btn, "Flip image horizontally")
            
            app.rotate_btn = tk.Button(flip_frame, text="Rot 90°", command=app.rotate_preview, width=6)
            app.rotate_btn.pack(side="left")
            Tooltip(app.rotate_btn, "Rotate image 90°")
            
            # Edit Drop-up
            app.edit_btn = tk.Menubutton(button_frame, text="Edit ^", relief="raised", direction="above")
            app.edit_menu = tk.Menu(app.edit_btn, tearoff=0)
            app.edit_btn.configure(menu=app.edit_menu)
            app.edit_menu.add_command(label="Live Pal Editor", command=app.open_live_palette_editor)
            app.edit_menu.add_command(label="Icon Editor", command=app._open_icon_editor)
            app.edit_btn.pack(side="left", padx=(0, 5))
            
            # Generate XML Button
            app.generate_xml_btn = tk.Button(button_frame, text="Generate XML", command=app.open_xml_generator_dialog)
            app.generate_xml_btn.pack(side="left", padx=(0, 5))
    
            # Export Drop-up
            app.export_btn = tk.Menubutton(button_frame, text="Export ^", relief="raised", direction="above")
            app.export_menu = tk.Menu(app.export_btn, tearoff=0)
            app.export_btn.configure(menu=app.export_menu)
            app.export_menu.add_command(label="All Frames", command=app.export_all_frames)
            app.export_menu.add_command(label="Quick Export", command=app.bulk_export_visuals)
            app.export_btn.pack(side="left", padx=(0, 5))
    
            # Reset Drop-up
            app.reset_btn = tk.Menubutton(button_frame, text="Reset ^", relief="raised", direction="above")
            app.reset_menu = tk.Menu(app.reset_btn, tearoff=0)
            app.reset_btn.configure(menu=app.reset_menu)
            app.reset_menu.add_command(label="Reset Frames", command=app.reset_frames)
            app.reset_menu.add_command(label="Reset Pals", command=app.reset_pals)
            app.reset_btn.pack(side="left", padx=(0, 5))
    
            # Debug Drop-up
            app.debug_btn = tk.Menubutton(button_frame, text="Debug ^", relief="raised", direction="above")
            app.debug_menu = tk.Menu(app.debug_btn, tearoff=0)
            app.debug_btn.configure(menu=app.debug_menu)
            app.debug_menu.add_command(label="Statistics", command=app.show_statistics)
            app.debug_menu.add_command(label="Debug Info", command=app.debug_info)
            app.debug_menu.add_command(label="Current Display Info", command=app.show_current_display_info)
            app.debug_btn.pack(side="left", padx=(0, 5))
            
            # Background color picker (right side of button bar)
            bg_color_frame = tk.Frame(button_frame)
            bg_color_frame.pack(side="right", padx=(5, 0))
            
            # View mode toggle button (Big Picture Mode / Small Preview Mode)
            app.view_mode_button = tk.Button(button_frame, text="Big Picture Mode", 
                                              command=app.toggle_view_mode, width=16)
            app.view_mode_button.pack(side="right", padx=(5, 10))
            
            tk.Label(bg_color_frame, text="BG:").pack(side="left")
            app.bg_color_button = tk.Button(bg_color_frame, text="🎨", font=("Arial", 12), 
                                            command=app.pick_background_color, width=3, height=1)
            app.bg_color_button.pack(side="left", padx=(2, 0))
            
            # Set initial button color based on loaded settings
            hex_color = f"#{app.background_color[0]:02x}{app.background_color[1]:02x}{app.background_color[2]:02x}"
            app.bg_color_button.configure(bg=hex_color)
            
            # Bind arrow keys for image navigation
            def on_arrow_key(event):
                # Check if focus is in a text input or dropdown
                focused = app.master.focus_get()
                import tkinter as tk
                from tkinter import ttk
                if isinstance(focused, (tk.Entry, ttk.Entry, tk.Text, ttk.Combobox)):
                    return
                    
                if event.keysym == "Left":
                    app.prev_image()
                elif event.keysym == "Right":
                    app.next_image()
            
            # Use bind_all to ensure arrow keys work even when sub-widgets (like sliders) have focus
            app.master.bind_all("<Left>", on_arrow_key)
            app.master.bind_all("<Right>", on_arrow_key)
