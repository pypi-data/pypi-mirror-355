import math
import cupy
import numba
import numpy as np
import torch
from numba import cuda, float32

GPU_TPB = 32
DATA_LEN = 1000
PERIODS_LEN = 1
PATCHED_DATA_LEN = DATA_LEN + 1
DURATIONS_LEN = 30
MAX_DURATION = 5
TRANSIT_DEPTH_MIN = 1e-6
GPU_ORIGINAL_FLUX_LEN = 1000
T0_FIT_MARGIN = 0.01
G = 6.673e-11  # gravitational constant [m^3 / kg / s^2]
R_sun = 695508000  # radius of the Sun [m]
R_earth = 6371000  # radius of the Earth [m]
R_jup = 69911000  # radius of Jupiter [m]
M_sun = 1.989 * 10 ** 30  # mass of the Sun [kg]
SECONDS_PER_DAY = 86400
pi = 3.141592653589793
SIGNAL_DEPTH = 0.5


def print_device_info():
    gpu = cuda.get_current_device()
    print("name = %s" % gpu.name)
    print("maxThreadsPerBlock = %s" % str(gpu.MAX_THREADS_PER_BLOCK))
    print("maxBlockDimX = %s" % str(gpu.MAX_BLOCK_DIM_X))
    print("maxBlockDimY = %s" % str(gpu.MAX_BLOCK_DIM_Y))
    print("maxBlockDimZ = %s" % str(gpu.MAX_BLOCK_DIM_Z))
    print("maxGridDimX = %s" % str(gpu.MAX_GRID_DIM_X))
    print("maxGridDimY = %s" % str(gpu.MAX_GRID_DIM_Y))
    print("maxGridDimZ = %s" % str(gpu.MAX_GRID_DIM_Z))
    print("maxSharedMemoryPerBlock = %s" % str(gpu.MAX_SHARED_MEMORY_PER_BLOCK))
    print("asyncEngineCount = %s" % str(gpu.ASYNC_ENGINE_COUNT))
    print("canMapHostMemory = %s" % str(gpu.CAN_MAP_HOST_MEMORY))
    print("multiProcessorCount = %s" % str(gpu.MULTIPROCESSOR_COUNT))
    print("warpSize = %s" % str(gpu.WARP_SIZE))
    print("unifiedAddressing = %s" % str(gpu.UNIFIED_ADDRESSING))
    print("pciBusID = %s" % str(gpu.PCI_BUS_ID))
    print("pciDeviceID = %s" % str(gpu.PCI_DEVICE_ID))

def get_device_count():
    return cupy.cuda.runtime.getDeviceCount()

def change_data_len(value):
    global DATA_LEN
    DATA_LEN = value


def change_patched_data_len(value):
    global PATCHED_DATA_LEN
    PATCHED_DATA_LEN = value


def change_durations_len(value):
    global DURATIONS_LEN
    DURATIONS_LEN = value


def change_max_durations(value):
    global MAX_DURATION
    MAX_DURATION = value


def change_periods_len(value):
    global PERIODS_LEN
    PERIODS_LEN = value

def change_transit_min_depth(value):
    global TRANSIT_DEPTH_MIN
    TRANSIT_DEPTH_MIN = value

def change_t0_fit_margin(value):
    global T0_FIT_MARGIN
    T0_FIT_MARGIN = value


def get_data_len():
    return DATA_LEN

def get_patched_len():
    return PATCHED_DATA_LEN


def get_durations_len():
    return DURATIONS_LEN

def get_periods_len():
    return PERIODS_LEN

def gpu_compute_partitions(*arrays_args):
    used_bytes = [arrays_arg.size * 4 if arrays_args.dtype == np.float32 else arrays_args * 8
                  for arrays_arg in arrays_args]
    return gpu_compute_partitions_by_bytes(used_bytes)

def gpu_compute_partitions_by_bytes(periods_len, *byte_values):
    used_bytes = [arrays_arg for arrays_arg in byte_values]
    gp_mem_tuple = torch.cuda.mem_get_info()
    used_bytes = np.sum(used_bytes)
    partitions = used_bytes // gp_mem_tuple[0] + 1
    mem_per_partition = used_bytes / partitions
    return partitions, mem_per_partition

def compute_duration_partitions(durations_len, max_duration_in_samples):
    duration_tuples = [0]
    durations_len_boundary = 0
    block_size_threshold = 2**16 - 1
    while durations_len_boundary < durations_len:
        if durations_len_boundary + block_size_threshold // max_duration_in_samples < durations_len:
            durations_len_boundary = durations_len_boundary + block_size_threshold // max_duration_in_samples
        else:
            durations_len_boundary = durations_len
        duration_tuples = duration_tuples + [durations_len_boundary]
    return duration_tuples


def get_memory_mb():
    free_memory, all_memory = torch.cuda.mem_get_info()
    return free_memory // 1e6, all_memory // 1e6



device = True
inline = True


@cuda.jit(device=device, inline=inline)
def partition(arr, ids, l, h):
    """
    Partition using pivot.

    Function takes last element as pivot, places the pivot element at its correct
    position in sorted array, and places all smaller (smaller than pivot) to left of
    pivot and all greater elements to right of pivot

    Source: Modified from https://www.geeksforgeeks.org/iterative-quick-sort/
    which was contributed by Mohit Kumra.

    Parameters
    ----------
    arr : vector of floats
        The array to be sorted.
    ids : vector of ints
        The unsorted IDs corresponding to arr, in other words range(len(arr)).
    l : int
        Starting index for sorting.
    h : int
        Ending index for sorting.

    Returns
    -------
    int
        the new pivot?

    """
    # index of smaller element
    i = l - 1

    pivot = arr[h]

    for j in range(l, h):

        # If current element is smaller than or equal to pivot
        if arr[j] <= pivot:

            # increment index of smaller element
            i += 1
            arr[i], arr[j] = arr[j], arr[i]
            ids[i], ids[j] = ids[j], ids[i]

    arr[i + 1], arr[h] = arr[h], arr[i + 1]
    ids[i + 1], ids[h] = ids[h], ids[i + 1]

    return i + 1


@cuda.jit(device=device, inline=inline)
def quickSortIterative(arr, stack, ids):
    """
    Perform iterative quicksort on array and an unsorted ID list of the array.

    Source: Modified from https://www.geeksforgeeks.org/iterative-quick-sort/
    which was contributed by Mohit Kumra.

    Parameters
    ----------
    arr : vector of floats
        The array to be sorted.
    stack : vector of ints
        Array initialized with 0's
    ids : vector of ints
        The unsorted IDs corresponding to arr, in other words range(len(arr)).

    Returns
    -------
    None.

    """
    # low and high indices.
    l, h = (0, len(arr) - 1)
    # stack = [0] * size
    # ids = list(range(len(arr)))

    # initialize top of stack
    top = -1

    # fill ids with range(len(arr))
    for i in range(len(arr)):
        ids[i] = i
        stack[i] = 0

    # push initial values of l and h to stack
    top = top + 1
    stack[top] = l
    top = top + 1
    stack[top] = h

    # Keep popping from stack while is not empty
    while top >= 0:

        # Pop h and l
        h = stack[top]
        top = top - 1
        l = stack[top]
        top = top - 1

        # Set pivot element at its correct position in
        # sorted array
        p = partition(arr, ids, l, h)

        # If there are elements on left side of pivot,
        # then push left side to stack
        if p - 1 > l:
            top = top + 1
            stack[top] = l
            top = top + 1
            stack[top] = p - 1

        # If there are elements on right side of pivot,
        # then push right side to stack
        if p + 1 < h:
            top = top + 1
            stack[top] = p + 1
            top = top + 1
            stack[top] = h

@cuda.jit
def periods_durations_in_samples(periods, durations_in_samples, R_s_max, M_s_max, R_s_min, M_s_min, upper_limit,
                                 original_flux_len, time_span, periods_durations_in_samples):
    x, y = cuda.grid(2)
    if x < periods.shape[0] and y < durations_in_samples.shape[0]:
        period_days = periods[x]
        p = periods[x] * SECONDS_PER_DAY # seconds per day
        R_s_max = R_s_max * R_sun  # radius of the Sun [m]
        M_s_max = M_s_max * M_sun  # mass of the Sun [kg]
        R_s_min = R_s_min * R_sun  # radius of the Sun [m]
        M_s_min = M_s_min * M_sun  # mass of the Sun [kg]
        T14max = (R_s_max + 2 * R_jup) * ((4 * p) / (pi * G * M_s_max)) ** (1 / 3)
        duration_max = T14max / p
        if duration_max > upper_limit:
            duration_max = upper_limit
        T14min = R_s_min * ((4 * p) / (pi * G * M_s_min)) ** (1 / 3)
        duration_min = T14min / p
        if duration_min > upper_limit:
            duration_min = upper_limit
        no_of_transits_naive = time_span / period_days
        duration_max = int(math.ceil(duration_max * original_flux_len * ((no_of_transits_naive + 1) / no_of_transits_naive)))
        duration_min = int(math.floor(duration_min * original_flux_len))
        if durations_in_samples[y] >= duration_min and durations_in_samples[y] <= duration_max:
            periods_durations_in_samples[x, y] = int(durations_in_samples[y])

def periods_durations_in_samples_sim(periods, durations_in_samples, R_s_max, M_s_max, R_s_min, M_s_min, upper_limit,
                                 original_flux_len, time_span, periods_durations_in_samples, x, y):
    #x, y = cuda.grid(2)
    if x < periods.shape[0] and y < durations_in_samples.shape[0]:
        period_days = periods[x]
        p = period_days * SECONDS_PER_DAY # seconds per day
        R_s_max = R_s_max * R_sun  # radius of the Sun [m]
        M_s_max = M_s_max * M_sun  # mass of the Sun [kg]
        R_s_min = R_s_min * R_sun  # radius of the Sun [m]
        M_s_min = M_s_min * M_sun  # mass of the Sun [kg]
        T14min = R_s_min * ((4 * p) / (pi * G * M_s_min)) ** (1 / 3)
        T14max = (R_s_max + 2 * R_jup) * ((4 * p) / (pi * G * M_s_max)) ** (1 / 3)
        duration_max = T14max / p
        if duration_max > upper_limit:
            duration_max = upper_limit
        duration_min = T14min / p
        if duration_min > upper_limit:
            duration_min = upper_limit
        no_of_transits_naive = time_span / period_days
        duration_max = int(math.ceil(duration_max * original_flux_len * ((no_of_transits_naive + 1) / no_of_transits_naive)))
        duration_min = int(math.floor(duration_min * original_flux_len))
        if durations_in_samples[y] >= duration_min and durations_in_samples[y] <= duration_max:
            periods_durations_in_samples[x, y] = int(durations_in_samples[y])

@cuda.jit
def foldfast(periods, time, time_folded):
    x, y = cuda.grid(2)
    if x < time_folded.shape[0] and y < time_folded.shape[1]:
        time_folded[x][y] = time[y] / periods[x] - math.floor(time[y] / periods[x])

def foldfast_sim(periods, time, time_folded, x, y):
    if x < time_folded.shape[0] and y < time_folded.shape[1]:
        time_folded[x][y] = time[y] / periods[x] - math.floor(time[y] / periods[x])

@cuda.reduce
def gpu_sum_reduce(a, b):
    return a + b

@cuda.jit
def gpu_edge_effect_correction_old(folded_flux, folded_dy, folded_patched_flux_deviation_corrected,
                               folded_inverse_squared_patched_folded_dy,
                               folded_patched_flux, patched_folded_dy, edge_effect):
    x, y = cuda.grid(2)
    if x < folded_patched_flux.shape[0]:
        if y < folded_flux.shape[1]:
            folded_patched_flux[x][y] = folded_flux[x][y]
            patched_folded_dy[x][y] = folded_dy[x][y]
            folded_inverse_squared_patched_folded_dy[x][y] = 1 / folded_dy[x][y] ** 2
            folded_patched_flux_deviation_corrected[x][y] = (1 - folded_flux[x][y]) ** 2 * folded_dy[x][y]
        else:
            folded_patched_flux[x][y] = folded_flux[x][y - folded_flux.shape[1]]
            patched_folded_dy[x][y] = folded_dy[x][y - folded_flux.shape[1]]
            folded_inverse_squared_patched_folded_dy[x][y] = 1 / folded_dy[x][y - folded_flux.shape[1]] ** 2
            folded_patched_flux_deviation_corrected[x][y] = (1 - folded_flux[x][y - folded_flux.shape[1]]) ** 2 * \
                                                            folded_dy[x][y - folded_flux.shape[1]]
            cuda.atomic.add(edge_effect, x, ((1 - (folded_patched_flux[x][y])) ** 2) * folded_inverse_squared_patched_folded_dy[x][y])
        #folded_patched_zero_flux[x][y] = folded_patched_flux[x][y] - 1

@cuda.jit
def gpu_edge_effect_correction(folded_flux, folded_dy, oot_residuals,
                               folded_inverse_squared_patched_folded_dy,
                               folded_patched_flux, patched_folded_dy, edge_effect):
    x, y = cuda.grid(2)
    if x < folded_patched_flux.shape[0] and y < folded_patched_flux.shape[1]:
        if y < folded_flux.shape[1]:
            folded_patched_flux[x][y] = folded_flux[x][y]
            patched_folded_dy[x][y] = folded_dy[x][y]
            folded_inverse_squared_patched_folded_dy[x][y] = 1 / folded_dy[x][y] ** 2
            oot_residuals[x][y] = (1 - folded_flux[x][y]) ** 2 * \
                                  folded_inverse_squared_patched_folded_dy[x][y]
        else:
            #numpy.sum(((1 - patched_data) ** 2) * inverse_squared_patched_dy)
            folded_patched_flux[x][y] = folded_flux[x][y - folded_flux.shape[1]]
            patched_folded_dy[x][y] = folded_dy[x][y - folded_flux.shape[1]]
            folded_inverse_squared_patched_folded_dy[x][y] = 1 / patched_folded_dy[x][y] ** 2
            oot_residuals[x][y] = (1 - folded_patched_flux[x][y]) ** 2 * \
                                  folded_inverse_squared_patched_folded_dy[x][y]
            cuda.atomic.add(edge_effect, x, oot_residuals[x][y])
        #folded_patched_zero_flux[x][y] = folded_patched_flux[x][y] - 1

def gpu_edge_effect_correction_sim(folded_flux, folded_dy, folded_patched_flux_deviation_corrected,
                               folded_inverse_squared_patched_folded_dy,
                               folded_patched_flux, patched_folded_dy, edge_effect, x, y):
    #x, y = cuda.grid(2)
    if x < folded_patched_flux.shape[0]:
        if y < folded_flux.shape[1]:
            folded_patched_flux[x][y] = folded_flux[x][y]
            patched_folded_dy[x][y] = folded_dy[x][y]
            folded_inverse_squared_patched_folded_dy[x][y] = 1 / folded_dy[x][y] ** 2
            folded_patched_flux_deviation_corrected[x][y] = (1 - folded_flux[x][y]) ** 2 * \
                                                            folded_inverse_squared_patched_folded_dy[x][y]
        else:
            #numpy.sum(((1 - patched_data) ** 2) * inverse_squared_patched_dy)
            folded_patched_flux[x][y] = folded_flux[x][y - folded_flux.shape[1]]
            patched_folded_dy[x][y] = folded_dy[x][y - folded_flux.shape[1]]
            folded_inverse_squared_patched_folded_dy[x][y] = 1 / patched_folded_dy[x][y] ** 2
            folded_patched_flux_deviation_corrected[x][y] = (1 - folded_patched_flux[x][y]) ** 2 * \
                                                            folded_inverse_squared_patched_folded_dy[x][y]
            edge_effect[x] = ((1 - (folded_patched_flux[x][y])) ** 2) * folded_inverse_squared_patched_folded_dy[x][y]

@cuda.jit
def sum_value_to_array(array, value):
    x, y = cuda.grid(2)
    if x < array.shape[0] and y < array.shape[1]:
        array[x, y] = array[x, y] + value

@cuda.jit
def subtract_array_to_value(value, array):
    x, y = cuda.grid(2)
    if x < array.shape[0] and y < array.shape[1]:
        array[x, y] = value - array[x, y]

@cuda.jit
def multiply_by_value(array, value):
    x, y = cuda.grid(2)
    if x < array.shape[0] and y < array.shape[1]:
        array[x, y] = array[x, y] * value

@cuda.jit
def multiply_by_itself_position_keep_sign(array1, array3):
    x, y = cuda.grid(2)
    if x < array1.shape[0] and y < array1.shape[1]:
        if array1[x, y] < 0:
            array3[x, y] = - array1[x, y] * array1[x, y]
        else:
            array3[x, y] = array1[x, y] * array1[x, y]

@cuda.jit
def multiply_by_itself_position(array1, array3):
    x, y = cuda.grid(2)
    if x < array1.shape[0] and y < array1.shape[1]:
        array3[x, y] = array1[x, y] * array1[x, y]



@cuda.jit
def residuals_cauchy(patched_flux, patched_flux_pow, patched_flux_pow_signed, folded_patched_flux_deviation_corrected,
                     inverse_squared_patched_folded_dy,
                     periods_durations_in_samples, fullsum, folded_running_means, overshoots,
                     lc_arr_pow, lc_arr_pow_signed, residuals_data):
    x, z, y = cuda.grid(3)
    if x < patched_flux.shape[0] and y < periods_durations_in_samples.shape[1]:
        duration_in_samples = periods_durations_in_samples[x][y]
        if duration_in_samples > 0 and 0 < z < patched_flux.shape[1] - duration_in_samples - 1:
            cumsum_left_index = z - 1
            cumsum_right_index = cumsum_left_index + duration_in_samples
            mean = 1 - ((folded_running_means[x, cumsum_right_index] -
                    folded_running_means[x, cumsum_left_index]) / duration_in_samples)
            xth_point = int(duration_in_samples * T0_FIT_MARGIN)
            if xth_point < 1:
                xth_point = 1
            if mean > TRANSIT_DEPTH_MIN and z % xth_point == 0:
                target_depth = mean * overshoots[y]
                patched_flux_pow_sum = (
                            patched_flux_pow[x, cumsum_right_index] - patched_flux_pow[x, cumsum_left_index])
                patched_flux_pow_signed_sum = (patched_flux_pow_signed[x, cumsum_right_index] - patched_flux_pow_signed[
                    x, cumsum_left_index])
                avg_inverse_squared_patched_folded_dy = (inverse_squared_patched_folded_dy[x, cumsum_right_index]
                                                         - inverse_squared_patched_folded_dy[
                                                             x, cumsum_left_index]) / duration_in_samples
                # (patched_data - 1 + (1 - lc_arr) * rev_sc) ** 2 * inverse_sq_dy
                # (patched_data_norm ** 2 + ((1 - lc_arr) * rev_sc) ** 2 + 2 * patched_data_norm * (1 - lc_arr) * rev_sc) * inverse_sq_dy # assume avg invs sq dy
                # #patched_data_norm ** 2 out of the equation
                # ((1 - lc_arr) * rev_sc) ** 2 + 2 * patched_data_norm * (1 - lc_arr) * rev_sc
                # # (1 - lc_arr) * rev_sc becomes lc_arr_norm = (1 - lc_arr) / SIGNAL_DEPTH
                # (lc_arr_norm * target_depth) ** 2 + 2 * patched_data_norm * lc_arr_norm * target_depth
                # target_depth * ((lc_arr_norm_pw * target_depth) + 2 * patched_data_norm * lc_arr_norm)

                # target_depth * ((lc_pow ** 2 * target_depth) + 2 * patched_data_norm * lc_arr_norm)
                # cauchy inequality
                # 2 * target_depth_pow * sqrt(sum(patched_data_norm ** 2) * sum(lc_arr_norm** 2)  )
                flux_lc_arr_mult = patched_flux_pow_signed_sum * lc_arr_pow_signed[y, duration_in_samples - 1]
                flux_lc_arr_mult = math.sqrt(flux_lc_arr_mult) if flux_lc_arr_mult > 0 else - math.sqrt(
                    -flux_lc_arr_mult)
                current_stat = float32(
                    fullsum[x] -
                    (folded_patched_flux_deviation_corrected[x, cumsum_right_index]  # subtracting residuals from oot
                     - folded_patched_flux_deviation_corrected[x, cumsum_left_index])
                    # + avg_inverse_squared_patched_folded_dy * # adding intransit residuals
                    #     (patched_flux_pow_sum +
                    #      target_depth * (1 + 2 * (patched_flux_pow_sum * lc_arr_pow[y, duration_in_samples -1]) ** (1/2))
                    #     )
                    + avg_inverse_squared_patched_folded_dy * (
                            patched_flux_pow_sum +
                            target_depth * (
                                    lc_arr_pow[y, duration_in_samples - 1] * target_depth +
                                    2 * flux_lc_arr_mult
                            )
                    )
                )
                if current_stat < cuda.atomic.min(residuals_data, (x, 0), current_stat):
                    residuals_data[x, 0] = current_stat
                    residuals_data[x, 1] = y
                    residuals_data[x, 2] = 1 - target_depth

def gpu_residuals_cauchy_sim(patched_flux, patched_flux_pow, patched_flux_pow_signed, folded_patched_flux_deviation_corrected,
                  inverse_squared_patched_folded_dy,
                  periods_durations_in_samples, fullsum, folded_running_means, overshoots,
                  lc_arr, lc_arr_pow, lc_arr_pow_signed, residuals_data, x, y, z):
    #x, z, y = cuda.grid(3)
    if x < patched_flux.shape[0] and y < periods_durations_in_samples.shape[1]:
        duration_in_samples = periods_durations_in_samples[x][y]
        if duration_in_samples > 0 and 0 < z < patched_flux.shape[1] - duration_in_samples - 1:
            cumsum_left_index = z - 1
            cumsum_right_index = cumsum_left_index + duration_in_samples
            mean = float32(1 - ((folded_running_means[x, cumsum_right_index] -
                    folded_running_means[x, cumsum_left_index]) / float32(duration_in_samples)))
            xth_point = int(duration_in_samples * T0_FIT_MARGIN)
            if xth_point < 1:
                xth_point = 1
            if mean > TRANSIT_DEPTH_MIN and z % xth_point == 0:
                target_depth = mean * overshoots[y]
                patched_flux_pow_sum = (patched_flux_pow[x, cumsum_right_index] - patched_flux_pow[x, cumsum_left_index])
                patched_flux_pow_signed_sum = (patched_flux_pow_signed[x, cumsum_right_index] - patched_flux_pow_signed[x, cumsum_left_index])
                avg_inverse_squared_patched_folded_dy = (inverse_squared_patched_folded_dy[x, cumsum_right_index]
                                                         - inverse_squared_patched_folded_dy[x, cumsum_left_index]) / duration_in_samples
                # (patched_data - 1 + (1 - lc_arr) * rev_sc) ** 2 * inverse_sq_dy
                # (patched_data_norm ** 2 + ((1 - lc_arr) * rev_sc) ** 2 + 2 * patched_data_norm * (1 - lc_arr) * rev_sc) * inverse_sq_dy # assume avg invs sq dy
                # #patched_data_norm ** 2 out of the equation
                # ((1 - lc_arr) * rev_sc) ** 2 + 2 * patched_data_norm * (1 - lc_arr) * rev_sc
                # # (1 - lc_arr) * rev_sc becomes lc_arr_norm = (1 - lc_arr) / SIGNAL_DEPTH
                # (lc_arr_norm * target_depth) ** 2 + 2 * patched_data_norm * lc_arr_norm * target_depth
                # target_depth * ((lc_arr_norm_pw * target_depth) + 2 * patched_data_norm * lc_arr_norm)

                # target_depth * ((lc_pow ** 2 * target_depth) + 2 * patched_data_norm * lc_arr_norm)
                # cauchy inequality
                # 2 * target_depth_pow * sqrt(sum(patched_data_norm ** 2) * sum(lc_arr_norm** 2)  )
                flux_lc_arr_mult = patched_flux_pow_signed_sum * lc_arr_pow_signed[y, duration_in_samples - 1]
                flux_lc_arr_mult = math.sqrt(flux_lc_arr_mult) if flux_lc_arr_mult > 0 else - math.sqrt(
                    -flux_lc_arr_mult)
                current_stat = float32(
                    fullsum[x] -
                    (folded_patched_flux_deviation_corrected[x, cumsum_right_index] # subtracting residuals from oot
                     - folded_patched_flux_deviation_corrected[x, cumsum_left_index])
                    # + avg_inverse_squared_patched_folded_dy * # adding intransit residuals
                    #     (patched_flux_pow_sum +
                    #      target_depth * (1 + 2 * (patched_flux_pow_sum * lc_arr_pow[y, duration_in_samples -1]) ** (1/2))
                    #     )
                    + avg_inverse_squared_patched_folded_dy * (
                            patched_flux_pow_sum +
                            target_depth * (
                                    lc_arr_pow[y, duration_in_samples - 1] * target_depth +
                                    2 * flux_lc_arr_mult
                            )
                    )
                )
                if current_stat < residuals_data[x, 0]:
                    #residuals_data[x, 0] = current_stat
                    residuals_data[x, 1] = y
                    residuals_data[x, 2] = 1 - target_depth

@cuda.jit(fastmath=True)
def residuals(patched_flux, patched_flux_pow, folded_patched_flux_deviation_corrected,
              inverse_squared_patched_folded_dy,
              periods_durations_in_samples, fullsum, folded_running_means, overshoots,
              lc_arr, lc_arr_pow, residuals_data):
    x, z, y = cuda.grid(3)
    if x < patched_flux.shape[0] and y < periods_durations_in_samples.shape[1]:
        duration_in_samples = periods_durations_in_samples[x][y]
        if duration_in_samples > 0 and z > 0 and z < patched_flux.shape[1] - duration_in_samples:
            cumsum_left_index = z - 1
            cumsum_right_index = cumsum_left_index + duration_in_samples
            mean = 1 - ((folded_running_means[x, cumsum_right_index] -
                         folded_running_means[x, cumsum_left_index]) / float32(duration_in_samples))
            # xth_point = 1  # How many cadences the template shifts forward in each step
            # if duration_in_samples > T0_FIT_MARGIN:
            xth_point = int(duration_in_samples * T0_FIT_MARGIN)
            if xth_point < 1:
                xth_point = 1
            if mean > TRANSIT_DEPTH_MIN and z % xth_point == 0:
                target_depth = mean * overshoots[y]
                target_depth_pow = target_depth * target_depth
                duration_limit = z + duration_in_samples
                # oot residuals
                current_stat = float32(fullsum[x] - \
                                       (folded_patched_flux_deviation_corrected[
                                            x, cumsum_right_index]
                                        - folded_patched_flux_deviation_corrected[x, cumsum_left_index]))
                # average flux error within window
                avg_inverse_squared_patched_folded_dy = (inverse_squared_patched_folded_dy[x, duration_limit]
                                                         - inverse_squared_patched_folded_dy[x, z]) / \
                                                        duration_in_samples
                # window_stat = sum((pf + lc_arr * dep) ** 2) = sum(pf ** 2 + lcarr ** 2 * dep ** 2 + 2 * pf * lcarr * dep) =
                # sum(pf ** 2) + sum(lcarr ** 2 * dep ** 2) + sum(2 * pdf * lcarr * dep) =
                # sum(pf ** 2) + sum(lcarr ** 2 * dep ** 2) + 2 * dept * sum(pdf * lcarr)

                # window_stat = 0
                # for index_width in range(z, duration_limit):
                #     window_stat = window_stat + \
                #                   (patched_flux[x, index_width] + (lc_arr[y][index_width - z] * target_depth)) ** 2
                # current_stat = current_stat + window_stat * avg_inverse_squared_patched_folded_dy

                # window_stat = 0
                # for index_width in range(z, duration_limit):
                #     window_stat = window_stat + \
                #                   patched_flux[x, index_width] ** 2 + \
                #                   (lc_arr[y][index_width - z] * target_depth) ** 2 + \
                #                   2 * patched_flux[x, index_width] * lc_arr[y][index_width - z] * target_depth
                # current_stat = current_stat + window_stat * avg_inverse_squared_patched_folded_dy
                stat1 = float32(0)
                for index_width in range(z, duration_limit):
                    stat1 = stat1 + patched_flux[x, index_width] * lc_arr[y, index_width - z]
                current_stat = current_stat + avg_inverse_squared_patched_folded_dy * (
                        (patched_flux_pow[x, duration_limit - 1] - patched_flux_pow[x, z - 1]) +
                        lc_arr_pow[y, duration_in_samples - 1] * target_depth_pow +
                        2 * target_depth * stat1
                )
                if current_stat < cuda.atomic.min(residuals_data, (x, 0), current_stat):
                    residuals_data[x, 1] = y
                    residuals_data[x, 2] = 1 - target_depth

@cuda.jit(fastmath=True)
def gpu_residuals_per_period(x, patched_flux, patched_flux_pow, folded_patched_flux_deviation_corrected,
                  inverse_squared_patched_folded_dy,
                  periods_durations_in_samples, fullsum, folded_running_means, overshoots,
                  lc_arr, lc_arr_pow, residuals_data):
    z, y, d = cuda.grid(3)
    if x < patched_flux.shape[0] and y < periods_durations_in_samples.shape[1]:
        duration_in_samples = periods_durations_in_samples[x][y]
        if duration_in_samples > 0 and z > 0 and z < patched_flux.shape[1] - duration_in_samples:
            cumsum_left_index = z - 1
            cumsum_right_index = cumsum_left_index + duration_in_samples
            mean = 1 - ((folded_running_means[x, cumsum_right_index] -
                         folded_running_means[x, cumsum_left_index]) / float32(duration_in_samples))
            # xth_point = 1  # How many cadences the template shifts forward in each step
            # if duration_in_samples > T0_FIT_MARGIN:
            xth_point = int(duration_in_samples * T0_FIT_MARGIN)
            if xth_point < 1:
                xth_point = 1
            if mean > TRANSIT_DEPTH_MIN and z % xth_point == 0:
                target_depth = mean * overshoots[y]
                target_depth_pow = target_depth * target_depth
                duration_limit = z + duration_in_samples
                current_stat = float32(fullsum[x] - \
                                       (folded_patched_flux_deviation_corrected[
                                            x, cumsum_right_index]  # subtracting residuals from oot
                                        - folded_patched_flux_deviation_corrected[x, cumsum_left_index]))
                avg_inverse_squared_patched_folded_dy = (inverse_squared_patched_folded_dy[
                                                             x, duration_limit]  # subtracting residuals from oot
                                                         - inverse_squared_patched_folded_dy[
                                                             x, z]) / duration_in_samples
                # window_stat = sum((pf + lc_arr * dep) ** 2) = sum(pf ** 2 + lcarr ** 2 * dep ** 2 + 2 * pf * lcarr * dep) =
                # sum(pf ** 2) + sum(lcarr ** 2 * dep ** 2) + sum(2 * pdf * lcarr * dep) =
                # sum(pf ** 2) + sum(lcarr ** 2 * dep ** 2) + 2 * dept * sum(pdf * lcarr)

                # window_stat = 0
                # for index_width in range(z, duration_limit):
                #     window_stat = window_stat + \
                #                   (patched_flux[x, index_width] + (lc_arr[y][index_width - z] * target_depth)) ** 2
                # current_stat = current_stat + window_stat * avg_inverse_squared_patched_folded_dy

                # window_stat = 0
                # for index_width in range(z, duration_limit):
                #     window_stat = window_stat + \
                #                   patched_flux[x, index_width] ** 2 + \
                #                   (lc_arr[y][index_width - z] * target_depth) ** 2 + \
                #                   2 * patched_flux[x, index_width] * lc_arr[y][index_width - z] * target_depth
                # current_stat = current_stat + window_stat * avg_inverse_squared_patched_folded_dy
                stat1 = float32(0)
                for index_width in range(z, duration_limit):
                    stat1 = stat1 + patched_flux[x, index_width] * lc_arr[y, index_width - z]
                current_stat = current_stat + avg_inverse_squared_patched_folded_dy * (
                        (patched_flux_pow[x, duration_limit - 1] - patched_flux_pow[x, z - 1]) +
                        lc_arr_pow[y, duration_in_samples - 1] * target_depth_pow +
                        2 * target_depth * stat1
                )
                if current_stat < cuda.atomic.min(residuals_data, (x, 0), current_stat):
                    residuals_data[x, 0] = current_stat
                    residuals_data[x, 1] = y
                    residuals_data[x, 2] = 1 - target_depth

    def final_T0_fit(self, signal, depth, t, y, dy, period, T0_fit_margin, show_progress_bar):
        dur = len(signal)
        scale = tls_constants.SIGNAL_DEPTH / (1 - depth) if depth >= 0 else tls_constants.SIGNAL_DEPTH / (1 + depth)
        signal = [1 - ((1 - value) / scale) if value <= 1 else 1 + ((value - 1) / scale) for value in signal]
        samples_per_period = numpy.size(y)

        if T0_fit_margin == 0:
            points = samples_per_period
        else:
            step_factor = T0_fit_margin * dur
            points = int(samples_per_period / step_factor)
        if points > samples_per_period:
            points = samples_per_period

        # Create all possible T0s from the start of [t] to [t+period] in [samples] steps
        T0_array = numpy.linspace(
            start=numpy.min(t), stop=numpy.min(t) + period, num=points
        )

        # Avoid showing progress bar when expected runtime is short
        if points > tls_constants.PROGRESSBAR_THRESHOLD and show_progress_bar:
            show_progress_info = True
        else:
            show_progress_info = False

        residuals_lowest = float("inf")
        T0 = 0

        if show_progress_info:
            print("Searching for best T0 for period", format(period, ".5f"), "days")
            pbar2 = tqdm(total=numpy.size(T0_array))
        signal_ootr = numpy.ones(len(y[dur:]))

        # Future speed improvement possible: Add multiprocessing. Will be slower for
        # short data and T0_FIT_MARGIN > 0.01, but faster for large data with dense
        # sampling (T0_FIT_MARGIN=0)
        for Tx in T0_array:
            phases = fold(time=t, period=period, T0=Tx)
            sort_index = numpy.argsort(phases, kind="mergesort")  # 75% of CPU time
            phases = phases[sort_index]
            flux = y[sort_index]
            dy = dy[sort_index]

            # Roll so that the signal starts at index 0
            # Numpy roll is slow, so we replace it with less elegant concatenate
            # flux = numpy.roll(flux, roll_cadences)
            # dy = numpy.roll(dy, roll_cadences)
            roll_cadences = int(dur / 2) + 1
            flux = numpy.concatenate([flux[-roll_cadences:], flux[:-roll_cadences]])
            dy = numpy.concatenate([flux[-roll_cadences:], flux[:-roll_cadences]])

            residuals_intransit = numpy.sum((flux[:dur] - signal) ** 2 / dy[:dur] ** 2)
            residuals_ootr = numpy.sum((flux[dur:] - signal_ootr) ** 2 / dy[dur:] ** 2)
            residuals_total = residuals_intransit + residuals_ootr

            if show_progress_info:
                pbar2.update(1)
            if residuals_total < residuals_lowest:
                residuals_lowest = residuals_total
                T0 = Tx
        if show_progress_info:
            pbar2.close()
        return T0
