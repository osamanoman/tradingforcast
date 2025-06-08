import os
import sys
import subprocess
import pathlib

REQUIREMENTS_FILE = 'requirements.txt'
OUTPUT_DIR = os.path.join('gflows-main', 'data', 'json')
API_KEY_ENV = 'POLYGON_API_KEY'


def check_python_version():
    if sys.version_info < (3, 7):
        print('Python 3.7 or higher is required.')
        sys.exit(1)

def install_requirements():
    print('Installing Python dependencies...')
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', REQUIREMENTS_FILE])
    except subprocess.CalledProcessError:
        print('Failed to install requirements. Please check your Python and pip installation.')
        sys.exit(1)

def ensure_output_dir():
    print(f'Ensuring output directory exists: {OUTPUT_DIR}')
    pathlib.Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

def check_env_vars():
    api_key = os.environ.get(API_KEY_ENV)
    if not api_key:
        print(f'WARNING: Environment variable {API_KEY_ENV} is not set.')
        print('The script will use the default API key in polygon_options.py unless you set this variable.')
    else:
        print(f'Environment variable {API_KEY_ENV} is set.')

def main():
    print('--- Project Setup: Start ---')
    check_python_version()
    install_requirements()
    ensure_output_dir()
    check_env_vars()
    print('\nSetup complete! You can now run your project scripts, e.g.:')
    print('    python scripts/polygon_options.py')
    print('--- Project Setup: Done ---')

if __name__ == '__main__':
    main() 