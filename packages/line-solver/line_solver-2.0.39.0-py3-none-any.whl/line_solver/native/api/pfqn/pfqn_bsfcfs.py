import numpy as np

def pfqn_bsfcfs(L, N, Z=None, tol=1e-6, maxiter=1000, QN=None, weight=None):
    L = np.array(L, dtype=float)
    N = np.array(N, dtype=float)

    if Z is None:
        Z = np.zeros_like(N, dtype=float)
    else:
        Z = np.array(Z, dtype=float)

    M, R = L.shape
    CN = np.zeros((M, R))

    if QN is None:
        QN = np.tile(N / M, (M, 1))
    else:
        QN = np.array(QN, dtype=float) + np.finfo(float).eps

    if weight is None:
        weight = np.ones((M, R), dtype=float)

    XN = np.zeros(R)
    UN = np.zeros((M, R))
    relprio = np.zeros((M, R))

    for it in range(1, maxiter + 1):
        QN_1 = QN.copy()
        relprio = QN * weight

        for r in range(R):
            for ist in range(M):
                CN[ist, r] = L[ist, r]
                for s in range(R):
                    if relprio[ist, r] == 0:
                        continue  # avoid division by zero
                    if s != r:
                        CN[ist, r] += L[ist, s] * QN[ist, s] * relprio[ist, s] / relprio[ist, r]
                    else:
                        CN[ist, r] += (
                            L[ist, r] * QN[ist, r] * (N[r] - 1) / N[r] * relprio[ist, s] / relprio[ist, r]
                        )

            XN[r] = N[r] / (Z[r] + np.sum(CN[:, r]))

        for r in range(R):
            for ist in range(M):
                QN[ist, r] = XN[r] * CN[ist, r]
                UN[ist, r] = XN[r] * L[ist, r]

        if np.max(np.abs(1 - QN / QN_1)) < tol:
            break

    RN = QN / XN
    return XN, QN, UN, RN, it
