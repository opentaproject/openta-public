import subprocess
import sys

def run_and_inspect(command):
    proc = subprocess.Popen(command, stdout=subprocess.PIPE, encoding='utf-8')
    header = '='*10 + " Running " + '='*10
    print(header)
    print(" ".join(command))
    print('='*len(header))
    while proc.poll() is None:
        sys.stdout.write(proc.stdout.readline())