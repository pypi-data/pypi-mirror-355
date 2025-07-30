import numpy as np
from line_solver import SchedStrategy

def pfqn_bs(L, N, Z=None, tol=1e-6, maxiter=1000, QN0=None, type=None):
    L = np.array(L, dtype=float)
    N = np.array(N, dtype=float)

    if Z is None:
        Z = np.zeros_like(N, dtype=float)
    else:
        Z = np.array(Z, dtype=float)

    M, R = L.shape
    CN = np.zeros((M, R))

    if QN0 is None:
        QN = np.tile(N / M, (M, 1))
    else:
        QN = np.array(QN0, dtype=float)

    if type is None:
        type = np.full((M,), SchedStrategy.PS)

    XN = np.zeros(R)
    UN = np.zeros((M, R))

    for it in range(1, maxiter + 1):
        QN_1 = QN.copy()
        for r in range(R):
            for ist in range(M):
                if L[ist, r] == 0:
                    CN[ist, r] = 0
                    continue

                cn = L[ist, r]
                for s in range(R):
                    if s != r:
                        if type[ist] == SchedStrategy.FCFS:
                            cn += L[ist, s] * QN[ist, s]
                        else:
                            cn += L[ist, r] * QN[ist, s]
                    else:
                        cn += L[ist, r] * QN[ist, r] * (N[r] - 1) / N[r]
                CN[ist, r] = cn

            XN[r] = N[r] / (Z[r] + np.sum(CN[:, r]))

        for r in range(R):
            for ist in range(M):
                QN[ist, r] = XN[r] * CN[ist, r]
                UN[ist, r] = XN[r] * L[ist, r]

        if np.max(np.abs(1 - QN / QN_1)) < tol:
            break

    RN = QN / XN
    return XN, QN, UN, RN, it
