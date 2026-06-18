import tkinter as tk
from code.creator.ui_builder import CreatorUIBuilder
from code.creator.generators import CreatorGenerators
from code.creator.data_handlers import CreatorDataHandlers
from code.utils.theme_manager import ThemeManager

class FashionCreatorApp(tk.Toplevel, CreatorUIBuilder, CreatorGenerators, CreatorDataHandlers):
    def __init__(self, master=None, data=None, previewer_app=None, quick_export=False):
        if master is None:
            self.root = tk.Tk()
            self.root.withdraw()
            super().__init__(self.root)
        else:
            super().__init__(master)
            self.root = master
        self.previewer_app = previewer_app
        self.init_data = data or {}
        self.quick_export = quick_export
        self.title("Fashion Creator")
        self.geometry("1400x900")
        
        # Center the window relative to the main app if available, otherwise center on screen
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        
        if self.previewer_app and hasattr(self.previewer_app, 'master') and self.previewer_app.master.winfo_exists():
            parent_x = self.previewer_app.master.winfo_rootx()
            parent_y = self.previewer_app.master.winfo_rooty()
            parent_width = self.previewer_app.master.winfo_width()
            parent_height = self.previewer_app.master.winfo_height()
            
            x = parent_x + (parent_width - width) // 2
            y = parent_y + (parent_height - height) // 2
        else:
            screen_width = self.winfo_screenwidth()
            screen_height = self.winfo_screenheight()
            x = (screen_width - width) // 2
            y = (screen_height - height) // 2
            
        # Ensure it doesn't spawn off-screen
        x = max(0, min(x, self.winfo_screenwidth() - width))
        y = max(0, min(y, self.winfo_screenheight() - height))
        
        self.geometry(f"+{x}+{y}")
        self.variables = {} 
        self.items = [] 
        
        self.build_ui()
        # Apply dark mode from previewer app's dark_mode setting if available
        theme_context = self.previewer_app if self.previewer_app else self
        if not hasattr(theme_context, 'dark_mode'):
            theme_context.dark_mode = False
        if not hasattr(theme_context, 'master'):
            theme_context.master = self
        ThemeManager.apply_theme(theme_context, self)
        if self.quick_export and self.previewer_app:
            self.refresh_step2()
            self.run_generation_flow()
            self.destroy()


if __name__ == "__main__":
    app = FashionCreatorApp()
    app.mainloop()
