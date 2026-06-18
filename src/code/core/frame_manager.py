import tkinter as tk
from tkinter import messagebox


class FrameManager:
    @staticmethod
    def _get_current_or_selected_frame(app):
        """Get the frame index to operate on (selected frame or current displayed frame)"""
        if app.selected_frame is not None:
            return app.selected_frame
        # Return first displayed frame in current mode
        if app.preview_var.get() in ["custom", "all"]:
            # Get first visible frame
            images = app.character_images.get(app.current_character, [])
            char_job_key = app._get_char_job_key()
            hidden = app.hidden_frames.get(char_job_key, set())
            for i in range(len(images)):
                if i not in hidden:
                    return i
            return 0  # Fallback
        else:
            return app.current_image_index

    @staticmethod
    def _get_selected_frames_list(app):
        """Get a list of frame indices to operate on (all selected frames, or primary selection if none)"""
        if app.selected_frames:
            return sorted(list(app.selected_frames))
        return [app._get_current_or_selected_frame()]

    @staticmethod
    def _select_frame(app, frame_index, event=None):
        """Select a frame (toggle selection on double-click, support Shift/Ctrl for multi-select)"""
        current_time = app._time_module.time()
        
        # Detect Shift key (bit 0x0001) and Control key (bit 0x0004)
        shift_held = event and (event.state & 0x0001)
        ctrl_held = event and (event.state & 0x0004)
        
        if shift_held and app.last_clicked_frame is not None:
            # Range selection
            start_idx = min(app.last_clicked_frame, frame_index)
            end_idx = max(app.last_clicked_frame, frame_index)
            # Add all in range to selection
            for i in range(start_idx, end_idx + 1):
                app.selected_frames.add(i)
            # Update single selected_frame for UI backwards compatibility
            app.selected_frame = frame_index
        elif ctrl_held:
            # Toggle individual frame
            if frame_index in app.selected_frames:
                app.selected_frames.remove(frame_index)
            else:
                app.selected_frames.add(frame_index)
            app.selected_frame = frame_index if app.selected_frames else None
        else:
            # Normal selection logic (clears others unless it's a double-click deselect within 300ms)
            is_double_click = (app.last_clicked_frame == frame_index and 
                             current_time - app.last_frame_click_time < 0.3)
            
            if is_double_click:
                # Double-click - set this frame for export
                app.selected_frames = {frame_index}
                app.selected_frame = frame_index
                app._set_export_frame()
                app.last_clicked_frame = None
            else:
                # Single click - select only this one
                app.selected_frames = {frame_index}
                app.selected_frame = frame_index
                app.last_clicked_frame = frame_index
        
        app.last_frame_click_time = current_time
        app._redraw_frames_with_selection()

    @staticmethod
    def _deselect_frame(app, refresh=True):
        """Deselect all frames"""
        app.selected_frame = None
        app.selected_frames.clear()
        app.last_clicked_frame = None
        if refresh:
            app._redraw_frames_with_selection()

    @staticmethod
    def _hide_current_frame(app):
        """Hide all currently selected frames"""
        char_job_key = app._get_char_job_key()
        if not char_job_key:
            return
        
        frames_to_hide = app._get_selected_frames_list()
        
        if char_job_key not in app.hidden_frames:
            app.hidden_frames[char_job_key] = set()
        
        for idx in frames_to_hide:
            app.hidden_frames[char_job_key].add(idx)
            # Log as requested by user for individual tracking
            print(f"DEBUG[hide]: Hiding frame {idx + 1} for {char_job_key}")
            
        app._save_per_character_frame_settings()
        
        # Clear selected frames that were hidden
        for idx in frames_to_hide:
            if idx in app.selected_frames:
                app.selected_frames.remove(idx)
        if app.selected_frame in frames_to_hide:
            app.selected_frame = next(iter(app.selected_frames)) if app.selected_frames else None
            
        # Auto-advance for Single View if current frame was hidden
        preview_mode = app.preview_var.get().lower()
        if preview_mode == "single" and app.current_image_index in app.hidden_frames.get(char_job_key, set()):
            images = app.character_images.get(app.current_character, [])
            total = len(images)
            if total > 0:
                next_idx = (app.current_image_index + 1) % total
                hid_set = app.hidden_frames.get(char_job_key, set())
                checked = 0
                while next_idx in hid_set and checked < total:
                    next_idx = (next_idx + 1) % total
                    checked += 1
                
                if next_idx != app.current_image_index:
                    app.current_image_index = next_idx
                    if next_idx < len(images):
                        app.load_image_from_path(images[next_idx])
                        return # display updated
            
        # Refresh display
        app.update_image_display()

    @staticmethod
    def _show_previous_frame(app):
        """Show the previous hidden frame (searching backwards)"""
        char_job_key = app._get_char_job_key()
        if not char_job_key:
            return
        
        current_frame = app._get_current_or_selected_frame()
        images = app.character_images.get(app.current_character, [])
        total_frames = len(images)
        
        if total_frames == 0:
            return
        
        hidden = app.hidden_frames.get(char_job_key, set())
        if not hidden:
            messagebox.showinfo("No Hidden Frames", "There are no hidden frames to show.")
            return
        
        # Search backwards from current frame
        search_idx = (current_frame - 1) % total_frames
        checked = 0
        
        while checked < total_frames:
            if search_idx in hidden:
                # Found a hidden frame - unhide it
                hidden.remove(search_idx)
                print(f"DEBUG[show]: Unhiding frame {search_idx + 1} for {char_job_key}")
                app._save_per_character_frame_settings()
                
                # Navigate to the frame
                if app.preview_var.get() == "single":
                    app.current_image_index = search_idx
                else:
                    app.selected_frame = search_idx
                    app.selected_frames = {search_idx}
                
                app.update_image_display()
                return
            search_idx = (search_idx - 1) % total_frames
            checked += 1
        
        messagebox.showinfo("No Hidden Frames", "No hidden frames found before this position.")

    @staticmethod
    def _show_all_frames(app):
        """Unhide all hidden frames for the current character/job"""
        char_job_key = app._get_char_job_key()
        if not char_job_key:
            return
            
        hidden = app.hidden_frames.get(char_job_key, set())
        if not hidden:
            messagebox.showinfo("No Hidden Frames", "There are no hidden frames to unhide.")
            return
            
        count = len(hidden)
        if not messagebox.askyesno("Show All", f"Unhide all {count} hidden frames for {char_job_key}?"):
            return
            
        app.hidden_frames[char_job_key] = set()
        print(f"DEBUG[show_all]: Unhiding all {count} frames for {char_job_key}")
        app._save_per_character_frame_settings()
        app.update_image_display()

    @staticmethod
    def _set_export_frame(app):
        """Set the current or selected frame as the export frame for this character"""
        if not hasattr(app, 'current_character') or not app.current_character:
            return
        
        frame_idx = app._get_current_or_selected_frame()
        app.export_frames[app.current_character] = frame_idx
        app._save_per_character_frame_settings()
        messagebox.showinfo("Export Frame Set", f"Frame {frame_idx + 1} set as export frame for {app.current_character}")

    @staticmethod
    def _show_next_frame(app):
        """Show the next hidden frame (searching forwards)"""
        char_job_key = app._get_char_job_key()
        if not char_job_key:
            return
        
        current_frame = app._get_current_or_selected_frame()
        images = app.character_images.get(app.current_character, [])
        total_frames = len(images)
        
        if total_frames == 0:
            return
        
        hidden = app.hidden_frames.get(char_job_key, set())
        if not hidden:
            return
        
        # Search forwards from current frame
        search_idx = (current_frame + 1) % total_frames
        checked = 0
        
        while checked < total_frames:
            if search_idx in hidden:
                # Found a hidden frame - unhide it
                hidden.remove(search_idx)
                print(f"DEBUG[show]: Unhiding frame {search_idx + 1} for {char_job_key}")
                app._save_per_character_frame_settings()
                
                # Navigate to the frame
                if app.preview_var.get() == "single":
                    app.current_image_index = search_idx
                else:
                    app.selected_frame = search_idx
                    app.selected_frames = {search_idx}
                
                app.update_image_display()
                return
            search_idx = (search_idx + 1) % total_frames
            checked += 1

    @staticmethod
    def _simple_prev_frame(app):
        """Navigate to previous frame in simple mode preview"""
        if not hasattr(app, 'current_character') or not app.current_character:
            return
        
        if app.current_character in app.character_images:
            total_frames = len(app.character_images[app.current_character])
            if total_frames > 0:
                app._simple_current_frame = (app._simple_current_frame - 1) % total_frames
                app._update_simple_preview()

    @staticmethod
    def _simple_next_frame(app):
        """Navigate to next frame in simple mode preview"""
        if not hasattr(app, 'current_character') or not app.current_character:
            return
        
        if app.current_character in app.character_images:
            total_frames = len(app.character_images[app.current_character])
            if total_frames > 0:
                app._simple_current_frame = (app._simple_current_frame + 1) % total_frames
                app._update_simple_preview()

    @staticmethod
    def reset_frames(app):
        """Reset all frame viewing options (hidden frames, etc.) to default"""
        if not messagebox.askyesno("Reset Frames", "Are you sure you want to unhide all hidden frames and reset frame navigation for this character?"):
            return
            
        char_job_key = app._get_char_job_key()
        if char_job_key and char_job_key in app.hidden_frames:
            del app.hidden_frames[char_job_key]
            # Log for tracking
            print(f"DEBUG[reset_frames]: Cleared all hidden frames for {char_job_key}")
            
        # Also reset custom start index and current frame for this character
        if hasattr(app, 'current_character'):
            app.custom_start_index = 0
            app.current_image_index = 0
            
            # Also reset per-character settings in memory
            if app.current_character in app.per_character_settings:
                settings = app.per_character_settings[app.current_character]
                settings['custom_start_index'] = 0
                settings['last_viewed_frame'] = 0
            
            app._save_character_settings(app.current_character)
            
            # Load the first image to reset the preview if in single mode
            if app.preview_var.get() == "single" and app.current_character in app.character_images:
                images = app.character_images[app.current_character]
                if images:
                    app.load_image_from_path(images[0])
            
        app._save_per_character_frame_settings()
        app.update_image_display()
        messagebox.showinfo("Reset Frames", "All frame visibility settings and preview position have been reset for this character.")

    @staticmethod
    def _hide_selected_frames(app):
        """Hide all currently selected frames."""
        if not hasattr(app, 'selected_frames') or not app.selected_frames:
            return
            
        char_job_key = app._get_char_job_key()
        if not char_job_key:
            return
            
        if char_job_key not in app.hidden_frames:
            app.hidden_frames[char_job_key] = set()
            
        # Add all selected frames to hidden
        count = 0
        for idx in app.selected_frames:
            if idx not in app.hidden_frames[char_job_key]:
                app.hidden_frames[char_job_key].add(idx)
                count += 1
                
        # Clear selection
        app.selected_frames.clear()
        
        # Log and save
        if count > 0:
            print(f"DEBUG: Hidden {count} frames for {char_job_key}")
            app._save_per_character_frame_settings()
            
        # Update display
        app.update_image_display()

    @staticmethod
    def undo_frame_visibility(app):
        """Undo the last frame visibility change"""
        if not app.frame_visibility_history:
            messagebox.showinfo("Undo", "No more undo steps available")
            return
        
        # Pop the last state
        state = app.frame_visibility_history.pop()
        
        # Support both old and new format
        if len(state) == 2:
            char_job_key, hidden_frames = state
            app.hidden_frames[char_job_key] = hidden_frames.copy()
        elif len(state) == 4:
            char_job_key, hidden_frames, flip, rot = state
            app.hidden_frames[char_job_key] = hidden_frames.copy()
            app.image_flip = flip
            app.image_rotation = rot
        
        # Update display
        if hasattr(app, 'update_image_display'):
            app.update_image_display()
        
        # Save settings
        app._save_settings()

    @staticmethod
    def toggle_all_frames_visibility(app):
        """Toggle visibility of all frames except current one"""
        char_job_key = app._get_char_job_key()
        if not char_job_key or not hasattr(app, 'current_character'):
            return
        
        if app.current_character not in app.character_images:
            return
        
        images = app.character_images[app.current_character]
        if not images:
            return
        
        # Save current state for undo
        app._save_frame_visibility_state()
        
        # Get current hidden frames
        hidden = app.hidden_frames.get(char_job_key, set())
        
        # Determine current frame
        current_frame = app.current_image_index
        
        # Check if all but current are hidden
        all_but_current_hidden = all(
            i in hidden for i in range(len(images)) if i != current_frame
        )
        
        if all_but_current_hidden:
            # Show all frames
            app.hidden_frames[char_job_key] = set()
        else:
            # Hide all but current
            app.hidden_frames[char_job_key] = set(
                i for i in range(len(images)) if i != current_frame
            )
        
        # Update display
        if hasattr(app, 'update_image_display'):
            app.update_image_display()
        
        # Save settings
        app._save_settings()

    @staticmethod
    def toggle_selected_frames_visibility(app):
        """Toggle visibility of selected frames"""
        char_job_key = app._get_char_job_key()
        if not char_job_key or not app.selected_frames:
            messagebox.showinfo("No Selection", "Please select frames first (Ctrl+Click)")
            return
        
        # Save current state for undo
        app._save_frame_visibility_state()
        
        # Get current hidden frames
        if char_job_key not in app.hidden_frames:
            app.hidden_frames[char_job_key] = set()
        
        hidden = app.hidden_frames[char_job_key]
        
        # Check if any selected frames are visible
        any_visible = any(frame not in hidden for frame in app.selected_frames)
        
        if any_visible:
            # Hide all selected frames
            hidden.update(app.selected_frames)
        else:
            # Show all selected frames
            hidden.difference_update(app.selected_frames)
        
        # Update display
        if hasattr(app, 'update_image_display'):
            app.update_image_display()
        
        # Save settings
        app._save_settings()

    @staticmethod
    def on_frame_click(app, event, frame_index):
        """Handle frame click with Ctrl+Click support for multi-selection in the compact editor"""
        # In small preview mode, select the color at the clicked pixel instead of the frame
        if getattr(app, 'view_mode', '') == "small_preview":
            app._select_color_from_frame_click(event, frame_index)
            return
        
        # User requested to remove frame selection entirely from Left Click.
        # Selection is handled by Right Click context menu.

    @staticmethod
    def _show_frame_context_menu(app, event, frame_idx):
        """Show context menu for frame"""
        menu = tk.Menu(app.master, tearoff=0)
        
        # Select Frame
        menu.add_command(label="Set as Current Frame", 
                        command=lambda: app._select_frame_context(frame_idx))
        
        # Switch to Single Preview
        menu.add_command(label="Switch to Single Preview", 
                        command=lambda: app._switch_to_single_preview(frame_idx))
        
        # Hide Frame
        menu.add_command(label="Hide Selected Frame", 
                        command=lambda: app._hide_frame_context(frame_idx))
        
        # View as Singular Frame (Requested feature)
        menu.add_command(label="View as Singular Frame", 
                        command=lambda: app._switch_to_single_preview(frame_idx))
        
        menu.tk_popup(event.x_root, event.y_root)

    @staticmethod
    def _select_frame_context(app, frame_idx):
        """Select the frame from context menu"""
        app.current_image_index = frame_idx
        # Select in grid if applicable
        app.selected_frame = frame_idx
        app.selected_frames = {frame_idx}
        if hasattr(app, 'update_image_display'):
            app.update_image_display()

    @staticmethod
    def _switch_to_single_preview(app, frame_idx):
        """Switch to single preview mode for the selected frame"""
        app.current_image_index = frame_idx
        app.selected_frame = frame_idx
        app.preview_var.set("single")
        
        # Use update_image_display to refresh the view
        if hasattr(app, 'update_image_display'):
            app.update_image_display()

    @staticmethod
    def _hide_frame_context(app, frame_idx):
        """Hide the selected frame"""
        char_job_key = app._get_char_job_key()
        if not char_job_key:
            return
            
        if char_job_key not in app.hidden_frames:
            app.hidden_frames[char_job_key] = set()
            
        app.hidden_frames[char_job_key].add(frame_idx)
        app._save_frame_visibility_state()
        
        # Refresh display
        if hasattr(app, 'update_image_display'):
            app.update_image_display()

    @staticmethod
    def prev_custom_frames(app):
        """Navigate to previous set of custom frames"""
        if not hasattr(app, 'current_character') or not app.current_character:
            return
            
        char_id = app.current_character
        if char_id not in app.character_images:
            return
            
        images = app.character_images[char_id]
        max_frames = len(images)
        
        # If we are displaying a specific chosen frame, navigate that sequentially
        if getattr(app, 'use_frame_choice', False) and hasattr(app, 'chosen_frame'):
            app.chosen_frame -= 1
            if app.chosen_frame < 1:
                app.chosen_frame = max_frames
            app.update_image_display()
            app._save_character_settings(char_id)
            return
        
        # Get current job
        current_job = app.job_var.get() if hasattr(app, 'job_var') else None
        
        # Get stored settings for this character/job combination
        char_settings = app.frame_range_settings.get(app.current_character, {})
        job_settings = char_settings.get(current_job, None)
        
        if job_settings:
            frame_count, start_frame, end_frame = job_settings
        else:
            start_frame = 0
            end_frame = max_frames - 1
            
        # Get hidden frames
        char_job_key = app._get_char_job_key()
        hidden = app.hidden_frames.get(char_job_key, set())
        
        # Move backward by custom_frame_count frames, skipping hidden
        step = max(1, getattr(app, 'custom_frame_count', 1))
        
        # Find previous valid frame by stepping 'step' times
        for _ in range(step):
            app.custom_start_index -= 1
            if app.custom_start_index < start_frame:
                app.custom_start_index = end_frame
                
            # Keep advancing backward if it's hidden, ensuring we don't infinite loop
            checked = 0
            total_range = end_frame - start_frame + 1
            while app.custom_start_index in hidden and checked < total_range:
                app.custom_start_index -= 1
                if app.custom_start_index < start_frame:
                    app.custom_start_index = end_frame
                checked += 1
        
        # Update zoom combo state after custom frame navigation
        app.update_zoom_combo_state()
        app.update_image_display()
        
        # Save character settings to remember the new start index
        app._save_character_settings(char_id)

    @staticmethod
    def next_custom_frames(app):
        """Navigate to next set of custom frames"""
        if not hasattr(app, 'current_character') or not app.current_character:
            return
            
        char_id = app.current_character
        if char_id not in app.character_images:
            return
            
        images = app.character_images[char_id]
        max_frames = len(images)
        
        # If we are displaying a specific chosen frame, navigate that sequentially
        if getattr(app, 'use_frame_choice', False) and hasattr(app, 'chosen_frame'):
            app.chosen_frame += 1
            if app.chosen_frame > max_frames:
                app.chosen_frame = 1
            app.update_image_display()
            app._save_character_settings(char_id)
            return
        
        # Get current job
        current_job = app.job_var.get() if hasattr(app, 'job_var') else None
        
        # Get stored settings for this character/job combination
        char_settings = app.frame_range_settings.get(app.current_character, {})
        job_settings = char_settings.get(current_job, None)
        
        if job_settings:
            frame_count, start_frame, end_frame = job_settings
        else:
            start_frame = 0
            end_frame = max_frames - 1
            
        # Get hidden frames
        char_job_key = app._get_char_job_key()
        hidden = app.hidden_frames.get(char_job_key, set())
        
        # Move forward by custom_frame_count frames, skipping hidden
        step = max(1, getattr(app, 'custom_frame_count', 1))
        
        # Find next valid frame by stepping 'step' times
        for _ in range(step):
            app.custom_start_index += 1
            if app.custom_start_index > end_frame:
                app.custom_start_index = start_frame
            
            # Keep advancing if it's hidden, ensuring we don't infinite loop
            checked = 0
            total_range = end_frame - start_frame + 1
            while app.custom_start_index in hidden and checked < total_range:
                app.custom_start_index += 1
                if app.custom_start_index > end_frame:
                    app.custom_start_index = start_frame
                checked += 1
        
        # Update zoom combo state after custom frame navigation
        app.update_zoom_combo_state()
        app.update_image_display()
        
        # Save character settings to remember the new start index
        app._save_character_settings(char_id)

    @staticmethod
    def get_current_displayed_frame(app):
        """Get the currently displayed frame index (0-based)"""
        if hasattr(app, 'current_character') and app.current_character:
            # Check explicitly set export frame
            if hasattr(app, 'export_frames') and app.current_character in app.export_frames:
                return app.export_frames[app.current_character]
                
            if app.preview_var.get() == "single":
                return app.current_image_index
            elif app.preview_var.get() == "all":
                # In all mode, default to first frame (index 0)
                return 0
            elif app.preview_var.get() == "custom":
                if app.use_frame_choice:
                    return app.chosen_frame - 1  # Convert 1-based to 0-based
                else:
                    # Return the first frame of the current custom display range
                    return getattr(app, 'custom_start_index', 0)
        return 0

    @staticmethod
    def get_custom_frame_range(app):
        """Get the range of frames to display in custom mode"""
        if not hasattr(app, 'current_character') or not app.current_character:
            return []
        
        if app.current_character not in app.character_images:
            return []
        
        images = app.character_images[app.current_character]
        max_frames = len(images)
        
        # Get current job
        current_job = app.job_var.get() if hasattr(app, 'job_var') else None
        
        # Get stored settings for this character/job combination
        char_settings = app.frame_range_settings.get(app.current_character, {})
        job_settings = char_settings.get(current_job, None)
        
        if job_settings:
            frame_count, start_frame, end_frame = job_settings
            # Validate stored settings
            
            # Calculate frame indices within the selected range
            # Note: Removed distributed logic to ensure navigation works consistently with a sliding window approach
            if False: # Disabled distributed logic
                pass

            
            if start_frame >= max_frames:
                start_frame = 0
            if end_frame >= max_frames:
                end_frame = max_frames - 1
            if start_frame > end_frame:
                start_frame = 0
                end_frame = max_frames - 1
            
            # Update instance variables
            app.custom_frame_count = frame_count
            app.custom_start_frame = start_frame
            app.custom_end_frame = end_frame
        else:
            # Use default values if no settings stored
            app.custom_frame_count = getattr(app, 'custom_frame_count', 3)
            app.custom_start_frame = getattr(app, 'custom_start_frame', 0)
            app.custom_end_frame = getattr(app, 'custom_end_frame', max_frames - 1)
            
        # Calculate frame indices within the selected range
        end_index = min(app.custom_start_index + app.custom_frame_count, max_frames)
        
        # Return the range of images to display
        return images[app.custom_start_index:end_index]

