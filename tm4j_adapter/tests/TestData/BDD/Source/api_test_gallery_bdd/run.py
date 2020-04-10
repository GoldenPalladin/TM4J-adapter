from common_api_tests import run
import os
import sys

if __name__ == '__main__':
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    run.start()
