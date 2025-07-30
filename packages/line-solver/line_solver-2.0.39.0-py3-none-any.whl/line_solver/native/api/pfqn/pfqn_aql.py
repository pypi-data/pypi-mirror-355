import numpy as np
from line_solver.native.util import *

import numpy as np

def oner(N, r):
    N = N.copy()
    r = np.atleast_1d(r)
    for s in r:
        if s > 0 and s <= len(N):  # MATLAB-style 1-based indexing
            N[s - 1] -= 1
    return N

def pfqn_aql(L, N, Z=None, TOL=1e-7, MAXITER=1000, QN0=None):
    L = np.array(L, dtype=float)
    N = np.array(N, dtype=float)
    M, K = L.shape

    if Z is None:
        Z = np.zeros(K)
    else:
        Z = np.array(Z, dtype=float)

    if QN0 is None:
        QN0 = np.tile(N, (M, 1)) / M
    else:
        QN0 = np.array(QN0, dtype=float) + np.finfo(float).eps

    Q = [None] * (K + 1)
    R = [None] * (K + 1)
    X = [None] * (K + 1)
    gamma = np.zeros((M, K))

    for t in range(K + 1):  # t = 0:K in MATLAB
        n = oner(N, t)
        Q[t] = np.zeros(M)
        for k in range(M):
            if t == 0:
                Q[t][k] = QN0[k].sum()
            else:
                Q[t][k] = QN0[k, t - 1]

    it = 0
    while True:
        Q_olditer = [q.copy() if q is not None else None for q in Q]
        it += 1

        for t in range(K + 1):
            n = oner(N, t)
            R[t] = np.zeros((M, K))
            for k in range(M):
                for s in range(K):
                    denom = sum(n) if sum(n) != 0 else 1
                    R[t][k, s] = L[k, s] * (1 + (sum(n) - 1) * (Q[t][k] / denom - gamma[k, s]))

            X[t] = np.zeros(K)
            for s in range(K):
                X[t][s] = n[s] / (Z[s] + sum(R[t][:, s]))

            for k in range(M):
                Q[t][k] = np.dot(X[t], R[t][k, :])

        for k in range(M):
            for s in range(K):
                gamma[k, s] = (Q[0][k] / sum(N)) - (Q[s + 1][k] / (sum(N) - 1))

        if np.max(np.abs((Q_olditer[0] - Q[0]) / Q[0])) < TOL or it == MAXITER:
            numIters = it
            break

    XN = X[0]
    RN = R[0]
    UN = np.zeros((M, K))
    QN = np.zeros((M, K))
    AN = np.zeros((M, K))

    for k in range(M):
        for s in range(K):
            UN[k, s] = XN[s] * L[k, s]
            QN[k, s] = UN[k, s] * (1 + Q[s + 1][k])
            AN[k, s] = Q[s + 1][k]

    return XN, QN, UN, RN, AN, numIters
