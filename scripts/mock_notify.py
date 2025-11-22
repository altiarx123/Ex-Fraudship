import sys
import os
# make sure parent dir (project root) is on sys.path so we can import app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import send_notification


def run():
    print('Sending mock log notification...')
    r = send_notification('Log', '+10000000000', 'Test fraud alert message')
    print('Result:', r)


if __name__ == '__main__':
    run()
