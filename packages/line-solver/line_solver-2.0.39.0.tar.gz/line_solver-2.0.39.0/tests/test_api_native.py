from line_solver.native import pfqn_aql, pfqn_ca, pfqn_mva, pfqn_bs
from numpy import *
import os
import sys
import unittest

# Ensure the line_solver package is accessible when running tests from the
# repository root.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class LineSolverTests(unittest.TestCase):

    def setUp(self):
        self.L = array([[10, 5], [5, 9]])
        self.N = array([100, 100])
        self.Z = array([91, 92])
        self.places = 4

    def test_pfqn_ca(self):
        [G, lG] = pfqn_ca(self.L, self.N, self.Z)
        self.assertAlmostEqual(lG, 549.1584415966641, places=self.places, msg='Failed unit test')

    def test_pfqn_aql(self):
        XN, QN, UN, RN, AN, numIters = pfqn_aql(self.L, self.N, self.Z)

        self.assertAlmostEqual(XN[0], 0.061597731494524, places=self.places, msg='Failed XN[0]')
        self.assertAlmostEqual(XN[1], 0.076795879677762, places=self.places, msg='Failed XN[1]')

        self.assertAlmostEqual(QN[0][0], 72.782660535149773, places=self.places, msg='Failed QN[0][0]')
        self.assertAlmostEqual(QN[0][1], 46.540350326698082, places=self.places, msg='Failed QN[0][1]')
        self.assertAlmostEqual(QN[1][0], 21.611947715909942, places=self.places, msg='Failed QN[1][0]')
        self.assertAlmostEqual(QN[1][1], 46.394426571188241, places=self.places, msg='Failed QN[1][1]')

        self.assertAlmostEqual(UN[0][0], 0.615977314945242, places=self.places, msg='Failed UN[0][0]')
        self.assertAlmostEqual(UN[0][1], 0.383979398388809, places=self.places, msg='Failed UN[0][1]')
        self.assertAlmostEqual(UN[1][0], 0.307988657472621, places=self.places, msg='Failed UN[1][0]')
        self.assertAlmostEqual(UN[1][1], 0.691162917099855, places=self.places, msg='Failed UN[1][1]')

        self.assertAlmostEqual(RN[0][0], 1181.580150814778, places=self.places, msg='Failed RN[0][0]')
        self.assertAlmostEqual(RN[0][1], 606.026623545149, places=self.places, msg='Failed RN[0][1]')
        self.assertAlmostEqual(RN[1][0], 350.856257860267, places=self.places, msg='Failed RN[1][0]')
        self.assertAlmostEqual(RN[1][1], 604.126570344987, places=self.places, msg='Failed RN[1][1]')

    def test_pfqn_mva(self):
        XN, QN, UN, RN, lGN = pfqn_mva(self.L, self.N, self.Z)

        self.assertAlmostEqual(XN[0], 0.061553999192827, places=self.places, msg='Failed XN[0]')
        self.assertAlmostEqual(XN[1], 0.076891999887990, places=self.places, msg='Failed XN[1]')

        self.assertAlmostEqual(QN[0][0], 72.876047419989234, places=self.places, msg='Failed QN[0][0]')
        self.assertAlmostEqual(QN[0][1], 46.750220410739203, places=self.places, msg='Failed QN[0][1]')
        self.assertAlmostEqual(QN[1][0], 21.522538653463496, places=self.places, msg='Failed QN[1][0]')
        self.assertAlmostEqual(QN[1][1], 46.175715599565720, places=self.places, msg='Failed QN[1][1]')

        self.assertAlmostEqual(UN[0][0], 0.615539991928272, places=self.places, msg='Failed UN[0][0]')
        self.assertAlmostEqual(UN[0][1], 0.384459999439950, places=self.places, msg='Failed UN[0][1]')
        self.assertAlmostEqual(UN[1][0], 0.307769995964136, places=self.places, msg='Failed UN[1][0]')
        self.assertAlmostEqual(UN[1][1], 0.692027998991910, places=self.places, msg='Failed UN[1][1]')

        self.assertAlmostEqual(RN[0][0], 1183.936842051384, places=self.places, msg='Failed RN[0][0]')
        self.assertAlmostEqual(RN[0][1], 607.998497617972, places=self.places, msg='Failed RN[0][1]')
        self.assertAlmostEqual(RN[1][0], 349.652970330017, places=self.places, msg='Failed RN[1][0]')
        self.assertAlmostEqual(RN[1][1], 600.526916543083, places=self.places, msg='Failed RN[1][1]')

    def test_pfqn_bs(self):
        XN, QN, UN, RN, it = pfqn_bs(self.L, self.N, self.Z)

        self.assertAlmostEqual(XN[0], 0.061736748903409, places=self.places, msg='Failed XN[0]')
        self.assertAlmostEqual(XN[1], 0.075876378039523, places=self.places, msg='Failed XN[1]')

        self.assertAlmostEqual(QN[0][0], 72.416372121381727, places=self.places, msg='Failed QN[0][0]')
        self.assertAlmostEqual(QN[0][1], 44.606488689804834, places=self.places, msg='Failed QN[0][1]')
        self.assertAlmostEqual(QN[1][0], 21.965583728408010, places=self.places, msg='Failed QN[1][0]')
        self.assertAlmostEqual(QN[1][1], 48.412884530559083, places=self.places, msg='Failed QN[1][1]')

        self.assertAlmostEqual(UN[0][0], 0.617367489034095, places=self.places, msg='Failed UN[0][0]')
        self.assertAlmostEqual(UN[0][1], 0.379381890197614, places=self.places, msg='Failed UN[0][1]')
        self.assertAlmostEqual(UN[1][0], 0.308683744517047, places=self.places, msg='Failed UN[1][0]')
        self.assertAlmostEqual(UN[1][1], 0.682887402355705, places=self.places, msg='Failed UN[1][1]')

        self.assertAlmostEqual(RN[0][0], 1172.986485483405, places=self.places, msg='Failed RN[0][0]')
        self.assertAlmostEqual(RN[0][1], 587.883737235982, places=self.places, msg='Failed RN[0][1]')
        self.assertAlmostEqual(RN[1][0], 355.794305961501, places=self.places, msg='Failed RN[1][0]')
        self.assertAlmostEqual(RN[1][1], 638.049492891471, places=self.places, msg='Failed RN[1][1]')

if __name__ == '__main__':
    unittest.main()
