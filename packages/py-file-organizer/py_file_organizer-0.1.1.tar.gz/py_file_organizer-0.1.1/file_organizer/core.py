import os
import shutil

def organize_files(directory_path):
    # Define your directory structure
    folder_structure = {
        "Documents": [".pdf", ".doc", ".docx", ".txt"],
        "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"],
        "Music": [".mp3", ".wav", ".aac"],
        "Videos": [".mp4", ".mkv", ".mov", ".avi"],
        "Archives": [".zip", ".tar", ".rar", ".gz"],
        "Code": [".py", ".js", ".html", ".css", ".java", ".cpp", ".rb", ".json"],
        "Spreadsheets": [".xls", ".xlsx", ".csv"],
        # Add more categories as needed
    }

    # Build extension-to-folder mapping
    ext_to_folder = {ext: folder for folder, exts in folder_structure.items() for ext in exts}

    # Pre-create all target folders
    for folder in folder_structure:
        os.makedirs(os.path.join(directory_path, folder), exist_ok=True)

    # Move files into their respective folders
    for item in os.listdir(directory_path):
        item_path = os.path.join(directory_path, item)
        if os.path.isfile(item_path):
            _, file_extension = os.path.splitext(item)
            folder = ext_to_folder.get(file_extension.lower())
            if folder:
                dest_path = os.path.join(directory_path, folder, item)
                # Avoid overwriting files with the same name
                if not os.path.exists(dest_path):
                    shutil.move(item_path, dest_path)
                else:
                    base, ext = os.path.splitext(item)
                    i = 1
                    while True:
                        new_name = f"{base}_{i}{ext}"
                        new_dest = os.path.join(directory_path, folder, new_name)
                        if not os.path.exists(new_dest):
                            shutil.move(item_path, new_dest)
                            break
                        i += 1 
