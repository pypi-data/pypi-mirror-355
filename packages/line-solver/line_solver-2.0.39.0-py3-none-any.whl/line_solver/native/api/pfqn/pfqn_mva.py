import numpy as np

def pfqn_mva(L, N, Z=None, mi=None):
    L = np.array(L, dtype=float)
    N = np.ceil(N).astype(int)
    M, R = L.shape

    if Z is None:
        Z = np.zeros(R)
    else:
        Z = np.array(Z, dtype=float)

    if mi is None:
        mi = np.ones(M)
    else:
        mi = np.array(mi, dtype=float)

    if np.all(N == 0):
        return [], [], [], [], 0

    if len(N) != R:
        raise ValueError("Demand matrix and population vector must have the same number of classes.")

    XN = np.zeros(R)
    QN = np.zeros((M, R))
    CN = np.zeros((M, R))
    UN = np.zeros((M, R))
    lGN = 0

    prods = np.ones(R - 1, dtype=int)
    for w in range(R - 1):
        prods[w] = np.prod(N[w + 1:] + 1)

    firstnonempty = R - 1
    while firstnonempty > 0 and N[firstnonempty] == 0:
        firstnonempty -= 1

    totpop = np.prod(N + 1)
    Q = np.zeros((totpop, M))
    currentpop = 1

    n = np.zeros(R, dtype=int)
    n[firstnonempty] = 1
    ctr = totpop

    while ctr:
        for s in range(R):
            if n[s] > 0:
                n[s] -= 1
                pos_n_1s = n[-1]
                for w in range(R - 1):
                    pos_n_1s += n[w] * prods[w]
                n[s] += 1

                CNtot = 0.0
                for i in range(M):
                    Lis = L[i, s]
                    CN[i, s] = Lis * (mi[i] + Q[pos_n_1s, i])
                    CNtot += CN[i, s]

                XN[s] = n[s] / (Z[s] + CNtot)

                for i in range(M):
                    QN[i, s] = XN[s] * CN[i, s]
                    Q[currentpop, i] += QN[i, s]

        # Update lGN (log normalizing constant)
        last_nnz = np.max(np.nonzero(n)[0]) if np.any(n > 0) else -1
        if last_nnz >= 1 and np.sum(n[:last_nnz]) == np.sum(N[:last_nnz]) and np.sum(n[last_nnz + 1:]) == 0:
            lGN -= np.log(XN[last_nnz])

        # Update population vector n
        s = R - 1
        while s >= 0 and (n[s] == N[s] or s > firstnonempty):
            s -= 1
        if s < 0:
            break
        n[s] += 1
        for j in range(s + 1, R):
            n[j] = 0

        ctr -= 1
        currentpop += 1

    for m in range(M):
        for r in range(R):
            UN[m, r] = XN[r] * L[m, r]

    return XN, QN, UN, CN, lGN
