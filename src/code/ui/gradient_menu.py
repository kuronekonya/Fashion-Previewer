import tkinter as tk
from tkinter import messagebox
from code.core.color_translator import ColorTranslator


class GradientMenu:
    @staticmethod
    def _open_gradient_menu(app, parent=None, is_compact=False):
        """Open the gradient/hue adjustment menu."""
        # Determine parent and mode
        app._gradient_is_compact = is_compact
        if parent:
            target_parent = parent
        elif hasattr(app, '_live_editor_window') and app._live_editor_window and app._live_editor_window.winfo_exists():
            target_parent = app._live_editor_window
        else:
            target_parent = app.master

        # For compact mode, save original colors for reset
        if is_compact:
            app._compact_original_colors = {}
            if hasattr(app, 'last_selected_palette') and app.last_selected_palette:
                for layer in app.palette_layers:
                    if app.last_selected_palette in getattr(layer, 'name', ''):
                        app._compact_original_colors[layer.name] = layer.colors.copy()
                        break

        # Create gradient menu window
        gradient_window = tk.Toplevel(target_parent)
        gradient_window.title("Gradient Hue Adjustment")
        gradient_window.resizable(False, False)
        gradient_window.transient(target_parent)
        gradient_window.grab_set()

        # Apply dark mode if active
        from code.utils.theme_manager import ThemeManager
        if getattr(app, 'dark_mode', False):
            ThemeManager.apply_theme(app, gradient_window)

        # Main frame
        main_frame = tk.Frame(gradient_window)
        main_frame.pack(padx=15, pady=15)

        # Title
        tk.Label(main_frame, text="Adjust all colors to match:", font=("Arial", 10, "bold")).pack(pady=(0, 5))

        # HSL adjustment checkboxes
        checkbox_frame = tk.Frame(main_frame)
        checkbox_frame.pack(pady=(0, 10))

        hue_var = tk.BooleanVar(value=getattr(app, '_gradient_adjust_hue', True))
        hue_cb = tk.Checkbutton(checkbox_frame, text="Hue", variable=hue_var,
                               command=lambda: GradientMenu._update_gradient_settings(app, 'hue', hue_var.get()))
        hue_cb.pack(side="left", padx=5)

        sat_var = tk.BooleanVar(value=getattr(app, '_gradient_adjust_saturation', False))
        sat_cb = tk.Checkbutton(checkbox_frame, text="Saturation", variable=sat_var,
                               command=lambda: GradientMenu._update_gradient_settings(app, 'saturation', sat_var.get()))
        sat_cb.pack(side="left", padx=5)

        value_var = tk.BooleanVar(value=getattr(app, '_gradient_adjust_value', False))
        value_cb = tk.Checkbutton(checkbox_frame, text="Value", variable=value_var,
                               command=lambda: GradientMenu._update_gradient_settings(app, 'value', value_var.get()))
        value_cb.pack(side="left", padx=5)

        gradient_colors = [
            ("Pastel Pink", "#FFD1DC", 350, "pastel"), ("Pastel Peach", "#FFDBCC", 20, "pastel"),
            ("Pastel Yellow", "#FFFACD", 60, "pastel"), ("Pastel Mint", "#F0FFF0", 120, "pastel"),
            ("Pastel Blue", "#E6E6FA", 240, "pastel"), ("Pastel Lavender", "#E6E6FA", 270, "pastel"),
            ("Pastel Rose", "#F8BBD0", 330, "pastel"), ("Pastel Aqua", "#E0FFFF", 180, "pastel"),
            ("Light Red", "#FFB3B3", 0, "light"), ("Light Orange", "#FFD9B3", 30, "light"),
            ("Light Yellow", "#FFFF99", 60, "light"), ("Light Green", "#B3FFB3", 120, "light"),
            ("Light Blue", "#B3B3FF", 240, "light"), ("Light Purple", "#D9B3FF", 270, "light"),
            ("Pink", "#FF69B4", 330), ("Cyan", "#00FFFF", 180),
            ("Red", "#FF0000", 0), ("Orange", "#FF8000", 30),
            ("Yellow", "#FFFF00", 60), ("Green", "#00FF00", 120),
            ("Blue", "#0000FF", 240), ("Purple", "#8000FF", 270),
            ("Magenta", "#FF00FF", 300), ("Teal", "#008080", 180),
            ("Dark Red", "#800000", 0, "dark"), ("Dark Orange", "#CC4400", 30, "dark"),
            ("Dark Yellow", "#CCCC00", 60, "dark"), ("Dark Green", "#008000", 120, "dark"),
            ("Dark Blue", "#000080", 240, "dark"), ("Dark Purple", "#4B0082", 270, "dark"),
            ("Brown", "#8B4513", 30, "brown"), ("Navy", "#191970", 240, "dark"),
            ("Cool Blue", "#0080FF", 210, "cool"), ("Cool Cyan", "#00BFFF", 195, "cool"),
            ("Cool Teal", "#008B8B", 180, "cool"), ("Cool Green", "#00FF80", 150, "cool"),
            ("Cool Purple", "#8000FF", 270, "cool"), ("Cool Violet", "#4000FF", 255, "cool"),
            ("Cool Indigo", "#4B0082", 275, "cool"), ("Cool Mint", "#00FF9F", 165, "cool"),
            ("Warm Red", "#FF4000", 15, "warm"), ("Warm Orange", "#FF8000", 30, "warm"),
            ("Warm Yellow", "#FFD700", 51, "warm"), ("Warm Pink", "#FF69B4", 330, "warm"),
            ("Warm Coral", "#FF7F50", 16, "warm"), ("Warm Peach", "#FFCBA4", 28, "warm"),
            ("Warm Gold", "#FFD700", 51, "warm"), ("Warm Amber", "#FFBF00", 45, "warm"),
            ("Orange", "#FF8000", 30, "secondary"), ("Green", "#00FF00", 120, "secondary"),
            ("Purple", "#8000FF", 270, "secondary"), ("Lime", "#80FF00", 90, "secondary"),
            ("Teal", "#00FF80", 150, "secondary"), ("Magenta", "#FF0080", 315, "secondary"),
            ("Chartreuse", "#80FF00", 90, "secondary"), ("Spring Green", "#00FF80", 150, "secondary"),
            ("Red-Orange", "#FF4000", 15, "tertiary"), ("Yellow-Orange", "#FFBF00", 45, "tertiary"),
            ("Yellow-Green", "#80FF00", 90, "tertiary"), ("Blue-Green", "#00FF80", 150, "tertiary"),
            ("Blue-Purple", "#4000FF", 255, "tertiary"), ("Red-Purple", "#FF0080", 315, "tertiary"),
            ("Vermillion", "#FF4000", 15, "tertiary"), ("Turquoise", "#00FFBF", 165, "tertiary"),
            ("Light Grey", "#C0C0C0", None, "light_grey"), ("Grey", "#808080", None, "grey"),
            ("Dark Grey", "#404040", None, "dark_grey"), ("White", "#FFFFFF", None, "white"),
            ("Black", "#000000", None, "black"), ("Beige", "#F5F5DC", 60, "beige"),
            ("Cream", "#FFFDD0", 60, "cream"), ("Tan", "#D2B48C", 30, "tan"),
        ]

        button_frame = tk.Frame(main_frame)
        button_frame.pack(pady=(0, 10))

        rows_data = [
            ("Pastel:", gradient_colors[0:8]), ("Light:", gradient_colors[8:16]),
            ("Standard:", gradient_colors[16:24]), ("Dark:", gradient_colors[24:32]),
            ("Cool:", gradient_colors[32:40]), ("Warm:", gradient_colors[40:48]),
            ("Secondary:", gradient_colors[48:56]), ("Tertiary:", gradient_colors[56:64]),
            ("Neutral:", gradient_colors[64:72]),
        ]

        for row_idx, (label, colors) in enumerate(rows_data):
            row = tk.Frame(button_frame)
            row.pack(pady=(0, 3) if row_idx < len(rows_data) - 1 else 0, anchor="w")
            tk.Label(row, text=label, font=("Arial", 8)).pack(side="left", padx=(0, 5))
            for color_data in colors:
                if color_data:
                    name, hex_color = color_data[0], color_data[1]
                    target_hue = color_data[2] if len(color_data) > 2 else None
                    variant = color_data[3] if len(color_data) > 3 else None
                    btn = tk.Button(row, text="  ", bg=hex_color, width=3, height=1,
                                    command=lambda h=target_hue, n=name, v=variant: GradientMenu._apply_gradient_hue(app, h, n, v))
                    btn.pack(side="left", padx=1)
                    if not hasattr(app, '_compact_swatch_widgets'):
                        app._compact_swatch_widgets = {}
                    app._compact_swatch_widgets[f'gradient_btn_{name}_{hex_color}_{id(btn)}'] = btn

        buttons_frame = tk.Frame(main_frame)
        buttons_frame.pack(pady=(10, 0))
        tk.Button(buttons_frame, text="Reset to Original",
                  command=lambda: GradientMenu._reset_gradient_colors(app)).pack(side="left", padx=(0, 10))
        tk.Button(buttons_frame, text="Close", command=gradient_window.destroy).pack(side="left")

        # Center the window relative to parent
        gradient_window.update_idletasks()
        width = gradient_window.winfo_width()
        height = gradient_window.winfo_height()
        try:
            x = target_parent.winfo_x() + (target_parent.winfo_width() - width) // 2
            y = target_parent.winfo_y() + (target_parent.winfo_height() - height) // 2
        except Exception:
            x = (app.master.winfo_screenwidth() - width) // 2
            y = (app.master.winfo_screenheight() - height) // 2
        gradient_window.geometry(f"+{x}+{y}")

        # Arrow key bindings for live editor simple preview navigation
        def _on_gradient_key(event):
            if getattr(app, 'live_pal_ui_mode', '') == "Simple":
                if event.keysym == "Left":
                    if hasattr(app, '_simple_prev_frame'):
                        app._simple_prev_frame()
                elif event.keysym == "Right":
                    if hasattr(app, '_simple_next_frame'):
                        app._simple_next_frame()

        gradient_window.bind("<Left>", _on_gradient_key)
        gradient_window.bind("<Right>", _on_gradient_key)
        gradient_window.focus_set()

        # Apply dark mode after building
        if getattr(app, 'dark_mode', False):
            ThemeManager.apply_theme(app, gradient_window)

    @staticmethod
    def _apply_gradient_hue(app, target_hue, color_name, variant=None):
        """Apply hue adjustment to colors in the current palette."""
        import colorsys

        # --- FIX: ensure app.char_num exists ---
        if not hasattr(app, "char_num"):
            import re
            cid = str(getattr(app, "char_id", ""))
            m = re.search(r"(\d+)$", cid)   # e.g. "chr019" -> "019"
            app.char_num = m.group(1) if m else "000"
        # ---------------------------------------

        if getattr(app, '_gradient_is_compact', False):
            # Compact mode logic
            if not hasattr(app, 'last_selected_palette') or not app.last_selected_palette:
                return
            
            ly = None
            palette_name = app.last_selected_palette
            palette_type = getattr(app, 'last_selected_palette_type', '')
            
            if hasattr(app, 'palette_layers'):
                for layer in app.palette_layers:
                    layer_name = getattr(layer, 'name', '')
                    layer_type = getattr(layer, 'palette_type', '')
                    
                    # Match by name or type using robust logic (consistent with other parts of the app)
                    import os
                    names_match = (palette_name == layer_name) or (os.path.basename(palette_name) == layer_name)
                    
                    if names_match or (palette_type == 'hair' and layer_type == 'hair') or \
                       (palette_type == 'third_job' and layer_type.startswith('3rd_job')) or \
                       (palette_type == 'fashion' and layer_type.startswith('fashion')):
                        ly = layer
                        break
            
            if ly is None:
                return
                
            # Match Live Editor logic: If Multi-Select ON and have selection, apply to selection.
            # Otherwise (Single select OR Multi-select with empty selection), apply to active range only.
            # In compact mode, ONLY apply to selected colors
            if getattr(app, 'view_mode', '') == "Small Preview Mode":
                if not hasattr(app, 'compact_selected_colors') or not app.compact_selected_colors:
                    return # Do nothing if nothing selected
                indices_to_modify = app.compact_selected_colors
            elif getattr(app, 'compact_multiselect_var', None) and app.compact_multiselect_var.get() and hasattr(app, 'compact_selected_colors') and app.compact_selected_colors:
                indices_to_modify = app.compact_selected_colors
            else:
                # Default to active indices (filtered view) instead of all colors
                indices_to_modify = app._get_editable_color_indices(ly)
                # Filter out 255
                indices_to_modify = [idx for idx in indices_to_modify if idx != 255]
        else:
            # Traditional Live Editor mode logic
            ly = app._live_current_layer()
            if ly is None:
                return

            # Determine which indices to modify based on multiselect state
            if app._multi_select.get() and app._selected_indices:
                indices_to_modify = app._selected_indices
            else:
                indices_to_modify = app._get_editable_color_indices(ly)
            
        # Special handling for neutral colors and variants
        if target_hue is None or variant in ["grey", "light_grey", "dark_grey", "black", "white"]:
            if variant == "light_grey" or color_name == "Light Grey":
                # Convert to light greyscale
                for i in indices_to_modify:
                    if i < len(ly.colors) and isinstance(ly.colors[i], tuple):
                        r, g, b = ly.colors[i]
                        grey = int(0.299 * r + 0.587 * g + 0.114 * b)
                        # Make it lighter
                        light_grey = min(255, int(grey * 1.5))
                        ly.colors[i] = (light_grey, light_grey, light_grey)
            elif variant == "dark_grey" or color_name == "Dark Grey":
                # Convert to dark greyscale
                for i in indices_to_modify:
                    if i < len(ly.colors) and isinstance(ly.colors[i], tuple):
                        r, g, b = ly.colors[i]
                        grey = int(0.299 * r + 0.587 * g + 0.114 * b)
                        # Make it darker
                        dark_grey = int(grey * 0.5)
                        ly.colors[i] = (dark_grey, dark_grey, dark_grey)
            elif variant == "grey" or color_name == "Grey":
                # Convert all colors to greyscale
                for i in indices_to_modify:
                    if i < len(ly.colors) and isinstance(ly.colors[i], tuple):
                        r, g, b = ly.colors[i]
                        grey = int(0.299 * r + 0.587 * g + 0.114 * b)
                        ly.colors[i] = (grey, grey, grey)
            elif variant == "black" or color_name == "Black":
                # Make all colors darker (reduce value significantly)
                for i in indices_to_modify:
                    if i < len(ly.colors) and isinstance(ly.colors[i], tuple):
                        r, g, b = ly.colors[i]
                        h, s, v = colorsys.rgb_to_hsv(r/255.0, g/255.0, b/255.0)
                        v = v * 0.2  # Reduce brightness to 20%
                        rr, gg, bb = colorsys.hsv_to_rgb(h, s, v)
                        ly.colors[i] = (int(rr*255), int(gg*255), int(bb*255))
            elif variant == "white" or color_name == "White":
                # Make all colors lighter (increase value significantly)
                for i in indices_to_modify:
                    if i < len(ly.colors) and isinstance(ly.colors[i], tuple):
                        r, g, b = ly.colors[i]
                        h, s, v = colorsys.rgb_to_hsv(r/255.0, g/255.0, b/255.0)
                        v = min(1.0, v + (1.0 - v) * 0.8)  # Increase brightness towards white
                        rr, gg, bb = colorsys.hsv_to_rgb(h, s, v)
                        ly.colors[i] = (int(rr*255), int(gg*255), int(bb*255))
        else:
            # Apply hue adjustment with optional lightness/darkness variants
            for i in indices_to_modify:
                if i < len(ly.colors) and isinstance(ly.colors[i], tuple):
                    r, g, b = ly.colors[i]
                    h, s, v = colorsys.rgb_to_hsv(r/255.0, g/255.0, b/255.0)
                    
                    # Store original HSV values
                    orig_h, orig_s, orig_v = h, s, v
                    
                    # Only adjust hue if enabled and color has some saturation
                    if app._gradient_adjust_hue and s > 0.1:  # Threshold to avoid adjusting near-grey colors
                        # Calculate hue difference and apply it
                        current_hue = h * 360
                        hue_diff = target_hue - current_hue
                        
                        # Normalize hue difference to [-180, 180] range for shortest rotation
                        if hue_diff > 180:
                            hue_diff -= 360
                        elif hue_diff < -180:
                            hue_diff += 360
                            
                        new_hue = (current_hue + hue_diff) % 360
                        h = new_hue / 360.0
                    
                    # Adjust saturation if enabled
                    if app._gradient_adjust_saturation:
                        s = orig_s  # Use original saturation as target
                        
                    # Adjust value if enabled
                    if app._gradient_adjust_value:
                        v = orig_v  # Use original value as target
                    
                    # Apply value variants
                    if variant == "pastel":
                        # Make colors very light and soft by increasing value and significantly reducing saturation
                        v = min(1.0, v + (1.0 - v) * 0.8)  # Increase brightness significantly
                        s = s * 0.3  # Reduce saturation significantly for soft pastel effect
                    elif variant == "light":
                        # Make colors lighter by increasing value and reducing saturation slightly
                        v = min(1.0, v + (1.0 - v) * 0.6)  # Increase brightness
                        s = s * 0.7  # Reduce saturation for pastel effect
                    elif variant == "dark":
                        # Make colors darker by decreasing value
                        v = v * 0.4  # Reduce brightness significantly
                    elif variant in ["beige", "cream", "tan"]:
                        # Special handling for earth tones - reduce saturation and adjust value
                        s = s * 0.3  # Very low saturation
                        if variant == "cream":
                            v = min(1.0, v + (1.0 - v) * 0.7)  # Light
                        elif variant == "tan":
                            v = v * 0.8  # Medium
                        else:  # beige
                            v = min(1.0, v + (1.0 - v) * 0.4)  # Light-medium
                elif variant == "brown":
                    # Brown is essentially dark orange with low saturation
                    s = s * 0.6
                    v = v * 0.5
                elif variant == "cool":
                    # Cool colors: slightly increase saturation and maintain cooler hues
                    s = min(1.0, s * 1.2)  # Increase saturation slightly
                    v = min(1.0, v * 1.1)  # Slightly brighter
                elif variant == "warm":
                    # Warm colors: increase saturation and warmth
                    s = min(1.0, s * 1.3)  # Increase saturation more
                    v = min(1.0, v * 1.05)  # Slightly brighter
                elif variant == "secondary":
                    # Secondary colors: full saturation, balanced brightness
                    s = min(1.0, s * 1.5)  # High saturation
                    v = min(1.0, v * 1.1)  # Slightly brighter
                elif variant == "tertiary":
                    # Tertiary colors: balanced saturation and brightness
                    s = min(1.0, s * 1.2)  # Moderate saturation increase
                    v = min(1.0, v * 1.05)  # Slightly brighter
                    
                # Convert back to RGB (for all variants)
                rr, gg, bb = colorsys.hsv_to_rgb(h, s, v)
                candidate_color = (int(rr*255), int(gg*255), int(bb*255))
                
                # Check if new color would be a keying color
                if candidate_color == (0, 255, 0) or candidate_color == (255, 0, 255):
                    candidate_color = ColorTranslator._find_nearest_non_keyed_color(candidate_color)
                
                ly.colors[i] = candidate_color
        
        # Sync HSV sliders to the new color of the currently selected index
        # This prevents sliders from being "stale" and reverting colors when moved
        if hasattr(app, "_live_selected_index") and hasattr(app, "_sync_hsv_from_rgb"):
            # Only sync if not in compact mode or if index valid
            if not getattr(app, '_gradient_is_compact', False):
                idx = app._live_selected_index
                if 0 <= idx < len(ly.colors):
                    r, g, b = ly.colors[idx]
                    app._sync_hsv_from_rgb(r, g, b)

        # Update the UI
        if getattr(app, '_gradient_is_compact', False):
            if hasattr(app, 'update_compact_palette_editor'):
                app.update_compact_palette_editor()
        else:
            app._live_refresh_swatches()
            
        app._debounced_display_update()
        
        # Update selection UI if available
        if hasattr(app, "_update_selection_ui"):
            app._update_selection_ui()
        
        # Track statistics: gradient applied to indexes
        if hasattr(app, 'statistics'):
            app.statistics.track_index_modification(indices_to_modify)

    @staticmethod
    def _update_gradient_settings(app, setting, value):
        """Update the HSL adjustment settings."""
        if setting == 'hue':
            app._gradient_adjust_hue = value
        elif setting == 'saturation':
            app._gradient_adjust_saturation = value
        elif setting == 'value':
            app._gradient_adjust_value = value

    @staticmethod
    def _reset_gradient_colors(app):
        """Reset colors to original palette colors before gradient changes and reset HSL settings."""
        # Reset HSL settings to defaults
        app._gradient_adjust_hue = True
        app._gradient_adjust_saturation = False
        app._gradient_adjust_value = False
        
        if getattr(app, '_gradient_is_compact', False):
            # Compact mode reset
            if not hasattr(app, '_compact_original_colors'):
                return
            
            # Find active layer
            ly = None
            if hasattr(app, 'last_selected_palette') and app.last_selected_palette:
                for layer in app.palette_layers:
                    if app.last_selected_palette in getattr(layer, 'name', ''):
                        ly = layer
                        break
            
            if ly and ly.name in app._compact_original_colors:
                ly.colors = app._compact_original_colors[ly.name].copy()
                
                # Update UI
                if hasattr(app, 'update_compact_palette_editor'):
                    app.update_compact_palette_editor()
                app._debounced_display_update()
            return
            
        ly = app._live_current_layer()
        if ly is None:
            return
        
        # Check if we have original colors stored
        if hasattr(ly, '_original_colors') and ly._original_colors:
            # Restore from stored original colors
            ly.colors = ly._original_colors.copy()
        else:
            # Fallback: try to reload from the original palette file
            try:
                # Try to reload the vanilla palette for this layer
                if hasattr(ly, 'name') and ly.name:
                    # Extract character and palette type info from layer name
                    import re
                    char_match = re.search(r'(?:chr)?(\d{3})', ly.name)
                    if char_match:
                        char_num = char_match.group(1)
                        palette_type = getattr(ly, 'palette_type', '')
                        
                        # Load vanilla palette
                        vanilla_colors = app._load_vanilla_palette_for_layer(char_num, palette_type, ly.name)
                        if vanilla_colors:
                            ly.colors = vanilla_colors.copy()
                            # Store as original colors for future resets
                            ly._original_colors = vanilla_colors.copy()
                        else:
                            print(f"Could not load vanilla palette for {ly.name}")
                    else:
                        print(f"Could not extract character info from layer name: {ly.name}")
                else:
                    print("CONSOLE ERROR MSG: Layer has no name attribute for vanilla palette lookup")
            except Exception as e:
                print(f"CONSOLE ERROR MSG: Error resetting gradient colors: {e}")
        
        # Update the UI
        app._live_refresh_swatches()
        app._debounced_display_update()
        
        # Update selection UI if available
        if hasattr(app, "_update_selection_ui"):
            app._update_selection_ui()

    @staticmethod
    def apply_gradient_compact(app):
        """Apply gradient from compact editor"""
        # Requirement: If no indexes are selected, gradient button should not work
        if not hasattr(app, 'compact_selected_colors') or not app.compact_selected_colors:
            messagebox.showinfo("Selection Required", "Please select one or more colors to apply a gradient.")
            return

        # Open the gradient menu in compact mode
        # This will use the window master as parent since we don't have the live editor window
        app._open_gradient_menu(parent=app.master, is_compact=True)

