from __future__ import division, print_function

import unittest

import numpy
import scipy.signal
from foldedleastsquares import transitleastsquares
from foldedleastsquares.template_generator.default_transit_template_generator import DefaultTransitTemplateGenerator
import pkg_resources


class TestTransitTemplateGenerator(DefaultTransitTemplateGenerator):
    def __init__(self):
        super().__init__()

class TestShapes(unittest.TestCase):
    def loadfile(self, filename):
        filename = TestShapes.get_path(filename)
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
        print("Starting test: transit shapes...", end="")

        # Testing transit shapes
        t, y = self.loadfile("EPIC206154641.csv")
        trend = scipy.signal.medfilt(y, 25)
        y_filt = y / trend

        # box
        model_box = transitleastsquares(t, y_filt)
        results_box = model_box.power(transit_template="box", period_grid=numpy.arange(1, 5, 0.01))
        numpy.testing.assert_equal(len(model_box.period_grid), 400)

        results_box = model_box.power(transit_template="box")
        numpy.testing.assert_almost_equal(
            results_box.duration, 0.06207881501022775, decimal=5)
        numpy.testing.assert_almost_equal(results_box.rp_rs, 0.08836981203437415, decimal=5)
        print("Test passed: Box-shaped")

        # grazing
        model_grazing = transitleastsquares(t, y_filt)
        results_grazing = model_grazing.power(transit_template="grazing")

        numpy.testing.assert_almost_equal(
            results_grazing.duration, 0.09079026695245815, decimal=5
        )
        numpy.testing.assert_almost_equal(
            min(results_grazing.chi2red), 0.06759475703796078, decimal=5)
        print("Test passed: Grazing-shaped")

        # comet
        model_comet = transitleastsquares(t, y_filt)
        results_comet = model_comet.power(transit_template="tailed")
        numpy.testing.assert_almost_equal(
            results_comet.duration, 0.23745146741412124, decimal=5
        )
        numpy.testing.assert_almost_equal(
            min(results_comet.chi2red), 0.0980794344892094, decimal=5)
        print("Test passed: Comet-shaped")

        model_custom = transitleastsquares(t, y_filt)
        try:
            results_custom = model_custom.power(transit_template="custom",
                                                transit_template_generator="wrongTransitTemplateGenerator")
            assert False
        except ValueError as e:
            if e.args[0] == "The custom transit_template_generator does not implement TransitTemplateGenerator.":
                print("Test passed: Wrong custom transit template generator.")
            else:
                assert False

        # custom
        model_custom = transitleastsquares(t, y_filt)
        results_custom = model_custom.power(transit_template="custom",
                                            transit_template_generator=TestTransitTemplateGenerator())
        numpy.testing.assert_almost_equal(
            results_custom.duration, 0.06828669651125058, decimal=5
        )
        numpy.testing.assert_almost_equal(
            min(results_custom.chi2red), 0.09977336183179186, decimal=5)
        print("Test passed: Custom-shaped")

        print("All tests passed")
