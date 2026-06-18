from tkinter import messagebox
import re

class IconEditor:
        def _notify_icon_editor_palette_change(app):
            """Notify the icon editor that palette layers have changed."""
            try:
                from icon_handler import IconHandler
                if (IconHandler._icon_editor_instance and 
                    IconHandler._icon_editor_instance.window and 
                    IconHandler._icon_editor_instance.window.winfo_exists()):
                    # Update the icon editor's palette layers
                    IconHandler._icon_editor_instance.update_palette_layers(app.palette_layers)
            except Exception as e:
                print(f"CONSOLE ERROR MSG: Error notifying icon editor of palette change: {e}")
    
        def _live_open_icon_editor(app):
            """Open the icon editor directly without saving a palette first."""
            ly = app._live_current_layer()
            if ly is None:
                return
            
            # Extract character ID and item name from the layer
            char_match = re.search(r'(?:chr)?(\d{3})', ly.name)
            if not char_match:
                messagebox.showerror("Error", "Could not determine character ID from layer name")
                return
            
            num = char_match.group(1)
            char_id = f"chr{num}"  # Normalize to chr format
            
            # Get the fashion type from the layer
            fashion_type = getattr(ly, "palette_type", "")
            if not fashion_type:
                messagebox.showerror("Error", "Could not determine fashion type from layer")
                return
            
            # Get current colors from the layer
            colors = ly.colors
            
            # Validate colors before proceeding
            if not colors or not isinstance(colors, list):
                messagebox.showerror("Error", "No valid color data found in the selected layer")
                return
            
            # Validate that colors contain valid RGB tuples
            valid_colors = []
            for i, color in enumerate(colors):
                if isinstance(color, (list, tuple)) and len(color) >= 3:
                    try:
                        r, g, b = int(color[0]), int(color[1]), int(color[2])
                        if 0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255:
                            valid_colors.append((r, g, b))
                        else:
                            print(f"CONSOLE ERROR MSG: Color values out of range at index {i}: {color}")
                            valid_colors.append((128, 128, 128))  # Default gray
                    except (ValueError, TypeError):
                        print(f"CONSOLE ERROR MSG: Invalid color at index {i}: {color}")
                        valid_colors.append((128, 128, 128))  # Default gray
                else:
                    print(f"CONSOLE ERROR MSG: Invalid color format at index {i}: {color}")
                    valid_colors.append((128, 128, 128))  # Default gray
            
            if not valid_colors:
                messagebox.showerror("Error", "No valid colors found in the selected layer")
                return
            
            # Create a temporary palette path for the editor
            temp_palette_path = f"temp_{ly.name}.pal"
            
            try:
                # Open the icon palette editor directly
                from icon_handler import IconPaletteEditor
                # Create icon handler and set main window reference
                from icon_handler import IconHandler
                icon_handler = IconHandler()
                icon_handler.main_window = app
                
                editor = IconPaletteEditor(
                    char_id=char_id,
                    fashion_type=fashion_type,
                    custom_palette=valid_colors,
                    palette_path=temp_palette_path,
                    palette_layers=app.palette_layers,  # Pass palette layers to enable dropdown refresh
                    live_editor_window=app._live_editor_window,
                    is_quicksave_mode=False,  # Editor mode - allow user to name file
                    icon_handler=icon_handler,
                    ui_mode=getattr(app, 'live_pal_ui_mode', 'Simple')
                )
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open icon editor: {e}")
    
        def _update_icon_editor_button_state(app):
            """Update the icon editor button state based on current palette types"""
            if not hasattr(app, 'icon_editor_button'):
                return
                
            # Check if live palette editor is open and editing non-impact types
            if hasattr(app, '_live_editor_window') and app._live_editor_window and app._live_editor_window.winfo_exists():
                # Check if current layer is hair or third job
                try:
                    current_layer = app._live_current_layer()
                    if current_layer and hasattr(current_layer, 'palette_type'):
                        palette_type = str(current_layer.palette_type).lower()
                        if palette_type in ("hair", "3rd_job_base"):
                            app.icon_editor_button.config(state="disabled", text="Icon Editor (N/A)")
                            return
                except Exception:
                    pass
            
            # Default state - enabled
            app.icon_editor_button.config(state="normal", text="Icon Editor")
    
        def _open_icon_editor(app):
            """Open the icon editor from the main screen."""
            from icon_handler import IconHandler
            icon_handler = IconHandler()
            # Pass the live editor window if it exists
            live_editor = getattr(app, '_live_editor_window', None)
            # Set the main window reference
            icon_handler.main_window = app
            # Pass current UI mode
            ui_mode = getattr(app, 'live_pal_ui_mode', 'Simple')
            last_pal = getattr(app, 'last_selected_palette', None)
            icon_handler.open_icon_editor(app.palette_layers, live_editor, ui_mode, last_selected_palette=last_pal)
    
