import os

def extract_py_files_to_single_file(root_dir, output_file):
    with open(output_file, 'w', encoding='utf-8') as out_f:
        for subdir, _, files in os.walk(root_dir):
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(subdir, file)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()
                        out_f.write(f"{filepath}\n")
                        out_f.write(content)
                        out_f.write("\n\n------\n\n")
                    except Exception as e:
                        print(f"Error reading {filepath}: {e}")

# Example usage
extract_py_files_to_single_file('./flotorch_eval', 'output.txt')
