"""Functions for rebinning histogram-like distributions."""

# TODO @dvp: implement propagation in result the indexes computed on shrink
#            for reuse in FMesh.shrink for equivalent grids or alike
from __future__ import annotations

from typing import TYPE_CHECKING, Any

import collections.abc
import gc
import itertools
from multiprocessing import Pool

import numpy as np

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

    from numpy.typing import ArrayLike, NDArray

    ArrayFloat = NDArray[Any, float]


__all__ = [
    "interpolate",
    "is_monotonically_increasing",
    "rebin_1d",
    "rebin_nd",
    "rebin_spec_composer",
    "shrink_1d",
    "shrink_nd",
    "trim_spec_composer",
]

__revision__ = "$Id$"

__ZERO = np.array([0.0], dtype=float)
__EXTERNAL_PROCESS_THRESHOLD = 1000000


# noinspection PyTypeChecker
def is_monotonically_increasing(a: NDArray) -> bool:
    # noinspection PyUnresolvedReferences
    if not a.size:
        return False
    iterator = iter(a)
    prev = next(iterator)
    for val in iterator:
        if prev < val:
            prev = val
        else:
            return False
    return True


# noinspection PyUnresolvedReferences
def set_axis(indices: ArrayLike, axis: int, a_shape: Sequence[int]) -> ArrayLike:
    shape = [1] * len(a_shape)
    shape[axis] = a_shape[axis]
    return indices.reshape(tuple(shape))


# noinspection PyUnresolvedReferences,PyTypeChecker
def interpolate(
    x_new: ArrayFloat, x: ArrayFloat, y: ArrayFloat, axis: int | None = None
) -> ArrayFloat:
    if y.ndim == 1:
        return np.interp(x_new, x, y)

    if axis is None:
        axis = 0

    x_new_indices = np.digitize(x_new, x)
    x_new_indices = x_new_indices.clip(1, len(x) - 1).astype(int)  # TODO @dvp: why astype?
    lo = x_new_indices - 1
    hi = x_new_indices
    x_lo = x[lo]
    deltas = x[hi] - x_lo
    nd = y.ndim
    slice1 = [slice(None)] * nd  # TODO @dvp: suspicious usage of slice duplicates
    slice2 = [slice(None)] * nd
    slice1[axis] = lo
    slice2[axis] = hi
    slice1 = tuple(slice1)
    slice2 = tuple(slice2)
    y_lo = y[slice1]
    y_deltas = y[slice2] - y_lo
    deltas = set_axis(deltas, axis, y_deltas.shape)
    slope = y_deltas / deltas
    new_deltas = x_new - x_lo
    new_deltas = set_axis(new_deltas, axis, slope.shape)
    return slope * new_deltas + y_lo


# noinspection PyUnresolvedReferences
def rebin_1d(
    a: np.ndarray,
    bins: np.ndarray,
    new_bins: np.ndarray,
    axis: int = 0,
    *,
    grouped: bool = False,
    assume_sorted: bool = False,
) -> np.ndarray:
    """Transforms 1-D histogram defined as `data` on the limiting points.

    define like `bins` to equivalent (see the terms below) histogram defined
    on other limiting points defined as `new_bins`.

    Notes:
        The algorithm maintains the equality of integral on intervals defined on
        new_bins for the original and rebinned distributions.

    Args:
        a: The array to rebin
        bins: Defines 1-D array representing `a` binning along the given `axis
        new_bins:  The new binning required.
        axis: int, optional
            An axis along which to rebin array `a`
        grouped: bool, optional
            Defines the approach for rebinning.

            - If `True`, then the values in `a` represent the data already
               integrated over bins, like in energy group distributions.
               On rebinning maintain equivalence of integral over same
               energy range in old and new bins.
            - If `False` (default), as for spatial binning - maintain the same
              average value in the same volume in old and new bins.
        assume_sorted: bool, optional
            If True, then skip assertion of bins sorting order,
            by default False - asserts the input_file data

    Returns:
        rebinned data
    """
    assert bins[0] <= new_bins[0], (
        "Rebinning doesn't provide extrapolation lower of the original bins"
    )
    assert new_bins[-1] <= bins[-1], (
        "Rebinning doesn't provide extrapolation upper of the original bins"
    )
    assert bins.size == a.shape[axis] + 1, (
        "The `a` array shape doesn't match the given bins and axis"
    )
    assert assume_sorted or is_monotonically_increasing(bins)
    assert assume_sorted or is_monotonically_increasing(new_bins)

    ndim = a.ndim

    if grouped:
        t = a
    else:
        diff = np.diff(bins)
        if ndim > 1:
            diffs_shape = [1] * ndim
            diffs_shape[axis] = a.shape[axis]
            diffs_shape = tuple(diffs_shape)
            diff = diff.reshape(diffs_shape)
        t = a * diff

    cum = np.cumsum(t, axis=axis)
    cum = np.insert(cum, 0, __ZERO, axis=axis)
    rebinned_data = interpolate(new_bins, bins, cum, axis=axis)
    rebinned_data = np.diff(rebinned_data, axis=axis)

    # del cum
    if a.size > __EXTERNAL_PROCESS_THRESHOLD:
        gc.collect()
        del gc.garbage[:]

    if not grouped:
        new_diff = np.diff(new_bins)
        if ndim > 1:
            diffs_shape = [1] * ndim
            diffs_shape[axis] = rebinned_data.shape[axis]
            new_diff = new_diff.reshape(tuple(diffs_shape))
        rebinned_data /= new_diff

    return rebinned_data


def rebin_nd(
    a: NDArray[float],
    rebin_spec: Iterable[tuple[NDArray[float], NDArray[float], int, bool]],
    *,
    assume_sorted: bool = False,
    external_process_threshold: int = __EXTERNAL_PROCESS_THRESHOLD,
) -> NDArray[float]:
    """Rebin an array `a` over multidimensional grid.

    Args:
        a: An array to rebin.
        rebin_spec: Iterator
            An iterator listing tuples specifying  bins, new_bins, axis and
            grouped  parameters for rebinning.
            See :py:func:`rebin_1d` for details on the parameters.
        assume_sorted: bool, optional
            If True skip assertion of bins sorting order,
            by default False - asserts the input_file data
        external_process_threshold: int
            If size of `a` is greater than that, then the computation
            is executed in external process, to achieve immediate memory cleanup.

    Returns:
        Rebinned data.
    """
    if not isinstance(rebin_spec, collections.abc.Iterator):
        rebin_spec = iter(rebin_spec)
    try:
        bins, new_bins, axis, grouped = next(rebin_spec)
    except StopIteration:
        return a

    if a.size > external_process_threshold:
        with Pool(processes=1) as pool:
            recursion_res = pool.apply(
                rebin_nd, args=(a, rebin_spec), kwds={"assume_sorted": assume_sorted}
            )
    else:
        recursion_res = rebin_nd(a, rebin_spec, assume_sorted=assume_sorted)

    res = rebin_1d(
        recursion_res, bins, new_bins, axis, grouped=grouped, assume_sorted=assume_sorted
    )

    del recursion_res
    if a.size > external_process_threshold:
        n = gc.collect()
        if n:
            del gc.garbage[:]

    return res


def rebin_spec_composer(
    bins_seq,
    new_bins_seq,
    axes=None,
    grouped_flags=None,
) -> Iterable[tuple[NDArray[float], NDArray[float], NDArray[float], NDArray[float]]]:
    """Compose rebin_spec parameter.

    See also :py:func:`mckit_meshes.utils.rebin.rebin_nd` with reasonable defaults
    for axes and grouped iterators.

    Args:
        bins_seq: sequence of ndarrays
            Iterates over the list of original bins
        new_bins_seq: sequence of ndarrays
            Iterates over the list of new bins.
        axes: sequence of ints, optional
            Iterates over the list of corresponding axes.
            If not provided (default), then iterates over sequence 0 ... len(bins).
        grouped_flags: sequence of booleans, optional
            Iterates over a sequence of grouped flags.
            If not provided (default),
            then all the axes considered as not grouped.
            If constant boolean value is proved, then for
            all the axes this value is applied.

    Returns:
        Iterator over the sequence of tuples (bins, new_bins, axis, grouped)
    """
    if not axes:
        axes = itertools.count()
    if isinstance(grouped_flags, bool):
        grouped_flags = itertools.repeat(grouped_flags)
    elif not grouped_flags:
        grouped_flags = itertools.repeat(False)
    return zip(bins_seq, new_bins_seq, axes, grouped_flags, strict=False)


# @numba.jit
def shrink_1d(
    a: np.ndarray,
    bins: np.ndarray,
    low: float | None = None,
    high: float | None = None,
    axis: int | None = None,
    *,
    assume_sorted: bool = False,
) -> tuple[np.ndarray, np.ndarray]:
    """Select sub-arrays of a `a` and corresponding `bins` for minimal span.

    of bins, which completely covers the range [`low`...`high`]
    both sides included.

    Args:
        a: ndarray
            An array to shrink.
        bins: ndarray
            Bins corresponding to the grid `a` over the given `axis`.
        low: float, optional
            Left edge of the range to shrink to.
            When omitted, the `bins` left edge is used.
        high: float
            Right edge of the range to shrink to.
            When omitted, the `bins` right edge is used.
        axis: int, optional
            An axis of `a` over which to shrink. Default axis = 0.
        assume_sorted: bool, optional
            If True skip assertion of bins sorting order,
            by default False - asserts the input_file data

    Returns:
        new_bins: ndarray
            The shrank bins
        new_data: ndarray
            The shrank grid
    """
    if low is None and high is None:
        return bins, a

    if axis is None:
        axis = 0

    assert a.shape[axis] == bins.size - 1
    assert assume_sorted or is_monotonically_increasing(bins)

    if low is None:
        low = bins[0]

    if high is None:
        high = bins[-1]

    if low == bins[0] and high == bins[-1]:
        return bins, a

    if low < bins[0] or bins[-1] < low:
        msg = (
            f"Low shrink edge is beyond the bins range: {low:g}"
            f" is not in [{bins[0]:g}..{bins[-1]:g}]",
        )
        raise ValueError(msg)

    if high < bins[0] or bins[-1] < high:
        msg = f"High shrink edge is beyond the bins range: {high} is not in [{bins[0]}..{bins[-1]}]"
        raise ValueError(msg)

    left_idx, right_idx = np.digitize([low, high], bins) - 1

    if left_idx > 0 and bins[left_idx] > low:
        left_idx -= 1

    if right_idx < bins.size - 1 and bins[right_idx] < high:
        right_idx += 1

    if right_idx - left_idx < 1:
        raise ValueError("Shrink results to empty grid")

    if left_idx == 0 and right_idx == bins.size:
        return bins, a

    indices = list(range(left_idx, right_idx + 1))
    new_bins = np.take(bins, indices)
    new_a = np.take(a, indices[:-1], axis=axis)

    return new_bins, new_a


def shrink_nd(
    a: np.ndarray,
    trim_spec: Iterable[tuple[np.ndarray, float, float, int]],
    *,
    assume_sorted: bool = False,
) -> tuple[list[np.ndarray] | None, np.ndarray]:
    """Perform multidimensional shrink.

    Args:
        a: The grid to shrink.
        trim_spec: sequence of tuples (bins, low, high, axis)
        assume_sorted:  If True skip assertion of bins sorting order,
                        by default False - asserts the input_file data

    Returns:
            A sequence with  new bins, if any, the shrunk or initial grid.
    """
    if not isinstance(trim_spec, collections.abc.Iterator):
        trim_spec = iter(trim_spec)
    try:
        bins, left, right, axis = next(trim_spec)
    except StopIteration:
        return None, a
    new_bins_seq, recursed_data = shrink_nd(a, trim_spec, assume_sorted=assume_sorted)
    top_bins, top_data = shrink_1d(
        recursed_data, bins, left, right, axis, assume_sorted=assume_sorted
    )
    new_bins_seq = [top_bins, *new_bins_seq] if new_bins_seq else [top_bins]
    return new_bins_seq, top_data


def trim_spec_composer(
    bins_seq,
    lefts=None,
    rights=None,
    axes=None,
) -> Iterable[tuple[NDArray[float], float, float, int]]:
    """Helps to compose trim_spec parameter in.

    :func:`mckit_meshes.utils.rebin.trim_nd` with
    reasonable defaults for lefts, rights and axes iterators.

    Args:
        bins_seq: sequence of ndarrays
            Iterates over the list of bins associated with a grid to be trimmed.
        lefts: sequence of floats
            Iterates over the list of left edges for trimming.
        rights: sequence of floats
            Iterates over the list of right edges for trimming.
        axes: sequence of ints, optional
            Iterates over the list of corresponding axes.
            If not provided (default), then iterates over sequence 0..len(bins).

    Returns:
        Iterator over the sequence of tuples (bins, lefts, rights, axis)
    """
    if not lefts:
        lefts = itertools.repeat(None)
    if not rights:
        rights = itertools.repeat(None)
    if not axes:
        axes = itertools.count()
    return zip(bins_seq, lefts, rights, axes, strict=False)
