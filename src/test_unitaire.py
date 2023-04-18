# -*- coding: utf-8 -*-
import numpy as np
import unittest
from hmm import viterbi 

observable_states= ['O1', 'O2', 'O3', 'O4']
hidden_states = ['R', 'DR', 'D', 'DG', 'G']
pi = [0.2, 0.2, 0.2, 0.2, 0.2] 

class TestViterbi(unittest.TestCase):

    ##############################
    # Test unitaire de Viterbi 1 #
    ##############################

    def test_viterbi(self):
        t=np.identity(5)

        e= np.array([[0.600, 0.175, 0.175, 0.050],
                 [0.050, 0.600, 0.175, 0.175],
                 [0.050, 0.175, 0.600, 0.175], 
                 [0.050, 0.175, 0.175, 0.600], 
                 [0.600, 0.050, 0.175, 0.175]])


        obs = np.array([0,0,1,0,0,3])
        result = np.array([0,0,0,0,0,0])

        np.testing.assert_array_equal(result, viterbi(pi, t, e, obs)[0])


    ##############################
    # Test unitaire de Viterbi 2 #
    ##############################


    def test_viterbi2(self):
        t2 = np.array([[0.250, 0.500, 0.025, 0.200, 0.025],
                       [0.250, 0.150, 0.075, 0.500, 0.025], 
                       [0.050, 0.025, 0.050, 0.850, 0.025], 
                       [0.025, 0.075, 0.150, 0.125, 0.625], 
                       [0.050, 0.075, 0.475, 0.025, 0.375]])



        e2=np.array([[0.25, 0.25, 0.25, 0], 
                     [0.25, 0.25, 0.25, 0], 
                     [0.25, 0.25, 0.25, 0], 
                     [0.25, 0.25, 0.25, 0], 
                     [0, 0, 0, 1]])

        obs2 = np.array([3,3,3,3,3,3])

        result2 = np.array([4,4,4,4,4,4])
        np.testing.assert_array_equal(result2, viterbi(pi, t2, e2, obs2)[0])


if __name__ == '__main__':
    unittest.main()
