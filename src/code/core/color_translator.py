import os
import re
PALETTE_SIZE = 256

class ColorTranslator:
        def categorize_palette(app, filename):
            """Categorize palette by its purpose based on filename - only uses character ID"""
            if not filename:
                return "unknown"
            
            filename_lower = filename.lower()
            
            # Hair palettes (chr###_0.pal to chr###_20.pal) - all are hair palettes
            # Must NOT start with 'w' to avoid matching fashion palettes like chr###_w00.pal
            if re.match(r'^chr\d{3}_\d+\.pal$', filename_lower):
                return "hair"
            
            # Fashion palettes (chr###_w##.pal) - categorize based on palette content analysis
            match = re.match(r'^chr(\d{3})_w\d+\.pal$', filename_lower)
            if match:
                char_num = match.group(1)
                
                # Always try to determine fashion type by analyzing palette content
                # Use the character number from the filename to analyze the palette
                return app.determine_fashion_type_from_palette_content(filename, char_num)
            
            return "unknown"
    
        def determine_fashion_type_from_palette_content(app, filename, char_num=None):
            """Determine fashion type by analyzing palette content based strictly on CHARACTER_RANGES"""
            if not char_num:
                if hasattr(app, 'current_character') and app.current_character:
                    char_num = app.current_character[3:]  # Extract "001" from "chr001"
                else:
                    return "unknown"
                    
            # For Paula characters, use the mapped character ID
            palette_char_num = char_num
            if char_num in ["025", "026", "027"]:
                if char_num == "025":
                    palette_char_num = "100"
                elif char_num == "026":
                    palette_char_num = "101"
                elif char_num == "027":
                    palette_char_num = "102"
            
            # Load the palette file
            try:
                from palette_ranges import CHARACTER_RANGES
                
                # Try different possible paths for the palette file
                script_dir = os.path.dirname(os.path.abspath(__file__))
                root_dir = getattr(app, "root_dir", 
                                  os.environ.get("FASHION_PREVIEWER_ROOT", 
                                               os.path.dirname(script_dir)))
                possible_paths = [
                    filename,  # Treat input as potential full path first
                    os.path.join("assets", "nonremovable_assets", "vanilla_pals", "fashion", filename),
                    os.path.join(root_dir, "exports", "custom_pals", "fashion", filename),
                    os.path.join(root_dir, "exports", "custom_fashion_pals", filename)  # backwards compatibility
                ]
                
                palette_data = None
                for path in possible_paths:
                    if os.path.exists(path) and os.path.isfile(path):
                        with open(path, "rb") as f:
                            data = f.read()
                        if len(data) == PALETTE_SIZE * 3:
                            palette_data = []
                            for i in range(PALETTE_SIZE):
                                r = data[i*3]
                                g = data[i*3+1] 
                                b = data[i*3+2]
                                palette_data.append((r, g, b))
                            break
                
                if not palette_data:
                    return "unknown"
                
                char_ranges = CHARACTER_RANGES.get(palette_char_num, {})
                if not char_ranges:
                    return "unknown"
                    
                best_match = "unknown"
                max_filled_percentage = 0.0
                tied_matches = []
                
                for fashion_type, ranges in char_ranges.items():
                    if fashion_type == "hair" or fashion_type == "3rd_job_base":
                        continue
                        
                    filled_count = 0
                    total_count = 0
                    for r in ranges:
                        for i in r:
                            total_count += 1
                            if i < len(palette_data):
                                color = palette_data[i]
                                # A simple check: if it's not purely empty padding, it's a color.
                                # We just avoid universal keying colors and magenta (255, 0, 255).
                                if not ColorTranslator.is_universal_keying_color(color) and color != (255, 0, 255):
                                    filled_count += 1
                                    
                    if total_count > 0:
                        percentage = filled_count / total_count
                        # Use a small epsilon to avoid floating point issues
                        if percentage > max_filled_percentage + 0.001:
                            max_filled_percentage = percentage
                            best_match = fashion_type
                            tied_matches = [fashion_type]
                        elif abs(percentage - max_filled_percentage) <= 0.001 and percentage > 0:
                            tied_matches.append(fashion_type)
                # If there's a tie, just rely on the first one that matched
                return best_match if max_filled_percentage > 0 else "unknown"
    
            except Exception as e:
                return "unknown"
    
        @staticmethod
        def is_universal_keying_color(color):
            """Check if a color is a universal keying color for ALL characters"""
            r, g, b = color
            
            # Pure green (0, 255, 0) - used by ALL characters including chr010
            if color == (0, 255, 0):
                return True
            
            # (0~25, 255, 0) pattern - used by chr002, chr008, chr024, and others
            # Analysis found: (5, 255, 0), (10, 255, 0), (14, 255, 0), (19, 255, 0), (23, 255, 0)
            if g == 255 and b == 0 and 0 <= r <= 25:
                return True
            
            # (0, 255, 0~21) pattern - used by chr003, chr011, chr019, and others
            # Analysis found: (0, 255, 21)
            if g == 255 and r == 0 and 0 <= b <= 21:
                return True
            
            return False
    
        def is_palette_keying_color(app, color, index, char_num):
            """Check if a color at a specific index is a keying color for the character"""
            # Universal keying colors for ALL characters
            if ColorTranslator.is_universal_keying_color(color) or color == (255, 0, 255):  # Magenta
                return True
            
            # Character-specific keying rules
            if char_num == "004":  # chr004 specific rules
                if color == (0, 0, 0):  # Black
                    return True
                if index == 255:  # Last color in palette
                    return True
            
            if app.is_green_padding(color) or app.is_magenta_transparency(color):
                return True

            return False
    
        def is_chr003_keying_color(app, color):
            """Check if a color is a keying color for chr003 (Sheep)"""
            # chr003 uses universal keying colors
            return ColorTranslator.is_universal_keying_color(color) or color == (255, 0, 255)  # Magenta
    
        def is_chr008_keying_color(app, color):
            """Check if a color is a keying color for chr008 (Raccoon)"""
            # chr008 uses universal keying colors
            return ColorTranslator.is_universal_keying_color(color) or color == (255, 0, 255)  # Magenta
    
        def is_chr011_keying_color(app, color):
            """Check if a color is a keying color for chr011 (Sheep 2nd Job)"""
            # chr011 uses the same keying patterns as chr003
            return ColorTranslator.is_universal_keying_color(color) or color == (255, 0, 255)  # Magenta
    
        def is_chr014_keying_color(app, color):
            """Check if a color is a keying color for chr014 (Lion 2nd Job)"""
            # chr014 uses more selective keying to avoid over-transparency
            # Only key out pure green and magenta, not green variants
            if color == (0, 255, 0) or color == (255, 0, 255):  # Pure green and magenta
                return True
            return False
    
        def is_blonde_like_color(app, color):
            """Check if a color is blonde-like (light yellow/orange)"""
            if not color or len(color) != 3:
                return False
            r, g, b = color
            # Check if it's a light color with yellow/orange tint
            return (r > 150 and g > 120 and b < 150 and 
                    r > g and g > b and  # Red > Green > Blue (yellow/orange tint)
                    (r + g + b) > 400)  # Light overall
    
        def is_hair_palette_keying_color(app, layer, color):
            """Check if a color is the keying color for a specific hair palette"""
            if layer.palette_type != "hair":
                return False
            
            # For chr001 hair palettes, always ignore 00FF00 (pure green)
            if app.current_character == "chr001" and color == (0, 255, 0):
                return True
            
            # For chr014 hair palettes, be more selective to avoid over-transparency
            if app.current_character == "chr014":
                # Only key out pure green and magenta, not green variants
                if color == (0, 255, 0) or color == (255, 0, 255):  # Pure green and magenta
                    return True
                return False
            
            # Universal keying colors for other characters
            if ColorTranslator.is_universal_keying_color(color) or color == (255, 0, 255):  # Magenta
                return True
        
            return False
    
        def is_fashion_palette_keying_color(app, layer, color, index):
            """Check if a color is a keying color for a fashion palette"""
            if not layer.palette_type.startswith("fashion_"):
                return False
            
            # For chr004 fashion palettes, ignore 00FF00 and the last color (index 255) no matter what
            if app.current_character == "chr004":
                if color == (0, 255, 0):  # Pure green
                    return True
                if index == 255:  # Last color in palette - always ignore
                    return True
                return False
            
            # Universal keying colors for ALL characters
            if ColorTranslator.is_universal_keying_color(color) or color == (255, 0, 255):  # Magenta
                return True
            
            # For other characters, use standard keying colors
            return (app.is_green_padding(color) or 
                    app.is_magenta_transparency(color))
    
        def _is_keyed_color(app, color, index=None):
            """Check if a color would be a keying color that should be avoided."""
            if color == (255, 0, 255) or color == (0, 255, 0):
                return True
            return False
    
        def _find_nearest_non_keyed_color(app, color):
            """Find the nearest color that isn't a keying color using HSV nudge."""
            if ColorTranslator._is_keyed_color(color, 0):
                import colorsys
                r, g, b = color
                h, s, v = colorsys.rgb_to_hsv(r/255.0, g/255.0, b/255.0)
                if v > 0.5:
                    v = max(0.0, v - 0.02)
                else:
                    v = min(1.0, v + 0.02)
                nr, ng, nb = colorsys.hsv_to_rgb(h, s, v)
                return (int(nr*255), int(ng*255), int(nb*255))
            return color
    
