import subprocess
import sys
import os

def run_and_inspect(command, env={}, cwd=None, shell=False):
    full_env = os.environ.copy()
    full_env.update(env)
    proc = subprocess.Popen(command, stdout=subprocess.PIPE, encoding='utf-8', env=full_env, cwd=cwd, shell=shell)
    header = '='*10 + " Running " + '='*10
    print(header)
    print(" ".join(command))
    print('='*len(header))
    while proc.poll() is None:
        sys.stdout.write(proc.stdout.readline())