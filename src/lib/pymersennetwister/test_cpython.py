#!/usr/bin/env python
from __future__ import division
from __future__ import print_function

import random
from mtwister import MTwister

def test_matches_cpython():
    # Set the python PRNG to a specific state
    random.seed(1)

    # Get the state of the python PRNG
    state = list(random.getstate()[1][:624])

    # Initialise MTwister with the same state
    mt = MTwister()
    mt.MT = state

    # Generated RNGs should be in exact agreement 
    N = 1000000
    for i in range(N):
        mtwister = mt.random_cpython()
        cpython  = random.random()
        assert mtwister == cpython,  "%i failed: %f != %f" % (i, mtwister, cpython)

    print("OK. MTwister and CPython.", N, "random numbers agree.")

