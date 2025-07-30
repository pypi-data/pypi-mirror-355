import os
import subprocess
import sys

def main():
    # 找到 exe 的安裝路徑
    pkg_dir = os.path.dirname(__file__)
    exe_path = os.path.join(pkg_dir, '..', 'scripts', 'myprog.exe')
    # 使用 subprocess 啟動
    sys.exit(subprocess.call([exe_path] + sys.argv[1:]))
