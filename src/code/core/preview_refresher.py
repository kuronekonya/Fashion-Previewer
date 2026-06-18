import tkinter as tk
from tkinter import messagebox
import os
from PIL import Image, ImageTk
import re
from icon_handler import CHARACTER_MAPPING
from fashionpreviewer import PALETTE_SIZE
from code.core.color_translator import ColorTranslator


class PreviewRefresher:
    @staticmethod
    def _redraw_frames_with_selection(app):
        """Redraw frames to show selection highlights"""
        # Optimized partial update for All/Custom modes
        mode = app.preview_var.get()
        if mode in ["all", "custom"]:
            if hasattr(app, 'canvas') and app.canvas.find_all():
                app.canvas.delete("selection")
                
                # Draw selection box for all selected frames
                targets = app.selected_frames if app.selected_frames else (
                    {app.selected_frame} if app.selected_frame is not None else set()
                )
                
                for idx in targets:
                    items = app.canvas.find_withtag(f"frame_{idx}")
                    if items:
                         for item in items:
                             bbox = app.canvas.bbox(item)
                             if bbox:
                                  x1, y1, x2, y2 = bbox
                                  app.canvas.create_rectangle(x1-2, y1-2, x2+2, y2+2,
                                        outline="red", width=2, tags="selection")
                return

        # Fallback to full update
        app.update_image_display()

    @staticmethod
    def refresh_data(app):
        """Reloads assets from disk (assets/rawbmps, pals, custom_fashion_pals, 3rd job) and rebuilds the UI without restarting."""
        try:
            # Save current selections & state
            prev_char_name = app.character_var.get() if hasattr(app, "character_var") else None
            prev_job_name = app.job_var.get() if hasattr(app, "job_var") else None
            prev_image_index = getattr(app, "current_image_index", 0)
            prev_preview = app.preview_var.get() if hasattr(app, "preview_var") else "single"
            prev_zoom = app.zoom_var.get() if hasattr(app, "zoom_var") else "100%"
            prev_custom_count = getattr(app, "custom_frame_count", 3)
            prev_custom_start = getattr(app, "custom_start_index", 0)

            saved_hair = app.hair_var.get() if hasattr(app, "hair_var") else "NONE"
            saved_third = app.third_job_var.get() if hasattr(app, "third_job_var") else "NONE"
            saved_fashion = {}
            if hasattr(app, "fashion_vars") and isinstance(app.fashion_vars, dict):
                for k, var in app.fashion_vars.items():
                    try:
                        saved_fashion[k] = var.get()
                    except Exception as e:
                        pass

            # Reset in-memory databases
            app.available_characters = []
            app.available_jobs = []
            app.character_images = {}
            app.fashion_palettes = {}
            app.hair_palettes = {}
            app.third_job_palettes = {}
            app.fashion_vars = {}

            # Reload from disk
            app.load_all_data()

            # Helper to see if a character+job still exists
            def find_char_id_by_name_job(name, job):
                for cid in app.available_characters:
                    if cid in CHARACTER_MAPPING:
                        info = CHARACTER_MAPPING[cid]
                        if info.get("name") == name and info.get("job") == job:
                            return cid
                return None

            # Restore character/job if possible
            target_char_id = None
            if prev_char_name and prev_job_name:
                target_char_id = find_char_id_by_name_job(prev_char_name, prev_job_name)
            if target_char_id is None and app.available_characters:
                target_char_id = app.available_characters[0]

            # Apply restored selection
            if target_char_id:
                # Set UI vars
                if target_char_id in CHARACTER_MAPPING:
                    app.character_var.set(CHARACTER_MAPPING[target_char_id]["name"])
                    app.job_var.set(CHARACTER_MAPPING[target_char_id]["job"])
                else:
                    app.character_var.set(target_char_id)
                # Build sections + palettes
                app.on_job_change()

                # Try to restore prior palette choices if still present
                try:
                    if saved_third and saved_third != "NONE" and os.path.exists(saved_third):
                        app.third_job_var.set(saved_third)
                except Exception as e:
                    pass

                try:
                    if saved_hair and saved_hair != "NONE" and os.path.exists(saved_hair):
                        app.hair_var.set(saved_hair)
                except Exception as e:
                    pass

                # Fashion per-type
                for k, v in saved_fashion.items():
                    if k in app.fashion_vars:
                        try:
                            if v == "NONE" or os.path.exists(v):
                                app.fashion_vars[k].set(v)
                        except Exception as e:
                            pass

                # Reload layers & image
                app.load_palettes()

                # Restore image index if valid
                if target_char_id in app.character_images:
                    imgs = app.character_images[target_char_id]
                    if imgs:
                        if 0 <= prev_image_index < len(imgs):
                            app.current_image_index = prev_image_index
                        else:
                            app.current_image_index = 0
                        app.load_character_image()

            # Restore preview/zoom/custom state
            try:
                app.preview_var.set(prev_preview)
            except Exception as e:
                pass
            try:
                app.zoom_var.set(prev_zoom)
            except Exception as e:
                pass
            app.custom_frame_count = prev_custom_count
            app.custom_start_index = prev_custom_start

            # Refresh display/controls
            app.update_zoom_combo_state()
            app.update_image_display()

            try:
                messagebox.showinfo("Refresh", "Assets reloaded. New palettes and images are now available.")
            except Exception as e:
                pass

        except Exception as e:
            try:
                messagebox.showerror("Refresh", f"Failed to refresh assets:\\n{e}")
            except Exception as e:
                pass

    @staticmethod
    def update_single_frame_display(app):
        """Update display for single frame mode"""
        # Check if canvas exists and is valid
        if not hasattr(app, 'canvas') or not app.canvas.winfo_exists():
            return
            
        # Double check if current frame is hidden
        char_job_key = app._get_char_job_key()
        hidden = app.hidden_frames.get(char_job_key, set())
        if app.current_image_index in hidden:
             # This should have been handled by update_image_display, but as a fallback:
             app.canvas.delete("all")
             app.canvas.create_text(200, 200, text="[Hidden Frame]", fill="gray")
             return

        if not app.original_image:
            app.canvas.delete("all")
            return
        
        # Get the merged palette
        merged_palette = app.get_merged_palette()
        

        
        # Create a new image with the merged palette
        w, h = app.original_image.size
        display_img = Image.new("P", (w, h))
        
        # Apply the merged palette FIRST
        display_img.putpalette(app._flatten_palette(merged_palette))
        
        # THEN copy the pixel data from original image
        display_img.putdata(app.original_image.get_flattened_data())
        

        
        # Replace transparency colors with background color in the merged palette
        merged_palette = app.get_merged_palette()
        display_palette = []
        
        for i, color in enumerate(merged_palette):
            if ColorTranslator.is_universal_keying_color(color) or color == (255, 0, 255):  # Green or magenta
                display_palette.append(app.background_color)
            else:
                display_palette.append(color)
        
        # Apply the modified palette to the display image
        display_img.putpalette(app._flatten_palette(display_palette))
        
        # Convert to RGB for display
        rgb_img = display_img.convert("RGB")
        
        rgb_img = app.apply_image_transformations(rgb_img)
        w, h = rgb_img.size
        

        
        # Apply zoom based on zoom setting
        zoom_level = app.zoom_var.get()
        display_img = rgb_img
        display_w, display_h = w, h
        
        if zoom_level == "200%":
            # Scale up to 200%
            display_w = int(w * 2)
            display_h = int(h * 2)
            display_img = rgb_img.resize((display_w, display_h), Image.Resampling.NEAREST)
        elif zoom_level == "300%":
            # Scale up to 300%
            display_w = int(w * 3)
            display_h = int(h * 3)
            display_img = rgb_img.resize((display_w, display_h), Image.Resampling.NEAREST)
        elif zoom_level == "400%":
            # Scale up to 400%
            display_w = int(w * 4)
            display_h = int(h * 4)
            display_img = rgb_img.resize((display_w, display_h), Image.Resampling.NEAREST)
        elif zoom_level == "500%":
            # Scale up to 500%
            display_w = int(w * 5)
            display_h = int(h * 5)
            display_img = rgb_img.resize((display_w, display_h), Image.Resampling.NEAREST)
        elif zoom_level == "Fit":
            # Fit to canvas size
            canvas_width = app.canvas.winfo_width()
            canvas_height = app.canvas.winfo_height()
            if canvas_width <= 1:  # Canvas not yet configured
                canvas_width = 400
            if canvas_height <= 1:
                canvas_height = 400
            
            # Calculate scale to fit within canvas
            scale_x = canvas_width / w
            scale_y = canvas_height / h
            scale = min(scale_x, scale_y)
            
            display_w = int(w * scale)
            display_h = int(h * scale)
            display_img = rgb_img.resize((display_w, display_h), Image.Resampling.LANCZOS)
        
        app.tk_image = ImageTk.PhotoImage(display_img)
        # Clear canvas and recreate image
        app.canvas.delete("all")
        
        # Get canvas dimensions for centering
        canvas_width = app.canvas.winfo_width()
        canvas_height = app.canvas.winfo_height()
        if canvas_width <= 1:  # Canvas not yet configured
            canvas_width = 400
        if canvas_height <= 1:
            canvas_height = 400
        
        # For single view: always center horizontally, center vertically if fits, otherwise top-align
        img_x = canvas_width // 2  # Always center horizontally
        
        # Ensure we don't exceed canvas bounds for wide images
        if display_w > canvas_width:
            # If image is wider than canvas, we need horizontal scrolling
            scroll_w = max(display_w, canvas_width)
        else:
            scroll_w = canvas_width
            
        if display_h <= canvas_height:
            # Image fits vertically - center it completely
            img_y = canvas_height // 2
            anchor = "center"
            # Set scroll region to canvas size for centered content
            app.canvas.config(scrollregion=(0, 0, scroll_w, canvas_height))
        else:
            # Image extends past bottom - center horizontally but align to top
            img_y = 0
            anchor = "n"  # North anchor (center horizontally, top vertically)
            # Set scroll region to image size for scrollable content
            app.canvas.config(scrollregion=(0, 0, scroll_w, display_h + 25))
        
        app.img_id = app.canvas.create_image(img_x, img_y, anchor=anchor, image=app.tk_image)
        
        
        # Define event handlers that prevent propagation
        def on_img_click(e, idx):
            # Use the new on_frame_click method for Ctrl+Click support
            if hasattr(app, 'on_frame_click'):
                app.on_frame_click(e, idx)
            else:
                # Fallback to old behavior
                app._select_frame(idx, e)
            app._identify_layer_from_click(idx, e)
            return "break"
        
        def on_img_right_click(e, idx):
            app._show_frame_context_menu(e, idx)
            return "break"
        
        # Add frame number text below the image
        if app.show_frame_labels:
            frame_number = app.current_image_index + 1
            if anchor == "center":
                # For fully centered images, position text below center
                text_x = img_x
                text_y = img_y + (display_h // 2) + 10
            else:
                # For top-aligned images (anchor="n"), position text below image center
                text_x = img_x  # Use same x as image (centered)
                text_y = display_h + 5
            
            text_color = "white" if getattr(app, 'dark_mode', False) else "black"
            text_id = app.canvas.create_text(text_x, text_y, text=str(frame_number), 
                                  anchor="n", font=("Arial", 8), fill=text_color)
            app.canvas.tag_bind(text_id, "<Button-1>", lambda e, idx=app.current_image_index: on_img_click(e, idx))
            app.canvas.tag_bind(text_id, "<Button-3>", lambda e, idx=app.current_image_index: on_img_right_click(e, idx))
        
        # Draw selection highlight if this frame is selected
        if app.selected_frame == app.current_image_index:
            # Calculate bounds
            if anchor == "center":
                x1 = img_x - display_w // 2
                y1 = img_y - display_h // 2
            else: # anchor == "n"
                x1 = img_x - display_w // 2
                y1 = img_y
            x2 = x1 + display_w
            y2 = y1 + display_h
            
            # Draw red selection box with slight padding
            app.canvas.create_rectangle(x1-2, y1-2, x2+2, y2+2, outline="red", width=2, tags="selection")

        # Bind events to the image
        app.canvas.tag_bind(app.img_id, "<Button-1>", lambda e, idx=app.current_image_index: on_img_click(e, idx))
        app.canvas.tag_bind(app.img_id, "<Button-3>", lambda e, idx=app.current_image_index: on_img_right_click(e, idx))
        
        # Bind background click to deselect only if clicking on empty canvas
        def on_canvas_click(e):
            # Check if we clicked on an item
            item = app.canvas.find_closest(e.x, e.y)
            if not item or app.canvas.type(item[0]) == "":
                app._deselect_frame()
        
        app.canvas.bind("<Button-1>", on_canvas_click)
        
        # Force canvas update
        app.canvas.update_idletasks()

    @staticmethod
    def update_all_frames_display(app):
        """Update display for all frames mode"""
        # Check if canvas exists and is valid
        if not hasattr(app, 'canvas') or not app.canvas.winfo_exists():
            return
            
        if not hasattr(app, 'current_character') or app.current_character not in app.character_images:
            app.canvas.delete("all")
            return
        
        images = app.character_images[app.current_character]
        if not images:
            app.canvas.delete("all")
            return
        
        # Get canvas dimensions - ensure canvas is updated first
        app.canvas.update_idletasks()
        canvas_width = app.canvas.winfo_width()
        canvas_height = app.canvas.winfo_height()
        if canvas_width <= 1:  # Canvas not yet configured
            canvas_width = 400
        if canvas_height <= 1:
            canvas_height = 400
        
        # Get zoom level and calculate scale factor
        zoom_level = app.zoom_var.get()
        zoom_scale = 1.0
        
        if zoom_level == "200%":
            zoom_scale = 2.0
        elif zoom_level == "300%":
            zoom_scale = 3.0
        elif zoom_level == "400%":
            zoom_scale = 4.0
        elif zoom_level == "500%":
            zoom_scale = 5.0
        elif zoom_level == "Fit":
            # Fit mode: only one image per row, scaled to fit canvas
            zoom_scale = 1.0
        # 100% stays at 1.0
        
        # Constants
        image_spacing = 10
        padding = 10
        
        # Process all images and calculate total height needed
        processed_images = []
        max_width = 0
        max_height = 0
        
        # Get hidden frames
        char_job_key = app._get_char_job_key()
        hidden_frames = app.hidden_frames.get(char_job_key, set())
        
        for i, image_path in enumerate(images):
            if i in hidden_frames:
                continue
            try:
                # Load and process image similar to single frame
                img = Image.open(image_path)
                
                # Apply palette processing
                if img.mode == 'P':
                    original_img = img.copy()
                    raw_palette = img.getpalette()
                    original_palette = [
                        (raw_palette[j*3], raw_palette[j*3+1], raw_palette[j*3+2])
                        for j in range(PALETTE_SIZE)
                    ]
                else:
                    # Convert to palette mode
                    if img.mode in ['RGBA', 'LA', 'PA']:
                        background = Image.new('RGB', img.size, app.background_color)
                        if img.mode == 'RGBA':
                            background.paste(img, mask=img.split()[-1])
                        else:
                            background.paste(img)
                        img = background
                    elif img.mode != 'RGB':
                        img = img.convert('RGB')
                    
                    img_palette = img.quantize(colors=256, method=Image.Quantize.MEDIANCUT)
                    raw_palette = img_palette.getpalette()
                    if raw_palette:
                        original_palette = [
                            (raw_palette[j*3], raw_palette[j*3+1], raw_palette[j*3+2])
                            for j in range(min(len(raw_palette)//3, PALETTE_SIZE))
                        ]
                        while len(original_palette) < PALETTE_SIZE:
                            original_palette.append((0, 0, 0))
                    else:
                        original_palette = [(0, 0, 0)] * PALETTE_SIZE
                    
                    original_img = img_palette
                
                # Apply current palette layers using the same logic as single frame
                # Temporarily set the original_palette for this image
                original_original_palette = app.original_palette
                app.original_palette = original_palette
                
                # Get the merged palette using the same method as single frame
                result_palette = app.get_merged_palette()
                
                # Restore the original palette
                app.original_palette = original_original_palette
                
                # Create display image
                w, h = original_img.size
                display_img = Image.new("P", (w, h))
                display_img.putpalette(app._flatten_palette(result_palette))
                display_img.putdata(original_img.get_flattened_data())
                
                # Convert to RGBA and apply transparency
                rgba_img = display_img.convert("RGBA")
                pixels = rgba_img.load()
                
                # Apply character-specific transparency based on original palette colors
                char_num = app.current_character[3:]
                
                # Debug: Count transparent pixels for this frame
                transparent_count = 0
                total_pixels = w * h
                
                # Debug: Track unique colors in this frame
                unique_colors = set()
                
                # Get original image pixel data to check original palette indices
                original_pixel_data = list(original_img.get_flattened_data())
                
                for y in range(h):
                    for x in range(w):
                        r, g, b, a = pixels[x, y]
                        color = (r, g, b)
                        unique_colors.add(color)
                        
                        should_make_transparent = False
                        
                        # Get the original palette index for this pixel
                        pixel_index = y * w + x
                        if pixel_index < len(original_pixel_data):
                            palette_index = original_pixel_data[pixel_index]
                            if palette_index < len(original_palette):
                                original_color = original_palette[palette_index]
                                
                                # Check if the original color was a keying color
                                # Never make black transparent
                                if original_color != (0, 0, 0):
                                    # Use character-specific keying logic
                                    if char_num == "014":
                                        # chr014 uses more selective keying
                                        if ColorTranslator.is_chr014_keying_color(original_color):
                                            should_make_transparent = True
                                    else:
                                        # Universal keying colors for other characters
                                        if ColorTranslator.is_universal_keying_color(original_color) or original_color == (255, 0, 255):  # Magenta
                                            should_make_transparent = True
                        
                        if should_make_transparent:
                            pixels[x, y] = (0, 0, 0, 0)
                            transparent_count += 1
                    
                    # Debug: Show transparency info for this frame
                    transparency_percentage = (transparent_count / total_pixels) * 100
    
                    
                    # Debug: Show unique colors if transparency is very low (might indicate issue)
                    if transparency_percentage < 1.0:
    
                        # Check for potential transparency colors that weren't detected
                        potential_transparency_colors = []
                        for color in unique_colors:
                            r, g, b = color
                            if g > 250 and r < 10 and b < 10:  # Very green colors
                                potential_transparency_colors.append(color)
                            elif r > 250 and g < 10 and b > 250:  # Very magenta colors
                                potential_transparency_colors.append(color)
                        if potential_transparency_colors:
                            # print(f"Debug: Potential transparency colors found: {potential_transparency_colors}")
                            pass
                
                # Convert to RGB (transparent pixels become background color)
                rgb_img = app.convert_rgba_to_rgb_with_green_transparency(rgba_img, app.background_color)
                
                rgb_img = app.apply_image_transformations(rgb_img)
                w, h = rgb_img.size
                
                # Store original dimensions for this image
                original_w, original_h = w, h
                
                # Apply zoom scaling - preserve original image sizes
                if zoom_level == "Fit":
                    # Fit mode: scale each image to fit canvas width with padding, one per row
                    available_width = canvas_width - (padding * 2)
                    available_height = canvas_height - (padding * 2)
                    
                    # Scale to fit within available space while maintaining aspect ratio
                    scale_x = available_width / w
                    scale_y = available_height / h
                    scale = min(scale_x, scale_y, 1.0)  # Don't scale up beyond 100%
                    
                    new_width = int(w * scale)
                    new_height = int(h * scale)
                    if scale != 1.0:
                        rgb_img = rgb_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                else:
                    # Apply zoom scaling based on original image size
                    new_width = int(w * zoom_scale)
                    new_height = int(h * zoom_scale)
                    
                    if zoom_scale != 1.0:
                        rgb_img = rgb_img.resize((new_width, new_height), Image.Resampling.NEAREST)
                
                processed_images.append((rgb_img, new_width, new_height, i))
                max_width = max(max_width, new_width)
                max_height = max(max_height, new_height)
                
            except Exception as e:
                continue
        
        if not processed_images:
            return
        
        # Dynamic layout calculation based on actual image sizes and zoom
        if zoom_level == "Fit":
            # Fit mode: one image per row, centered
            rows = []
            current_y = padding
            
            for i, (rgb_img, img_width, img_height, original_idx) in enumerate(processed_images):
                # Center each image horizontally
                x_pos = (canvas_width - img_width) // 2
                rows.append((i, x_pos, current_y, img_width, img_height))
                current_y += img_height + image_spacing
                
                # Add space for frame label
                current_y += 15  # Additional space for text
            
            total_height = current_y - image_spacing + padding  # Remove last spacing, add bottom padding
        else:
            # Dynamic rows: pack images efficiently based on their actual sizes
            rows = []
            current_row = []
            current_row_width = 0
            current_y = padding
            available_width = canvas_width - (padding * 2)
            
            for i, (rgb_img, img_width, img_height, original_idx) in enumerate(processed_images):
                # Check if this image fits in the current row
                needed_width = img_width
                if current_row:  # Add spacing if not first in row
                    needed_width += image_spacing
                
                if current_row and (current_row_width + needed_width) > available_width:
                    # Start a new row
                    # First, finalize the current row
                    if current_row:
                        rows.append(current_row)
                        # Calculate row height (tallest image in row)
                        row_height = max(img_data[2] for img_data in current_row)
                        current_y += row_height + image_spacing + 15  # Add space for text
                    
                    # Start new row with this image
                    current_row = [(i, img_width, img_height)]
                    current_row_width = img_width
                else:
                    # Add to current row
                    current_row.append((i, img_width, img_height))
                    current_row_width += needed_width
            
            # Add the last row if it has images
            if current_row:
                rows.append(current_row)
                row_height = max(img_data[2] for img_data in current_row)
                current_y += row_height + image_spacing + 15  # Add space for text
            
            total_height = current_y + padding
            
            # Convert rows to positioned items
            positioned_items = []
            current_y = padding
            
            for row in rows:
                # Calculate total width of this row
                row_width = sum(img_data[1] for img_data in row) + (len(row) - 1) * image_spacing
                # Center the row horizontally
                start_x = (canvas_width - row_width) // 2
                
                # Calculate row height
                row_height = max(img_data[2] for img_data in row)
                
                # Position each image in the row
                current_x = start_x
                for img_index, img_width, img_height in row:
                    # Center vertically within row
                    y_pos = current_y + (row_height - img_height) // 2
                    positioned_items.append((img_index, current_x, y_pos, img_width, img_height))
                    current_x += img_width + image_spacing
                
                current_y += row_height + image_spacing + 15  # Add space for text
            
            rows = positioned_items
            
        # Clear canvas just before drawing to prevent strobing
        app.canvas.delete("all")
        if hasattr(app, 'all_frame_images'):
            app.all_frame_images.clear()
        else:
            app.all_frame_images = []
            
        for item in rows:
            if zoom_level == "Fit":
                img_index, x_pos, y_pos, img_width, img_height = item
            else:
                img_index, x_pos, y_pos, img_width, img_height = item
            
            # Unpack with original index
            rgb_img, _, _, original_idx = processed_images[img_index]
            
            # Create PhotoImage and store reference
            photo_img = ImageTk.PhotoImage(rgb_img)
            app.all_frame_images.append(photo_img)
            # Create the image
            img_id = app.canvas.create_image(x_pos, y_pos, anchor="nw", image=photo_img, tags=("image", f"frame_{original_idx}"))
            
            # Draw selection box if selected (Only in Big Picture Mode)
            is_small_preview = getattr(app, 'view_mode', '') == "small_preview"
            if (original_idx in app.selected_frames or original_idx == app.selected_frame) and not is_small_preview:
                app.canvas.create_rectangle(x_pos-2, y_pos-2, x_pos+img_width+2, y_pos+img_height+2, 
                                           outline="red", width=2, tags="selection")
            
            # Add frame number text below the image
            frame_number = original_idx + 1  # Use original index for correct frame number
            text_y = y_pos + img_height + 5
            text_color = "white" if getattr(app, 'dark_mode', False) else "black"
            text_id = app.canvas.create_text(x_pos + img_width // 2, text_y, text=str(frame_number), 
                                  anchor="n", font=("Arial", 8), fill=text_color)
            
            # Bind events - use wrappers to prevent propagation
            def on_click(e, idx):
                # Use the new on_frame_click method for Ctrl+Click support
                should_continue = True
                if hasattr(app, 'on_frame_click'):
                    # If on_frame_click returns False, we stop processing (don't identify layer)
                    result = app.on_frame_click(e, idx)
                    if result is False:
                        should_continue = False
                else:
                    # Fallback to old behavior
                    app._select_frame(idx, e)
                
                if should_continue:
                    app._identify_layer_from_click(idx, e)
                return "break"
            
            def on_right_click(e, idx):
                app._show_frame_context_menu(e, idx)
                return "break"
            
            app.canvas.tag_bind(img_id, "<Button-1>", lambda e, idx=original_idx: on_click(e, idx))
            app.canvas.tag_bind(img_id, "<Button-3>", lambda e, idx=original_idx: on_right_click(e, idx))
            app.canvas.tag_bind(text_id, "<Button-1>", lambda e, idx=original_idx: on_click(e, idx))
            app.canvas.tag_bind(text_id, "<Button-3>", lambda e, idx=original_idx: on_right_click(e, idx))

            # Store reference to prevent garbage collection
            if not hasattr(app, 'all_frame_images'):
                app.all_frame_images = []
            app.all_frame_images.append(photo_img)
        
        # Bind background click to deselect only if clicking on empty canvas
        def on_canvas_click(e):
            item = app.canvas.find_closest(e.x, e.y)
            if not item or app.canvas.type(item[0]) == "":
                app._deselect_frame()
        
        app.canvas.bind("<Button-1>", on_canvas_click)
        
        # Set vertical scroll region only - width matches canvas width
        app.canvas.config(scrollregion=(0, 0, canvas_width, total_height))
        
        # Force canvas update to ensure display refreshes
        app.canvas.update_idletasks()

    @staticmethod
    def update_custom_frames_display(app):
        """Update display for custom frames mode"""
        # Check if canvas exists and is valid
        if not hasattr(app, 'canvas') or not app.canvas.winfo_exists():
            return
            
        if not hasattr(app, 'current_character') or app.current_character not in app.character_images:
            app.canvas.delete("all")
            return
            
        # Get all images for the current character
        all_images = app.character_images[app.current_character]
        if not all_images:
            app.canvas.delete("all")
            return
            
        # Get current job and frame range settings
        current_job = app.job_var.get() if hasattr(app, 'job_var') else None
        char_settings = app.frame_range_settings.get(app.current_character, {})
        job_settings = char_settings.get(current_job, None)
        
        if job_settings:
            frame_count, start_frame, end_frame = job_settings
        else:
            frame_count = getattr(app, 'custom_frame_count', 3)
            
        # Ensure custom_start_index is within bounds
        if app.custom_start_index >= len(all_images):
            app.custom_start_index = 0
        if app.custom_start_index < 0:
            app.custom_start_index = 0
            
        # Get hidden frames
        char_job_key = app._get_char_job_key()
        hidden = app.hidden_frames.get(char_job_key, set())
        print(f"DEBUG: Custom View - Hidden Frames for {char_job_key}: {hidden}")

        # Collect visible indices starting from custom_start_index
        visible_indices = []
        idx = app.custom_start_index
        
        # Limit to available images
        total_images = len(all_images)
        
        # Try to fill the requested frame count
        while len(visible_indices) < frame_count and idx < total_images:
            if idx not in hidden:
                visible_indices.append(idx)
            idx += 1
            
        print(f"DEBUG: Custom View - Showing Indices: {visible_indices}")
        
        # Get the selected frames
        custom_images = [all_images[i] for i in visible_indices]
        if not custom_images:
            app.canvas.delete("all")
            return
            
        # Store the frame indices for reference
        app.custom_frames = list(visible_indices)
        
        # Sync custom_start_index to the first actual visible frame to prevent arrow key "locking" on hidden frames
        if visible_indices:
            app.custom_start_index = visible_indices[0]
        
        # Get canvas dimensions - ensure canvas is updated first
        app.canvas.update_idletasks()
        canvas_width = app.canvas.winfo_width()
        canvas_height = app.canvas.winfo_height()
        if canvas_width <= 1:  # Canvas not yet configured
            canvas_width = 400
        if canvas_height <= 1:
            canvas_height = 400
        
        # Get zoom level and calculate scale factor
        zoom_level = app.zoom_var.get()
        zoom_scale = 1.0
        
        if zoom_level == "200%":
            zoom_scale = 2.0
        elif zoom_level == "300%":
            zoom_scale = 3.0
        elif zoom_level == "400%":
            zoom_scale = 4.0
        elif zoom_level == "500%":
            zoom_scale = 5.0
        elif zoom_level == "Fit":
            # Fit mode: only one image per row, scaled to fit canvas
            zoom_scale = 1.0
        # 100% stays at 1.0
        
        # Constants
        image_spacing = 10
        padding = 10
        
        # Process custom images and calculate total height needed
        processed_images = []
        max_width = 0
        max_height = 0
        
        for i, image_path in enumerate(custom_images):
            original_idx = visible_indices[i]
            # No need for second hidden check as visible_indices is already filtered
            try:
                # Load and process image similar to single frame
                img = Image.open(image_path)
                
                # Apply palette processing
                if img.mode == 'P':
                    original_img = img.copy()
                    raw_palette = img.getpalette()
                    original_palette = [
                        (raw_palette[j*3], raw_palette[j*3+1], raw_palette[j*3+2])
                        for j in range(PALETTE_SIZE)
                    ]
                else:
                    # Convert to palette mode
                    if img.mode in ['RGBA', 'LA', 'PA']:
                        background = Image.new('RGB', img.size, app.background_color)
                        if img.mode == 'RGBA':
                            background.paste(img, mask=img.split()[-1])
                            img = background
                        else:
                            background.paste(img)
                            img = background
                    elif img.mode != 'RGB':
                        img = img.convert('RGB')
                    
                    img_palette = img.quantize(colors=256, method=Image.Quantize.MEDIANCUT)
                    raw_palette = img_palette.getpalette()
                    if raw_palette:
                        original_palette = [
                            (raw_palette[j*3], raw_palette[j*3+1], raw_palette[j*3+2])
                            for j in range(min(len(raw_palette)//3, PALETTE_SIZE))
                        ]
                        while len(original_palette) < PALETTE_SIZE:
                            original_palette.append((0, 0, 0))
                    else:
                        original_palette = [(0, 0, 0)] * PALETTE_SIZE
                    
                    original_img = img_palette
                
                # Apply current palette layers using the same logic as single frame
                # Temporarily set the original_palette for this image
                original_original_palette = app.original_palette
                app.original_palette = original_palette
                
                # Get the merged palette using the same method as single frame
                result_palette = app.get_merged_palette()
                
                # Restore the original palette
                app.original_palette = original_original_palette
                
                # Create display image
                w, h = original_img.size
                display_img = Image.new("P", (w, h))
                display_img.putpalette(app._flatten_palette(result_palette))
                display_img.putdata(original_img.get_flattened_data())
                
                # Convert to RGBA and apply transparency
                rgba_img = display_img.convert("RGBA")
                pixels = rgba_img.load()
                
                # Apply character-specific transparency based on original palette colors
                char_num = app.current_character[3:]
                
                # Debug: Count transparent pixels for this frame
                transparent_count = 0
                total_pixels = w * h
                
                # Debug: Track unique colors in this frame
                unique_colors = set()
                
                # Get original image pixel data to check original palette indices
                original_pixel_data = list(original_img.get_flattened_data())
                
                for y in range(h):
                    for x in range(w):
                        r, g, b, a = pixels[x, y]
                        color = (r, g, b)
                        unique_colors.add(color)
                        
                        should_make_transparent = False
                        
                        # Get the original palette index for this pixel
                        pixel_index = y * w + x
                        if pixel_index < len(original_pixel_data):
                            palette_index = original_pixel_data[pixel_index]
                            if palette_index < len(original_palette):
                                original_color = original_palette[palette_index]
                                
                                # Check if the original color was a keying color
                                # Never make black transparent
                                if original_color != (0, 0, 0):
                                    # Use character-specific keying logic
                                    if char_num == "014":
                                        # chr014 uses more selective keying
                                        if ColorTranslator.is_chr014_keying_color(original_color):
                                            should_make_transparent = True
                                    else:
                                        # Universal keying colors for other characters
                                        if ColorTranslator.is_universal_keying_color(original_color) or original_color == (255, 0, 255):  # Magenta
                                            should_make_transparent = True
                        
                        if should_make_transparent:
                            pixels[x, y] = (0, 0, 0, 0)
                            transparent_count += 1
                    
                    # Debug: Show transparency info for this frame
                    transparency_percentage = (transparent_count / total_pixels) * 100
    
                    
                    # Debug: Show unique colors if transparency is very low (might indicate issue)
                    if transparency_percentage < 1.0:
    
                        # Check for potential transparency colors that weren't detected
                        potential_transparency_colors = []
                        for color in unique_colors:
                            r, g, b = color
                            if g > 250 and r < 10 and b < 10:  # Very green colors
                                potential_transparency_colors.append(color)
                            elif r > 250 and g < 10 and b > 250:  # Very magenta colors
                                potential_transparency_colors.append(color)
                        if potential_transparency_colors:
                            # print(f"Debug: Potential transparency colors found: {potential_transparency_colors}")
                            pass
                
                # Convert to RGB (transparent pixels become background color)
                rgb_img = app.convert_rgba_to_rgb_with_green_transparency(rgba_img, app.background_color)
                
                rgb_img = app.apply_image_transformations(rgb_img)
                w, h = rgb_img.size
                
                # Store original dimensions for this image
                original_w, original_h = w, h
                
                # Apply zoom scaling - preserve original image sizes
                if zoom_level == "Fit":
                    # Fit mode: scale each image to fit canvas width with padding, one per row
                    available_width = canvas_width - (padding * 2)
                    available_height = canvas_height - (padding * 2)
                    
                    # Scale to fit within available space while maintaining aspect ratio
                    scale_x = available_width / w
                    scale_y = available_height / h
                    scale = min(scale_x, scale_y, 1.0)  # Don't scale up beyond 100%
                    
                    new_width = int(w * scale)
                    new_height = int(h * scale)
                    if scale != 1.0:
                        rgb_img = rgb_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                else:
                    # Apply zoom scaling based on original image size
                    new_width = int(w * zoom_scale)
                    new_height = int(h * zoom_scale)
                    
                    if zoom_scale != 1.0:
                        rgb_img = rgb_img.resize((new_width, new_height), Image.Resampling.NEAREST)
                
                processed_images.append((rgb_img, new_width, new_height, original_idx))
                max_width = max(max_width, new_width)
                max_height = max(max_height, new_height)
                
            except Exception as e:
                continue
        
        if not processed_images:
            return
        
        # Dynamic layout calculation based on actual image sizes and zoom
        if zoom_level == "Fit":
            # Fit mode: one image per row, centered
            rows = []
            current_y = padding
            
            for i, (rgb_img, img_width, img_height, original_idx) in enumerate(processed_images):
                # Center each image horizontally
                x_pos = (canvas_width - img_width) // 2
                rows.append((i, x_pos, current_y, img_width, img_height))
                current_y += img_height + image_spacing
                
                # Add space for frame label if enabled
                if app.show_frame_labels:
                    current_y += 15  # Additional space for text
            
            total_height = current_y - image_spacing + padding  # Remove last spacing, add bottom padding
        else:
            # Dynamic rows: pack images efficiently based on their actual sizes
            rows = []
            current_row = []
            current_row_width = 0
            current_y = padding
            available_width = canvas_width - (padding * 2)
            
            for i, (rgb_img, img_width, img_height, original_idx) in enumerate(processed_images):
                # Check if this image fits in the current row
                needed_width = img_width
                if current_row:  # Add spacing if not first in row
                    needed_width += image_spacing
                
                if current_row and (current_row_width + needed_width) > available_width:
                    # Start a new row
                    # First, finalize the current row
                    if current_row:
                        rows.append(current_row)
                        # Calculate row height (tallest image in row)
                        row_height = max(img_data[2] for img_data in current_row)
                        current_y += row_height + image_spacing
                        if app.show_frame_labels:
                            current_y += 15  # Additional space for text
                    
                    # Start new row with this image
                    current_row = [(i, img_width, img_height)]
                    current_row_width = img_width
                else:
                    # Add to current row
                    current_row.append((i, img_width, img_height))
                    current_row_width += needed_width
            
            # Add the last row if it has images
            if current_row:
                rows.append(current_row)
                row_height = max(img_data[2] for img_data in current_row)
                current_y += row_height
                if app.show_frame_labels:
                    current_y += 15
            
            total_height = current_y + padding
            
            # Convert rows to positioned items
            positioned_items = []
            current_y = padding
            
            for row in rows:
                # Calculate total width of this row
                row_width = sum(img_data[1] for img_data in row) + (len(row) - 1) * image_spacing
                # Center the row horizontally
                start_x = (canvas_width - row_width) // 2
                
                # Calculate row height
                row_height = max(img_data[2] for img_data in row)
                
                # Position each image in the row
                current_x = start_x
                for img_index, img_width, img_height in row:
                    # Center vertically within row
                    y_pos = current_y + (row_height - img_height) // 2
                    positioned_items.append((img_index, current_x, y_pos, img_width, img_height))
                    current_x += img_width + image_spacing
                
                current_y += row_height + image_spacing
                if app.show_frame_labels:
                    current_y += 15
            
            rows = positioned_items
            
        # Clear canvas just before drawing to prevent strobing
        app.canvas.delete("all")
        if hasattr(app, 'custom_frame_images'):
            app.custom_frame_images.clear()
        else:
            app.custom_frame_images = []
        
        # Create PhotoImage objects and place them
        for item in rows:
            if zoom_level == "Fit":
                img_index, x_pos, y_pos, img_width, img_height = item
            else:
                img_index, x_pos, y_pos, img_width, img_height = item
            
            # Unpack with original index
            rgb_img, _, _, original_idx = processed_images[img_index]
            
            # Create PhotoImage and store reference
            photo_img = ImageTk.PhotoImage(rgb_img)
            app.custom_frame_images.append(photo_img)
            # Create the image
            img_id = app.canvas.create_image(x_pos, y_pos, anchor="nw", image=photo_img, tags=("image", f"frame_{original_idx}"))

            # Draw selection box if selected (Only in Big Picture Mode)
            is_small_preview = getattr(app, 'view_mode', '') == "small_preview"
            if (original_idx in app.selected_frames or original_idx == app.selected_frame) and not is_small_preview:
                app.canvas.create_rectangle(x_pos-2, y_pos-2, x_pos+img_width+2, y_pos+img_height+2, 
                                           outline="red", width=2, tags="selection")
            
            # Add frame number text below the image if enabled
            if app.show_frame_labels:
                frame_number = original_idx + 1  # Use original index
                text_y = y_pos + img_height + 5  # Position text 5 pixels below the image
                # Add frame number
                text_color = "white" if getattr(app, 'dark_mode', False) else "black"
                text_id = app.canvas.create_text(x_pos + img_width // 2, text_y, text=str(frame_number), 
                                      anchor="n", font=("Arial", 8), fill=text_color)
            
            # Bind events - use wrappers to prevent propagation
            def on_click(e, idx):
                # Use the new on_frame_click method for Ctrl+Click support
                if hasattr(app, 'on_frame_click'):
                    app.on_frame_click(e, idx)
                else:
                    # Fallback to old behavior
                    app._select_frame(idx, e)
                return "break"
            
            def on_right_click(e, idx):
                app._show_frame_context_menu(e, idx)
                return "break"
            
            app.canvas.tag_bind(img_id, "<Button-1>", lambda e, idx=original_idx: on_click(e, idx))
            app.canvas.tag_bind(img_id, "<Button-3>", lambda e, idx=original_idx: on_right_click(e, idx))
            
            if app.show_frame_labels:
                app.canvas.tag_bind(text_id, "<Button-1>", lambda e, idx=original_idx: on_click(e, idx))
                app.canvas.tag_bind(text_id, "<Button-3>", lambda e, idx=original_idx: on_right_click(e, idx))
            
            # Store reference to prevent garbage collection
            app.custom_frame_images.append(photo_img)
        
        # Bind background click to deselect only if clicking on empty canvas
        def on_canvas_click(e):
            item = app.canvas.find_closest(e.x, e.y)
            if not item or app.canvas.type(item[0]) == "":
                app._deselect_frame()
        
        app.canvas.bind("<Button-1>", on_canvas_click)
        
        # Set vertical scroll region only - width matches canvas width
        app.canvas.config(scrollregion=(0, 0, canvas_width, total_height))
        
        # Force canvas update to ensure display refreshes
        app.canvas.update_idletasks()
        
        # Update navigation buttons to ensure they're properly enabled
        app.update_navigation_buttons()

    @staticmethod
    def _update_simple_preview(app):
        """Update the simple mode preview image"""
        if not hasattr(app, '_simple_preview_canvas') or not app._simple_preview_canvas or not app._simple_preview_canvas.winfo_exists():
            return
        
        if not hasattr(app, 'current_character') or not app.current_character:
            app._simple_preview_canvas.delete("all")
            return
        
        if app.current_character not in app.character_images:
            app._simple_preview_canvas.delete("all")
            return
        
        images = app.character_images[app.current_character]
        if not images or app._simple_current_frame >= len(images):
            app._simple_preview_canvas.delete("all")
            return
        
        # Get the current image with palettes applied
        try:
            # Get the original image for the current frame
            original_img = images[app._simple_current_frame]
            
            # Apply palettes to this specific frame
            current_img = app._apply_palettes_to_image_path(original_img)
            
            if not current_img:
                # Fallback to original image
                current_img = Image.open(original_img)
            
            if current_img:
                # Apply zoom
                zoom = app._simple_zoom_var.get()
                img_width, img_height = current_img.size
                
                # Get actual canvas dimensions dynamically for fit calculation
                canvas_width = app._simple_preview_canvas.winfo_width()
                canvas_height = app._simple_preview_canvas.winfo_height()
                
                # Fallback to reasonable defaults if canvas not yet configured
                if canvas_width <= 1:
                    canvas_width = 380
                if canvas_height <= 1:
                    canvas_height = 200
                
                if zoom == "Fit":
                    # Calculate scale to fit within the canvas
                    scale_x = canvas_width / img_width
                    scale_y = canvas_height / img_height
                    scale = min(scale_x, scale_y)  # Allow scaling up or down
                    new_width = int(img_width * scale)
                    new_height = int(img_height * scale)
                elif zoom == "200%":
                    new_width = img_width * 2
                    new_height = img_height * 2
                elif zoom == "300%":
                    new_width = img_width * 3
                    new_height = img_height * 3
                elif zoom == "400%":
                    new_width = img_width * 4
                    new_height = img_height * 4
                elif zoom == "500%":
                    new_width = img_width * 5
                    new_height = img_height * 5
                else:  # 100%
                    new_width = img_width
                    new_height = img_height
                
                # Resize image
                display_img = current_img.resize((new_width, new_height), Image.NEAREST)
                
                # Create PhotoImage and store reference
                photo = ImageTk.PhotoImage(display_img)
                
                # Clear canvas and display image
                app._simple_preview_canvas.delete("all")
                
                # Center the image in the canvas using dynamic dimensions + pan offset
                center_x = canvas_width // 2 + int(app._simple_pan_offset_x)
                center_y = canvas_height // 2 + int(app._simple_pan_offset_y)
                app._simple_preview_canvas.create_image(center_x, center_y, anchor="center", image=photo)
                
                # Keep reference to prevent garbage collection
                app._simple_current_image = photo
                
                # Update frame label
                if hasattr(app, '_simple_frame_label'):
                    total_frames = len(images)
                    app._simple_frame_label.config(text=f"Frame {app._simple_current_frame + 1} / {total_frames}")
                
        except Exception as e:
            print(f"CONSOLE ERROR MSG: Error updating simple preview: {e}")
            app._simple_preview_canvas.delete("all")

    @staticmethod
    def _live_refresh_swatches(app):
        """Refresh swatch button colors from the currently selected layer; keep selection highlight."""
        # Don't refresh if we're currently updating selection to prevent conflicts
        if getattr(app, '_updating_live_selection', False):
            return
            
        ly = app._live_current_layer()
        if ly is None:
            return
        cols = ly.colors
        
        if app.live_pal_ui_mode == "Simple":
            # Simple mode: only update editable color swatches
            editable_indices = app._get_editable_color_indices()
            for display_idx, palette_idx in enumerate(editable_indices):
                if display_idx >= len(app._live_swatches) or app._live_swatches[display_idx] is None:
                    continue
                
                r, g, b = cols[palette_idx] if isinstance(cols[palette_idx], tuple) else (0, 0, 0)
                try:
                    canvas = app._live_swatches[display_idx]
                    hex_color = f"#{int(r):02x}{int(g):02x}{int(b):02x}"
                    canvas.delete("all")
                    # Use larger rectangle size for simple mode (40x40)
                    canvas.create_rectangle(1, 1, 39, 39, fill=hex_color, outline="black", width=1)
                except Exception as e:
                    pass
        else:
            # Advanced mode: update all 256 colors
            for i in range(PALETTE_SIZE):
                r,g,b = cols[i] if isinstance(cols[i], tuple) else (0,0,0)
                try:
                    # Update canvas rectangle color
                    canvas = app._live_swatches[i]
                    if canvas is None:
                        continue
                    hex_color = f"#{int(r):02x}{int(g):02x}{int(b):02x}"
                    canvas.delete("all")
                    canvas.create_rectangle(1, 1, 19, 19, fill=hex_color, outline="black", width=1)
                except Exception as e:
                    pass
        
        # Keep selection visuals
        if hasattr(app, "_update_selection_ui"):
            app._update_selection_ui()
        
        # Update simple mode preview if in simple mode
        if app.live_pal_ui_mode == "Simple" and hasattr(app, '_update_simple_preview'):
            app._update_simple_preview()

    @staticmethod
    def refresh_custom_pals(app, update_ui=True):
        """Refresh custom pals by reloading them and optionally updating the UI"""
        # Remove the guard clause - we want to refresh all custom pals regardless of current character
        
        # Clear existing custom palettes from ALL data structures
        root_dir = getattr(app, "root_dir", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        for char_id in list(app.fashion_palettes.keys()):
            # Get the absolute paths of custom fashion palette directories
            custom_fashion_pals_path = os.path.join(root_dir, "exports", "custom_pals", "fashion")
            old_custom_fashion_pals_path = os.path.join(root_dir, "exports", "custom_fashion_pals")
            custom_fashion_abs = os.path.abspath(custom_fashion_pals_path)
            old_custom_fashion_abs = os.path.abspath(old_custom_fashion_pals_path)
            
            # Only keep palettes that are NOT in custom fashion directories
            app.fashion_palettes[char_id] = [
                path for path in app.fashion_palettes[char_id] 
                if not (os.path.abspath(path).startswith(custom_fashion_abs) or 
                       os.path.abspath(path).startswith(old_custom_fashion_abs))
            ]
        
        for char_id in list(app.hair_palettes.keys()):
            # Get the absolute paths of custom hair palette directories
            custom_hair_pals_path = os.path.join(root_dir, "exports", "custom_pals", "hair")
            old_custom_fashion_pals_path = os.path.join(root_dir, "exports", "custom_fashion_pals")
            custom_hair_abs = os.path.abspath(custom_hair_pals_path)
            old_custom_fashion_abs = os.path.abspath(old_custom_fashion_pals_path)
            
            # Only keep palettes that are NOT in custom directories
            app.hair_palettes[char_id] = [
                path for path in app.hair_palettes[char_id] 
                if not (os.path.abspath(path).startswith(custom_hair_abs) or 
                       os.path.abspath(path).startswith(old_custom_fashion_abs))
            ]
        
        # Reload custom palettes from new directory structure
        custom_pals_paths = app.get_custom_pals_paths()
        for custom_pals_path in custom_pals_paths:
            if not os.path.exists(custom_pals_path):
                continue
            for file in os.listdir(custom_pals_path):
                if file.lower().endswith('.pal'):
                    # Check for fashion palettes (chr###_w#.pal through chr###_w######.pal)
                    fashion_match = re.match(r'^chr(\d{3})_w\d+\.pal$', file.lower())
                    if fashion_match:
                        char_num = fashion_match.group(1)
                        char_id_for_pal = f"chr{char_num}"
                        if char_id_for_pal not in app.fashion_palettes:
                            app.fashion_palettes[char_id_for_pal] = []
                        
                        # Validate the palette file before adding it
                        palette_path = os.path.join(custom_pals_path, file)
                        try:
                            with open(palette_path, "rb") as f:
                                data = f.read()
                            
                            if len(data) != PALETTE_SIZE * 3:
                                continue
                            
                            # Validate that all bytes are valid (0-255)
                            valid_file = True
                            for i in range(PALETTE_SIZE * 3):
                                if not (0 <= data[i] <= 255):
                                    valid_file = False
                                    break
                            
                            if valid_file:
                                app.fashion_palettes[char_id_for_pal].append(palette_path)
                            
                        except Exception as e:
                            print(f"CONSOLE ERROR MSG: Failed to load custom fashion palette {file}: {e}")
                            continue
                    
                    # Check for hair palettes (chr###_#.pal)
                    hair_match = re.match(r'^chr(\d{3})_\d+\.pal$', file.lower())
                    if hair_match:
                        char_num = hair_match.group(1)
                        char_id_for_pal = f"chr{char_num}"
                        if char_id_for_pal not in app.hair_palettes:
                            app.hair_palettes[char_id_for_pal] = []
                        
                        # Validate the palette file before adding it
                        palette_path = os.path.join(custom_pals_path, file)
                        try:
                            with open(palette_path, "rb") as f:
                                data = f.read()
                            
                            if len(data) != PALETTE_SIZE * 3:
                                continue
                            
                            # Validate that all bytes are valid (0-255)
                            valid_file = True
                            for i in range(PALETTE_SIZE * 3):
                                if not (0 <= data[i] <= 255):
                                    valid_file = False
                                    break
                            
                            if valid_file:
                                app.hair_palettes[char_id_for_pal].append(palette_path)
                            
                        except Exception as e:
                            print(f"CONSOLE ERROR MSG: Failed to load custom hair palette {file}: {e}")
                            continue
        
        # Update the UI sections to reflect the new custom pals (only if requested)
        if update_ui:
            # Save current selections before updating UI
            saved_hair_selection = getattr(app, 'hair_var', tk.StringVar()).get() if hasattr(app, 'hair_var') else "NONE"
            saved_third_job_selection = getattr(app, 'third_job_var', tk.StringVar()).get() if hasattr(app, 'third_job_var') else "NONE"
            saved_fashion_selections = {}
            if hasattr(app, 'fashion_vars'):
                for fashion_type, var in app.fashion_vars.items():
                    saved_fashion_selections[fashion_type] = var.get()
            
            app.update_hair_section()
            app.update_fashion_section()
            
            # Restore selections after updating UI
            if hasattr(app, 'hair_var') and saved_hair_selection != "NONE":
                app.hair_var.set(saved_hair_selection)
            
            if hasattr(app, 'third_job_var') and saved_third_job_selection != "NONE":
                app.third_job_var.set(saved_third_job_selection)
            
            if hasattr(app, 'fashion_vars'):
                for fashion_type, saved_value in saved_fashion_selections.items():
                    if fashion_type in app.fashion_vars and saved_value != "NONE":
                        app.fashion_vars[fashion_type].set(saved_value)

