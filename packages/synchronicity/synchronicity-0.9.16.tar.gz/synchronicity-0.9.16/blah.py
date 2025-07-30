import gc

import time

from synchronicity import Synchronizer

def foo():
    Synchronizer()

foo()
time.sleep(0.1)