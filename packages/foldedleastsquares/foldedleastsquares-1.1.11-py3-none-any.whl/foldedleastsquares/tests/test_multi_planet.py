from __future__ import division, print_function
import numpy
import scipy
import scipy.signal
from foldedleastsquares import transitleastsquares, transit_mask, cleaned_array
import pkg_resources

import unittest

class TestMultiPlanet(unittest.TestCase):
    def loadfile(self, filename):
        filename = TestMultiPlanet.get_path(filename)
        data = numpy.genfromtxt(filename, delimiter=",", dtype="f8, f8", names=["t", "y"])
        return data["t"], data["y"]

    @staticmethod
    def get_path(path):
        """
        Gets right path for tests environment
        :param path:
        :return: the real path of the test resource
        """
        return pkg_resources.resource_filename(__name__, path)

    def test(self):
        print("Starting test: Multi-planet...", end="")
        t, y = self.loadfile("EPIC201367065.csv")
        trend = scipy.signal.medfilt(y, 25)
        y_filt = y / trend

        model = transitleastsquares(t, y_filt)
        results = model.power()

        numpy.testing.assert_almost_equal(max(results.power), 44.990958555357125, decimal=3)
        numpy.testing.assert_almost_equal(
            max(results.power_raw), 42.93056655774114, decimal=3
        )
        numpy.testing.assert_almost_equal(min(results.power), -0.6175100139942419, decimal=3)
        numpy.testing.assert_almost_equal(
            min(results.power_raw), -0.3043720539933344, decimal=3
        )
        print("Detrending of power spectrum from power_raw passed")

        # Mask of the first planet
        intransit = transit_mask(t, results.period, 2 * results.duration, results.T0)
        y_second_run = y_filt[~intransit]
        t_second_run = t[~intransit]
        t_second_run, y_second_run = cleaned_array(t_second_run, y_second_run)

        # Search for second planet
        model_second_run = transitleastsquares(t_second_run, y_second_run)
        results_second_run = model_second_run.power()
        numpy.testing.assert_almost_equal(
            results_second_run.duration, 0.14596011421893682, decimal=3
        )
        numpy.testing.assert_almost_equal(
            results_second_run.SDE, 34.99113045986177, decimal=3
        )
        numpy.testing.assert_almost_equal(
            results_second_run.rp_rs, 0.025852178872027086, decimal=3
        )

        print("Passed")
