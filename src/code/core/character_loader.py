from fashionpreviewer import DEFAULT_FRAMES, DEFAULT_FLIPPED
import json

class CharacterLoader:
        def _save_per_character_frame_settings(app):
            """Save per-character hidden frames and export frames to settings"""
            try:
                settings_path = app._get_settings_path()
                
                # Load existing settings
                try:
                    with open(settings_path, 'r') as f:
                        data = json.load(f)
                except (FileNotFoundError, json.JSONDecodeError):
                    data = {'global': {}, 'per_character': {}}
                
                # Ensure per_character section exists
                if 'per_character' not in data:
                    data['per_character'] = {}
                
                # Update hidden frames for each character+job
                for char_job_raw, hidden_set in app.hidden_frames.items():
                    char_job = str(char_job_raw).strip().lower()
                    if char_job not in data['per_character']:
                        data['per_character'][char_job] = {}
                    data['per_character'][char_job]['hidden_frames'] = list(hidden_set)
                
                # Update export frames for each character
                for char_id_raw, frame_idx in app.export_frames.items():
                    char_id = str(char_id_raw).strip().lower()
                    # Find all char_job keys for this character
                    for char_job in list(data['per_character'].keys()):
                        if str(char_job).lower().startswith(char_id + '_'):
                            data['per_character'][char_job]['export_frame'] = frame_idx
                
                # Save to file
                with open(settings_path, 'w') as f:
                    json.dump(data, f, indent=4)
                    
            except Exception as e:
                print(f"CONSOLE ERROR MSG: Error saving per-character frame settings: {e}")
    
        def _load_character_settings(app, char_id):
            """Load per-character settings for the given character"""
            char_id = str(char_id).strip().lower()
            if not hasattr(app, 'per_character_settings'):
                app.per_character_settings = {}
                
            char_settings = app.per_character_settings.get(char_id, {})
            
            # Load per-character settings
            app.custom_frame_count = char_settings.get('custom_frame_count', 3)
            app.custom_start_index = char_settings.get('custom_start_index', 0)
            app.use_frame_choice = char_settings.get('use_frame_choice', False)
            app.chosen_frame = char_settings.get('chosen_frame', 1)
            
            # Calculate default frame
            default_frame = 0
            from icon_handler import CHARACTER_MAPPING
            if hasattr(app, 'current_character') and app.current_character in CHARACTER_MAPPING:
                char_info = CHARACTER_MAPPING[app.current_character]
                name = char_info.get("name", "")
                job = char_info.get("job", "")
                if name in DEFAULT_FRAMES and job in DEFAULT_FRAMES[name]:
                    # Values are already 0-indexed in DEFAULT_FRAMES
                    default_frame = DEFAULT_FRAMES[name][job]
                    
            # Load last viewed frame index
            app.current_image_index = char_settings.get('last_viewed_frame', default_frame)
            
            # Apply default flip state if this is a first-load (no saved settings) and character has a flip default
            if not char_settings:
                name = ""
                job = ""
                from icon_handler import CHARACTER_MAPPING
                if hasattr(app, 'current_character') and app.current_character in CHARACTER_MAPPING:
                    info = CHARACTER_MAPPING[app.current_character]
                    name = info.get("name", "")
                    job = info.get("job", "")
                if name in DEFAULT_FLIPPED and job in DEFAULT_FLIPPED[name]:
                    app.image_flip = True
                else:
                    app.image_flip = False
            
            # Store loaded palettes for UI update methods to use
            app.loaded_palettes = char_settings.get('palette_selections', {})
    
        def _save_character_settings(app, char_id):
            """Save per-character settings for the given character"""
            char_id = str(char_id).strip().lower()
            if not hasattr(app, 'per_character_settings'):
                app.per_character_settings = {}
            
            # Capture current palette selections if they exist
            palette_selections = {}
            if hasattr(app, 'hair_var'):
                palette_selections['hair'] = app.hair_var.get()
            if hasattr(app, 'third_job_var'):
                palette_selections['third_job'] = app.third_job_var.get()
            if hasattr(app, 'fashion_vars'):
                palette_selections['fashion'] = {k: v.get() for k, v in app.fashion_vars.items()}
                
            # Save per-character settings (including palette selections)
            app.per_character_settings[char_id] = {
                'custom_frame_count': app.custom_frame_count,
                'custom_start_index': app.custom_start_index,
                'use_frame_choice': app.use_frame_choice,
                'chosen_frame': app.chosen_frame,
                'last_viewed_frame': app.current_image_index,
                'palette_selections': palette_selections
            }
            
            # Save to file
            app._save_settings()
    
        def get_character_palette_ranges(app, char_num, palette_type):
            """Get the allowed index ranges for a specific character and palette type"""
            # Comprehensive hard-coded palette ranges based on gap analysis
            character_ranges = {
                "001": {
                    "fashion_1": [range(111, 128)],  # w00-w06: 111-127
                    "fashion_2": [range(128, 152)],  # w10-w16: 128-151
                    "fashion_3": [range(154, 160)],  # w20-w26: 154-159
                    "fashion_4": [range(160, 169)],  # w30-w36: 160-168
                    "fashion_5": [range(173, 192)],  # w40-w46: 173-191
                    "hair": [range(208, 226)]  # Hair palettes: 208-225
                },
                "002": {
                    "fashion_1": [range(111, 128)],  # w00-w06: 111-127
                    "fashion_2": [range(128, 137)],  # w10-w16: 128-136
                    "fashion_3": [range(140, 144)],  # w20-w26: 140-143
                    "fashion_4": [range(144, 154)],  # w30-w36: 144-153
                    "fashion_5": [range(160, 172)],  # w40-w46: 160-171
                    "fashion_6": [range(176, 185)],  # w50-w56: 176-184
                    "hair": [range(208, 226)]  # Hair palettes: 208-225
                },
                "003": {
                    "fashion_1": [range(0, 254)],  # w00-w06: 0-253
                    "fashion_2": [range(0, 135)],  # w10-w16: 0-134
                    "fashion_3": [range(0, 136), range(137, 144)],  # w20-w26: 0-135, 137-143
                    "fashion_4": [range(0, 136), range(144, 154)],  # w30-w36: 0-135, 144-153
                    "fashion_5": [range(0, 154), range(155, 160)],  # w40-w46: 0-153, 155-159
                    "fashion_6": [range(0, 175)],  # w50-w56: 0-174
                    "hair": [range(208, 226)]  # Hair palettes: 208-225
                },
                "004": {
                    "fashion_1": [range(111, 133)],  # w00-w06: 111-132
                    "fashion_2": [range(134, 145)],  # w10-w16: 134-144
                    "fashion_3": [range(146, 160)],  # w20-w26: 146-159
                    "fashion_4": [range(160, 172)],  # w30-w36: 160-171
                    "fashion_5": [range(176, 198)],  # w40-w46: 176-197
                    "hair": [range(208, 226)]  # Hair palettes: 208-219
                },
                "005": {
                    "fashion_1": [range(111, 119)],  # w00-w06: 111-118
                    "fashion_2": [range(122, 128)],  # w10-w16: 122-127
                    "fashion_3": [range(128, 139)],  # w20-w26: 128-138
                    "fashion_4": [range(140, 144)],  # w30-w36: 140-143
                    "fashion_5": [range(144, 208)],  # w40-w46: 144-207
                    "hair": [range(208, 226)]  # Hair palettes: 208-225
                },
                "006": {
                    "fashion_1": [range(111, 147)],  # w00-w06: 111-146
                    "fashion_2": [range(148, 166)],  # w10-w16: 148-165
                    "fashion_3": [range(167, 190)],  # w20-w26: 167-189
                    "fashion_4": [range(191, 202)],  # w30-w36: 191-201
                    "fashion_5": [range(202, 208)],  # w40-w46: 202-207
                    "hair": [range(208, 226)]  # Hair palettes: 208-225
                },
                "007": {
                    "fashion_1": [range(111, 120)],  # w00-w06: 111-119
                    "fashion_2": [range(124, 128)],  # w10-w16: 124-127
                    "fashion_3": [range(128, 138)],  # w20-w26: 128-137
                    "fashion_4": [range(144, 168)],  # w30-w36: 144-167
                    "fashion_5": [range(169, 192)],  # w40-w46: 169-191
                    "fashion_6": [range(192, 202)],  # w50-w56: 192-201
                    "hair": [range(208, 226)]  # Hair palettes: 208-225
                },
                "008": {
                    "fashion_1": [range(0, 95), range(111, 134)],  # w00-w06: 0-94, 111-133
                    "fashion_2": [range(137, 144)],  # w10-w16: 137-143
                    "fashion_3": [range(144, 151)],  # w20-w26: 144-150
                    "hair": [range(208, 226)]  # Hair palettes: 208-225
                },
                "009": {
                    "fashion_1": [range(111, 127)],  # w00-w04: 111-126
                    "fashion_2": [range(128, 152)],  # w10-w14: 128-151
                    "fashion_3": [range(153, 157)],  # w20-w24: 153-156
                    "fashion_4": [range(158, 163)],  # w30-w34: 158-162
                    "fashion_5": [range(164, 171)],  # w40-w44: 164-170
                    "fashion_6": [range(172, 178)],  # w50-w54: 172-177
                    "hair": [range(208, 226)]  # Hair palettes: 208-225
                },
                "010": {
                    "fashion_1": [range(111, 122)],  # w00-w04: 111-121
                    "fashion_2": [range(123, 149)],  # w10-w14: 123-148
                    "fashion_3": [range(150, 158)],  # w20-w24: 150-157
                    "fashion_4": [range(159, 176)],  # w30-w34: 159-175
                    "fashion_5": [range(177, 201)],  # w40-w44: 177-200
                    "hair": [range(208, 226)]  # Hair palettes: 208-225
                },
                "011": {
                    "fashion_1": [range(0, 110), range(111, 137)],  # w00-w04: 0-109, 111-136
                    "fashion_2": [range(0, 137), range(138, 149)],  # w10-w14: 0-136, 138-148
                    "fashion_3": [range(0, 149), range(150, 236)],  # w20-w24: 0-148, 150-235
                    "fashion_4": [range(0, 177)],  # w30-w34: 0-176
                    "fashion_5": [range(0, 177), range(178, 198)],  # w40-w44: 0-176, 178-197
                    "hair": [range(208, 226)]  # Hair palettes: 208-225
                },
                "012": {
                    "fashion_1": [range(111, 121)],  # w00-w04: 111-120
                    "fashion_2": [range(122, 133)],  # w10-w14: 122-132
                    "fashion_3": [range(134, 159)],  # w20-w24: 134-158
                    "fashion_4": [range(160, 172)],  # w30-w34: 160-171
                    "fashion_5": [range(173, 195)],  # w40-w44: 173-194
                    "hair": [range(208, 226)]  # Hair palettes: 208-225
                },
                "013": {
                    "fashion_1": [range(111, 131)],  # w00-w04: 111-130
                    "fashion_2": [range(132, 148)],  # w10-w14: 131-148
                    "fashion_3": [range(149, 153)],  # w20-w24: 149-157
                    "fashion_4": [range(154, 157)],  # w30-w34: 158-165
                    "fashion_5": [range(158, 177)],  # Shoes: 166-176
                    "hair": [range(208, 226)]  # Hair palettes: 208-225
                },
                "014": {
                    "fashion_1": [range(111, 116)],  # w00-w04: 111-115
                    "fashion_2": [range(118, 155)],  # w10-w14: 118-154
                    "fashion_3": [range(156, 165)],  # w20-w24: 156-164
                    "fashion_4": [range(166, 172)],  # w30-w34: 166-171
                    "fashion_5": [range(173, 185)],  # w40-w44: 173-184
                    "hair": [range(208, 232)]  # Hair palettes: 208-231
                },
                "015": {
                    "fashion_1": [range(111, 123)],  # w00-w04: 111-122
                    "fashion_2": [range(124, 132)],  # w10-w14: 124-131
                    "fashion_3": [range(133, 143)],  # w20-w24: 133-142
                    "fashion_4": [range(144, 149)],  # w30-w34: 144-148
                    "fashion_5": [range(150, 164)],  # w40-w44: 150-163
                    "hair": [range(208, 226)]  # Hair palettes: 208-225
                },
                "016": {
                    "fashion_1": [range(111, 121)],  # w00-w04: 111-120
                    "fashion_2": [range(122, 148)],  # w10-w14: 122-147
                    "fashion_3": [range(149, 156)],  # w20-w24: 149-155
                    "hair": [range(208, 226)]  # Hair palettes: 208-225
                },
                "017": {
                    "fashion_1": [range(111, 124)],  # w00-w03: 111-123
                    "fashion_2": [range(128, 141)],  # w10-w13: 128-140
                    "fashion_3": [range(144, 160)],  # w20-w23: 144-159
                    "fashion_4": [range(160, 168), range(170, 176)],  # w30-w33: 160-167, 170-175
                    "fashion_5": [range(176, 190)],  # w40-w43, w50: 176-189
                    "3rd_job_base": [range(111, 190)],  # 3rd job base fashion: 111-189
                    "hair": [range(208, 232)]  # Hair palettes: 208-231
                },
                "018": {
                    "fashion_1": [range(111, 113)],  # w00-w03: 111-112
                    "fashion_2": [range(116, 149)],  # w10-w13: 116-148
                    "fashion_3": [range(150, 157), range(158, 174)],  # w20-w23: 150-156, 158-173
                    "fashion_4": [range(176, 181)],  # w30-w33: 176-180
                    "fashion_5": [range(181, 184), range(187, 205)],  # w40-w41, w43: 181-183, 187-204
                    "fashion_6": [range(187, 205)],  # w50-w51: 187-204
                    "3rd_job_base": [range(111, 205)],  # 3rd job base fashion: 111-204
                    "hair": [range(208, 231)]  # Hair palettes: 208-230
                },
                "019": {
                    "fashion_1": [range(0, 110), range(111, 141)],  # w00-w03: 0-109, 111-140
                    "fashion_2": [range(0, 143), range(144, 155)],  # w10-w13: 0-142, 144-154
                    "fashion_3": [range(0, 155), range(156, 174)],  # w20-w23: 0-154, 156-173
                    "fashion_4": [range(0, 174), range(175, 192)],  # w30-w33: 0-173, 175-191
                    "fashion_5": [range(0, 191), range(195, 208)],  # w40-w43: 0-190, 195-207
                    "hair": [range(208, 226)]  # Hair palettes: 208-225
                },
                "020": {
                    "fashion_1": [range(111, 139)],  # w00-w03: 111-138
                    "fashion_2": [range(140, 148)],  # w10-w13: 140-147
                    "fashion_3": [range(150, 160)],  # w20-w23: 150-159
                    "fashion_4": [range(160, 173)],  # w30-w33: 160-172
                    "fashion_5": [range(173, 192)],  # w40-w43: 173-191
                    "3rd_job_base": [range(111, 192)],  # 3rd job base fashion: 111-191
                    "hair": [range(208, 219)]  # Hair palettes: 208-218
                },
                "021": {
                    "fashion_1": [range(111, 132)],  # w00-w03: 111-131
                    "fashion_2": [range(133, 137)],  # w10-w13: 133-136
                    "fashion_3": [range(140, 152)],  # w20-w23: 140-151
                    "fashion_4": [range(153, 168)],  # w30-w33: 153-167
                    "fashion_5": [range(173, 185)],  # w40: 173-184
                    "hair": [range(208, 226)]  # Hair palettes: 208-225
                },
                "022": {
                    "fashion_1": [range(111, 137)],  # w00-w03: 111-136
                    "fashion_2": [range(140, 161)],  # w10-w13: 140-160
                    "fashion_3": [range(164, 177)],  # w20-w23: 164-176
                    "fashion_4": [range(180, 198)],  # w30-w33: 180-197
                    "fashion_5": [range(158, 177)],  # w40: 158-176
                    "3rd_job_base": [range(111, 198)],  # 3rd job base fashion: 111-197
                    "hair": [range(208, 232)]  # Hair palettes: 208-231
                },
                "023": {
                    "fashion_1": [range(111, 125), range(126, 144)],  # w00-w03: 111-124, 126-143
                    "fashion_2": [range(144, 148)],  # w10-w13: 144-147
                    "fashion_3": [range(150, 156), range(160, 186)],  # w20-w23: 150-155, 160-185
                    "fashion_4": [range(188, 194)],  # w30-w33, w40-w41: 188-193
                    "hair": [range(208, 226)]  # Hair palettes: 208-225
                },
                "024": {
                    "fashion_1": [range(111, 131)],  # 111-130
                    "fashion_2": [range(134, 149)],  # 134-148
                    "fashion_3": [range(150, 165)],  # 150-164
                    "fashion_4": [range(166, 174)],  # 166-173
                    "fashion_5": [range(176, 182)],  # Formal Shoes
                    "hair": [range(208, 226)]  # Hair palettes: 208-225
                },
                "100": {
                    "fashion_1": [range(111, 142)],  # group 1: 111-141
                    "fashion_2": [range(142, 154)],  # group 2: 142-153
                    "fashion_3": [range(154, 168)],  # group 3: 154-167
                    "fashion_4": [range(168, 174), range(189, 193)],  # group 4: 168-173 AND 189-192
                    "fashion_5": [range(174, 177)],  # group 5: 174-176
                    "fashion_6": [range(177, 189)],  # group 6: 177-188
                    "fashion_7": [range(189, 193)],  # group 7: 189-192
                    "hair": [range(208, 226)]  # Hair palettes: 208-225
                },
                "101": {
                    "fashion_1": [range(111, 142)],  # w00-w04: 111-141
                    "fashion_2": [range(142, 156)],  # w10-w14: 142-155
                    "fashion_3": [range(156, 174)],  # w20-w24: 156-173
                    "fashion_4": [range(174, 178)],  # w30-w34: 174-177
                    "fashion_5": [range(178, 190)],  # w40-w44: 178-189
                    "fashion_6": [range(190, 193)],  # w50-w54: 190-192
                    "hair": [range(208, 226)]  # Hair palettes: 208-225
                },
                "102": {
                    "fashion_1": [range(111, 118)],  # w00-w03: 111-117
                    "fashion_2": [range(119, 147)],  # w10-w13: 119-146
                    "fashion_3": [range(148, 151)],  # w20-w23: 148-150
                    "fashion_4": [range(152, 166)],  # w30-w33: 152-165
                    "fashion_5": [range(167, 175)],  # w40-w43: 167-174
                    "fashion_6": [range(176, 182)],  # w50-w53: 176-181
                    "fashion_7": [range(183, 192)],  # w60-w63: 183-191
                    "fashion_8": [range(192, 208)],  # w70-w73: 192-207
                    "hair": [range(208, 226)]  # Hair palettes: 208-225
                }
            }
            
            # Get ranges for this character and palette type
            if char_num in character_ranges and palette_type in character_ranges[char_num]:
                return character_ranges[char_num][palette_type]
            
            # Fallback: return all indices for unknown characters or palette types
            return [range(256)]
    
        def _get_char_job_key(app):
            """Get the character/job key for frame visibility tracking"""
            if not hasattr(app, 'current_character') or not app.current_character:
                return None
            current_job = app.job_var.get() if hasattr(app, 'job_var') else None
            return f"{app.current_character}_{current_job}"
    
