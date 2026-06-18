class WindowBehavior:
    @staticmethod
    def on_app_close(app):
        """Save settings and statistics before closing"""
        if getattr(app, 'current_character', None):
            app._save_character_settings(app.current_character)
        if hasattr(app, '_save_settings'):
            app._save_settings()
        if hasattr(app, '_save_statistics'):
            app._save_statistics()
        if hasattr(app, 'master'):
            app.master.destroy()
