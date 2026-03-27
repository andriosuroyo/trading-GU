import os
import json
import argparse

def get_template(filepath):
    with open(filepath, 'r', encoding='utf-16le') as f:
        return f.read()

def write_setfile(filepath, content):
    # MT5 requires UTF-16LE with BOM (\xff\xfe)
    with open(filepath, 'wb') as f:
        f.write(b'\xff\xfe' + content.encode('utf-16le'))

def generate_sets(config_file):
    with open(config_file, 'r') as f:
        configs = json.load(f)
        
    setfiles_dir = r'c:\Trading_GU\Setfiles'
    gu_template_path = os.path.join(setfiles_dir, 'gu_template.set')
    sl_template_path = os.path.join(setfiles_dir, 'sl_template.set')
    
    if not os.path.exists(gu_template_path) or not os.path.exists(sl_template_path):
        print("Templates not found! Ensure gu_template.set and sl_template.set exist in Setfiles.")
        return
        
    base_gu = get_template(gu_template_path)
    base_sl = get_template(sl_template_path)
    
    for c in configs:
        name = c['name']
        print(f"Generating sets for {name}...")
        
        # Build GU File
        gu_content = base_gu
        if 'gu' in c:
            for key, val in c['gu'].items():
                # Replace the entire line containing the key
                # Assuming standard format: Key=Value
                if val is True: val = "true"
                elif val is False: val = "false"
                else: val = str(val)
                
                # We need to find the line starting with the key
                lines = gu_content.split('\n')
                for i, line in enumerate(lines):
                    if line.startswith(f"{key}="):
                        lines[i] = f"{key}={val}"
                        break
                gu_content = '\n'.join(lines)
                
        write_setfile(os.path.join(setfiles_dir, f"gu_{name}.set"), gu_content)
        
        # Build SL File
        sl_content = base_sl
        if 'sl' in c:
            for key, val in c['sl'].items():
                if val is True: val = "true"
                elif val is False: val = "false"
                else: val = str(val)
                
                lines = sl_content.split('\n')
                for i, line in enumerate(lines):
                    if line.startswith(f"{key}="):
                        lines[i] = f"{key}={val}"
                        break
                sl_content = '\n'.join(lines)
                
        write_setfile(os.path.join(setfiles_dir, f"sl_{name}.set"), sl_content)
        
    print(f"Successfully generated {len(configs)} configuration pairs.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Generate MT5 UTF-16LE Setfiles from JSON config.")
    parser.add_argument('config', help='Path to the JSON config file')
    args = parser.parse_args()
    generate_sets(args.config)
