
class IndexLoader:
        def _find_layer_by_pixel_index(app, pixel_idx):
            """Find the active layer that contains the given pixel index"""
            if not hasattr(app, 'palette_layers'):
                return None
                
            char_num = app.current_character.replace("chr", "")
            # Filter for active layers
            active_layers = [ly for ly in app.palette_layers if getattr(ly, "active", False)]
            
            found_layer = None
            for ly in active_layers:
                ptype = getattr(ly, "palette_type", "")
                if not ptype: continue
                
                ranges = app.get_character_palette_ranges(char_num, ptype)
                if ranges:
                    for r in ranges:
                        if pixel_idx in r:
                            found_layer = ly
                            break
                if found_layer: break
                
            return found_layer
    
        def get_allowed_indices_for_palette(app, layer, char_num):
            """Get the allowed index range for a palette based on character and palette type"""
            if not char_num or not layer:
                return set()  # No character loaded or no layer
            
            # For Paula characters, use the mapped character ID for palette ranges
            if char_num in ["025", "026", "027"]:
                if char_num == "025":
                    palette_char_num = "100"  # Paula 1st Job
                elif char_num == "026":
                    palette_char_num = "101"  # Paula 2nd Job
                elif char_num == "027":
                    palette_char_num = "102"  # Paula 3rd Job
            else:
                palette_char_num = char_num
            
            # Get the ranges for this character and palette type
            ranges = app.get_character_palette_ranges(palette_char_num, layer.palette_type)
            
            # Convert ranges to a set of indices
            allowed_indices = set()
            for r in ranges:
                allowed_indices.update(r)
            
            return allowed_indices
    
        def _get_editable_color_indices(app, layer=None):
            """Get the list of editable color indices for the specified layer or current character/fashion type"""
            try:
                # Import the CHARACTER_RANGES
                from palette_ranges import CHARACTER_RANGES
                
                # Use the provided layer or get current layer from the live editor
                current_layer = layer if layer is not None else app._live_current_layer()
                if not current_layer or not hasattr(current_layer, 'name'):
                    return []
                
                # Use the palette_type that's already set by the original UI's categorization
                fashion_type = getattr(current_layer, 'palette_type', None)
                
                if not fashion_type:
                    return []
    
                # If fashion_type is a verbose name (e.g. "Checkered Dress"), convert it back to key (e.g. "fashion_1")
                if fashion_type and not fashion_type.startswith("fashion_") and fashion_type != "hair" and fashion_type != "3rd_job_base":
                     # We need to find which key corresponds to this name for the current character
                     # Extract character number from layer name first to ensure we look up the right map
                     temp_layer_name = current_layer.name.lower()
                     temp_char_num = None
                     import re
                     for pattern in [r'chr(\d{3})', r'chr(\d+)', r'(\d{3})', r'(\d+)']:
                        char_match = re.search(pattern, temp_layer_name)
                        if char_match:
                            temp_char_num = char_match.group(1).zfill(3)
                            break
                     
                     if temp_char_num and hasattr(app, 'fashion_names'):
                         # Handle Paula mapping for name lookup
                         map_lookup_id = temp_char_num
                         if temp_char_num == "025": map_lookup_id = "100"
                         elif temp_char_num == "026": map_lookup_id = "101"
                         elif temp_char_num == "027": map_lookup_id = "102"
                         
                         if map_lookup_id in app.fashion_names:
                             mapping = app.fashion_names[map_lookup_id]
                             # Case-insensitive search
                             for key, name in mapping.items():
                                 if name.lower() == fashion_type.lower():
                                     fashion_type = key
                                     break
                
                # Extract character number from layer name
                layer_name = current_layer.name.lower()
                char_num = None
                import re
                
                # Try different patterns for character extraction
                for pattern in [r'chr(\d{3})', r'chr(\d+)', r'(\d{3})', r'(\d+)']:
                    char_match = re.search(pattern, layer_name)
                    if char_match:
                        char_num = char_match.group(1).zfill(3)  # Pad to 3 digits
                        break
                
                if not char_num:
                    return []
                
                # Get ranges for this character/fashion type
                ranges = CHARACTER_RANGES.get(char_num, {}).get(fashion_type, [])
                
                if not ranges:
                    return []
                
                editable_indices = []
                for r in ranges:
                    for idx in r:
                        editable_indices.append(idx)
                
                return editable_indices
                
            except Exception as e:
                print(f"CONSOLE ERROR MSG: Error getting editable color indices: {e}")
                return []
    
