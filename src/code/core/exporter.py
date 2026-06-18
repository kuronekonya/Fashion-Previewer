import time
import re
import os
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image
from tkinter import ttk
from code.core.color_translator import ColorTranslator
from fashionpreviewer import PALETTE_SIZE
from code.utils.theme_manager import ThemeManager

class Exporter:
        def export_background(app):
            """Export based on current settings (BMP or PNG)"""
            if app.use_bmp_export:
                app.export_background_bmp()
            else:
                app.export_transparent_png()
    
        def export_background_bmp(app, frame=None, force_portrait=False, silent=False):
            """Export current image as BMP with background color
            
            Args:
                frame: Optional frame to export instead of current frame
                force_portrait: If True, forces portrait mode regardless of settings
                silent: If True, bypasses file dialog and appends timestamp"""
            if not app.original_image:
                messagebox.showinfo("Notice", "No image loaded.")
                return
                
            # Save current state
            current_layers = [layer.active for layer in app.palette_layers]
                
            # Get base paths
            root_dir = getattr(app, "root_dir", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            export_dir = os.path.join(root_dir, "exports", "images")
            
            # Get the frame index for export (respects user choice)
            frame_index = frame if frame is not None else app.get_current_displayed_frame()
            
            # Save current portrait setting if forcing portrait
            old_portrait = app.use_portrait_export
            if force_portrait:
                app.use_portrait_export = True
            
            # Get base file name without extension using view count from statistics
            key = f"{app.current_character}_{app.current_job}"
            view_count = app.statistics.character_edits.get(key, {'views': 0})['views']
            base_name = f"{app.current_character}_view{view_count}"
            
            if silent:
                timestamp = int(time.time())
                base_name = f"{base_name}_{timestamp}"
            
            # Get the current image with all palettes applied
            if not hasattr(app, 'update_single_frame_display'):
                raise AttributeError("Cannot get current display image")
                
            img = app.get_display_image_for_export(frame_index)
            if img is None:
                raise AttributeError("Failed to get current display image")
            
            try:
                # Get save path for regular BMP
                default_path = os.path.join(export_dir, f"{base_name}.bmp")
                
                if silent:
                    file_path = default_path
                else:
                    file_path = filedialog.asksaveasfilename(
                        defaultextension=".bmp",
                        filetypes=[("BMP files", "*.bmp")],
                        initialfile=os.path.basename(default_path),
                        initialdir=os.path.dirname(default_path)
                    )
                
                if not file_path:
                    return
                    
                # Get the target directory and base filename from user's chosen path
                target_dir = os.path.dirname(file_path)
                base_filename = os.path.splitext(os.path.basename(file_path))[0]
                
                # Prepare all export operations
                export_ops = []
                
                # Get save paths for each format
                regular_path = file_path  # Use exactly what the user chose
                portrait_path = os.path.join(target_dir, f"{base_filename}_illu.bmp")  # Just _illu for regular portraits
                
                # Regular BMP export
                def save_regular():
                    img.save(regular_path, "BMP")
                    return "Regular BMP"
                export_ops.append(save_regular)
                
                # Portrait export (if selected)
                if app.use_portrait_export:
                    def save_portrait():
                        # Create a 105x105 image
                        x = (105 - img.width) // 2
                        y = (105 - img.height) // 2
                        
                        # Create mask for non-background pixels in the frame
                        mask = Image.new("L", img.size, 0)
                        for i, pixel in enumerate(img.get_flattened_data()):
                            if pixel != app.background_color:
                                mask.putpixel((i % img.width, i // img.width), 255)
                        
                        outputs = []
                        
                        # Handle regular background color output
                        if app.cute_bg_option in ["no_cute_bg", "both"]:
                            # Create image with user's background color
                            regular_img = Image.new("RGB", (105, 105), app.background_color)
                            regular_img.paste(img, (x, y), mask)
                            regular_img = app._apply_transforms(regular_img)
                            regular_img.save(portrait_path.replace(".bmp", "_illu.bmp"), "BMP", quality=24)
                            outputs.append("Portrait (105x105) with Background Color")
                        
                        # Handle cute background output
                        if app.cute_bg_option in ["cute_bg", "both"]:
                            if app.myshop_base is None:
                                messagebox.showerror("Error", "MyShop base image not found. Please ensure myshop_base.bmp exists in the assets/nonremovable_assets folder.")
                                return "Failed: MyShop base image not found"
                            
                            # Create a copy of the base image and convert to RGB
                            cute_img = app.myshop_base.copy().convert("RGB")
                            
                            # Replace magenta (255, 0, 255) with user's background color
                            data = list(cute_img.get_flattened_data())
                            for i, pixel in enumerate(data):
                                if pixel == (255, 0, 255):  # Magenta
                                    data[i] = app.background_color
                            cute_img.putdata(data)
                            
                            # Paste the frame onto the base image
                            cute_img.paste(img, (x, y), mask)
                            cute_img = app._apply_transforms(cute_img)
                            cute_img.save(portrait_path.replace(".bmp", "_illu_cute.bmp"), "BMP", quality=24)
                            outputs.append("Portrait (105x105) with Cute BG")
                        
                        return " & ".join(outputs)
                    export_ops.append(save_portrait)
                
                
                # Execute all export operations
                exported = []
                errors = []
                for export_op in export_ops:
                    try:
                        result = export_op()
                        exported.append(result)
                    except Exception as e:
                        errors.append(str(e))
                
                # Show results if not silent
                if not silent:
                    if exported:
                        success_msg = "Exported:\n- " + "\n- ".join(exported)
                        if errors:
                            success_msg += "\n\nErrors:\n- " + "\n- ".join(errors)
                        messagebox.showinfo("Export Complete", success_msg)
                    else:
                        error_msg = "Failed to export any files:\n- " + "\n- ".join(errors)
                        messagebox.showerror("Export Failed", error_msg)
                    
                # Restore layer state
                for layer, was_active in zip(app.palette_layers, current_layers):
                    layer.active = was_active
                    
                # Restore portrait setting if it was forced
                if force_portrait:
                    app.use_portrait_export = old_portrait
                
            except Exception as e:
                # Restore layer state even on error
                for layer, was_active in zip(app.palette_layers, current_layers):
                    layer.active = was_active
                    
                # Restore portrait setting if it was forced
                if force_portrait:
                    app.use_portrait_export = old_portrait
                    
                messagebox.showerror("Error", f"Failed to export image: {e}")
    
        def export_transparent_png(app):
            """Export the current frame as a transparent PNG with palettes applied"""
            if not app.original_image:
                messagebox.showinfo("Notice", "Please load a character image first.")
                return
                
            # Save current state
            current_layers = [layer.active for layer in app.palette_layers]
            
            # Get base paths
            root_dir = getattr(app, "root_dir", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            export_dir = os.path.join(root_dir, "exports", "images")
            
            # Get the frame index for export (respects user choice)
            app.get_current_displayed_frame()
            
            # Get base file name without extension using view count from statistics
            key = f"{app.current_character}_{app.current_job}"
            view_count = app.statistics.character_edits.get(key, {'views': 0})['views']
            base_name = f"{app.current_character}_view{view_count}"
            
            # Get save path for regular PNG
            default_path = os.path.join(export_dir, f"{base_name}.png")
            file_path = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[("PNG Images", "*.png")],
                initialfile=os.path.basename(default_path),
                initialdir=os.path.dirname(default_path)
            )
            
            if not file_path:
                return
                
            # Get the target directory and base filename from user's chosen path
            target_dir = os.path.dirname(file_path)
            base_filename = os.path.splitext(os.path.basename(file_path))[0]
            
            try:
                # Get the merged palette
                app.get_merged_palette()
                
                # Get the current image with all palettes applied
                img = app.get_display_image_for_export()
                if img is None:
                    raise AttributeError("Failed to get current display image")
                
                # Prepare export operations
                export_ops = []
                
                # Regular PNG export
                def save_regular():
                    # Convert to RGBA to handle transparency
                    rgba_img = img.convert("RGBA")
                    pixels = rgba_img.load()
                    
                    # Apply character-specific transparency
                    if hasattr(app, 'current_character') and app.current_character:
                        char_num = app.current_character[3:]
                        transparent_count = 0
                        img.width * img.height
                        
                        for y in range(img.height):
                            for x in range(img.width):
                                pixel = img.getpixel((x, y))
                                should_make_transparent = False
                                
                                # Check if the pixel should be transparent
                                if pixel != (0, 0, 0):  # Never make black transparent
                                    if char_num == "014":
                                        if ColorTranslator.is_chr014_keying_color(pixel):
                                            should_make_transparent = True
                                    else:
                                        if ColorTranslator.is_universal_keying_color(pixel) or pixel == (255, 0, 255):  # Magenta
                                            should_make_transparent = True
                                
                                if should_make_transparent:
                                    pixels[x, y] = (0, 0, 0, 0)  # Transparent
                                    transparent_count += 1
                    
                    # Save regular PNG
                        rgba_img = app._apply_transforms(rgba_img)
                        rgba_img.save(file_path, "PNG")
                    return "Regular PNG"
                
                export_ops.append(save_regular)
                
                # Portrait export (if selected)
                if app.use_portrait_export:
                    def save_portrait():
                        # Create a 105x105 image
                        x = (105 - img.width) // 2
                        y = (105 - img.height) // 2
                        
                        # Create mask for non-background pixels in the frame
                        mask = Image.new("L", img.size, 0)
                        for i, pixel in enumerate(img.get_flattened_data()):
                            if pixel != app.background_color:
                                mask.putpixel((i % img.width, i // img.width), 255)
                        
                        outputs = []
                        
                        # Handle regular portrait output with transparency
                        if app.cute_bg_option in ["no_cute_bg", "both"]:
                            # Create transparent base image
                            portrait_img = Image.new("RGBA", (105, 105), (0, 0, 0, 0))
                            # Convert frame to RGBA for transparency
                            frame_rgba = img.convert("RGBA")
                            # Make background color transparent
                            frame_data = list(frame_rgba.get_flattened_data())
                            for i, pixel in enumerate(frame_data):
                                if pixel[:3] == app.background_color:
                                    frame_data[i] = (0, 0, 0, 0)
                            frame_rgba.putdata(frame_data)
                            # Paste the frame onto the transparent base
                            portrait_img.paste(frame_rgba, (x, y), mask)
                            # Save as PNG with _illu suffix (no "regular" suffix)
                            portrait_path = os.path.join(target_dir, f"{base_filename}_illu.png")
                            portrait_img = app._apply_transforms(portrait_img)
                            portrait_img.save(portrait_path, "PNG")
                            outputs.append("Portrait (105x105) with Transparency")
                        
                        # Handle cute background output
                        if app.cute_bg_option in ["cute_bg", "both"]:
                            if app.myshop_base is None:
                                messagebox.showerror("Error", "MyShop base image not found. Please ensure myshop_base.bmp exists in the assets/nonremovable_assets folder.")
                                return "Failed: MyShop base image not found"
                            
                            # Create a copy of the base image and convert to RGBA
                            cute_img = app.myshop_base.copy().convert("RGBA")
                            
                            # Replace magenta with transparency
                            data = list(cute_img.get_flattened_data())
                            for i, pixel in enumerate(data):
                                if pixel[:3] == (255, 0, 255):  # Magenta
                                    data[i] = (0, 0, 0, 0)  # Transparent
                            cute_img.putdata(data)
                            
                            # Convert frame to RGBA and make background transparent
                            frame_rgba = img.convert("RGBA")
                            frame_data = list(frame_rgba.get_flattened_data())
                            for i, pixel in enumerate(frame_data):
                                if pixel[:3] == app.background_color:
                                    frame_data[i] = (0, 0, 0, 0)
                            frame_rgba.putdata(frame_data)
                            
                            # Paste the frame onto the base image
                            cute_img.paste(frame_rgba, (x, y), mask)
                            # Save as PNG with _illu_cute suffix
                            cute_path = os.path.join(target_dir, f"{base_filename}_illu_cute.png")
                            cute_img = app._apply_transforms(cute_img)
                            cute_img.save(cute_path, "PNG")
                            outputs.append("Portrait (105x105) with Cute BG")
                        
                        return " & ".join(outputs)
                    
                    export_ops.append(save_portrait)
                
                # Execute all export operations
                exported = []
                errors = []
                for export_op in export_ops:
                    try:
                        result = export_op()
                        exported.append(result)
                    except Exception as e:
                        errors.append(str(e))
                
                # Show results
                if exported:
                    success_msg = "Exported:\n- " + "\n- ".join(exported)
                    if errors:
                        success_msg += "\n\nErrors:\n- " + "\n- ".join(errors)
                    messagebox.showinfo("Export Complete", success_msg)
                else:
                    error_msg = "Failed to export any files:\n- " + "\n- ".join(errors)
                    messagebox.showerror("Export Failed", error_msg)
                    
                # Restore layer state
                for layer, was_active in zip(app.palette_layers, current_layers):
                    layer.active = was_active
                
            except Exception as e:
                # Restore layer state even on error
                for layer, was_active in zip(app.palette_layers, current_layers):
                    layer.active = was_active
                messagebox.showerror("Error", f"Export failed: {e}")
    
        def export_all_frames(app):
            """Export all frames in the current character's folder with current palettes applied"""
            if not hasattr(app, 'current_character') or not app.current_character:
                messagebox.showinfo("Notice", "Please select a character first.")
                return
                
            # Save current state
            current_layers = [layer.active for layer in app.palette_layers]
            
            if not app.character_images or app.current_character not in app.character_images:
                messagebox.showinfo("Notice", "No images found for this character.")
                return
            
            # Create a folder name based on character and current palettes
            char_name = app.character_var.get()
            job_name = app.job_var.get()
            
            # Clean up job name (remove "Job" part)
            if job_name.endswith(" Job"):
                job_name = job_name[:-4]  # Remove " Job" suffix
            
            # Get selected palette names for folder naming
            palette_parts = []
            
            # Add hair palette (h# format)
            if app.hair_var.get() != "NONE":
                hair_name = os.path.basename(app.hair_var.get())
                hair_name = hair_name.replace('.pal', '')
                if hair_name.startswith('chr') and '_' in hair_name:
                    hair_name = hair_name.split('_', 1)[1]  # Remove chr###_ prefix
                palette_parts.append(f"h{hair_name}")
            
            # Add fashion palettes (f1w##, f2w##, etc.)
            for fashion_type, var in app.fashion_vars.items():
                if var.get() != "NONE":
                    fashion_name = os.path.basename(var.get())
                    fashion_name = fashion_name.replace('.pal', '')
                    if fashion_name.startswith('chr') and '_' in fashion_name:
                        fashion_name = fashion_name.split('_', 1)[1]  # Remove chr###_ prefix
                    
                    # Extract fashion type number (fashion_1 -> f1, fashion_2 -> f2, etc.)
                    fashion_num = fashion_type.split('_')[1]
                    palette_parts.append(f"f{fashion_num}{fashion_name}")
            
            # Add 3rd job base fashion (just the number)
            if hasattr(app, 'third_job_var') and app.third_job_var.get() != "NONE":
                third_job_name = os.path.basename(app.third_job_var.get())
                third_job_name = third_job_name.replace('.pal', '')
                palette_parts.append(third_job_name)
            
            # Create folder name
            if palette_parts:
                folder_name = f"{char_name}_{job_name}_{'_'.join(palette_parts)}"
            else:
                folder_name = f"{char_name}_{job_name}_original"
            
            # Clean folder name (remove invalid characters and fix path separators)
            folder_name = "".join(c for c in folder_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            folder_name = folder_name.replace(' ', '_')
            folder_name = folder_name.replace('\\', '_')  # Replace backslashes with underscores
            folder_name = folder_name.replace('/', '_')   # Replace forward slashes with underscores
            
            # Ask user for base output directory (default to exports/images)
            default_export_dir = os.path.join(app.root_dir, "exports", "images")
            base_output_dir = filedialog.askdirectory(
                title="Select base directory for export",
                initialdir=default_export_dir
            )
            if not base_output_dir:
                return
            
            # Create the specific folder
            output_dir = os.path.join(base_output_dir, folder_name)
            try:
                os.makedirs(output_dir, exist_ok=True)
                print(f"Export directory created: {output_dir}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to create export directory: {e}")
                return
            
            try:
                images = app.character_images[app.current_character]
                total_images = len(images)
                
                # Show progress dialog
                progress_window = tk.Toplevel(app.master)
                progress_window.title("Exporting Frames")
                progress_window.transient(app.master)
                progress_window.grab_set()
                
                progress_label = tk.Label(progress_window, text="Exporting frames...")
                progress_label.pack(pady=10)
                
                progress_bar = ttk.Progressbar(progress_window, length=250, mode='determinate')
                progress_bar.pack(pady=5)
                
                # Center the progress window after content is created
                progress_window.update_idletasks()
                app._center_window_on_parent(progress_window, app.master)
                
                exported_count = 0
                
                for i, image_path in enumerate(images):
                    # Update progress
                    progress_bar['value'] = (i / total_images) * 100
                    progress_label.config(text=f"Exporting frame {i+1}/{total_images}")
                    progress_window.update()
                    
                    try:
                        # Load the image
                        img = Image.open(image_path)
                        
                        # Apply the same processing as the current frame
                        if img.mode == 'P':
                            # Already palette mode - preserve original structure
                            original_img = img.copy()
                            raw_palette = img.getpalette()
                            original_palette = [
                                (raw_palette[j*3], raw_palette[j*3+1], raw_palette[j*3+2])
                                for j in range(PALETTE_SIZE)
                            ]
                        else:
                            # For non-palette images, convert more carefully to preserve transparency
                            if img.mode in ['RGBA', 'LA', 'PA']:
                                # Handle alpha channel properly
                                if img.mode == 'RGBA':
                                    # Create a new image with transparent background
                                    new_img = Image.new('RGBA', img.size, (0, 0, 0, 0))
                                    new_img.paste(img, mask=img.split()[-1])
                                    img = new_img
                                else:
                                    # Convert to RGBA first
                                    img = img.convert('RGBA')
                            
                            # Convert to RGB if needed, but preserve transparency info
                            if img.mode == 'RGBA':
                                # Create a palette that preserves transparency
                                background = Image.new('RGB', img.size, (0, 255, 0))  # Use green as background
                                background.paste(img, mask=img.split()[-1])
                                img = background
                            elif img.mode != 'RGB':
                                img = img.convert('RGB')
                            
                            # Use a more careful quantization that preserves keying colors
                            img_palette = img.quantize(colors=256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
                            raw_palette = img_palette.getpalette()
                            if raw_palette:
                                original_palette = [
                                    (raw_palette[j*3], raw_palette[j*3+1], raw_palette[j*3+2])
                                    for j in range(min(len(raw_palette)//3, PALETTE_SIZE))
                                ]
                                while len(original_palette) < PALETTE_SIZE:
                                    original_palette.append((0, 255, 0))  # Fill with green instead of black
                            else:
                                original_palette = [(0, 255, 0)] * PALETTE_SIZE  # Use green instead of black
                            
                            original_img = img_palette
                        
                        # Apply current palette layers using the same logic as single frame
                        # Temporarily set the original_palette for this image
                        original_original_palette = app.original_palette
                        app.original_palette = original_palette
                        
                        # Get the merged palette using the same method as single frame
                        result_palette = app.get_merged_palette()
                        
                        # Restore the original palette
                        app.original_palette = original_original_palette
                        
                        # Create output image
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
                        w * h
                        
                        # Get original image pixel data to check original palette indices
                        original_pixel_data = list(original_img.get_flattened_data())
                        
                        for y in range(h):
                            for x in range(w):
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
        
                        
                        # Save the image
                        filename = os.path.basename(image_path)
                        name, ext = os.path.splitext(filename)
                        output_path = os.path.join(output_dir, f"{name}.png")
                        rgba_img = app._apply_transforms(rgba_img)
                        rgba_img.save(output_path, "PNG")
                        
                        exported_count += 1
                        
                    except Exception as e:
                        print(f"CONSOLE ERROR MSG: Error processing {image_path}: {e}")
                        continue
                
                progress_window.destroy()
                messagebox.showinfo("Success", f"Exported {exported_count}/{total_images} frames to:\n{output_dir}")
                
                # Restore layer state
                for layer, was_active in zip(app.palette_layers, current_layers):
                    layer.active = was_active
                
            except Exception as e:
                # Restore layer state even on error
                for layer, was_active in zip(app.palette_layers, current_layers):
                    layer.active = was_active
                messagebox.showerror("Error", f"Export failed: {e}")
    
        def export_pal(app):
            """Export all active palettes as one combined palette in either VGA 24-bit format or PNG grid"""
            if not app.palette_layers:
                messagebox.showinfo("Notice", "No palette layers loaded.")
                return
            
            # Get all active layers
            active_layers = [layer for layer in app.palette_layers if layer.active]
            
            if not active_layers:
                messagebox.showinfo("Notice", "No active palette layers to export.")
                return
            
            # Set initial directory based on palette format
            root_dir = getattr(app, "root_dir", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
            # Set file type and initial directory based on palette format
            if app.palette_format == "pal":
                file_types = [("VGA 24-bit Palette Files", "*.pal")]
                default_ext = ".pal"
                initial_dir = os.path.join(root_dir, "exports", "full_pals")
            else:  # png
                file_types = [("PNG Files", "*.png")]
                default_ext = ".png"
                initial_dir = os.path.join(root_dir, "exports", "images")
            
            path = filedialog.asksaveasfilename(
                defaultextension=default_ext,
                initialdir=initial_dir,
                filetypes=file_types
            )
            if not path:
                return
            
            try:
                # Get the merged palette (with export_mode=True to preserve keyed colors for game engine)
                merged_palette = app.get_merged_palette(export_mode=True)
                
                if app.palette_format == "pal":
                    # Ensure we have exactly 256 colors for VGA palette
                    while len(merged_palette) < 256:
                        merged_palette.append((0, 0, 0))  # Fill with black if needed
                    
                    # Write VGA 24-bit format: each color as 3 bytes (R, G, B) in sequence
                    with open(path, "wb") as f:
                        for r, g, b in merged_palette[:256]:  # Ensure exactly 256 colors
                            f.write(bytes([r, g, b]))
                else:  # PNG grid
                    # Create a 503x503 image (16x16 grid where each color is ~31.4375x31.4375)
                    grid_img = Image.new("RGB", (503, 503), (0, 0, 0))
                    
                    # Fill in the colors in a 16x16 grid
                    for i, color in enumerate(merged_palette):
                        if i >= 256:  # Maximum 256 colors in 16x16 grid
                            break
                        
                        # Calculate position in 16x16 grid
                        grid_x = i % 16
                        grid_y = i // 16
                        
                        # Calculate pixel ranges for this cell, handling the remainder
                        x_start = (grid_x * 503) // 16
                        x_end = ((grid_x + 1) * 503) // 16
                        y_start = (grid_y * 503) // 16
                        y_end = ((grid_y + 1) * 503) // 16
                        
                        # Fill the exact pixel range for this cell
                        for px in range(x_start, x_end):
                            for py in range(y_start, y_end):
                                grid_img.putpixel((px, py), color)
                    
                    # Save the PNG
                    grid_img = app._apply_transforms(grid_img)
                    grid_img.save(path, "PNG")
                
                # Show which layers were combined
                layer_names = [layer.name for layer in active_layers]
                messagebox.showinfo("Success", f"Exported VGA 24-bit palette to {path}\n\nCombined layers:\n" + "\n".join(f"• {name}" for name in layer_names))
            except Exception as e:
                messagebox.showerror("Error", f"Export failed: {e}")
    
        def bulk_export_visuals(app):
            """Bulk export visuals: Portrait + Icons for all selected fashions"""
            import os
            from tkinter import messagebox
            from icon_handler import IconHandler
            
            exported_count = 0
            try:
                # 1. Export Portrait (silently honoring settings)
                frame = app.get_current_displayed_frame()
                if frame is not None:
                    app.export_background_bmp(frame, force_portrait=True, silent=True)
                    exported_count += 1
                    
                # 2. Export Icons (for all loaded fashion palettes)
                if hasattr(app, 'palette_layers'):
                    icon_handler = IconHandler()
                    icon_handler.main_window = app
                    
                    # Use a timestamp to prevent overwriting
                    timestamp = int(time.time())
                    
                    for layer in app.palette_layers:
                        # Export all loaded palettes, regardless of whether they are checked as "active" in the checklist
                        # Extract fashion type safely (e.g. fashion_1)
                        if hasattr(layer, 'palette_type') and layer.palette_type.startswith('fashion_'):
                            fashion_type = layer.palette_type
                            
                            # Use the layer name but append the timestamp to prevent overwrites
                            icon_pal_name = f"{os.path.splitext(layer.name)[0]}_{timestamp}"
                            
                            success = icon_handler.save_as_icon(
                                app.current_character,
                                fashion_type,
                                layer.colors,
                                icon_pal_name
                            )
                            if success:
                                exported_count += 1
                
                if exported_count > 0:
                    messagebox.showinfo("Success", f"Successfully bulk exported {exported_count} visuals/icons.\nPortraits were saved to exports/images.\nIcons were saved to exports/icons.")
                else:
                    messagebox.showinfo("Notice", "Nothing was exported.")
                    
            except Exception as e:
                print(f"CONSOLE ERROR MSG: Error in bulk_export_visuals: {e}")
                messagebox.showerror("Error", f"Failed to bulk export visuals: {e}")
    
        def _quick_export_icon(app):
            """Quickly export icon without opening the editor."""
            from tkinter import messagebox
            from icon_handler import IconHandler
            
            # Check if we have active layers
            active_layers = [ly for ly in app.palette_layers if getattr(ly, "active", False)]
            if not active_layers:
                return  # Silently return - no prompt
                
            # Determine the target layer first based on last_selected_palette
            last_pal = getattr(app, 'last_selected_palette', None)
            target_layer = None
            if last_pal:
                import os
                last_pal_base = os.path.basename(last_pal)
                for ly in active_layers:
                    if ly.name == last_pal_base:
                        target_layer = ly
                        break
            
            # If the targeted layer is hair or third job, silently return
            if target_layer and hasattr(target_layer, 'palette_type'):
                palette_type = str(target_layer.palette_type).lower()
                if palette_type in ("hair", "3rd_job_base"):
                    return  # Silently return - no prompt for hair/third job
            
            # Filter out hair and third job layers
            base_fashion_layers = [ly for ly in active_layers if hasattr(ly, "palette_type") and 
                                 ly.palette_type.startswith("fashion_") and 
                                 not (ly.name and ("hair" in ly.name.lower() or "third" in ly.name.lower()))]
                                 
            if not base_fashion_layers:
                return  # Silently return - no prompt
    
            # If we have a target layer from last_selected_palette, use it if it's fashion
            selected_layer = None
            if target_layer and hasattr(target_layer, "palette_type") and target_layer.palette_type.startswith("fashion_"):
                selected_layer = target_layer
    
            if not selected_layer:
                if len(base_fashion_layers) > 1:
                    # Fallback to dialog if we couldn't determine target or target wasn't fashion
                    import tkinter as tk
                    from tkinter import ttk
                    # ... (rest of the dialog logic as is)
                    
                    dialog = tk.Toplevel(app.master)
                    dialog.title("Select Layer")
                    dialog.geometry("350x150")
                    dialog.transient(app.master)
                    dialog.grab_set()
                    
                    # Center dialog
                    if hasattr(app, '_center_window_on_parent'):
                        app._center_window_on_parent(dialog, app.master)
                    
                    tk.Label(dialog, text="Multiple layers selected.\nChoose which one to export:", pady=10).pack()
                    
                    selected_var = tk.StringVar()
                    # Default to first one
                    selected_var.set(base_fashion_layers[0].name)
                    
                    # Map names to layers
                    layer_map = {ly.name: ly for ly in base_fashion_layers}
                    
                    combo = ttk.Combobox(dialog, textvariable=selected_var, values=list(layer_map.keys()), state="readonly", width=30)
                    combo.pack(padx=20, pady=5)
                    
                    result = {"layer": None}
                    
                    def on_ok():
                        if selected_var.get() in layer_map:
                            result["layer"] = layer_map[selected_var.get()]
                        dialog.destroy()
                        
                    def on_cancel():
                        dialog.destroy()
                    
                    # Handle window close button
                    dialog.protocol("WM_DELETE_WINDOW", on_cancel)
                        
                    btn_frame = tk.Frame(dialog)
                    btn_frame.pack(pady=10)
                    
                    tk.Button(btn_frame, text="Export", command=on_ok, width=10).pack(side=tk.LEFT, padx=5)
                tk.Button(btn_frame, text="Cancel", command=on_cancel, width=10).pack(side=tk.LEFT, padx=5)
                
                app.master.wait_window(dialog)
                
                if result["layer"]:
                    selected_layer = result["layer"]
                else:
                    return # User cancelled
            else:
                selected_layer = base_fashion_layers[0]
    
            ly = selected_layer
            
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
            
            # Get the current colors from the layer
            try:
                current_colors = []
                for i, color in enumerate(ly.colors):
                    if isinstance(color, (list, tuple)) and len(color) >= 3:
                        r, g, b = color[:3]
                        if 0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255:
                            current_colors.append((int(r), int(g), int(b)))
                        else:
                            print(f"CONSOLE ERROR MSG: Color values out of range at index {i}: {color}")
                            current_colors.append((128, 128, 128))  # Default gray
                    else:
                        print(f"CONSOLE ERROR MSG: Invalid color format at index {i}: {color}")
                        current_colors.append((128, 128, 128))  # Default gray
            except Exception as e:
                messagebox.showerror("Error", f"Failed to get colors from layer: {e}")
                return
            
            if not current_colors:
                messagebox.showerror("Error", "No valid colors found in the selected layer")
                return
            
            # Create icon handler and export
            icon_handler = IconHandler()
            icon_handler.main_window = app
            
            # Create a temporary palette path for naming
            temp_palette_path = f"temp_{ly.name}.pal"
            
            try:
                success = icon_handler.save_as_icon(
                    char_id,
                    fashion_type,
                    current_colors,
                    temp_palette_path
                )
                if success:
                    messagebox.showinfo("Success", "Icon exported successfully!")
                else:
                    messagebox.showerror("Error", "Failed to export icon.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export icon: {e}")
    
        def _quick_export_icon_from_dialog(app, path, ly, dialog):
            """Quick export icon from the Post-Pal Save Menu dialog."""
            from tkinter import messagebox
            from icon_handler import IconHandler
            
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
            
            try:
                # Read the newly saved palette
                with open(path, 'rb') as f:
                    saved_pal_data = f.read()
                
                # Convert to RGB tuples
                saved_palette = []
                for i in range(0, len(saved_pal_data), 3):
                    r = saved_pal_data[i]
                    g = saved_pal_data[i+1]
                    b = saved_pal_data[i+2]
                    saved_palette.append((r, g, b))
                
                # Create icon handler and export
                icon_handler = IconHandler()
                icon_handler.main_window = app
                
                success = icon_handler.save_as_icon(
                    char_id,
                    fashion_type,
                    saved_palette,
                    path
                )
                if success:
                    messagebox.showinfo("Success", "Icon exported successfully!")
                    # Close the dialog after successful export
                    dialog.destroy()
                else:
                    messagebox.showerror("Error", "Failed to export icon.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export icon: {e}")
    
        def _quick_export_icon_from_dialog_no_close(app, path, ly):
            """Quick export icon from the Post-Pal Save Menu dialog without closing it."""
            from tkinter import messagebox
            from icon_handler import IconHandler
            
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
            
            try:
                # Read the newly saved palette
                with open(path, 'rb') as f:
                    saved_pal_data = f.read()
                
                # Convert to RGB tuples
                saved_palette = []
                for i in range(0, len(saved_pal_data), 3):
                    r = saved_pal_data[i]
                    g = saved_pal_data[i+1]
                    b = saved_pal_data[i+2]
                    saved_palette.append((r, g, b))
                
                # Create icon handler and export
                icon_handler = IconHandler()
                icon_handler.main_window = app
                
                success = icon_handler.save_as_icon(
                    char_id,
                    fashion_type,
                    saved_palette,
                    path
                )
                if success:
                    messagebox.showinfo("Success", "Icon exported successfully!")
                    # Don't close the dialog - keep it open
                else:
                    messagebox.showerror("Error", "Failed to export icon.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export icon: {e}")
    
        def _ask_icon_save_choice(app, path, ly):
            """Show a simple dialog asking how to handle icon saving."""
            dialog = tk.Toplevel(app._live_editor_window)
            dialog.title("Post-Pal QuickSave Menu")
            dialog.resizable(False, False)
            dialog.transient(app._live_editor_window)
            dialog.grab_set()
            
            # Make it modal
            result = {"choice": None}
            
            # Helper functions that perform actions without closing dialog
            def save_icon():
                """Save icon - quick export if checkbox is checked, otherwise prompt for filename"""
                from tkinter import messagebox, filedialog
                
                # Check if quick export is enabled
                if quick_export_var.get():
                    # Quick export mode - directly export the icon without closing dialog
                    app._quick_export_icon_from_dialog_no_close(path, ly)
                else:
                    # Normal mode - prompt user for filename and save icon
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
                                
                                print(f"\nRead saved palette from: {path}")
                                print(f"Found {len(saved_palette)} colors")
                                
                                # Prompt user for filename
                                pal_name = os.path.splitext(os.path.basename(path))[0]
                                # Remove temp prefix if present
                                if pal_name.startswith("temp_"):
                                    pal_name = pal_name[5:]
                                
                                default_name = f"{char_id}_{fashion_type}_{pal_name}.bmp"
                                file_path = filedialog.asksaveasfilename(
                                    title="Save Icon As",
                                    defaultextension=".bmp",
                                    filetypes=[("BMP files", "*.bmp"), ("All files", "*.*")],
                                    initialfile=default_name,
                                    parent=dialog
                                )
                                
                                if file_path:
                                    # Ensure the file has .bmp extension
                                    if not file_path.lower().endswith('.bmp'):
                                        file_path += '.bmp'
                                    
                                    # Create icon handler and save with user-specified filename
                                    from icon_handler import IconHandler
                                    icon_handler = IconHandler()
                                    icon_handler.main_window = app
                                    
                                    # Find the base BMP path for the character/fashion
                                    bmp_path, _ = icon_handler._get_icon_paths(char_id, fashion_type)
                                    
                                    if bmp_path and os.path.exists(bmp_path):
                                        # Get keying color
                                        
                                        success = icon_handler.save_as_icon(
                                            char_id,
                                            fashion_type,
                                            saved_palette,
                                            path,
                                            file_path
                                        )
                                        if success:
                                            messagebox.showinfo("Success", f"Icon saved as: {os.path.basename(file_path)}")
                                        else:
                                            messagebox.showerror("Error", "Failed to save icon.")
                                    else:
                                        messagebox.showerror("Error", "Could not find base BMP for this character/fashion.")
                            except Exception as e:
                                print(f"CONSOLE ERROR MSG: Error saving icon: {e}")
                                messagebox.showerror("Error", f"Failed to save palette: {str(e)}")
                
                # Bring dialog back to front
                dialog.lift()
                dialog.focus_force()
            
            def save_portrait():
                """Save portrait - quick export if checkbox is checked, otherwise prompt for filename"""
                from tkinter import messagebox
                try:
                    frame = app.get_current_displayed_frame()
                    if frame is not None:
                        # Both quick export and normal mode use the same method
                        # The export_background_bmp method already handles filename prompting
                        app.export_background_bmp(frame, force_portrait=True)
                    else:
                        messagebox.showerror("Error", "No frame available for portrait export.")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to export portrait: {e}")
                
                # Bring dialog back to front
                dialog.lift()
                dialog.focus_force()
            
            # Simple layout
            tk.Label(dialog, text="Do you want to quicksave export or edit the icon?", 
                    font=("Arial", 10)).pack(pady=10)
            
            # Quick Export checkbox
            checkbox_frame = tk.Frame(dialog)
            checkbox_frame.pack(pady=(0, 10))
            
            # Get initial value from settings
            initial_quick_export = getattr(app, 'use_quick_export', False)
            quick_export_var = tk.BooleanVar(value=initial_quick_export)
            
            # Three main action buttons
            button_frame = tk.Frame(dialog)
            button_frame.pack(pady=10)
            
            tk.Button(button_frame, text="Save Icon", 
                     command=save_icon,
                     width=13).pack(side=tk.LEFT, padx=5)
            
            tk.Button(button_frame, text="Save Portrait", 
                     command=save_portrait,
                     width=13).pack(side=tk.LEFT, padx=5)
            
            # Live Edit Icon button (will be shown/hidden based on checkbox)
            live_edit_button = tk.Button(button_frame, text="Live Edit Icon", 
                                       command=lambda: app._close_dialog(dialog, result, "openeditor"),
                                       width=13)
            live_edit_button.pack(side=tk.LEFT, padx=5)
            
            def toggle_quick_export():
                """Toggle quick export mode and show/hide Live Edit Icon button"""
                app.use_quick_export = quick_export_var.get()
                # Save the setting
                app._save_settings()
                
                # Show/hide the Live Edit Icon button based on checkbox state
                if quick_export_var.get():
                    live_edit_button.pack_forget()  # Hide the button
                else:
                    live_edit_button.pack(side=tk.LEFT, padx=5)  # Show the button
            
            quick_export_checkbox = tk.Checkbutton(checkbox_frame, text="Quick Export (Skip Icon Editor)", 
                                                 variable=quick_export_var,
                                                 command=toggle_quick_export)
            quick_export_checkbox.pack()
            
            # Set initial button state based on checkbox
            if initial_quick_export:
                live_edit_button.pack_forget()
            
            # "No thanks" button at the bottom
            no_button_frame = tk.Frame(dialog)
            no_button_frame.pack(pady=(0, 10))
            
            tk.Button(no_button_frame, text="No I'm good c:", 
                     command=lambda: app._close_dialog(dialog, result, "no"),
                     width=13).pack(pady=(0, 5))
                     
            tk.Button(no_button_frame, text="Generate XML", 
                     command=lambda: [app._close_dialog(dialog, result, "no"), app.open_xml_generator_dialog()],
                     width=13).pack()
            
            # Bring dialog to front and center it
            dialog.lift()
            dialog.focus_force()
            dialog.update_idletasks()
            app._center_window_on_parent(dialog, app._live_editor_window)
            
            ThemeManager.apply_theme(app, dialog)
    
        def quick_xml_export(app, data):
            """Quick Export logic"""
            try:
                import fashion_creator
                fashion_creator.FashionCreatorApp(app.master, data, previewer_app=app, quick_export=True)
            except Exception as e:
                from tkinter import messagebox
                messagebox.showerror("Error", f"Failed to quick export: {e}")
                print(f"Failed to quick export: {e}")
    
        def quick_export(app):
            """Quick export current frame"""
            # Use existing export functionality
            if hasattr(app, 'export_current_frame'):
                app.export_current_frame()
            elif hasattr(app, '_open_icon_editor'):
                # Open icon editor for export
                app._open_icon_editor()
    
        def export_background_compact(app):
            """Export background from compact editor"""
            # Use existing export functionality
            if hasattr(app, 'export_current_frame'):
                app.export_current_frame()
            elif hasattr(app, '_open_icon_editor'):
                app._open_icon_editor()
    
        def export_pal_compact(app):
            """Export palette from compact editor"""
            # Find the currently selected palette layer
            if not hasattr(app, 'last_selected_palette') or not app.last_selected_palette:
                from tkinter import messagebox
                messagebox.showinfo("Export Palette", "Please select a palette first.")
                return
    
            matching_layer = None
            palette_name = app.last_selected_palette
            palette_type = getattr(app, 'last_selected_palette_type', '')
    
            if hasattr(app, 'palette_layers'):
                for layer in app.palette_layers:
                    layer_name = getattr(layer, 'name', '')
                    layer_type = getattr(layer, 'palette_type', '')
                    
                    # Match by name or type - same logic as update_compact_palette_editor
                    names_match = (palette_name == layer_name) or (os.path.basename(palette_name) == layer_name)
    
                    if names_match or \
                       (palette_type == 'hair' and layer_type == 'hair') or \
                       (palette_type == 'third_job' and layer_type.startswith('3rd_job')) or \
                       (palette_type == 'fashion' and layer_type.startswith('fashion')):
                        matching_layer = layer
                        break
            
            if matching_layer:
                # Call save with the specific layer
                app._live_save_item_pal(layer=matching_layer)
            else:
                # Fallback to opening the live editor if we can't find the layer
                if hasattr(app, 'open_live_palette_editor'):
                    app.open_live_palette_editor()
    
