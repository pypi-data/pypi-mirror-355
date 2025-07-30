# dcrb/launcher.py
import os
import subprocess
import sys

def main():
    # 找到 exe 的安裝路徑
    pkg_dir = os.path.dirname(__file__)
    exe_path = os.path.join(pkg_dir, '..', 'scripts', 'dcrb.exe')
    # 呼叫 dcrb.exe，並把所有參數帶過去
    sys.exit(subprocess.call([exe_path] + sys.argv[1:]))
