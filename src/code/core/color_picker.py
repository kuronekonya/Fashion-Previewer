from PIL import Image
from code.core.color_translator import ColorTranslator

class ColorPicker:
        def _toggle_colorpicker(app):
            """Toggle colorpicker mode on/off for simple palette editor."""
            app.colorpicker_active = not app.colorpicker_active
            
            if app.colorpicker_active:
                app._colorpicker_btn.configure(text="🎨 Exit")
                # Change cursor for all clickable areas
                if hasattr(app, '_simple_preview_canvas'):
                    app._simple_preview_canvas.configure(cursor="crosshair")
                for swatch in app._live_swatches:
                    if swatch and swatch.winfo_exists():
                        swatch.configure(cursor="crosshair")
            else:
                app._colorpicker_btn.configure(text="🎨 Pick")
                # Reset cursors
                if hasattr(app, '_simple_preview_canvas'):
                    app._simple_preview_canvas.configure(cursor="")
                for swatch in app._live_swatches:
                    if swatch and swatch.winfo_exists():
                        swatch.configure(cursor="")
    
        def _colorpick_from_simple_palette(app, palette_idx):
            """Pick color from simple palette square."""
            current_layer = app._live_current_layer()
            if current_layer and palette_idx < len(current_layer.colors):
                picked_color = current_layer.colors[palette_idx]
                
                # Check if picked color is a keying color and find alternative if needed
                if ColorTranslator._is_keyed_color(picked_color):
                    picked_color = ColorTranslator._find_nearest_non_keyed_color(picked_color)
                    print(f"Avoided keying color, using alternative: {picked_color}")
                
                app._apply_colorpicked_color_simple(picked_color)
    
        def _colorpick_from_simple_preview(app, event):
            """Pick color from simple preview image."""
            try:
                if not hasattr(app, 'current_character') or not app.current_character:
                    return
                
                if app.current_character not in app.character_images:
                    return
                
                images = app.character_images[app.current_character]
                if not images or app._simple_current_frame >= len(images):
                    return
                
                # Get click coordinates relative to the canvas
                click_x = event.x
                click_y = event.y
                
                # Get the current zoom and image dimensions
                zoom = app._simple_zoom_var.get()
                canvas_width = app._simple_preview_canvas.winfo_width()
                canvas_height = app._simple_preview_canvas.winfo_height()
                
                if canvas_width <= 1:
                    canvas_width = 380
                if canvas_height <= 1:
                    canvas_height = 200
                
                # Load the original image to get pixel data
                original_img_path = images[app._simple_current_frame]
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
                    scale = 2
                elif zoom == "300%":
                    display_width = img_width * 3
                    display_height = img_height * 3
                    scale = 3
                elif zoom == "400%":
                    display_width = img_width * 4
                    display_height = img_height * 4
                    scale = 4
                elif zoom == "500%":
                    display_width = img_width * 5
                    display_height = img_height * 5
                    scale = 5
                else:  # 100%
                    display_width = img_width
                    display_height = img_height
                    scale = 1
                
                # Calculate image position (centered)
                image_x = (canvas_width - display_width) // 2
                image_y = (canvas_height - display_height) // 2
                
                # Check if click is within the image
                if (image_x <= click_x <= image_x + display_width and 
                    image_y <= click_y <= image_y + display_height):
                    
                    # Convert click coordinates to image coordinates
                    relative_x = click_x - image_x
                    relative_y = click_y - image_y
                    
                    # Scale back to original image coordinates
                    if zoom == "Fit":
                        original_x = int(relative_x / scale)
                        original_y = int(relative_y / scale)
                    else:
                        original_x = int(relative_x / scale)
                        original_y = int(relative_y / scale)
                    
                    # Ensure coordinates are within image bounds
                    if 0 <= original_x < img_width and 0 <= original_y < img_height:
                        # Get the palette index at this pixel
                        pixel_index = original_img.getpixel((original_x, original_y))
                        
                        # Get the actual color from the merged palette
                        merged_palette = app.get_merged_palette()
                        if pixel_index < len(merged_palette):
                            picked_color = merged_palette[pixel_index]
                            
                            # Check if it's a transparency color and use background color instead
                            if ColorTranslator.is_universal_keying_color(picked_color) or picked_color == (255, 0, 255):
                                picked_color = app.background_color
                            
                            app._apply_colorpicked_color_simple(picked_color)
                            
            except Exception as e:
                print(f"CONSOLE ERROR MSG: Error picking color from simple preview: {e}")
    
        def _apply_colorpicked_color_simple(app, picked_color):
            """Apply a picked color to the selected palette indices in simple mode."""
            current_layer = app._live_current_layer()
            if not current_layer:
                return
            
            # Check if picked color is a keying color and find alternative if needed
            if ColorTranslator._is_keyed_color(picked_color):
                picked_color = ColorTranslator._find_nearest_non_keyed_color(picked_color)
                print(f"Avoided keying color, using alternative: {picked_color}")
            
            # Get selected indices or current index
            targets = sorted(app._selected_indices) if app._multi_select.get() and app._selected_indices else [app._live_selected_index]
            
            for i in targets:
                if i < len(current_layer.colors):
                    current_layer.colors[i] = picked_color
                    
                    # Update statistics
                    app.statistics.indexes_changed += 1
                    app.statistics.colors_saved += 1
                    if hasattr(app, 'current_character') and hasattr(app, 'current_job'):
                        app.statistics.add_palette_edit(app.current_character, app.current_job)
                        app.statistics.live_palette_files_edited.add(current_layer.name)
                    # Track index modification (outside the loop to count as single event)
                    if hasattr(app, 'statistics'):
                        app.statistics.track_index_modification(targets)
                    app._save_statistics()
                    
                    # Update swatch if in simple mode
                    if app.live_pal_ui_mode == "Simple":
                        editable_indices = app._get_editable_color_indices()
                        if i in editable_indices:
                            display_idx = editable_indices.index(i)
                            if display_idx < len(app._live_swatches) and app._live_swatches[display_idx] is not None:
                                canvas = app._live_swatches[display_idx]
                                hex_color = f"#{picked_color[0]:02x}{picked_color[1]:02x}{picked_color[2]:02x}"
                                canvas.delete("all")
                                canvas.create_rectangle(1, 1, 39, 39, fill=hex_color, outline="black", width=1)
            
            # Update UI elements
            if hasattr(app, "_update_selection_ui"):
                app._update_selection_ui()
            
            r, g, b = picked_color
            app._picker_preview.config(bg=f"#{r:02x}{g:02x}{b:02x}")
            app._picker_hex.delete(0, "end")
            app._picker_hex.insert(0, f"#{r:02x}{g:02x}{b:02x}")
            
            app._debounced_display_update()
            app._sync_hsv_from_rgb(r, g, b)
            
            # Update simple mode preview if in simple mode
            if hasattr(app, '_update_simple_preview'):
                app._update_simple_preview()
            
            # Exit colorpicker mode after picking
            if app.colorpicker_active:
                app._toggle_colorpicker()
    
        def _select_color_from_frame_click(app, event, frame_index):
            """Select the palette color at the clicked pixel location in small preview mode"""
            try:
                if not hasattr(app, 'current_character') or not app.current_character:
                    return
                
                if app.current_character not in app.character_images:
                    return
                
                images = app.character_images[app.current_character]
                if not images or frame_index >= len(images):
                    return
                
                # Load the original image to get pixel data
                original_img_path = images[frame_index]
                original_img = Image.open(original_img_path).convert("P")
                img_width, img_height = original_img.size
                
                # Get the image item on the canvas
                # We tagged it with "frame_{frame_index}"
                tag = f"frame_{frame_index}"
                bbox = app.canvas.bbox(tag)
                
                if not bbox:
                    return
                    
                x1, y1, x2, y2 = bbox
                
                # Get click coordinates relative to the CANVAS (accounting for scroll)
                canvas_click_x = app.canvas.canvasx(event.x)
                canvas_click_y = app.canvas.canvasy(event.y)
                
                # Calculate coordinates relative to the image top-left
                rel_x = canvas_click_x - x1
                rel_y = canvas_click_y - y1
                
                # Calculate scale based on displayed size vs original size
                current_w = x2 - x1
                current_h = y2 - y1
                
                scale_x = current_w / img_width if img_width > 0 else 1.0
                scale_y = current_h / img_height if img_height > 0 else 1.0
                
                # Convert to original image coordinates
                original_x = int(rel_x / scale_x)
                original_y = int(rel_y / scale_y)
                
                # Ensure coordinates are within image bounds
                if 0 <= original_x < img_width and 0 <= original_y < img_height:
                    # Get the palette index at this pixel
                    pixel_index = original_img.getpixel((original_x, original_y))
                    
                    # Identify and switch to the layer for this pixel
                    found_layer = app._find_layer_by_pixel_index(pixel_index)
                    if found_layer:
                        app._compact_active_layer = found_layer
                        app.last_selected_palette = found_layer.name
                        # Update Compact Editor UI (refresh swatches)
                        if hasattr(app, 'update_compact_palette_editor'):
                            app.update_compact_palette_editor()
    
                    # Check if we have a compact active layer and if this index is editable
                    if hasattr(app, '_compact_active_layer') and app._compact_active_layer:
                        # Get editable indices for the current layer
                        app.current_character.replace("chr", "")
                        getattr(app._compact_active_layer, 'palette_type', '')
                        
                        editable_indices = app._get_editable_color_indices(app._compact_active_layer)
                        
                        if pixel_index in editable_indices:
                            # Select this color in the compact editor
                            if not hasattr(app, 'compact_selected_colors'):
                                app.compact_selected_colors = set()
                            
                            # Check if multiselect is enabled OR Ctrl is pressed
                            multiselect = getattr(app, 'compact_multiselect_var', None)
                            ctrl_pressed = (event.state & 0x4) != 0
                            
                            if (multiselect and multiselect.get()) or ctrl_pressed:
                                # Toggle selection
                                if pixel_index in app.compact_selected_colors:
                                    app.compact_selected_colors.remove(pixel_index)
                                    if pixel_index in app.compact_base_colors:
                                        del app.compact_base_colors[pixel_index]
                                else:
                                    app.compact_selected_colors.add(pixel_index)
                                    # Store base color for this index
                                    if pixel_index < len(app._compact_active_layer.colors):
                                        app.compact_base_colors[pixel_index] = app._compact_active_layer.colors[pixel_index]
                            else:
                                # Single selection - clear previous and select this one
                                app.compact_selected_colors.clear()
                                app.compact_base_colors.clear()
                                app.compact_selected_colors.add(pixel_index)
                                # Store base color for this index
                                if pixel_index < len(app._compact_active_layer.colors):
                                    app.compact_base_colors[pixel_index] = app._compact_active_layer.colors[pixel_index]
                            
                            # Reset sliders to 0
                            if hasattr(app, 'compact_hue_var'):
                                app.compact_hue_var.set(0)
                                app.compact_sat_var.set(0)
                                app.compact_val_var.set(0)
                            
                            # Update the UI highlights
                            if hasattr(app, '_update_compact_swatch_highlights'):
                                app._update_compact_swatch_highlights()
                            
            except Exception as e:
                # Silently fail - don't disrupt the user experience
                pass
    
