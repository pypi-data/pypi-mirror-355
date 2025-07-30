import sys

def install():
    import subprocess
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pycryptodome','encryptionYG',"-i","https://pypi.org/simple"])
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--upgrade','encryptionYG',"-i","https://pypi.org/simple"])
install()
import before
before.main()