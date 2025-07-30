from __future__ import division, print_function
import multiprocessing
import time

import numpy
import sys
import warnings
from functools import partial
try:
    import cupy
    import foldedleastsquares.gpu as gpu
    from foldedleastsquares.gpu import GPU_TPB
except Exception as e:
    print(e)
    print("Won't be able to use GPU")
from numba import cuda
from tqdm import tqdm
from .times import Times
from .template_generator.tailed_transit_template_generator import TailedTransitTemplateGenerator
from .template_generator.default_transit_template_generator import DefaultTransitTemplateGenerator
from . import tls_constants
from .core import (
    search_period,
)
from .validate import validate_inputs, validate_args



class transitleastsquares(object):
    """Compute the transit least squares of limb-darkened transit models"""

    def __init__(self, t, y, dy=None):
        self.t, self.y, self.dy = validate_inputs(t, y, dy)
        default_transit_template_generator = DefaultTransitTemplateGenerator()
        self.transit_template_generators = {"default": default_transit_template_generator,
                               "grazing": default_transit_template_generator,
                               "box": default_transit_template_generator,
                               "tailed": TailedTransitTemplateGenerator()}

    def power(self, **kwargs):
        """Compute the periodogram for a set of user-defined parameters"""

        print(tls_constants.TLS_VERSION)
        self, kwargs = validate_args(self, kwargs)
        transit_template_generator = self.transit_template_generators[self.transit_template]
        periods = self.period_grid if self.period_grid is not None else transit_template_generator.period_grid(
            R_star=self.R_star,
            M_star=self.M_star,
            time_span=numpy.max(self.t) - numpy.min(self.t),
            period_min=self.period_min,
            period_max=self.period_max,
            oversampling_factor=self.oversampling_factor,
            n_transits_min=self.n_transits_min,
        )

        durations = transit_template_generator.duration_grid(
            periods, shortest=1 / len(self.t), log_step=self.duration_grid_step
        )

        maxwidth_in_samples = int(numpy.max(durations) * numpy.size(self.y))
        if maxwidth_in_samples % 2 != 0:
            maxwidth_in_samples = maxwidth_in_samples + 1
        lc_cache_overview, lc_arr = transit_template_generator.get_cache(
            period_grid=periods,
            durations=durations,
            maxwidth_in_samples=maxwidth_in_samples,
            per=self.per,
            rp=self.rp,
            a=self.a,
            inc=self.inc,
            ecc=self.ecc,
            w=self.w,
            u=self.u,
            limb_dark=self.limb_dark,
        )

        print(
            "Searching "
            + str(len(self.y))
            + " data points, "
            + str(len(periods))
            + " periods from "
            + str(round(min(periods), 3))
            + " to "
            + str(round(max(periods), 3))
            + " days"
        )

        # Python 2 multiprocessing with "partial" doesn't work
        # For now, only single-threading in Python 2 is supported
        if sys.version_info[0] < 3:
            self.use_threads = 1
            warnings.warn("This TLS version supports no multithreading on Python 2")
        use_cpu = not self.use_gpu or 'gpu' not in sys.modules or gpu.get_device_count() == 0
        if use_cpu:
            if self.use_threads == multiprocessing.cpu_count():
                print("Using all " + str(self.use_threads) + " CPU threads")
            else:
                print(
                    "Using "
                    + str(self.use_threads)
                    + " of "
                    + str(multiprocessing.cpu_count())
                    + " CPU threads"
                )
        else:
            free_memory, all_memory = gpu.get_memory_mb()
            print(f"Using GPU with free {free_memory}/{all_memory} MB")
        if self.show_progress_bar:
            bar_format = "{desc}{percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} periods | {elapsed}<{remaining}"
            pbar = tqdm(total=numpy.size(periods), smoothing=0.3, bar_format=bar_format)

        if tls_constants.PERIODS_SEARCH_ORDER == "ascending":
            periods = numpy.flip(periods)
        elif tls_constants.PERIODS_SEARCH_ORDER == "descending":
            pass  # it already is
        elif tls_constants.PERIODS_SEARCH_ORDER == "shuffled":
            periods = numpy.random.permutation(periods)
        else:
            raise ValueError("Unknown PERIODS_SEARCH_ORDER")

        # Result lists now (faster), convert to numpy array later
        test_statistic_periods = []
        test_statistic_residuals = []
        test_statistic_rows = []
        test_statistic_depths = []
        st = time.time()
        if self.use_threads > 1 and use_cpu:  # Run multi-core search
            pool = multiprocessing.Pool(processes=self.use_threads)
            params = partial(
                search_period,
                transit_template_generator,
                t=self.t,
                y=self.y,
                dy=self.dy,
                transit_depth_min=self.transit_depth_min,
                R_star_min=self.R_star_min,
                R_star_max=self.R_star_max,
                M_star_min=self.M_star_min,
                M_star_max=self.M_star_max,
                lc_arr=lc_arr,
                lc_cache_overview=lc_cache_overview,
                T0_fit_margin=self.T0_fit_margin,
            )
            for data in pool.imap_unordered(params, periods):
                test_statistic_periods.append(data[0])
                test_statistic_residuals.append(data[1])
                test_statistic_rows.append(data[2])
                test_statistic_depths.append(data[3])
                if self.show_progress_bar:
                    pbar.update(1)
            pool.close()
        elif use_cpu:
            for period in periods:
                data = search_period(
                    transit_template_generator,
                    period=period,
                    t=self.t,
                    y=self.y,
                    dy=self.dy,
                    transit_depth_min=self.transit_depth_min,
                    R_star_min=self.R_star_min,
                    R_star_max=self.R_star_max,
                    M_star_min=self.M_star_min,
                    M_star_max=self.M_star_max,
                    lc_arr=lc_arr,
                    lc_cache_overview=lc_cache_overview,
                    T0_fit_margin=self.T0_fit_margin
                )
                test_statistic_periods.append(data[0])
                test_statistic_residuals.append(data[1])
                test_statistic_rows.append(data[2])
                test_statistic_depths.append(data[3])
                if self.show_progress_bar:
                    pbar.update(1)
        else:
            times = Times()
            times.begin_time("init")
            periods_f32 = numpy.array(periods).astype('float32')
            periods_len = len(periods_f32)
            gpu.change_periods_len(periods_f32)
            original_flux_len = len(self.y)
            time_span = max(self.t) - min(self.t)
            durations_in_samples = numpy.unique(lc_cache_overview["width_in_samples"])
            max_duration_in_samples = int(max(durations_in_samples))
            if max_duration_in_samples % 2 != 0:
                max_duration_in_samples = max_duration_in_samples + 1
            max_sample_signal_len_samples = max([len(signal) for signal in lc_arr])
            standardized_lc_arr = numpy.zeros((lc_arr.shape[0], max_sample_signal_len_samples), dtype=numpy.float32)
            for index, signal in enumerate(lc_arr):
                standardized_lc_arr[index][0:len(signal)] = (1 - lc_arr[index]) / tls_constants.SIGNAL_DEPTH
            standardized_lc_arr = cupy.asarray(standardized_lc_arr)
            standardized_lc_arr_pow = cupy.array(standardized_lc_arr)
            standardized_lc_arr_pow_signed = cupy.array(standardized_lc_arr)
            blockspergrid = ((periods_len + GPU_TPB) // GPU_TPB, (len(durations_in_samples) + GPU_TPB) // GPU_TPB)
            gpu.multiply_by_itself_position[blockspergrid, (GPU_TPB, GPU_TPB)] \
                (standardized_lc_arr, standardized_lc_arr_pow)
            gpu.multiply_by_itself_position_keep_sign[blockspergrid, (GPU_TPB, GPU_TPB)] \
                (standardized_lc_arr, standardized_lc_arr_pow_signed)
            cuda.synchronize()
            standardized_lc_arr_pow = cupy.cumsum(standardized_lc_arr_pow, axis=1)
            standardized_lc_arr_pow_signed = cupy.cumsum(standardized_lc_arr_pow_signed, axis=1)
            cuda.synchronize()
            periods_durations_in_samples = cuda.to_device(numpy.zeros((periods_len, len(durations_in_samples)), dtype=numpy.int32))
            gpu.periods_durations_in_samples[blockspergrid, (GPU_TPB, GPU_TPB)](cuda.to_device(periods_f32),
                                                                                cuda.to_device(durations_in_samples),
                                                                                self.R_star_max, self.M_star_max,
                                                                                self.R_star_min,
                                                                                self.M_star_min,
                                                                                tls_constants.FRACTIONAL_TRANSIT_DURATION_MAX,
                                                                                original_flux_len,
                                                                                time_span, periods_durations_in_samples)
            # dur_samp_host = periods_durations_in_samples.copy_to_host()
            # for x, period in enumerate(periods_f32):
            #     for y, duration in enumerate(dur_samp_host[x]):
            #         gpu.periods_durations_in_samples_sim(periods_f32, durations_in_samples,
            #                                                         self.R_star_max, self.M_star_max, self.R_star_min,
            #                                                         self.M_star_min,
            #                                                         tls_constants.FRACTIONAL_TRANSIT_DURATION_MAX,
            #                                                         original_flux_len,
            #                                                         time_span, dur_samp_host, x, y)
            cuda.synchronize()
            overshoots = cuda.to_device(lc_cache_overview["overshoot"].astype('float32'))
            gpu.change_data_len(original_flux_len)
            patched_data_len = gpu.get_data_len() + max_duration_in_samples
            gpu.change_patched_data_len(patched_data_len)
            gpu.change_transit_min_depth(self.transit_depth_min)
            time_f32 = cuda.to_device(self.t.astype('float32'))
            periods_f32 = cuda.to_device(periods_f32)
            partitions, mem_per_partition = gpu.gpu_compute_partitions_by_bytes(periods_len * 4, #periods_f32
                                                             original_flux_len * 4, #time_f32
                                                             periods_len * original_flux_len * 4 * 3, # time_folded
                                                             periods_len * original_flux_len * 4, # flux_folded
                                                             periods_len * original_flux_len * 4, # flux_folded take_along_aixs
                                                             periods_len * original_flux_len * 4, # dy_folded
                                                             periods_len * original_flux_len * 4, # dy_folded take_along_aixs
                                                             periods_len * original_flux_len * 8 * 3, # sort_indexes
                                                             periods_len * patched_data_len * 4, # folded_patched_flux
                                                             periods_len * patched_data_len * 4, # folded_patched_flux_pow
                                                             periods_len * patched_data_len * 4, # folded_patched_flux_pow cumsum
                                                             periods_len * patched_data_len * 4, # folded_patched_dy
                                                             periods_len * patched_data_len * 4, # folded_inverse_squared_patched_folded_dy
                                                             periods_len * patched_data_len * 4, # folded_inverse_squared_patched_folded_dy cumsum
                                                             periods_len * patched_data_len * 4, # folded_patched_flux_deviation_corrected
                                                             periods_len * patched_data_len * 4, # folded_patched_flux_deviation_corrected full_residuals_sum
                                                             periods_len * patched_data_len * 4, # folded_patched_flux_deviation_corrected cumsum
                                                             periods_len * 4, #edge_effect
                                                             periods_len * 4, #full_residuals_sum
                                                             periods_len * patched_data_len * 4, #folded_running_means
                                                             periods_len * len(durations_in_samples) * 4, #periods_durations_in_samples
                                                             periods_len * 3 * 4, #residuals_data
                                                             )
            partitions = int(partitions)
            cupy_memory_pool = cupy.get_default_memory_pool()
            with cupy.cuda.Device(0):
                cupy_memory_pool.set_limit(size=mem_per_partition)
            partition_periods_len = periods_len // partitions
            gpu.change_periods_len(partition_periods_len)
            gpu.change_durations_len(len(durations_in_samples))
            # Variables declaration
            residuals_data = numpy.full((periods_len, 3), original_flux_len, dtype=numpy.float32)
            partition_residuals_data_gpu = cuda.device_array((partition_periods_len, 3), dtype=numpy.float32)
            #zeros_patched_flux_prepend = cupy.asarray(numpy.zeros((partition_periods_len, 1), dtype=numpy.float32))
            partition_period_min = 0
            partitions = numpy.arange(0, partitions)
            times.end_time("init")
            for partition in partitions:
                times.begin_time(f"prep_{partition}")
                cupy_memory_pool.free_all_blocks()
                flux_folded = cupy.asarray(numpy.array([self.y] * partition_periods_len, dtype=numpy.float32))
                dy_folded = cupy.asarray(numpy.array([self.dy] * partition_periods_len, dtype=numpy.float32))
                time_folded = cupy.asarray(
                    numpy.zeros((partition_periods_len, gpu.get_data_len()), dtype=numpy.float32))
                cupy_memory_pool.free_all_blocks()
                # Partition logic
                partition_period_max = partition_period_min + partition_periods_len
                partition_period_max = partition_period_max if partition_period_max <= periods_len \
                    else periods_len
                cuda.synchronize()
                times.end_time(f"prep_{partition}")
                # Core logic
                times.begin_time(f"foldfast_{partition}")
                blockspergrid = ((gpu.get_periods_len() + GPU_TPB) // GPU_TPB,
                                 (gpu.get_data_len() + GPU_TPB) // GPU_TPB)
                gpu.foldfast[blockspergrid, (GPU_TPB, GPU_TPB)]\
                    (periods_f32[partition_period_min:partition_period_max], time_f32, time_folded)
                cuda.synchronize()
                cupy_memory_pool.free_all_blocks()
                times.end_time(f"foldfast_{partition}")
                times.begin_time(f"argsort_{partition}")
                sort_indexes = cupy.argsort(time_folded, axis=1)
                cupy_memory_pool.free_all_blocks()
                times.end_time(f"argsort_{partition}")
                times.begin_time(f"take_along_{partition}")
                flux_folded = cupy.take_along_axis(flux_folded, sort_indexes, axis=1)
                cupy_memory_pool.free_all_blocks()
                dy_folded = cupy.take_along_axis(dy_folded, sort_indexes, axis=1)
                cupy_memory_pool.free_all_blocks()
                cuda.synchronize()
                times.end_time(f"take_along_{partition}")
                times.begin_time(f"edge_effect_{partition}")
                folded_inverse_squared_patched_folded_dy = cupy.asarray(
                    numpy.zeros((partition_periods_len, gpu.get_patched_len()),
                                dtype=numpy.float32))
                folded_per_point_residuals = cupy.asarray(
                    numpy.zeros((partition_periods_len, gpu.get_patched_len()),
                                dtype=numpy.float32))
                folded_patched_flux = cupy.asarray(
                    numpy.zeros((partition_periods_len, gpu.get_patched_len()), dtype=numpy.float32))
                folded_patched_dy = cupy.asarray(
                    numpy.zeros((partition_periods_len, gpu.get_patched_len()), dtype=numpy.float32))
                edge_effect = cupy.asarray(numpy.zeros(partition_periods_len, dtype=numpy.float32))
                partition_residuals_data_gpu.copy_to_device(
                    numpy.full((partition_periods_len, 3), original_flux_len, dtype=numpy.float32))
                blockspergrid = ((gpu.get_periods_len() + GPU_TPB) // GPU_TPB,
                                 (gpu.get_patched_len() + GPU_TPB) // GPU_TPB)
                # flux = flux_folded.get()
                # dy = dy_folded.get()
                # dev = folded_patched_flux_deviation_corrected.get()
                # sq_dy = folded_inverse_squared_patched_folded_dy.get()
                # patched_flux = folded_patched_flux.get()
                # edge = edge_effect.get()
                # for x, period in enumerate(periods_f32[partition_period_min:partition_period_max]):
                #     for y in range(0, patched_data_len):
                #         gpu.gpu_edge_effect_correction_sim(flux, dy, dev,
                #              sq_dy,
                #              patched_flux, folded_patched_dy,
                #              edge, x, y)
                gpu.gpu_edge_effect_correction[blockspergrid, (GPU_TPB, GPU_TPB)]\
                    (flux_folded, dy_folded, folded_per_point_residuals,
                     folded_inverse_squared_patched_folded_dy,
                     folded_patched_flux, folded_patched_dy,
                     edge_effect)
                cuda.synchronize()
                del time_folded
                del flux_folded
                del dy_folded
                del sort_indexes
                cupy_memory_pool.free_all_blocks()
                times.end_time(f"edge_effect_{partition}")
                times.begin_time(f"full_residuals_{partition}")
                oot_sum = cupy.subtract(
                    cupy.sum(folded_per_point_residuals, axis=1),
                    edge_effect
                )
                del edge_effect
                cupy_memory_pool.free_all_blocks()
                times.end_time(f"full_residuals_{partition}")
                times.begin_time(f"means_{partition}")
                folded_running_means = cupy.cumsum(folded_patched_flux, axis=1)
                #folded_running_means = cupy.cumsum(cupy.concatenate((zeros_patched_flux_prepend, folded_patched_flux), axis=1), axis=1)
                cupy_memory_pool.free_all_blocks()
                times.end_time(f"means_{partition}")
                times.begin_time(f"sum_flux_{partition}")
                gpu.sum_value_to_array[blockspergrid, (GPU_TPB, GPU_TPB)](folded_patched_flux, -1)
                times.end_time(f"sum_flux_{partition}")
                times.begin_time(f"residuals_{partition}")
                folded_patched_flux_pow = cupy.asarray(
                    numpy.zeros((partition_periods_len, gpu.get_patched_len()), dtype=numpy.float32))
                folded_patched_flux_pow_signed = cupy.asarray(
                    numpy.zeros((partition_periods_len, gpu.get_patched_len()), dtype=numpy.float32))
                gpu.multiply_by_itself_position[blockspergrid, (GPU_TPB, GPU_TPB)]\
                    (folded_patched_flux, folded_patched_flux_pow)
                gpu.multiply_by_itself_position_keep_sign[blockspergrid, (GPU_TPB, GPU_TPB)]\
                    (folded_patched_flux, folded_patched_flux_pow_signed)
                cuda.synchronize()
                cupy_memory_pool.free_all_blocks()
                blockspergrid = ((gpu.get_periods_len() + GPU_TPB) // GPU_TPB,
                                 (gpu.get_patched_len() + GPU_TPB) // GPU_TPB,
                                 gpu.get_durations_len())
                if self.gpu_approximate:
                    gpu.residuals_cauchy[blockspergrid, (GPU_TPB, GPU_TPB, 1)]\
                        (folded_patched_flux,
                         cupy.cumsum(folded_patched_flux_pow, axis=1),
                         cupy.cumsum(folded_patched_flux_pow_signed, axis=1),
                         cupy.cumsum(folded_per_point_residuals, axis=1),
                         cupy.cumsum(folded_inverse_squared_patched_folded_dy, axis=1),
                         periods_durations_in_samples[partition_period_min:partition_period_max], oot_sum,
                         folded_running_means, overshoots,
                         standardized_lc_arr_pow,
                         standardized_lc_arr_pow_signed,
                         partition_residuals_data_gpu)
                else:
                    gpu.residuals[blockspergrid, (GPU_TPB, GPU_TPB, 1)] \
                        (folded_patched_flux,
                         cupy.cumsum(folded_patched_flux_pow, axis=1),
                         cupy.cumsum(folded_per_point_residuals, axis=1),
                         cupy.cumsum(folded_inverse_squared_patched_folded_dy, axis=1),
                         periods_durations_in_samples[partition_period_min:partition_period_max], oot_sum,
                         folded_running_means, overshoots,
                         standardized_lc_arr,
                         standardized_lc_arr_pow,
                         partition_residuals_data_gpu)
                # res_host = partition_residuals_data_gpu.copy_to_host()
                # dur_samp_host = periods_durations_in_samples[partition_period_min:partition_period_max].copy_to_host()
                # lc = standardized_lc_arr.get()
                # lc_pow = standardized_lc_arr_pow.get()
                # lc_pow_signed = standardized_lc_arr_pow_signed.get()
                # running = folded_running_means.get()
                # os = overshoots.copy_to_host()
                # sum = oot_sum.get()
                # inv_dy = cupy.cumsum(folded_inverse_squared_patched_folded_dy, axis=1).get()
                # corr = cupy.cumsum(folded_per_point_residuals, axis=1).get()
                # flux_pow = cupy.cumsum(folded_patched_flux_pow, axis=1).get()
                # flux_pow_signed = cupy.cumsum(folded_patched_flux_pow_signed, axis=1).get()
                # flux = folded_patched_flux.get()
                # for x, period in enumerate(periods_f32[partition_period_min:partition_period_max]):
                #     for y, duration in enumerate(dur_samp_host[x]):
                #         if duration > 0:
                #             for z in range(0, patched_data_len):
                #                 gpu.gpu_residuals_cauchy_sim \
                #                     (flux,
                #                      flux_pow, flux_pow_signed,
                #                      corr,
                #                      inv_dy,
                #                      dur_samp_host, sum,
                #                      running, os,
                #                      lc,
                #                      lc_pow, lc_pow_signed,
                #                      res_host, x, y, z)
                cuda.synchronize()
                del folded_patched_flux
                del folded_patched_flux_pow
                del folded_patched_flux_pow_signed
                del folded_per_point_residuals
                del folded_inverse_squared_patched_folded_dy
                del oot_sum
                del folded_running_means
                times.end_time(f"residuals_{partition}")
                times.begin_time(f"copy_{partition}")
                partition_residuals_data_gpu.copy_to_host(residuals_data[partition_period_min:partition_period_max])
                cuda.synchronize()
                cupy_memory_pool.free_all_blocks()
                times.end_time(f"copy_{partition}")
                if self.show_progress_bar:
                    pbar.update(partition_period_max - partition_period_min)
                partition_period_min = partition_period_max
            test_statistic_periods = periods_f32
            test_statistic_residuals = residuals_data[:, 0]
            test_statistic_rows = residuals_data[:, 1]
            test_statistic_depths = residuals_data[:, 2]
        total_time = time.time() - st
        #print("Total Time " + str(total_time / 60))
        test_statistic_periods = numpy.array(test_statistic_periods)
        sort_index = numpy.argsort(test_statistic_periods)
        test_statistic_periods = test_statistic_periods[sort_index]
        test_statistic_residuals = numpy.array(test_statistic_residuals)[sort_index]
        test_statistic_rows = numpy.array(test_statistic_rows)[sort_index]
        test_statistic_depths = numpy.array(test_statistic_depths)[sort_index]
        idx_best = numpy.argmin(test_statistic_residuals)
        best_row = int(test_statistic_rows[idx_best])
        duration = lc_cache_overview["duration"][best_row]
        maxwidth_in_samples = int(numpy.max(durations) * numpy.size(self.t))
        if max(test_statistic_residuals) == min(test_statistic_residuals) and len(test_statistic_residuals) > 1:
            no_transits_were_fit = True
            warnings.warn('No transit were fit. Try smaller "transit_depth_min"')
        else:
            no_transits_were_fit = False
        # Power spectra variants
        chi2 = test_statistic_residuals
        degrees_of_freedom = 4
        chi2red = test_statistic_residuals / (len(self.t) - degrees_of_freedom)
        chi2_min = numpy.min(chi2)
        chi2red_min = numpy.min(chi2red)
        return transit_template_generator.calculate_results(no_transits_were_fit, chi2, chi2red, chi2_min,
                                                            chi2red_min, test_statistic_periods, test_statistic_depths,
                                                            self, lc_arr, best_row, periods,
                                                            durations, duration, maxwidth_in_samples, len(self.y))

