from __future__ import division, print_function
import numpy
from foldedleastsquares import transitleastsquares

import unittest

class TestValidation(unittest.TestCase):
    def test(self):

        t = y = numpy.linspace(0, 1, 2000)

        try:
            model = transitleastsquares(t, y)
            results = model.power(use_threads=0)
        except:
            print("Test passed: use_threads=0")
        try:
            model = transitleastsquares(t, y)
            results = model.power(use_threads="1")
        except:
            print("Test passed: use_threads='1'")
