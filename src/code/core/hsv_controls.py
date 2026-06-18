
class HSVControls:
        def _hsv_debounced_change(app, *_):
            """Debounce slider/entry changes and call _live_hsv_changed() once per burst. Prevents jitter by avoiding recursion and canceling stale callbacks."""
            # Cancel any prior scheduled call
            try:
                if getattr(app, "_hsv_after_id", None):
                    try:
                        app.master.after_cancel(app._hsv_after_id)
                    except Exception:
                        pass
            except Exception:
                pass
        
            def _apply():
                # Clear token to avoid future cancels on this one
                app._hsv_after_id = None
                # Guard to avoid re-entrancy if widgets update vars
                if getattr(app, "_hsv_guard", False):
                    return
                try:
                    app._hsv_guard = True
                    if hasattr(app, "_live_hsv_changed"):
                        app._live_hsv_changed()
                finally:
                    app._hsv_guard = False
        
            # Schedule a single near-future update (~60 FPS)
            try:
                app._hsv_after_id = app.master.after(16, _apply)
            except Exception:
                _apply()
    
