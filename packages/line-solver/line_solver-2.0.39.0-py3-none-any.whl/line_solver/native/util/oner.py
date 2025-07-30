import numpy as np

def oner(N = None,r = None):
    # N=ONER(N,r)
    # Decrement element in position of r of input vector

    # Copyright (c) 2012-2022, Imperial College London
    # All rights reserved.
    N = N.copy()
    r = np.atleast_1d(r)
    for s in r:
        if 0 < s < len(N):  # Match MATLAB's 1-based indexing, skip s=0, avoid out-of-bounds
            N[s] -= 1
    return N
