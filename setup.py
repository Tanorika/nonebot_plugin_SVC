import os
import sys
import re
from pathlib import Path
import winreg
'''Old function
def detect_python_path():
    path_list = os.environ['Path'].split(';')
    python_path = None
    python_version = None
    python_pattern = re.compile(r'python (3[.][0-9]+([.][0-9]+)?)?')

    for path in path_list:
        if 'python' in path.lower():
            python_exec = Path(path) / 'python.exe'
            if python_exec.exists():
                version_string = os.popen(f'"{python_exec}" --version').read().strip()
                match = python_pattern.search(version_string.lower())
                if match:
                    python_path = path
                    python_version = match.group(1)
                    break
    print(version_string)
    return python_path, python_version

def modify_pyvenv_cfg(python_path, python_version):
    pyvenv_path = Path('.\\venv\\pyvenv.cfg')

    if not pyvenv_path.exists():
        print("Error: pyvenv.cfg not found.")
        sys.exit(1)

    with pyvenv_path.open('r') as f:
        content = f.readlines()

    if len(content) != 1:
        print("Venv already created.")
        sys.exit(1)

    with pyvenv_path.open('w') as f:
        f.write(f"home = {python_path}\n")
        f.writelines(content)
        f.write(f"version = {python_version}\n")


def create_venv(python_path, python_version):
    pyvenv_path = Path('.\\venv\\pyvenv.cfg')
    venv_path = Path('.\\venv')
    venv_abs_path = os.path.abspath(venv_path)

    if not pyvenv_path.exists():
        print("Error: pyvenv.cfg not found.")
        sys.exit(1)

    with pyvenv_path.open('r') as f:
        content = f.readlines()

    home_line = None
    version_line = None

    for i, line in enumerate(content):
        if line.startswith("home ="):
            home_line = i
        if line.startswith("version ="):
            version_line = i

    with pyvenv_path.open('w') as f:
        if home_line is not None and version_line is not None:
            for i, line in enumerate(content):
                if i == home_line:
                    f.write(f"home = {python_path}\n")
                elif i == version_line:
                    f.write(f"version = {python_version}\n")
                else:
                    f.write(line)
        else:
            f.write(f"home = {python_path}\n")
            f.writelines(content)
            f.write(f"version = {python_version}\n")
    
    with open(".\\venv\\Scripts\\activate", "r") as file:
        content = file.readlines()

    with open(".\\venv\\Scripts\\activate", "w") as file:
        for line in content:
            if line.startswith("VIRTUAL_ENV="):
                line = f"VIRTUAL_ENV=\"{venv_abs_path}\"\n"
            file.write(line)
'''
def check_ffmpeg_path():
    path_list = os.environ['Path'].split(';')
    ffmpeg_found = False

    for path in path_list:
        if 'ffmpeg' in path.lower() and 'bin' in path.lower():
            ffmpeg_found = True
            print("FFmpeg already installed, skipping...")
            break

    return ffmpeg_found

def add_ffmpeg_path_to_user_variable():
    ffmpeg_bin_path = Path('.\\ffmpeg\\bin')
    if ffmpeg_bin_path.is_dir():
        abs_path = str(ffmpeg_bin_path.resolve())
        
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Environment",
                0,
                winreg.KEY_READ | winreg.KEY_WRITE
            )
            
            try:
                current_path, _ = winreg.QueryValueEx(key, "Path")
                if abs_path not in current_path:
                    new_path = f"{current_path};{abs_path}"
                    winreg.SetValueEx(key, "Path", 0, winreg.REG_EXPAND_SZ, new_path)
                    print(f"Added FFmpeg path to user variable 'Path': {abs_path}")
                else:
                    print("FFmpeg path already exists in the user variable 'Path'.")
            finally:
                winreg.CloseKey(key)
        except WindowsError:
            print("Error: Unable to modify user variable 'Path'.")
            sys.exit(1)

    else:
        print("Error: ffmpeg\\bin folder not found in the current path.")
        sys.exit(1)

def main():
    current_workdir_name = os.path.basename(os.getcwd())
    if current_workdir_name != "so-vits-svc":
        print("请将整合包文件夹名称修改为so-vits-svc,否则可能会导致运行出错")
        sys.exit(1)
    else:
        if not check_ffmpeg_path():
            add_ffmpeg_path_to_user_variable()
            
if __name__ == "__main__":
    main()