"""Run helper for the Streamlit app.
- Tries to import streamlit; if missing, attempts to install dependencies from requirements.txt.
- Launches Streamlit via the current Python interpreter to avoid 'streamlit: command not found' PATH issues.
Usage:
    python run_app.py        # will try to install missing deps and start the app
    python run_app.py --no-install  # will not attempt installs, only try to run
"""
import subprocess
import sys
import importlib
import os

def ensure_streamlit(allow_install=True):
    try:
        import streamlit
        print('streamlit available:', streamlit.__version__)
        return True
    except Exception as e:
        print('streamlit not importable:', e)
        if not allow_install:
            print('\nTo install, run:')
            print(f'  {sys.executable} -m pip install -r requirements.txt')
            return False
        print('Attempting to install requirements from requirements.txt...')
        req = os.path.join(os.path.dirname(__file__), 'requirements.txt')
        if not os.path.exists(req):
            print('requirements.txt not found; cannot install automatically.')
            return False
        cmd = [sys.executable, '-m', 'pip', 'install', '-r', req]
        try:
            proc = subprocess.run(cmd, check=False)
            if proc.returncode != 0:
                print('pip install returned code', proc.returncode)
                return False
            # try import again
            try:
                importlib.invalidate_caches()
                import streamlit
                print('streamlit installed:', streamlit.__version__)
                return True
            except Exception as e2:
                print('Still cannot import streamlit after install:', e2)
                return False
        except Exception as ex:
            print('Failed to run pip install:', ex)
            return False

if __name__ == '__main__':
    allow_install = True
    if '--no-install' in sys.argv:
        allow_install = False
    ok = ensure_streamlit(allow_install=allow_install)
    if not ok:
        sys.exit(1)
    # Launch Streamlit using the current python executable to avoid shell PATH issues
    cmd = [sys.executable, '-m', 'streamlit', 'run', 'app.py']
    print('\nStarting Streamlit with:')
    print(' '.join(cmd))
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print('Streamlit run interrupted')
    except Exception as e:
        print('Failed to start Streamlit:', e)

