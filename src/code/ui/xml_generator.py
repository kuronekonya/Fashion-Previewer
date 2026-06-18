import tkinter as tk
from code.utils.theme_manager import ThemeManager


class XMLGenerator:
    @staticmethod
    def open_xml_generator_dialog(app):
        """Open a dialog to prompt for XML Generation metadata"""
        dialog = tk.Toplevel(app.master)
        dialog.title("Generate XML")
        dialog.geometry("420x300")
        dialog.resizable(False, False)
        dialog.transient(app.master)
        dialog.grab_set()
        
        # Center on parent window
        dialog.update_idletasks()
        if hasattr(app, '_center_window_on_parent'):
            app._center_window_on_parent(dialog, app.master)

        
        # Try to load previous xml settings
        prev_settings = getattr(app, "last_xml_settings", {
            "id": "14000",
            "color": "Blue",
            "artist": "Anonymous",
            "server": "MyServer"
        })
        
        frame = tk.Frame(dialog)
        frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)
        
        tk.Label(frame, text="Starting ID:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        id_var = tk.StringVar(value=prev_settings.get("id", "14000"))
        tk.Entry(frame, textvariable=id_var).grid(row=0, column=1, sticky="w", padx=5, pady=5)
        
        tk.Label(frame, text="Color Name:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        color_var = tk.StringVar(value=prev_settings.get("color", "Blue"))
        tk.Entry(frame, textvariable=color_var).grid(row=1, column=1, sticky="w", padx=5, pady=5)
        
        tk.Label(frame, text="Artist:").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        artist_var = tk.StringVar(value=prev_settings.get("artist", "Anonymous"))
        tk.Entry(frame, textvariable=artist_var).grid(row=2, column=1, sticky="w", padx=5, pady=5)
        
        tk.Label(frame, text="Server Name:").grid(row=3, column=0, sticky="e", padx=5, pady=5)
        server_var = tk.StringVar(value=prev_settings.get("server", "MyServer"))
        tk.Entry(frame, textvariable=server_var).grid(row=3, column=1, sticky="w", padx=5, pady=5)
        
        # Buttons
        btn_frame = tk.Frame(frame)
        btn_frame.grid(row=4, column=0, columnspan=2, pady=20)
        
        def save_and_get_data():
            data = {
                "id": id_var.get(),
                "color": color_var.get(),
                "artist": artist_var.get(),
                "server": server_var.get()
            }
            app.last_xml_settings = data
            return data
            
        def on_open_full():
            data = save_and_get_data()
            dialog.destroy()
            app.open_full_creator(data)
            
        def on_quick_export():
            data = save_and_get_data()
            dialog.destroy()
            app.quick_xml_export(data)
            
        tk.Button(btn_frame, text="Open Full", command=on_open_full).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Quick Export", command=on_quick_export).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        ThemeManager.apply_theme(app, dialog)

    @staticmethod
    def quick_xml_export(app, data):
        from code.core.exporter import Exporter
        return Exporter.quick_xml_export(app, data)

