from pathlib import Path

def find_files(directory):
    return Path(directory).rglob('*.template')

directory = '/Users/sameer.wadkar/Documents/GitHub/model-export-process/templates/'  # Replace with your directory path
for file_path in find_files(directory):
    fp = str(file_path)
    print(fp.removeprefix(directory))