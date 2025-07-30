from __future__ import division, print_function

import os
import time

import numpy
import scipy
import scipy.signal
from foldedleastsquares import transitleastsquares, transit_mask, cleaned_array
import pkg_resources

import unittest

class TestMultiPlanet(unittest.TestCase):
    def loadfile(self, filename):
        filename = TestMultiPlanet.get_path(filename)
        try:
            data = numpy.genfromtxt(filename, delimiter=",", dtype="f8, f8, f8", names=["t", "y", "dy"])
            return data["t"], data["y"], data["dy"]
        except:
            data = numpy.genfromtxt(filename, delimiter=",", dtype="f8, f8", names=["t", "y"])
            return data["t"], data["y"], None

    @staticmethod
    def get_path(path):
        """
        Gets right path for tests environment
        :param path:
        :return: the real path of the test resource
        """
        return pkg_resources.resource_filename(__name__, path)

    def test_gpu(self):
        print("Starting test: Multi-planet...", end="")
        t, y, dy = self.loadfile("EPIC201367065.csv")
        trend = scipy.signal.medfilt(y, 25)
        y_filt = y / trend
        model = transitleastsquares(t, y_filt)
        total_gpu_time = time.time()
        results_gpu = model.power(use_gpu=True, show_progress_bar=False)
        total_gpu_time = time.time() - total_gpu_time
        total_gpu_approximate_time = time.time()
        results_gpu_approximate = model.power(use_gpu=True, gpu_approximate=True, show_progress_bar=False)
        total_gpu_approximate_time = time.time() - total_gpu_approximate_time
        #self.plot_results(results_gpu, t ,y)
        total_cpu_time = time.time()
        results_cpu = model.power(use_threads=os.cpu_count(), show_progress_bar=False)
        total_cpu_time = time.time() - total_cpu_time
        #self.plot_results(results_cpu, t, y)
        print("TIMES CPU: ", total_cpu_time)
        print("TIMES GPU: ", total_gpu_time)
        print("TIMES GPU APPROXIMATE: ", total_gpu_approximate_time)
        #self.assertLess(total_gpu_time, total_cpu_time)
        self.assertLess(total_gpu_approximate_time, total_cpu_time)
        self.assertAlmostEqual(results_gpu.period, results_cpu.period, 3)
        self.assertAlmostEqual(results_gpu_approximate.period, results_cpu.period, 3)
        numpy.testing.assert_almost_equal(max(results_cpu.power), 47.585106066175584, decimal=3)
        numpy.testing.assert_almost_equal(
            max(results_cpu.power_raw), 42.93056655774114, decimal=3
        )
        numpy.testing.assert_almost_equal(min(results_cpu.power), -0.6531152137309356, decimal=3)
        numpy.testing.assert_almost_equal(
            min(results_cpu.power_raw), -0.3043720539933344, decimal=3
        )
        print("Detrending of power spectrum from power_raw passed")

        # Mask of the first planet
        intransit = transit_mask(t, results_cpu.period, 2 * results_cpu.duration, results_cpu.T0)
        y_second_run = y_filt[~intransit]
        t_second_run = t[~intransit]
        t_second_run, y_second_run = cleaned_array(t_second_run, y_second_run)

        # Search for second planet
        model = transitleastsquares(t_second_run, y_second_run)
        total_gpu_time = time.time()
        results_gpu = model.power(use_gpu=True, show_progress_bar=False)
        total_gpu_time = time.time() - total_gpu_time
        total_gpu_approximate_time = time.time()
        results_gpu_approximate = model.power(use_gpu=True, gpu_approximate=True, show_progress_bar=False)
        total_gpu_approximate_time = time.time() - total_gpu_approximate_time
        #self.plot_results(results_gpu, t_second_run, y_second_run)
        total_cpu_time = time.time()
        results_cpu = model.power(use_threads=os.cpu_count(), show_progress_bar=False)
        total_cpu_time = time.time() - total_cpu_time
        #self.plot_results(results_cpu, t_second_run, y_second_run)
        print("TIMES CPU: ", total_cpu_time)
        print("TIMES GPU: ", total_gpu_time)
        print("TIMES GPU APPROXIMATE: ", total_gpu_approximate_time)
        self.assertLess(total_gpu_time, total_cpu_time)
        self.assertLess(total_gpu_approximate_time, total_cpu_time)
        self.assertAlmostEqual(results_gpu.period, results_cpu.period, 3)
        self.assertAlmostEqual(results_gpu_approximate.period, results_cpu.period, 3)
        numpy.testing.assert_almost_equal(
            results_cpu.duration, 0.14596011421893682, decimal=3
        )
        numpy.testing.assert_almost_equal(
            results_cpu.SDE, 35.031824450265, decimal=3
        )
        numpy.testing.assert_almost_equal(
            results_cpu.rp_rs, 0.025852178872027086, decimal=3
        )

        print("Passed")

    def plot_results(self, results, t, y):
        import matplotlib.pyplot as plt
        import scipy.stats as stats
        plt.plot(results.periods, results.chi2)
        plt.show()
        plt.plot(results.periods, results.chi2red)
        plt.show()
        plt.plot(results.periods, results.power_raw)
        plt.show()
        plt.plot(results.periods, results.power)
        plt.show()
        time_folded = (t - results.T0) / results.period - numpy.floor((t - results.T0) / results.period)
        duration = results.duration / results.period
        args = numpy.argsort(time_folded).flatten()
        time_folded = time_folded[args]
        flux_folded = y[args]
        span = duration * 4
        bin_means, bin_edges, binnumber = stats.binned_statistic(time_folded, flux_folded, statistic='mean', bins=200)
        bin_stds, _, _ = stats.binned_statistic(time_folded, flux_folded, statistic='std', bins=200)
        bin_width = (bin_edges[1] - bin_edges[0])
        bin_centers = bin_edges[1:] - bin_width / 2
        plt.scatter(time_folded, flux_folded)
        plt.scatter(bin_centers, bin_means)
        plt.xlim(0.5 - span, 0.5 + span)
        plt.hlines(1, 0, 0.5 - duration / 2, color="red")
        plt.hlines(results.depth, 0.5 - duration / 2, 0.5 + duration / 2, color="red")
        plt.hlines(1, 0.5 + duration / 2, 1, color="red")
        plt.show()
