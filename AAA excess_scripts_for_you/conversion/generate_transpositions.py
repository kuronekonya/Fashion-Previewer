
import re
import os

def parse_md_file(file_path):
    print(f"Parsing {file_path}...")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    transpositions = {}
    fixed_indices = {}
    
    current_char = None
    current_item = None
    current_icon_index = None
    current_base_index = None
    base_rgb = None
    icon_rgb = None
    
    char_pattern = re.compile(r'^# Chr(\d+)')
    item_pattern = re.compile(r'^## (.+)')
    # Matches "Base: r, g, b"
    color_pattern = re.compile(r'^(?:Base|Icon): (\d+), (\d+), (\d+)')
    
    # Exception text
    exception_text = "Do not translate the following indexes across the active palette to the icon palette--keep them as they are on the icon palette always: "
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # ... (char, item headers)
        m_char = char_pattern.match(line)
        if m_char:
            current_char = f"chr{m_char.group(1)}"
            if current_char not in transpositions:
                transpositions[current_char] = {}
            current_item = None
            continue

        m_item = item_pattern.match(line)
        if m_item:
            raw_item = m_item.group(1).lower()
            current_item = ''.join(c for c in raw_item if c.isalnum())
            if current_char and current_item:
                if current_item not in transpositions[current_char]:
                    transpositions[current_char][current_item] = {}
            continue
            
        # ... (fixed index check - unchanged)
        if exception_text in line:
            # Parse the numbers list
            numbers_part = line.split(exception_text)[1].strip()
            # Remove any trailing periods or text
            numbers_part = re.split(r'[^\d,\s]', numbers_part)[0]
            indices = [int(x.strip()) for x in numbers_part.split(',') if x.strip().isdigit()]
            
            if current_char and current_item:
                if current_char not in fixed_indices:
                    fixed_indices[current_char] = {}
                if current_item not in fixed_indices[current_char]:
                    fixed_indices[current_char][current_item] = []
                fixed_indices[current_char][current_item].extend(indices)
            continue

        # Check for Index lines
        if line.startswith("Index "):
            # Special case: "Index 0 (Icon) Index 130 (base)"
            lower_line = line.lower()
            if "(icon)" in lower_line and "(base)" in lower_line:
                # Regex for explicit mapping
                m_complex = re.search(r'index\s+(\d+)\s*\(icon\).*index\s+(\d+)\s*\(base\)', lower_line)
                if m_complex:
                    current_icon_index = int(m_complex.group(1))
                    current_base_index = int(m_complex.group(2))
                else:
                    print(f"Warning: Could not parse complex index line: {line}")
                    current_base_index = None
                    current_icon_index = None
            else:
                # Simple "Index 160"
                m_idx = re.search(r'Index (\d+)', line)
                if m_idx:
                    val = int(m_idx.group(1))
                    current_base_index = val
                    current_icon_index = val
                else:
                    current_base_index = None
                    current_icon_index = None
            
            # Reset colors
            base_rgb = None
            icon_rgb = None
            continue
            
        # ... (color parsing - unchanged)
        if line.startswith("Base:"):
            m_col = color_pattern.match(line)
            if m_col:
                base_rgb = (int(m_col.group(1)), int(m_col.group(2)), int(m_col.group(3)))
        elif line.startswith("Icon:"):
            m_col = color_pattern.match(line)
            if m_col:
                icon_rgb = (int(m_col.group(1)), int(m_col.group(2)), int(m_col.group(3)))
                
        # If we have all data, calculate
        if current_char and current_item and current_base_index is not None and base_rgb and icon_rgb:
            r_diff = int(icon_rgb[0]) - int(base_rgb[0])
            g_diff = int(icon_rgb[1]) - int(base_rgb[1])
            b_diff = int(icon_rgb[2]) - int(base_rgb[2])
            
            # Store tuple of (offset, icon_index)
            # Or dict? Tuple is more compact. (offset_tuple, icon_index)
            # Actually dict is clearer in generated code.
            transpositions[current_char][current_item][current_base_index] = {
                'offset': (r_diff, g_diff, b_diff),
                'icon_index': current_icon_index
            }
            
            # Reset to avoid double adding
            base_rgb = None
            icon_rgb = None
            
    return transpositions, fixed_indices

def generate_python_file(transpositions, fixed_indices, output_path):
    with open(output_path, 'w') as f:
        f.write("# Auto-generated icon transposition data\n")
        f.write("# Format: {char_id: {fashion_item_clean: {base_index: {'offset': (dR, dG, dB), 'icon_index': idx}}}}\n\n")
        
        f.write("ICON_TRANSPOSITIONS = {\n")
        for char_id in sorted(transpositions.keys()):
            f.write(f"    '{char_id}': {{\n")
            for item in sorted(transpositions[char_id].keys()):
                f.write(f"        '{item}': {{\n")
                for idx in sorted(transpositions[char_id][item].keys()):
                    data = transpositions[char_id][item][idx]
                    f.write(f"            {idx}: {data},\n")
                f.write("        },\n")
            f.write("    },\n")
        f.write("}\n\n")
        
        f.write("# Indices that should NOT be translated (keep original icon color)\n")
        # ... (rest unchanged)
        f.write("FIXED_ICON_INDICES = {\n")
        for char_id in sorted(fixed_indices.keys()):
            f.write(f"    '{char_id}': {{\n")
            for item in sorted(fixed_indices[char_id].keys()):
                indices = fixed_indices[char_id][item]
                f.write(f"        '{item}': {sorted(indices)},\n")
            f.write("    },\n")
        f.write("}\n")

if __name__ == "__main__":
    md_path = "palettes_dump_icon_with_base.md"
    py_path = "src/icon_transpositions.py"
    
    if os.path.exists(md_path):
        trans, fixed = parse_md_file(md_path)
        print(f"Found {len(trans)} characters.")
        for char in trans:
            print(f"  {char}: {len(trans[char])} items")
            
        generate_python_file(trans, fixed, py_path)
        print(f"Generated {py_path}")
    else:
        print(f"Error: {md_path} not found")
