import tkinter as tk
from tkinter import messagebox

class CustomPreviewDialog:
    def __init__(app, parent, max_frames, start_frame=0, end_frame=None, num_frames=3, use_bmp=False, show_labels=True, initial_frame=None):
        app.parent = parent
        app.result = None
        app.max_frames = max_frames
        app.use_bmp = use_bmp
        app.show_labels = show_labels
        app.initial_frame = initial_frame if initial_frame is not None else 0
        
        # Get parent's export settings if available
        if type(parent).__name__ == "PaletteTool":
            app.use_bmp = parent.use_bmp_export
            app.use_portrait = parent.use_portrait_export
            app.show_labels = parent.show_frame_labels
            app.cute_bg_option = parent.cute_bg_option  # Initialize cute background option from parent
        else:
            app.use_portrait = False
            app.cute_bg_option = "no_cute_bg"  # Default value for non-PaletteTool parents
        
        # Determine the widget parent for the dialog
        widget_parent = parent.master if type(parent).__name__ == "PaletteTool" else parent
        
        # Create dialog window
        app.dialog = tk.Toplevel(widget_parent)
        app.dialog.title("Custom Preview Settings")
        app.dialog.transient(widget_parent)
        app.dialog.grab_set()
        app.dialog.resizable(False, False)
        
        from code.utils.theme_manager import ThemeManager
        ThemeManager.apply_theme(parent, app.dialog)
        
        # Build the dialog content first, then center
        # (centering will be done after content is created)
        
        # Container frame for content and buttons
        container = tk.Frame(app.dialog)
        container.pack(fill="both", expand=True)
        
        # Main frame for content
        main_frame = tk.Frame(container)
        main_frame.pack(fill="both", padx=20, pady=(10,0))
        
        # Title
        title_label = tk.Label(main_frame, text="Custom Frame Settings", font=("Arial", 12, "bold"))
        title_label.pack(pady=(0, 2))  # Reduced padding
        
        # Total frames info
        total_frames_label = tk.Label(main_frame, text=f"Total Available Frames: {max_frames}", font=("Arial", 10))
        total_frames_label.pack(pady=(0, 5))
        
        # Frame count input
        count_frame = tk.Frame(main_frame)
        count_frame.pack(fill="x", pady=(0,2))  # Reduced padding
        
        tk.Label(count_frame, text="Number of Frames:").pack(side="left")
        
        app.frame_var = tk.StringVar(value=str(num_frames))
        app.frame_entry = tk.Entry(count_frame, textvariable=app.frame_var, width=10)
        app.frame_entry.pack(side="left", padx=(5, 0))
        
        # Frame range inputs
        range_frame = tk.Frame(main_frame)
        range_frame.pack(fill="x", pady=0)
        
        # Start frame
        start_frame_container = tk.Frame(range_frame)
        start_frame_container.pack(fill="x", pady=1)  # Reduced padding
        tk.Label(start_frame_container, text="Start Frame:").pack(side="left")
        # Always use initial_frame (current frame) as the default start frame, convert to 1-based
        initial_start = app.initial_frame
        app.start_var = tk.StringVar(value=str(initial_start + 1))  # Convert to 1-based
        app.start_entry = tk.Entry(start_frame_container, textvariable=app.start_var, width=10)
        app.start_entry.pack(side="left", padx=(5, 0))
        
        # End frame
        end_frame_container = tk.Frame(range_frame)
        end_frame_container.pack(fill="x", pady=1)  # Reduced padding
        tk.Label(end_frame_container, text="End Frame:").pack(side="left")
        # Convert end frame to 1-based
        end_value = end_frame if end_frame is not None else max_frames - 1
        app.end_var = tk.StringVar(value=str(end_value + 1))  # Convert to 1-based
        app.end_entry = tk.Entry(end_frame_container, textvariable=app.end_var, width=10)
        app.end_entry.pack(side="left", padx=(5, 0))
        
        # Create horizontal container for export format boxes
        export_container = tk.Frame(main_frame)
        export_container.pack(fill="x", pady=(2,2), padx=5)
        
        # Left box - Export Format
        format_frame = tk.LabelFrame(export_container, text="Export Format")
        format_frame.pack(side="left", fill="both", expand=True, padx=(0,3))
        
        # Right box - Portrait BG
        bg_frame = tk.LabelFrame(export_container, text="Portrait BG")
        bg_frame.pack(side="right", fill="both", expand=True, padx=(3,0))
        
        # Palette format frame (separate)
        palette_frame = tk.LabelFrame(main_frame, text="Palette Format")
        palette_frame.pack(fill="x", pady=(0,2), padx=5)  # Reduced padding
        
        app.palette_format_var = tk.StringVar(value="png")
        tk.Radiobutton(palette_frame, text="PAL", variable=app.palette_format_var,
                      value="pal").pack(side="left", padx=10, pady=2)
        tk.Radiobutton(palette_frame, text="PNG Grid", variable=app.palette_format_var,
                      value="png").pack(side="left", padx=10, pady=2)
        
        # (Removed Export Palette button visibility toggle as per UI revamp)
        
        # Initialize variables
        app.format_var = tk.BooleanVar(value=app.use_bmp)
        app.portrait_var = tk.BooleanVar(value=app.use_portrait)
        app.cute_bg_var = tk.StringVar(value=app.cute_bg_option)
        
        # Add trace to update parent's export button when format changes
        def on_format_change(*args):
            is_bmp = app.format_var.get()
            if type(parent).__name__ == "PaletteTool":
                parent.use_bmp_export = is_bmp
                parent.update_export_button_text()
                parent.master.update()  # Force update of the main window
            
            # Portrait mode is always enabled
            app.portrait_checkbox.configure(state="normal")
            
            # Update BG Style options based on Portrait mode
            app.update_bg_style_state()
        app.format_var.trace_add("write", on_format_change)
        
        # Left box content - Format options with reduced padding
        tk.Radiobutton(format_frame, text="Transparent PNG", variable=app.format_var, 
                      value=False).pack(anchor="w", padx=5, pady=1)
        tk.Radiobutton(format_frame, text="Background BMP", variable=app.format_var, 
                      value=True).pack(anchor="w", padx=5, pady=1)
        
        # Portrait checkbox with extra padding after BMP option
        app.portrait_checkbox = tk.Checkbutton(format_frame, text="Portrait export (105x105)", 
                                              variable=app.portrait_var,
                                              command=app.update_bg_style_state)
        app.portrait_checkbox.pack(anchor="w", padx=5, pady=(5,1))
        
        # Right box content - Portrait BG options with reduced padding
        app.cute_bg_frame = tk.Frame(bg_frame)
        app.cute_bg_frame.pack(anchor="w", padx=5, pady=1)
        
        # Create radio buttons with initial state based on portrait mode
        initial_state = "normal" if app.portrait_var.get() else "disabled"
        tk.Radiobutton(app.cute_bg_frame, text="No cute BG", variable=app.cute_bg_var,
                      value="no_cute_bg", state=initial_state).pack(side="top", anchor="w", pady=1)
        tk.Radiobutton(app.cute_bg_frame, text="Cute BG", variable=app.cute_bg_var,
                      value="cute_bg", state=initial_state).pack(side="top", anchor="w", pady=1)
        tk.Radiobutton(app.cute_bg_frame, text="Both", variable=app.cute_bg_var,
                      value="both", state=initial_state).pack(side="top", anchor="w", pady=1)
        
        # Update parent's settings when any option changes
        def update_parent_settings(*args):
            if type(app.parent).__name__ == "PaletteTool":
                old_mode = getattr(app.parent, 'live_pal_ui_mode', 'Advanced')
                app.parent.use_bmp_export = app.format_var.get()
                app.parent.use_portrait_export = app.portrait_var.get()
                app.parent.cute_bg_option = app.cute_bg_var.get()
                app.parent.show_frame_labels = app.labels_var.get()
                app.parent.palette_format = app.palette_format_var.get()
                app.parent.use_frame_choice = app.user_choice_var.get()
                new_mode = app.live_pal_ui_var.get()
                app.parent.live_pal_ui_mode = new_mode
                if hasattr(app, 'show_export_button_var'):
                    app.parent.show_export_palette_button = app.show_export_button_var.get()
                if hasattr(app, 'show_dev_buttons_var'):
                    app.parent.show_dev_buttons = app.show_dev_buttons_var.get()
                # Update excess colors prompt setting (invert because setting is "dont_show")
                app.parent.dont_show_excess_colors_prompt = not app.show_excess_colors_prompt_var.get()
                
                # If the live editor is open and the mode changed, rebuild the grid
                if (old_mode != new_mode and 
                    hasattr(app.parent, '_live_editor_window') and 
                    app.parent._live_editor_window and 
                    app.parent._live_editor_window.winfo_exists()):
                    app.parent._rebuild_live_palette_grid()
                    
                if app.user_choice_var.get() and hasattr(app, 'frame_choice_var'):
                    try:
                        app.parent.chosen_frame = int(app.frame_choice_var.get())
                    except (ValueError, AttributeError):
                        pass
                
        # Update checkbox states when format changes
        def update_checkbox_states(*args):
            state = "normal" if app.format_var.get() else "disabled"
            app.portrait_checkbox.config(state=state)
            if not app.format_var.get():
                app.portrait_var.set(False)
            update_parent_settings()
        
        # Frame label toggle
        label_frame = tk.Frame(main_frame)
        label_frame.pack(fill="x", pady=1)  # Minimal padding
        
        app.labels_var = tk.BooleanVar(value=app.show_labels)
        tk.Checkbutton(label_frame, text="Show Frame Numbers", variable=app.labels_var).pack(side="left")
        
        # User Choice Frame Export option
        choice_frame = tk.Frame(main_frame)
        choice_frame.pack(fill="x", pady=(1,2))  # Minimal padding
        
        # Initialize with parent's settings if available
        initial_choice = False
        
        if type(app.parent).__name__ == "PaletteTool":
            initial_choice = app.parent.use_frame_choice
            # If frame choice was previously used, use that frame, otherwise use the initial frame
            if app.parent.use_frame_choice:
                initial_frame = app.parent.chosen_frame
            else:
                initial_frame = app.initial_frame
                # Frame choice should be off by default
                initial_choice = False
        
        app.user_choice_var = tk.BooleanVar(value=initial_choice)
        choice_checkbox = tk.Checkbutton(choice_frame, text="User Choice Frame Export", 
                                       variable=app.user_choice_var,
                                       command=app.toggle_frame_choice)
        choice_checkbox.pack(side="left")
        
        # Frame number entry
        app.frame_choice_container = tk.Frame(choice_frame)
        app.frame_choice_container.pack(side="left", padx=(10,0))
        
        tk.Label(app.frame_choice_container, text="Frame:").pack(side="left")
        app.frame_choice_var = tk.StringVar(value=str(initial_frame))  # Already 1-based
        app.frame_choice_entry = tk.Entry(app.frame_choice_container, 
                                        textvariable=app.frame_choice_var,
                                        width=5)
        app.frame_choice_entry.pack(side="left", padx=(5,5))
        
        # Live Pal Editor UI option
        live_pal_frame = tk.LabelFrame(main_frame, text="Live Pal Editor UI")
        live_pal_frame.pack(fill="x", pady=(2,2), padx=5)
        
        # Get parent's live pal editor UI mode if available
        if type(parent).__name__ == "PaletteTool":
            initial_mode = getattr(parent, 'live_pal_ui_mode', 'Advanced')
        else:
            initial_mode = 'Advanced'
        
        app.live_pal_ui_var = tk.StringVar(value=initial_mode)
        app.live_pal_ui_var.trace_add("write", update_parent_settings)
        tk.Radiobutton(live_pal_frame, text="Simple", variable=app.live_pal_ui_var,
                      value="Simple").pack(side="left", padx=10, pady=2)
        tk.Radiobutton(live_pal_frame, text="Advanced", variable=app.live_pal_ui_var,
                      value="Advanced").pack(side="left", padx=10, pady=2)
        
        # Add validation to prevent unexpected changes
        def validate_frame_choice(*args):
            try:
                value = int(app.frame_choice_var.get())
                if type(app.parent).__name__ == "PaletteTool":
                    max_frame = len(app.parent.character_images.get(app.parent.current_character, []))
                    if value < 1:
                        app.frame_choice_var.set("1")
                    elif value > max_frame:
                        app.frame_choice_var.set(str(max_frame))
            except ValueError:
                # If not a valid number, don't change anything
                pass
            
        app.frame_choice_var.trace_add("write", validate_frame_choice)
        
        
        # Show/hide frame choice based on initial state
        if initial_choice:
            app.frame_choice_container.pack(side="left", padx=(10,0))
        else:
            app.frame_choice_container.pack_forget()
        
        # Add traces for immediate updates
        app.format_var.trace_add("write", update_checkbox_states)
        app.portrait_var.trace_add("write", update_parent_settings)
        app.labels_var.trace_add("write", update_parent_settings)
        app.cute_bg_var.trace_add("write", update_parent_settings)
        app.palette_format_var.trace_add("write", update_parent_settings)
        app.user_choice_var.trace_add("write", update_parent_settings)
        
        # (Removed Show Dev Buttons checkbox as per UI revamp)
        
        # Excess Colors Prompt checkbox
        excess_colors_frame = tk.Frame(main_frame)
        excess_colors_frame.pack(fill="x", pady=(5, 0))
        
        # Get initial value from parent if available
        initial_show_excess_prompt = True  # Default to True (show prompts)
        if type(parent).__name__ == "PaletteTool":
            # Load from settings - note: setting is "dont_show" so we invert it
            dont_show = getattr(parent, 'dont_show_excess_colors_prompt', False)
            initial_show_excess_prompt = not dont_show
        
        app.show_excess_colors_prompt_var = tk.BooleanVar(value=initial_show_excess_prompt)
        app.show_excess_colors_checkbox = tk.Checkbutton(excess_colors_frame, text="Show Excess Colors Prompts", 
                                                         variable=app.show_excess_colors_prompt_var)
        app.show_excess_colors_checkbox.pack(anchor="center")
        
        # Add trace for show_excess_colors_prompt_var after it's created
        app.show_excess_colors_prompt_var.trace_add("write", update_parent_settings)
        
        # Validation message
        app.validation_label = tk.Label(main_frame, text="", fg="red", wraplength=250)
        app.validation_label.pack(pady=5)
        
        # Button frame in the middle
        button_frame = tk.Frame(main_frame)
        button_frame.pack(fill="x", pady=(10, 40))
        
        # Center container for buttons
        button_container = tk.Frame(button_frame)
        button_container.pack(anchor="center")
        
        # Credits button with the same style as the main UI
        credits_button = tk.Button(button_container, text="Credits ♥", command=app.parent.show_credits,
                                bg="#C8A2C8", fg="white", activebackground="#B695B6", activeforeground="white")
        credits_button.pack(side="left", padx=5)
        
        # OK button (wider)
        app.ok_button = tk.Button(button_container, text="OK", command=app.ok_clicked, width=12)
        app.ok_button.pack(side="left", padx=5)
        
        # Cancel button
        cancel_button = tk.Button(button_container, text="Cancel", command=app.cancel_clicked, width=8)
        cancel_button.pack(side="left", padx=5)
        
        # Bind validation to input changes
        app.frame_var.trace_add("write", lambda *args: app.validate_inputs())
        app.start_var.trace_add("write", lambda *args: app.validate_inputs())
        app.end_var.trace_add("write", lambda *args: app.validate_inputs())
        
        # Center the dialog after all content is created
        app.dialog.update_idletasks()
        app._center_dialog_on_parent()
        
        # Bind Enter key to OK
        app.dialog.bind("<Return>", lambda e: app.ok_clicked())
        app.dialog.bind("<Escape>", lambda e: app.cancel_clicked())
        
        # Allow arrow keys to change frames while options menu is open, unless typing in an entry
        def on_left_arrow(event):
            if event.widget.winfo_class() not in ('Entry', 'Text', 'TCombobox'):
                if hasattr(app.parent, 'next_image'):
                    app.parent.next_image(-1)
        
        def on_right_arrow(event):
            if event.widget.winfo_class() not in ('Entry', 'Text', 'TCombobox'):
                if hasattr(app.parent, 'next_image'):
                    app.parent.next_image(1)
                    
        app.dialog.bind("<Left>", on_left_arrow)
        app.dialog.bind("<Right>", on_right_arrow)
        
        # Focus on entry
        app.frame_entry.focus_set()
        app.frame_entry.select_range(0, tk.END)
        
        # Initial validation (but don't auto-adjust values during initialization)
        app._initializing = True
        app.validate_inputs()
        app._initializing = False
        
        # Add a Reset Defaults button at the very bottom
        reset_defaults_frame = tk.Frame(container)
        reset_defaults_frame.pack(fill="x", side="bottom", pady=(0, 5))
        tk.Button(reset_defaults_frame, text="Reset to default settings", 
                  command=app.reset_to_defaults, fg="#d9534f", font=("Arial", 8, "underline"),
                  cursor="hand2", relief="flat").pack(anchor="center")
        
    def validate_inputs(app):
        """Validate all inputs and update UI accordingly"""
        try:
            frames = int(app.frame_var.get())
            # Convert from 1-based to 0-based for internal validation
            start_frame = int(app.start_var.get()) - 1
            end_frame = int(app.end_var.get()) - 1
            
            if frames <= 0:
                app.show_validation_error("Number of frames must be greater than 0")
                return False
            if frames > app.max_frames:
                app.frame_var.set(str(app.max_frames))
                return True
            if start_frame < 0:
                app.start_var.set("1")
                return True
            if end_frame >= app.max_frames:
                app.end_var.set(str(app.max_frames))
                return True
            if start_frame > end_frame:
                app.start_var.set(str(end_frame + 1))
                return True
            # If frame count is larger than the range, auto-adjust it (but not during initialization)
            range_size = end_frame - start_frame + 1
            if range_size < frames and not getattr(app, '_initializing', False):
                app.frame_var.set(str(range_size))
                frames = range_size  # Update frames to match range
                return True  # Allow validation to pass with adjusted frame count
                
            app.validation_label.config(text="")
            app.ok_button.config(state="normal")
            return True
            
        except ValueError:
            app.show_validation_error("Please enter valid numbers")
            return False
            
    def show_validation_error(app, message):
        """Display validation error and disable OK button"""
        app.validation_label.config(text=message)
        app.ok_button.config(state="disabled")
    
    def update_bg_style_state(app):
        """Enable/disable BG Style options based on Portrait mode"""
        state = "normal" if app.portrait_var.get() else "disabled"
        for child in app.cute_bg_frame.winfo_children():
            if isinstance(child, tk.Radiobutton):
                child.configure(state=state)
        if not app.portrait_var.get():
            app.cute_bg_var.set("no_cute_bg")  # Reset to default when disabled
    

    
    def toggle_frame_choice(app):
        """Toggle visibility of frame choice entry"""
        if app.user_choice_var.get():
            app.frame_choice_container.pack(side="left", padx=(10,0))
        else:
            app.frame_choice_container.pack_forget()

    def reset_to_defaults(app):
        """Reset all option settings to their default values"""
        from tkinter import messagebox
        if not messagebox.askyesno("Warning", "Are you sure you want to clear this?"):
            return
            
        # Reset internal variables
        app.frame_var.set("3")
        app.start_var.set("1")
        app.end_var.set(str(app.max_frames))
        app.format_var.set(False) # Transparent PNG
        app.portrait_var.set(False)
        app.cute_bg_var.set("no_cute_bg")
        app.labels_var.set(True)
        app.user_choice_var.set(False)
        app.palette_format_var.set("png")
        app.live_pal_ui_var.set("Advanced")
        app.show_excess_colors_prompt_var.set(True)
        
        # Update parent settings immediately (live sync)
        if type(app.parent).__name__ == "PaletteTool":
            app.parent.use_bmp_export = False
            app.parent.use_portrait_export = False
            app.parent.cute_bg_option = "no_cute_bg"
            app.parent.show_frame_labels = True
            app.parent.use_frame_choice = False
            app.parent.palette_format = "png"

            app.parent.live_pal_ui_mode = "Advanced"
            app.parent.dont_show_excess_colors_prompt = False
            
            # Update UI elements in parent
            app.parent.update_export_button_text()
            app.parent.update_zoom_combo_state()
        
        # Refresh dialog UI elements
        app.validate_inputs()
        app.toggle_frame_choice()
        app.update_bg_style_state()
        
        messagebox.showinfo("Reset Settings", "Settings have been reset to defaults.")
            
    def ok_clicked(app, close=True):
        try:
            frames = int(app.frame_var.get())
            # Convert from 1-based to 0-based for internal storage
            start_frame = int(app.start_var.get()) - 1
            end_frame = int(app.end_var.get()) - 1
            # Smart mode switching based on frame range settings
            if type(app.parent).__name__ == "PaletteTool":
                current_mode = app.parent.preview_var.get()
                
                # Determine the appropriate mode based on frame settings
                if start_frame == 0 and end_frame == app.max_frames - 1:
                    # Full range (1 to max) - check if should be in all mode
                    if frames == app.max_frames:
                        # Full range with all frames - should be in all mode
                        target_mode = "all"
                    else:
                        # Full range but not all frames - use custom mode
                        target_mode = "custom"
                elif start_frame == 0 and end_frame == 0:
                    # Single frame (1 to 1) - could be single mode
                    if frames == 1:
                        target_mode = "single"
                        # Set the single frame index
                        app.parent.current_image_index = 0
                    else:
                        target_mode = "custom"
                else:
                    # Custom range - always use custom mode
                    target_mode = "custom"
                
                # Apply the mode change if needed
                if current_mode != target_mode:
                    app.parent.preview_var.set(target_mode)
                    # Ensure UI reflects the mode change immediately
                    try:
                        app.parent.on_preview_mode_change()
                    except Exception:
                        pass
            # Validate frame choice if enabled
            if app.user_choice_var.get():
                try:
                    # Get the frame number from user input (1-based)
                    chosen_frame = int(app.frame_choice_var.get())
                    if type(app.parent).__name__ == "PaletteTool":
                        max_frame = len(app.parent.character_images.get(app.parent.current_character, []))
                        if chosen_frame < 1 or chosen_frame > max_frame:
                            messagebox.showerror("Invalid Input", f"Frame number must be between 1 and {max_frame}.")
                            return
                        # Keep as 1-based, don't convert to 0-based
                except ValueError:
                    messagebox.showerror("Invalid Input", "Please enter a valid frame number.")
                    return
            
            # Validate inputs
            if frames <= 0:
                messagebox.showerror("Invalid Input", "Number of frames must be greater than 0.")
                return
            
            if frames > app.max_frames:
                messagebox.showwarning("Too Many Frames", 
                                     f"You cannot display more than {app.max_frames} frames for lag purposes.\n"
                                     f"The number has been set to {app.max_frames}.")
                frames = app.max_frames
                app.frame_var.set(str(frames))
            
            if start_frame < 0:
                messagebox.showerror("Invalid Input", "Start frame must be greater than or equal to 0")
                return
            if end_frame >= app.max_frames:
                messagebox.showerror("Invalid Input", f"End frame must be less than {app.max_frames}")
                return
            if start_frame > end_frame:
                messagebox.showerror("Invalid Input", "Start frame must be less than or equal to end frame")
                return
            # If frame count is larger than the range, auto-adjust it
            range_size = end_frame - start_frame + 1
            if range_size < frames:
                frames = range_size  # Update frames to match range
                app.frame_var.set(str(frames))  # Update the display
            
            # Check for 50+ frames warning if it's a PaletteTool
            if type(app.parent).__name__ == "PaletteTool" and frames > 50:
                if not app.parent._get_50_frames_warning_preference():
                    # Show warning dialog
                    warning_dialog = FramesWarningDialog(app, frames)
                    result, dont_show_again = warning_dialog.show()
                    
                    # Save the "don't show again" preference if user checked it
                    if dont_show_again:
                        app.parent._save_50_frames_warning_preference(True)
                    
                    if not result:
                        # User chose "Nah I'm good" - highlight fields and return to dialog
                        app._highlight_frame_fields()
                        app.dialog.lift()
                        app.dialog.focus_force()
                        return
                
            # Update parent's settings if it's a PaletteTool
            if type(app.parent).__name__ == "PaletteTool":
                app.parent.use_bmp_export = app.format_var.get()
                app.parent.use_portrait_export = app.portrait_var.get()
                app.parent.cute_bg_option = app.cute_bg_var.get()  # This is handled separately from the result tuple
                app.parent.palette_format = app.palette_format_var.get()  # Update palette format
                app.parent.show_frame_labels = app.labels_var.get()
                app.parent.use_frame_choice = app.user_choice_var.get()
                app.parent.live_pal_ui_mode = app.live_pal_ui_var.get()  # Update live pal editor UI mode
                # Update excess colors prompt setting (invert because setting is "dont_show")
                app.parent.dont_show_excess_colors_prompt = not app.show_excess_colors_prompt_var.get()
                if app.user_choice_var.get():
                    app.parent.chosen_frame = int(app.frame_choice_var.get())  # Keep as 1-based
                # Apply immediate frame settings for custom preview
                app.parent.custom_frame_count = frames
                if not app.user_choice_var.get():
                    app.parent.custom_start_index = start_frame
                
                # Save settings to file (global settings + per-character)
                app.parent._save_settings()
                if app.parent.current_character:
                    app.parent._save_character_settings(app.parent.current_character)
            
            # Include user's frame choice if enabled (keep as 1-based for result tuple)
            chosen_frame = int(app.frame_choice_var.get()) if app.user_choice_var.get() else None
            app.result = (frames, start_frame, end_frame, app.format_var.get(), app.labels_var.get(), 
                         app.portrait_var.get(), app.user_choice_var.get(), chosen_frame,
                         app.palette_format_var.get(), app.cute_bg_var.get(), app.live_pal_ui_var.get(),
                         app.show_excess_colors_prompt_var.get())
            if close:
                app.dialog.destroy()
            
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid number.")
    
    def cancel_clicked(app):
        app.dialog.destroy()
    
    def _center_dialog_on_parent(app):
        """Center the dialog on its parent window."""
        widget_parent = app.parent.master if type(app.parent).__name__ == "PaletteTool" else app.parent
        
        # Get actual dialog dimensions after content is rendered
        dialog_width = app.dialog.winfo_width()
        dialog_height = app.dialog.winfo_height()
        
        if widget_parent and widget_parent.winfo_exists():
            # Center on parent window
            parent_x = widget_parent.winfo_x()
            parent_y = widget_parent.winfo_y()
            parent_width = widget_parent.winfo_width()
            parent_height = widget_parent.winfo_height()
            
            # Calculate center position relative to parent
            x = parent_x + (parent_width - dialog_width) // 2
            y = parent_y + (parent_height - dialog_height) // 2
        else:
            # Center on screen if no parent
            screen_width = app.dialog.winfo_screenwidth()
            screen_height = app.dialog.winfo_screenheight()
            x = (screen_width - dialog_width) // 2
            y = (screen_height - dialog_height) // 2
        
        # Set the dialog position (keep current size)
        app.dialog.geometry(f"+{x}+{y}")
    
    def _highlight_frame_fields(app):
        """Highlight the frame-related input fields to draw attention"""
        # Store original colors
        if not hasattr(app, '_original_colors'):
            app._original_colors = {}
            
        # Highlight start frame entry
        if hasattr(app, 'start_entry'):
            app._original_colors['start'] = app.start_entry.cget('bg')
            app.start_entry.config(bg='#ffcccc')  # Light red
            
        # Highlight end frame entry  
        if hasattr(app, 'end_entry'):
            app._original_colors['end'] = app.end_entry.cget('bg')
            app.end_entry.config(bg='#ffcccc')  # Light red
            
        # Highlight frames entry
        if hasattr(app, 'frame_entry'):
            app._original_colors['frames'] = app.frame_entry.cget('bg')
            app.frame_entry.config(bg='#ffcccc')  # Light red
            
        # Schedule removal of highlighting after 3 seconds
        app.dialog.after(3000, app._remove_highlight)
    
    def _remove_highlight(app):
        """Remove highlighting from frame fields"""
        if hasattr(app, '_original_colors'):
            if hasattr(app, 'start_entry') and 'start' in app._original_colors:
                app.start_entry.config(bg=app._original_colors['start'])
            if hasattr(app, 'end_entry') and 'end' in app._original_colors:
                app.end_entry.config(bg=app._original_colors['end'])
            if hasattr(app, 'frame_entry') and 'frames' in app._original_colors:
                app.frame_entry.config(bg=app._original_colors['frames'])


class FramesWarningDialog:
    """Warning dialog for displaying 50+ frames in custom preview"""
    
    def __init__(self, parent, frame_count):
        self.parent = parent
        self.frame_count = frame_count
        self.result = False
        self.dont_show_again = False
        
        # Create the dialog window
        self.dialog = tk.Toplevel(parent.dialog)
        self.dialog.title("Warning - High Frame Count")
        self.dialog.geometry("500x180")
        self.dialog.resizable(False, False)
        
        # Make it modal and bring to front
        self.dialog.transient(parent.dialog)
        self.dialog.grab_set()
        self.dialog.lift()
        self.dialog.focus_force()
        
        # Center the dialog on the parent dialog
        self._center_dialog()
        
        self._create_ui()
        
    def _center_dialog(self):
        """Center the dialog on the parent dialog"""
        self.dialog.update_idletasks()
        
        # Get parent dialog position and size
        parent_x = self.parent.dialog.winfo_x()
        parent_y = self.parent.dialog.winfo_y()
        parent_width = self.parent.dialog.winfo_width()
        parent_height = self.parent.dialog.winfo_height()
        
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
        message = f"WARNING: Over 50 frames displayed ({self.frame_count} frames), this may be very laggy on older computers. Continue?"
        
        msg_label = tk.Label(main_frame, text=message, wraplength=460, justify="left", font=("Arial", 10))
        msg_label.pack(pady=(0, 20))
        
        # Button frame
        button_frame = tk.Frame(main_frame)
        button_frame.pack(fill="x", pady=(0, 10))
        
        # Buttons
        ballsy_btn = tk.Button(button_frame, text="Yeah I'm ballsy", command=self._on_ballsy, 
                              bg="#4CAF50", fg="white", font=("Arial", 10, "bold"), width=15)
        ballsy_btn.pack(side="left", padx=(0, 10))
        
        good_btn = tk.Button(button_frame, text="Nah I'm good", command=self._on_good, 
                            bg="#f44336", fg="white", font=("Arial", 10), width=15)
        good_btn.pack(side="left")
        
        # Don't show again checkbox
        self.dont_show_var = tk.BooleanVar()
        checkbox = tk.Checkbutton(main_frame, text="Don't show again", 
                                 variable=self.dont_show_var, font=("Arial", 9))
        checkbox.pack(anchor="w")
        
        # Handle window close event
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_good)
        
    def _on_ballsy(self):
        """User chose to proceed with high frame count"""
        self.result = True
        self.dont_show_again = self.dont_show_var.get()
        self.dialog.destroy()
        
    def _on_good(self):
        """User chose not to proceed with high frame count"""
        self.result = False
        self.dont_show_again = self.dont_show_var.get()
        self.dialog.destroy()
        
    def show(self):
        """Show the dialog and return the result"""
        self.dialog.wait_window()
        return self.result, self.dont_show_again


