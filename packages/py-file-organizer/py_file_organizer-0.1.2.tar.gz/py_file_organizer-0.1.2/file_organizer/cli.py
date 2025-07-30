import os
from file_organizer import organize_files

def main():
    while True:
        directory = input("Enter the full path to the directory you want to organize (or 'q' to quit): ").strip()
        if directory.lower() == 'q':
            print("Exiting program.")
            break
        if not os.path.isdir(directory):
            print("Invalid directory. Please try again.")
            continue
        organize_files(directory)
        print(f"Files in {directory} have been organized successfully.")
        break

if __name__ == "__main__":
    main() 
