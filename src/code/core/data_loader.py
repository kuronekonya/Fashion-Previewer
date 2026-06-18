import os
import re
from icon_handler import CHARACTER_MAPPING
PALETTE_SIZE = 256

def fix_working_directory():
    script_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if os.getcwd() != script_dir:
        os.chdir(script_dir)

class DataLoader:
        @staticmethod
        def load_all_data(app):
            """Load all available characters, images, and palettes"""
            # Fix working directory first
            fix_working_directory()
            
            # Build map of (name, job) -> char_id to support new folder structure
            name_job_map = {}
            for char_id, info in CHARACTER_MAPPING.items():
                if 'name' in info and 'job' in info:
                    # Identify primary ID: prefer ID that doesn't have 'main_id' key
                    if 'main_id' in info:
                        continue
                    key = (info['name'].lower(), info['job'].lower())
                    name_job_map[key] = char_id
    
            # Load character images from assets/rawbmps folder
            rawbmps_path = "assets/rawbmps"
            if os.path.exists(rawbmps_path):
                for entry in os.listdir(rawbmps_path):
                    entry_path = os.path.join(rawbmps_path, entry)
                    if not os.path.isdir(entry_path):
                        continue
                        
                    # Case 1: Legacy structure - direct chrXXX folders
                    entry_lower = entry.lower()
                    if entry_lower.startswith("chr") and entry_lower in [k.lower() for k in CHARACTER_MAPPING.keys()]:
                        char_id = None
                        # Find the actual key case from CHARACTER_MAPPING
                        for k in CHARACTER_MAPPING:
                            if k.lower() == entry_lower:
                                char_id = k
                                break
                        
                        if char_id:
                            char_path = entry_path
                        images = []
                        for file in os.listdir(char_path):
                            if file.lower().endswith(('.bmp', '.png')):
                                images.append(os.path.join(char_path, file))
                        if images:
                            app.character_images[char_id] = sorted(images)
                            if char_id not in app.available_characters:
                                app.available_characters.append(char_id)
                                
                    # Case 2: New structure - "N. Name" folders with job subfolders
                    else:
                        # Match "1. Bunny" -> "Bunny"
                        match = re.match(r'^\d+\.\s*(.+)$', entry)
                        char_name_key = match.group(1).lower() if match else entry.lower()
                        
                        # Scan for job subfolders
                        for sub in os.listdir(entry_path):
                            sub_path = os.path.join(entry_path, sub)
                            if os.path.isdir(sub_path):
                                job_key = sub.lower() # "1st job", etc
                                
                                key = (char_name_key, job_key)
                                if key in name_job_map:
                                    char_id = name_job_map[key]
                                    
                                    images = []
                                    for file in os.listdir(sub_path):
                                        if file.lower().endswith(('.bmp', '.png')):
                                            images.append(os.path.join(sub_path, file))
                                    
                                    if images:
                                        app.character_images[char_id] = sorted(images)
                                        if char_id not in app.available_characters:
                                            app.available_characters.append(char_id)
            
            # Load fashion palettes from assets/nonremovable_assets/vanilla_pals/fashion folder
            script_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            root_dir = getattr(app, "root_dir", os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
            fashion_path = os.path.join(script_dir, "assets", "nonremovable_assets", "vanilla_pals", "fashion")
            if os.path.exists(fashion_path):
                for file in os.listdir(fashion_path):
                    if file.lower().endswith('.pal'):
                        char_match = re.match(r'^chr(\d{3})_w\d+\.pal$', file.lower())
                        if char_match:
                            char_num = char_match.group(1)
                            char_id = f"chr{char_num}"
                            if char_id not in app.fashion_palettes:
                                app.fashion_palettes[char_id] = []
                            
                            # Validate the palette file before adding it
                            palette_path = os.path.join(fashion_path, file)
                            try:
                                with open(palette_path, "rb") as f:
                                    data = f.read()
                                
                                if len(data) != PALETTE_SIZE * 3:
                                    print(f"CONSOLE ERROR MSG: Invalid fashion palette file {file} - incorrect size: {len(data)} bytes")
                                    continue
                                
                                # Validate that all bytes are valid (0-255)
                                valid_file = True
                                for i in range(PALETTE_SIZE * 3):
                                    if not (0 <= data[i] <= 255):
                                        print(f"CONSOLE ERROR MSG: Invalid fashion palette file {file} - invalid byte at position {i}")
                                        valid_file = False
                                        break
                                
                                if valid_file:
                                    app.fashion_palettes[char_id].append(palette_path)
                                
                            except Exception as e:
                                print(f"CONSOLE ERROR MSG: Failed to load fashion palette {file}: {e}")
                                continue
            
            # Load custom fashion palettes from root/exports/custom_pals/fashion AND backwards compatibility
            root_dir = getattr(app, "root_dir", 
                              os.environ.get("FASHION_PREVIEWER_ROOT", 
                                           os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            
            # Check both new and old paths for custom fashion palettes
            custom_fashion_paths = [
                os.path.join(root_dir, "exports", "custom_pals", "fashion"),
                os.path.join(root_dir, "exports", "custom_fashion_pals")  # backwards compatibility
            ]
            
            for custom_pals_path in custom_fashion_paths:
                path_type = "new" if "custom_pals" in custom_pals_path and "fashion" in custom_pals_path else "legacy"
                
                if not os.path.exists(custom_pals_path):
                    if path_type == "new":
                        os.makedirs(custom_pals_path, exist_ok=True)
                    continue
                for file in os.listdir(custom_pals_path):
                    if file.lower().endswith('.pal'):
                        # Check for fashion palettes (chr###_w#.pal through chr###_w######.pal)
                        fashion_match = re.match(r'^chr(\d{3})_w\d+\.pal$', file.lower())
                        if fashion_match:
                            char_num = fashion_match.group(1)
                            char_id = f"chr{char_num}"
                            if char_id not in app.fashion_palettes:
                                app.fashion_palettes[char_id] = []
                            
                            # Validate the palette file before adding it
                            palette_path = os.path.join(custom_pals_path, file)
                            try:
                                with open(palette_path, "rb") as f:
                                    data = f.read()
                                
                                if len(data) != PALETTE_SIZE * 3:
                                    continue
                                
                                # Validate that all bytes are valid (0-255)
                                valid_file = True
                                for i in range(PALETTE_SIZE * 3):
                                    if not (0 <= data[i] <= 255):
                                        print(f"CONSOLE ERROR MSG: Invalid custom fashion palette file {file} - invalid byte at position {i}")
                                        valid_file = False
                                        break
                                
                                if valid_file:
                                    app.fashion_palettes[char_id].append(palette_path)
                                
                            except Exception as e:
                                print(f"CONSOLE ERROR MSG: Failed to load custom fashion palette {file}: {e}")
                                continue
            
            # Load hair palettes from assets/nonremovable_assets/vanilla_pals/hair folder
            script_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            root_dir = getattr(app, "root_dir", os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
            hair_path = os.path.join(script_dir, "assets", "nonremovable_assets", "vanilla_pals", "hair")
            if os.path.exists(hair_path):
                for file in os.listdir(hair_path):
                    if file.lower().endswith('.pal'):
                        char_match = re.match(r'^chr(\d{3})_\d+\.pal$', file)
                        if char_match:
                            char_num = char_match.group(1)
                            char_id = f"chr{char_num}"
                            if char_id not in app.hair_palettes:
                                app.hair_palettes[char_id] = []
                            
                            # Validate the palette file before adding it
                            palette_path = os.path.join(hair_path, file)
                            try:
                                with open(palette_path, "rb") as f:
                                    data = f.read()
                                
                                if len(data) != PALETTE_SIZE * 3:
                                    print(f"CONSOLE ERROR MSG: Invalid hair palette file {file} - incorrect size: {len(data)} bytes")
                                    continue
                                
                                # Validate that all bytes are valid (0-255)
                                for i in range(PALETTE_SIZE * 3):
                                    if not (0 <= data[i] <= 255):
                                        print(f"CONSOLE ERROR MSG: Invalid hair palette file {file} - invalid byte at position {i}")
                                        continue
                                
                                app.hair_palettes[char_id].append(palette_path)
                                
                            except Exception as e:
                                print(f"CONSOLE ERROR MSG: Failed to load hair palette {file}: {e}")
                                continue
            
            # Load custom hair palettes from exports/custom_pals/hair folder
            root_dir = getattr(app, "root_dir", os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
            custom_hair_path = os.path.join(root_dir, "exports", "custom_pals", "hair")
            if os.path.exists(custom_hair_path):
                for file in os.listdir(custom_hair_path):
                    if file.lower().endswith('.pal'):
                        # Match pattern: chr###_#.pal (where # can be any number of digits)
                        char_match = re.match(r'^chr(\d{3})_(\d+)\.pal$', file)
                        if char_match:
                            char_num = char_match.group(1)
                            char_id = f"chr{char_num}"
                            if char_id not in app.hair_palettes:
                                app.hair_palettes[char_id] = []
                            
                            # Validate the custom palette file before adding it
                            palette_path = os.path.join(custom_hair_path, file)
                            try:
                                with open(palette_path, "rb") as f:
                                    data = f.read()
                                
                                if len(data) != PALETTE_SIZE * 3:
                                    print(f"CONSOLE ERROR MSG: Invalid custom hair palette file {file} - incorrect size: {len(data)} bytes")
                                    continue
                                
                                # Validate that all bytes are valid (0-255)
                                for i in range(PALETTE_SIZE * 3):
                                    if not (0 <= data[i] <= 255):
                                        print(f"CONSOLE ERROR MSG: Invalid custom hair palette file {file} - invalid byte at position {i}")
                                        continue
                                
                                app.hair_palettes[char_id].append(palette_path)
                                
                            except Exception as e:
                                print(f"CONSOLE ERROR MSG: Failed to load custom hair palette {file}: {e}")
                                continue
            
            # Load 3rd job base fashion palettes
            script_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            root_dir = getattr(app, "root_dir", os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
            third_job_path = os.path.join(script_dir, "assets", "nonremovable_assets", "vanilla_pals", "3rd_default_fashion")
            if os.path.exists(third_job_path):
                for char_folder in os.listdir(third_job_path):
                    if char_folder.startswith("chr") and os.path.isdir(os.path.join(third_job_path, char_folder)):
                        char_path = os.path.join(third_job_path, char_folder)
                        palettes = []
                        for file in os.listdir(char_path):
                            if file.lower().endswith('.pal'):
                                # Validate the palette file before adding it
                                palette_path = os.path.join(char_path, file)
                                try:
                                    with open(palette_path, "rb") as f:
                                        data = f.read()
                                    
                                    if len(data) != PALETTE_SIZE * 3:
                                        print(f"CONSOLE ERROR MSG: Invalid 3rd job palette file {file} - incorrect size: {len(data)} bytes")
                                        continue
                                    
                                    # Validate that all bytes are valid (0-255)
                                    for i in range(PALETTE_SIZE * 3):
                                        if not (0 <= data[i] <= 255):
                                            print(f"CONSOLE ERROR MSG: Invalid 3rd job palette file {file} - invalid byte at position {i}")
                                            continue
                                    
                                    palettes.append(palette_path)
                                    
                                except Exception as e:
                                    print(f"CONSOLE ERROR MSG: Failed to load 3rd job palette {file}: {e}")
                                    continue
                        if palettes:
                            app.third_job_palettes[char_folder] = sorted(palettes)
            
            # Get unique jobs from available characters
            jobs = set()
            for char_id in app.available_characters:
                if char_id in CHARACTER_MAPPING:
                    jobs.add(CHARACTER_MAPPING[char_id]["job"])
            app.available_jobs = sorted(list(jobs))
            
            # Print summary of loaded data
