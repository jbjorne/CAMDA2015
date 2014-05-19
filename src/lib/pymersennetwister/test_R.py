#!/usr/bin/env python
# Compare the output of this mersenne twister implementation against that of R
from __future__ import division
from __future__ import print_function

from mtwister import *

# pre-calculated R output for set.seed(1) and runif(1000) from R
from R_seed_and_randoms import seed, randoms     

def test_matches_R_mersenne():
    mt = MTwister()
    mt.set_seed_R(1) # Set the state from an int using the same technique as R
    mt.check_seed()

    assert all(x==y for x, y in zip(seed, mt.MT)), "MTwister set_seed_R(1) does not match R set.seed(1)"

    for ii, r in enumerate(randoms):
        mt_random = mt.random()
        assert abs(mt_random - r) < 1e-10, "%f != %f at position %i" % (mt_random, r, ii)

    # The first 10 numbers representing the state when set.seed(2) is called in R
    randoms_seed_R2 = [2675630718, 3580216551, 3529861116, 158863565, 3201097002, 242367651, 2603734408, 2756175337, 438890646, 4153820703]
    mt.set_seed_R(2)
    mt.check_seed()
    assert all(x==y for x,y in zip(mt.MT[:10], randoms_seed_R2))
