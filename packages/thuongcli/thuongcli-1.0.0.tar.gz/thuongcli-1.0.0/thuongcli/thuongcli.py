# 73e1cli/73e1cli.py

import argparse
import os

def clean_temp_files(temp_folder):
    if temp_folder and os.path.exists(temp_folder):
        for root, dirs, files in os.walk(temp_folder, topdown=False):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    os.remove(file_path)
                    print(f"Deleted file: {file_path}")
                except Exception as e:
                    print(f"Failed to delete file {file_path}: {e}")
            for dir in dirs:
                dir_path = os.path.join(root, dir)
                try:
                    # Only remove empty directories
                    os.rmdir(dir_path)
                    print(f"Deleted directory: {dir_path}")
                except Exception as e:
                    print(f"Failed to clean {temp_folder}: {e}")

def main():
    parser = argparse.ArgumentParser(prog="mycli")
    parser.add_argument("--name", "-n", help="Your name", default="Tran Dinh Thuong")
    parser.add_argument("--shutdown", "-s", action="store_true", help="Shutdown the computer")
    parser.add_argument("--restart", "-r", action="store_true", help="Restart the computer")
    parser.add_argument("--sleep", "-sl", action="store_true", help="Put the computer to sleep")
    parser.add_argument("--version", "-v", action="version", version="mycli 0.1.1", help="Show version information")
    parser.add_argument("--youtube", "-y", action="store_true", help="Open YouTube in the default web browser")
    parser.add_argument("--clean", "-c", action="store_true", help="Clean temporary files")
    parser.add_argument("--deepclean", "-dc", action="store_true", help="Xoa tat ca các tep va thu muc trong thu muc Downloads")
    args = parser.parse_args()
    print(f"Hello, {args.name}!")
    if args.shutdown:
        os.system("shutdown /s /t 0")
    elif args.restart:
        os.system("shutdown /r /t 0")
    elif args.sleep:
        os.system("rundll32.exe powrprof.dll,SetSuspendState 1,1,1")
    elif args.youtube:
        os.system("start https://www.youtube.com")
    elif args.clean:
        temp_folder = os.path.join(os.getenv('SystemRoot'), 'TEMP')
        print("-" * 50)
        print(f"Xac nhan xoa cac tep va thu muc tam thoi tai thu muc: {temp_folder}")
        print("Nhan y de xoa, nhan n de bo qua.")
        user_input = input("Ban co muon xoa khong? (y/n): ").lower()
        while user_input not in ['y', 'n']:
            user_input = input("Nhap y de xoa, nhap n de bo qua: ").lower()
        if user_input == 'y':
            clean_temp_files(temp_folder)
        else:
            print("Bo qua viec xoa tep tam thoi.")
        print("-" * 50)
        
        temp_folder = os.getenv("TEMP")
        print(f"Xac nhan xoa cac tep va thu muc tam thoi tai thu muc: {temp_folder}")
        print("Nhan y de xoa, nhan n de bo qua.")
        user_input = input("Ban co muon xoa khong? (y/n): ").lower()
        while user_input not in ['y', 'n']:
            user_input = input("Nhap y de xoa, nhap n de bo qua: ").lower()
        if user_input == 'y':
            clean_temp_files(temp_folder)
        else:
            print("Bo qua viec xoa tep tam thoi.")
        print("-" * 50)
        
        temp_folder = os.getenv("TMP")
        print(f"Xac nhan xoa cac tep va thu muc tam thoi tai thu muc: {temp_folder}")
        print("Nhan y de xoa, nhan n de bo qua.")
        user_input = input("Ban co muon xoa khong? (y/n): ").lower()
        while user_input not in ['y', 'n']:
            user_input = input("Nhap y de xoa, nhap n de bo qua: ").lower()
        if user_input == 'y':
            clean_temp_files(temp_folder)
        else:
            print("Bo qua viec xoa tep tam thoi.")
        print("-" * 50)
    elif args.deepclean:
        temp_folder = os.path.join(os.path.expanduser("~"), "Downloads")
        print("-" * 50)
        print(f"Xac nhan xoa cac tep va thu muc tam thoi tai thu muc: {temp_folder}")
        print("Nhan y de xoa, nhan n de bo qua.")
        user_input = input("Ban co muon xoa khong? (y/n): ").lower()
        while user_input not in ['y', 'n']:
            user_input = input("Nhap y de xoa, nhap n de bo qua: ").lower()
        if user_input == 'y':
            clean_temp_files(temp_folder)
        else:
            print("Bo qua viec xoa tep tam thoi.")
        print("-" * 50)

if __name__ == "__main__":
    main()