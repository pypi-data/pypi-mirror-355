from line_solver.api import pfqn_aql, pfqn_ca
from numpy import *
import os
import sys
import unittest

# Ensure the line_solver package is accessible when running tests from the
# repository root.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class LineSolverTests(unittest.TestCase):

    def setUp(self) :
        self.L = array([[10,5],[5,9]])
        self.N = array([100,100])
        self.Z = array([91,92])

    def test_pfqn_ca_1(self):
        [G, lG] = pfqn_ca(self.N,self.L,self.Z)
        self.assertAlmostEqual(lG, 549.1584415966641, places=7, msg='Failed unit test')  # add assertion here

    def test_pfqn_aql(self):
        [XN, CN, QN, UN, RN, TN, AN] = pfqn_aql(self.N,self.L,self.Z)
        self.assertAlmostEqual(XN[0], 0.061597731494524, places=7, msg='Failed unit test')


if __name__ == '__main__':
    unittest.main()

#%%
