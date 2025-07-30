# dcrb/launcher.py
import os
import subprocess
import sys

def main():
    # __file__ 就在 dcrb/launcher.py，exe 就在同個資料夾
    pkg_dir = os.path.dirname(__file__)
    exe_path = os.path.join(pkg_dir, 'dcrb.exe')
    # 如果找不到，就跳錯誤
    if not os.path.isfile(exe_path):
        print(f"Error: 找不到 {exe_path}", file=sys.stderr)
        sys.exit(1)
    # 呼叫 dcrb.exe
    sys.exit(subprocess.call([exe_path] + sys.argv[1:]))
