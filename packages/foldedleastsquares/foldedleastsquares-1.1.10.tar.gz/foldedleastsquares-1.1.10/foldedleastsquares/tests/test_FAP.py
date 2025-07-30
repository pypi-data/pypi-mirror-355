from __future__ import division, print_function

import numpy
from foldedleastsquares import FAP
import unittest

class TestFAP(unittest.TestCase):
    def test(self):
        print("Starting test FAP...", end="")
        numpy.testing.assert_equal(FAP(SDE=2), numpy.nan)
        numpy.testing.assert_equal(FAP(SDE=7), 0.009443778)
        numpy.testing.assert_equal(FAP(SDE=99), 8.0032e-05)
        print("passed")
