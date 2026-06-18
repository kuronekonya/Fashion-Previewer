import tkinter as tk
from tkinter import ttk

class ThemeManager:
    @staticmethod
    def toggle_dark_mode(app):
        """Toggle dark mode on and off"""
        app.dark_mode = not getattr(app, 'dark_mode', False)
        if hasattr(app, '_save_settings'):
            app._save_settings()
        ThemeManager.apply_theme(app)
        
    @staticmethod
    def apply_theme(app, widget=None):
        """Recursively apply the current theme to all widgets"""
        master_widget = getattr(app, 'master', app)
        if widget is None:
            widget = master_widget
            
        is_dark = getattr(app, 'dark_mode', False)
        
        # Define colors - darker for true dark mode
        bg_color = "#1E1E1E" if is_dark else "#F0F0F0"
        fg_color = "#FFFFFF" if is_dark else "#000000"
        canvas_bg = "#151515" if is_dark else "white"
        input_bg = "#252525" if is_dark else "white"
        select_color = "#333333" if is_dark else "white"
        btn_bg = "#2D2D2D" if is_dark else "#E0E0E0"
        
        # Base application background
        if widget == master_widget:
            try:
                master_widget.configure(bg=bg_color)
            except:
                pass
                
        # Don't theme the swatch frames in compact editor to preserve their colors
        if hasattr(app, '_compact_swatch_widgets') and widget in app._compact_swatch_widgets.values():
            return
            
        # Don't theme the bg color button so it retains its color choice
        if hasattr(app, 'bg_color_button') and widget == app.bg_color_button:
            return
            
        try:
            wtype = widget.winfo_class()
            
            if wtype in ("Frame", "Toplevel", "Tk"):
                widget.configure(bg=bg_color)
                
            elif wtype in ("Label", "LabelFrame", "Labelframe", "Radiobutton", "Checkbutton"):
                widget.configure(bg=bg_color, fg=fg_color)
                if wtype in ("Radiobutton", "Checkbutton"):
                    hover_bg = "#333333" if is_dark else "#D0D0D0"
                    widget.configure(selectcolor=select_color, activebackground=hover_bg, activeforeground=fg_color)
                    
            elif wtype == "Canvas":
                current_bg = widget.cget("bg")
                if current_bg in ("white", "#1E1E1E", "#151515", "#F0F0F0", "#2E2E2E", "#202020", "SystemButtonFace", "", "#d9d9d9"):
                    # Use canvas_bg (darker) for the main preview canvas, otherwise use normal bg_color
                    if hasattr(app, 'canvas') and widget == app.canvas:
                        widget.configure(bg=canvas_bg, highlightbackground=canvas_bg)
                    else:
                        widget.configure(bg=bg_color, highlightbackground=bg_color)
                    
            elif wtype in ("Entry", "Listbox"):
                widget.configure(bg=input_bg, fg=fg_color, insertbackground=fg_color, highlightbackground=bg_color)
                
            elif wtype in ("Button", "Menubutton"):
                # Only theme standard buttons and menubuttons
                is_gradient = False
                try:
                    if widget.cget("text") == "🌈":
                        widget.configure(bg="#FF4081", fg=fg_color, activebackground="#E91E63", activeforeground=fg_color)
                        is_gradient = True
                except:
                    pass
                if not is_gradient:
                    widget.configure(bg=bg_color, fg=fg_color, activebackground="#333333" if is_dark else "#D0D0D0", activeforeground=fg_color)
                
            elif wtype == "Scrollbar":
                widget.configure(bg=btn_bg, troughcolor=bg_color, activebackground="#505050" if is_dark else "#D0D0D0")
                
            elif wtype == "Text":
                widget.configure(bg=input_bg, fg=fg_color, insertbackground=fg_color, highlightbackground=bg_color)
                
            elif wtype in ("Scale", "TScale"):
                widget.configure(bg=bg_color, fg=fg_color, highlightbackground=bg_color)
                try:
                    widget.configure(troughcolor=bg_color)
                except:
                    pass
        except Exception:
            pass
            
        # Apply ttk styles globally
        try:
            wtype_for_style = widget.winfo_class() if hasattr(widget, 'winfo_class') else ""
            if widget == master_widget or wtype_for_style in ("Toplevel", "Tk"):
                style = ttk.Style()
                if is_dark:
                    style.theme_use('clam')
                    style.configure('.', background=bg_color, foreground=fg_color)
                    
                    combo_bg = "#252525" if is_dark else input_bg
                    style.configure('TCombobox', fieldbackground=combo_bg, background=combo_bg, foreground=fg_color, selectbackground=select_color, selectforeground=fg_color)
                    style.map('TCombobox', fieldbackground=[('readonly', combo_bg)], background=[('readonly', combo_bg)], foreground=[('readonly', fg_color)])
                    try:
                        master_widget.option_add('*TCombobox*Listbox.background', combo_bg)
                        master_widget.option_add('*TCombobox*Listbox.foreground', fg_color)
                        master_widget.option_add('*TCombobox*Listbox.selectBackground', select_color)
                        master_widget.option_add('*TCombobox*Listbox.selectForeground', fg_color)
                    except:
                        pass
                        
                    style.configure('TEntry', fieldbackground=combo_bg, background=combo_bg, foreground=fg_color)
                    style.map('TEntry', fieldbackground=[('!disabled', combo_bg)], background=[('!disabled', combo_bg)], foreground=[('!disabled', fg_color)])

                    style.configure('TNotebook', background=bg_color, tabmargins=[2, 5, 2, 0])
                    style.configure('TNotebook.Tab', background=btn_bg, foreground=fg_color, padding=[10, 2])
                    style.map('TNotebook.Tab', background=[('selected', input_bg)], expand=[('selected', [1, 1, 1, 0])])
                    style.configure('TScrollbar', background=btn_bg, troughcolor=bg_color, arrowcolor=fg_color, bordercolor=bg_color, lightcolor=bg_color, darkcolor=bg_color)
                    style.configure('Vertical.TScrollbar', background=btn_bg, troughcolor=bg_color, arrowcolor=fg_color, bordercolor=bg_color, lightcolor=bg_color, darkcolor=bg_color)
                    style.configure('Horizontal.TScrollbar', background=btn_bg, troughcolor=bg_color, arrowcolor=fg_color, bordercolor=bg_color, lightcolor=bg_color, darkcolor=bg_color)
                    style.configure('TScale', background=bg_color, troughcolor=bg_color, slidercolor=btn_bg, bordercolor=bg_color, lightcolor=bg_color, darkcolor=bg_color)
                    style.configure('Horizontal.TScale', background=bg_color, troughcolor=bg_color, slidercolor=btn_bg)
                    style.configure('TButton', background=btn_bg, foreground=fg_color, bordercolor=bg_color, lightcolor=bg_color, darkcolor=bg_color)
                    style.map('TButton', background=[('active', "#333333")], foreground=[('active', fg_color)])
                    
                    # Add Treeview, LabelFrame, and Checkbutton styling for dark mode
                    style.configure('Treeview', background=input_bg, foreground=fg_color, fieldbackground=input_bg)
                    style.map('Treeview', background=[('selected', select_color)], foreground=[('selected', fg_color)])
                    style.configure('Treeview.Heading', background=btn_bg, foreground=fg_color)
                    style.map('Treeview.Heading', background=[('active', "#333333")], foreground=[('active', fg_color)])
                    
                    style.configure('TLabelframe', background=bg_color)
                    style.configure('TLabelframe.Label', background=bg_color, foreground=fg_color)
                    
                    style.configure('TCheckbutton', background=bg_color, foreground=fg_color)
                    style.map('TCheckbutton', background=[('active', bg_color)], foreground=[('active', fg_color)])
                else:
                    try:
                        style.theme_use('vista')
                    except tk.TclError:
                        try:
                            style.theme_use('winnative')
                        except tk.TclError:
                            style.theme_use('default')
        except Exception:
            pass

        # Recursively apply to children
        for child in widget.winfo_children():
            ThemeManager.apply_theme(app, child)
