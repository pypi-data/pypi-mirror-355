"""Weight mesh class and functions."""

from __future__ import annotations

from typing import TYPE_CHECKING, NamedTuple, TextIO

import sys

from dataclasses import dataclass
from enum import IntEnum

import numpy as np

import mckit_meshes.mesh.geometry_spec as gs
from mckit_meshes.utils import print_n

if TYPE_CHECKING:
    # noinspection PyCompatibility
    from collections.abc import Generator, Iterable

    from numpy.typing import ArrayLike

GeometrySpec = gs.CartesianGeometrySpec | gs.CylinderGeometrySpec
Point = np.ndarray


def ensure_float_arrays(*arrays: ArrayLike) -> Generator[np.ndarray]:
    yield from (np.asarray(x, dtype=float) for x in arrays)


class Particles(IntEnum):
    """Particle kind enum."""

    neutron = 0
    photon = 1
    n = 0
    p = 1


# noinspection GrazieInspection,PyUnresolvedReferences
class WgtMesh:
    """Class to work with MCNP weight window files."""

    def __init__(
        self,
        geometry_spec: GeometrySpec,
        energies,
        weights,
    ):
        self._energies: list[np.ndarray] = list(ensure_float_arrays(*energies))
        self._geometry_spec = geometry_spec
        self._weights: list[np.ndarray] = list(ensure_float_arrays(*weights))
        self.validate()

    def print_mcnp_generator_spec(self, io=None, ref="600 0 50", columns: int = 6) -> None:
        if io is None:
            io = sys.stdout
        print(f"mesh   ref={ref}", file=io)
        self._geometry_spec.print_specification(io, columns=columns)
        print("wwge:n", end=" ", file=io)
        second_indent = " " * 15
        print_n(
            gs.format_floats(self.energies[0][1:]),
            io=io,
            indent=second_indent,
            max_columns=columns,
        )
        if len(self.energies) > 1:
            print("wwge:p", end=" ", file=io)
            print_n(
                gs.format_floats(self.energies[1][1:]),
                io=io,
                indent=second_indent,
                max_columns=columns,
            )

    def print_meshtal_spec(
        self,
        io: TextIO | None = None,
        tally_n_number: int = 14,
        tally_p_number: int = 24,
        columns: int = 6,
    ) -> None:
        if io is None:
            io = sys.stdout
        print(f"fc{tally_n_number}    === WW generation mesh for neutrons", file=io)
        print(f"fmesh{tally_n_number}:n", file=io)
        self._geometry_spec.print_specification(io, columns=columns)
        indent = " " * 8
        print(indent, "emesh=", sep="", end="", file=io)
        second_indent = indent + " " * 6
        print_n(
            gs.format_floats(self.energies[0][1:]),
            io=io,
            indent=second_indent,
            max_columns=columns,
        )
        if len(self.energies) > 1:
            print(f"fc{tally_p_number}    === WW generation mesh for photons", file=io)
            print(f"fmesh{tally_p_number}:p", file=io)
            self._geometry_spec.print_specification(io, columns=columns)
            print(indent, "emesh=", sep="", end="", file=io)
            # TODO dvp: try to use do_print_bins here
            print_n(
                gs.format_floats(self.energies[1][1:]),
                io=io,
                indent=second_indent,
                max_columns=columns,
            )

    def validate(self) -> None:
        if len(self.weights) != len(self.energies):
            msg = (
                f"Number of energy bins {len(self.energies)} is not equal "
                f"to number of weight parts {len(self.weights)}"
            )
            raise ValueError(msg)
        for part, ebins in enumerate(self.energies):
            # noinspection PyUnresolvedReferences
            expected_shape = (
                ebins.size - 1,
                self.ibins.size - 1,
                self.jbins.size - 1,
                self.kbins.size - 1,
            )
            if self.weights[part].shape != expected_shape:
                msg = (
                    f"Incompatible number of ebins, voxels and weights: {self.weights[part].shape} "
                    "!= {expected_shape}"
                )
                raise ValueError(msg)

    @property
    def energies(self) -> list[ArrayLike]:
        return self._energies

    @property
    def origin(self) -> ArrayLike:
        return self._geometry_spec.origin

    @property
    def ibins(self) -> ArrayLike:
        return self._geometry_spec.ibins

    @property
    def jbins(self) -> ArrayLike:
        return self._geometry_spec.jbins

    @property
    def kbins(self) -> ArrayLike:
        return self._geometry_spec.kbins

    @property
    def count_voxels(self) -> int:
        return (self.ibins.size - 1) * (self.jbins.size - 1) * (self.kbins.size - 1)

    @property
    def weights(self) -> list[np.ndarray]:
        return self._weights

    @property
    def neutron_weights(self) -> np.ndarray:
        return self._weights[0]

    @property
    def photon_weights(self) -> np.ndarray:
        assert len(self._weights) == 2, "Photon weights are not defined in the mesh"
        return self._weights[1]

    @property
    def is_cylinder(self) -> bool:
        return self._geometry_spec.cylinder

    @property
    def axs(self) -> np.ndarray | None:
        return self._geometry_spec.axs

    @property
    def vec(self) -> np.ndarray | None:
        return self._geometry_spec.vec

    @property
    def count_parts(self) -> int:
        return len(self.weights)

    def part(self, particle: Particles) -> tuple[np.ndarray, np.ndarray]:
        return self.energies[particle], self.weights[particle]

    def __hash__(self):
        return hash(
            (
                self._geometry_spec.__hash__(),
                self.energies,
                self.weights,
            ),
        )

    def __eq__(self, other):
        if not self.bins_are_equal(other):
            return False
        for p in range(len(self.weights)):
            if not np.array_equal(self.weights[p], other.weights[p]):
                return False
        return True

    def bins_are_equal(self, other: WgtMesh) -> bool:
        if not isinstance(other, WgtMesh):
            msg = f"Invalid class of object to compare: {other.__class__}"
            raise TypeError(msg)
        if self._geometry_spec == other.geometry_spec:
            le = len(self.energies)
            if le == len(other.energies):
                return all(np.array_equal(self.energies[i], other.energies[i]) for i in range(le))
        return False

    def __add__(self, other) -> WgtMesh:
        assert self.bins_are_equal(other)
        weights = [a + b for a, b in zip(self.weights, other.weights, strict=False)]
        return WgtMesh(
            self._geometry_spec,
            self.energies,
            weights,
        )

    def __sub__(self, other) -> WgtMesh:
        assert self.bins_are_equal(other)
        weights = [a - b for a, b in zip(self.weights, other.weights, strict=False)]
        return WgtMesh(
            self._geometry_spec,
            self.energies,
            weights,
        )

    def __mul__(self, coeff: float) -> WgtMesh:
        weights = [w * coeff for w in self.weights]
        return WgtMesh(
            self._geometry_spec,
            self.energies,
            weights,
        )

    def __rmul__(self, coeff: float) -> WgtMesh:
        return self.__mul__(coeff)

    # def __repr__(self):

    # noinspection SpellCheckingInspection
    def write(self, stream: TextIO) -> None:
        """Writes the mesh to stream.

        See WWINP format, MCNP User Manual, Appendix J, Table J.1

        Args;
            stream: a stream to write to
        """
        data = []
        _if, _iv, _ni = 1, 1, len(self.energies)
        _nr = 16 if self.is_cylinder else 10
        data += produce_strings([_if, _iv, _ni, _nr], "{0:10d}")
        # remove the first "\n"
        data = data[1:]

        _ne = [x.size - 1 for x in self._energies]
        data += produce_strings(_ne, "{0:10d}")
        _nfx = self.ibins.size - 1
        _nfy = self.jbins.size - 1
        _nfz = self.kbins.size - 1
        _x0, _y0, _z0 = self.origin
        _nfmx, _xm = gs.compute_intervals_and_coarse_bins(self.ibins)
        _ncx = len(_nfmx)
        _nfmy, _ym = gs.compute_intervals_and_coarse_bins(self.jbins)
        _ncy = len(_nfmy)
        _nfmz, _zm = gs.compute_intervals_and_coarse_bins(self.kbins)
        _ncz = len(_nfmz)
        _nwg = 1
        _data = [_nfx, _nfy, _nfz, _x0, _y0, _z0, _ncx, _ncy, _ncz]
        if self.is_cylinder:
            if self.axs is None:
                msg = "axs is not specified in cylinder mesh"
                raise ValueError(msg)
            _xmax, _ymax, _zmax = self.axs
            if self.vec is None:
                msg = "vec is not specified in cylinder mesh"
                raise ValueError(msg)
            _xr, _yr, _zr = self.vec
            _data += [_xmax, _ymax, _zmax, _xr, _yr, _zr]
            _nwg = 2
        _data += [_nwg]
        data += produce_strings(_data, "{0:#13.5g}")
        # Block 2
        _nc = [_ncx, _ncy, _ncz]
        _nfm = [_nfmx, _nfmy, _nfmz]
        _r = [_xm, _ym, _zm]
        for i in range(3):
            data1 = [_r[i][0]]
            for j in range(_nc[i]):
                data1 += [_nfm[i][j], _r[i][j + 1], 1]
            data += produce_strings(data1, "{0:#13.5g}")
        for p in range(_ni):
            w = self._weights[p]
            data += produce_strings(self.energies[p][1:], "{0:#13.5g}")  # omit the first zero
            data1 = [
                w[e, i, j, k]
                for e in range(_ne[p])
                for k in range(_nfz)
                for j in range(_nfy)
                for i in range(_nfx)
            ]
            data += produce_strings(data1, "{0:#13.5g}")
        stream.write("".join(data))

    @dataclass
    class _Reader:
        data: list[str]
        index: int = 0

        def get(self, items: int) -> list[str]:
            i = self.index
            self.index += items
            return self.data[i : self.index]

        def get_floats(self, items: int) -> Iterable[float]:
            return map(float, self.get(items))

        def get_ints(self, items: int) -> Iterable[int]:
            return map(int, self.get(items))

        def get_ints_written_as_floats(self, items: int) -> Iterable[int]:
            return map(int, self.get_floats(items))

        def skip(self, items: int = 1) -> None:
            self.index += items

    # noinspection SpellCheckingInspection
    @classmethod
    def read(cls, f: TextIO) -> WgtMesh:
        """Read an MCNP weights file.

        See format description at MCNP User Manual, Version 5 (p.489 or Appendix J, p. J-1)

        Args:
            f: Input file in WWINP format

        Returns:
            WgtMesh: loaded mesh.
        """
        _if, _iv, number_of_particles, number_of_parameters = (
            int(s) for s in f.readline().split()[:4]
        )

        reader = WgtMesh._Reader(f.read().split())
        sizes_of_energy_bins = tuple(reader.get_ints(number_of_particles))

        # cells along axes
        _nfx, _nfy, _nfz = reader.get_ints_written_as_floats(3)

        # origin
        _x0, _y0, _z0 = reader.get_floats(3)

        # coarse bins along axes
        _ncx, _ncy, _ncz = reader.get_ints_written_as_floats(3)
        if number_of_parameters == 16:
            _xmax, _ymax, _zmax, _xr, _yr, _zr = reader.get_floats(6)
            axs = np.array([_xmax, _ymax, _zmax], dtype=float)
            vec = np.array([_xr, _yr, _zr], dtype=float)
        else:
            axs = None
            vec = None

        # skip NWG
        reader.skip()

        delta = 3 * _ncx + 1
        _x = parse_coordinates(reader.get(delta))

        delta = 3 * _ncy + 1
        _y = parse_coordinates(reader.get(delta))

        delta = 3 * _ncz + 1
        _z = parse_coordinates(reader.get(delta))

        _e = []
        _w = []

        for p in range(number_of_particles):
            nep = sizes_of_energy_bins[p]
            if nep > 0:
                ebins = np.fromiter(reader.get_floats(nep), dtype=float)
                ebins = np.insert(ebins, 0, 0.0)
                _e.append(ebins)
                _wp = np.zeros((nep, _nfx, _nfy, _nfz), dtype=float)
                _wp_data = np.fromiter(reader.get_floats(_wp.size), dtype=float)
                for e in range(nep):
                    for k in range(_nfz):
                        for j in range(_nfy):
                            for i in range(_nfx):
                                cell_index = i + _nfx * (j + _nfy * (k + _nfz * e))
                                _wp[e, i, j, k] = _wp_data[cell_index]
                _w.append(_wp)
                assert np.all(
                    np.transpose(_wp_data.reshape((nep, _nfz, _nfy, _nfx)), (0, 3, 2, 1)) == _wp,
                )
        geometry_spec = make_geometry_spec(_x, _y, _z, [_x0, _y0, _z0], axs=axs, vec=vec)
        return cls(geometry_spec, _e, _w)

    def get_mean_square_distance_weights(self, point) -> WgtMesh:
        w = self._geometry_spec.get_mean_square_distance_weights(point)
        _w = []
        for _e in self.energies:
            le = len(_e)
            t = w.reshape((1, *self._geometry_spec.bins_shape))
            t = np.repeat(t, le, axis=0)
            _w.append(t)
        return WgtMesh(
            self._geometry_spec,
            self.energies,
            _w,
        )

    class MergeSpec(NamedTuple):
        wm: WgtMesh
        nps: int

    @classmethod
    def merge(cls, *merge_specs: MergeSpec | tuple[WgtMesh, int]) -> MergeSpec:
        r"""Combine weight meshes produced from different runs with weighting factor.

        Note:
            Importance of a mesh voxel `i` is $1/w_i$ and is proportional
            to average portion $p_i$ of passing particle weight W to a tally,
            for which the weight mesh is computed.
            To obtain combined weight on merging two meshes,
            we will combine the probabilities using weighting factors and
            use reciprocal of a result as a resulting weight of mesh voxel.
            The weighting factors are usually NPS (Number particles sampled)
            from a run on which a mesh was produced.

            The combined probability in resulting voxel `i` is:

            .. math::

                w_ij - weight in voxel i of mesh j
                n_j -  nps - weighting factor on combining of mesh j

                p_ij = 1/w_ij - probability for voxel i of mesh j

                p_i = \frac{ \sum_j{n_j*p_ij} { \sum_j{n_j} }

            So, the resulting voxel `i` weight level is:

            .. math::
                w_i = \frac{1} {p_i}


        Args:
            merge_specs: iterable of pairs (WgtMesh, nps), where `nps` is weighting factor

        Returns:
            MergeSpec: merged weights and total nps (or sum of weighting factors)



        """
        first = merge_specs[0]

        if not isinstance(first, WgtMesh.MergeSpec):
            first = WgtMesh.MergeSpec(*first)  # convert tuple to MergeSpec

        if len(merge_specs) > 1:
            second = WgtMesh.merge(*merge_specs[1:])
            merged_weights = []
            assert first.wm.bins_are_equal(second.wm)
            for i, weights in enumerate(first.wm.weights):
                nps_first, probabilities_first = prepare_probabilities_and_nps(first.nps, weights)
                nps_second, probabilities_second = prepare_probabilities_and_nps(
                    second.nps,
                    second.wm.weights[i],
                )
                nps = np.array(nps_first + nps_second, dtype=float)
                combined_probabilities = (
                    nps_first * probabilities_first + nps_second * probabilities_second
                ) * reciprocal(nps)
                merged_weights.append(reciprocal(combined_probabilities))
            wm = first.wm
            return WgtMesh.MergeSpec(
                cls(
                    wm.geometry_spec,
                    wm.energies,
                    merged_weights,
                ),
                first.nps + second.nps,
            )

        return first

    def reciprocal(self) -> WgtMesh:
        """Invert weights values.

        To be used for anti-forward method of weight generation.

        Returns:
        -------
        out:
            Reciprocal of this weights
        """
        return WgtMesh(self._geometry_spec, self.energies, list(map(reciprocal, self.weights)))

    def normalize(
        self,
        normalization_point: Point,
        normalized_value: float = 1.0,
        energy_bin=-1,
    ) -> WgtMesh:
        """Scale weights to have value `value` at `normalisation_point`.

        All other voxels are scaled proportionally.

        Args:
            normalization_point:  Coordinates of point where the weights should equal `value`.
            normalized_value: The value which should be at `normalization_point`
            energy_bin: index of energy bin at which set normalized value, default - the last one.

        Returns:
            New normalized weights.
        """
        _gs = self._geometry_spec
        x, y, z = normalization_point
        ix, iy, iz = _gs.select_indexes(i_values=x, j_values=y, k_values=z)

        value_at_normalisation_point = self.weights[0][energy_bin, ix, iy, iz]
        """The value at last energy bin about 20 MeV at neutron weights."""

        factor = normalized_value / value_at_normalisation_point
        """Scale all other weights by this value."""

        new_weights = [w * factor for w in self.weights]
        # TODO @dvp: revise for multiple energy bins,
        #           may be add scaling values for each energy bin and particle

        return WgtMesh(_gs, self.energies, new_weights)

    def invert(self, normalization_point: Point, normalized_value: float = 1.0) -> WgtMesh:
        """Get reciprocal of self weights and normalize to 1 at given point.

        Important:
            A caller specifies normalization_point in local coordinates.
            See :class:`GeometrySpec.local_coordinates`.

        Args:
            normalization_point: Point at which output weights should be 1
            normalized_value: value which should be set at `normalization_point`.

        Returns:
            WgtMesh: Normalized reciprocal of self weights.
        """
        return self.reciprocal().normalize(normalization_point, normalized_value)

    @property
    def geometry_spec(self) -> GeometrySpec:
        return self._geometry_spec

    def drop_lower_energies(self, min_energy: float, part: int = 0) -> WgtMesh:
        if len(self.energies) <= part:
            msg = f"invalid value for weights object part: {part}"
            raise ValueError(msg)
        energies = self.energies[part]
        energies_to_retain = min_energy <= energies
        energies_to_retain[0] = True
        if np.all(energies_to_retain):
            return self
        new_energies = []
        new_weights = []
        for i in range(len(self.energies)):
            if i == part:
                new_energies.append(self.energies[i][energies_to_retain])
                new_weights.append(self.weights[i][energies_to_retain[1:], :, :, :])
            else:
                new_energies.append(self.energies[i])
                new_weights.append(self.weights[i])
        return WgtMesh(self._geometry_spec, new_energies, new_weights)


def reciprocal(a: np.ndarray, zero_index: np.ndarray | None = None) -> np.ndarray:
    if a.dtype != float:
        a = np.array(a, dtype=float)
    if zero_index is None:
        zero_index = a == 0.0
    else:
        assert np.array_equal(zero_index, a == 0.0)
    result: np.ndarray = np.reciprocal(a, where=np.logical_not(zero_index))
    # this fixes bug in numpy reciprocal: it doesn't pass zero values
    # note: the bug doesn't show up on debugging
    result[zero_index] = 0.0
    return result


def prepare_probabilities_and_nps(_nps: int, _weights: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Computes intermediate data for merging procedure.

    The probabilities are reciprocals to weights.
    Zero weights mean zero probabilities and don't affect the merged result.

    Args:
        _nps:
            weighting multiplier
        _weights:
            weights to convert to probabilities
    Returns:
        normalization factors and probabilities
    """
    nps_array = np.full_like(_weights, _nps, dtype=int)
    zero_index = _weights == 0.0
    probabilities = reciprocal(_weights, zero_index=zero_index)
    nps_array[zero_index] = 0  # voxels with zero weight don't affect weighted sum
    return nps_array, probabilities


def produce_strings(stream, format_spec) -> list[str]:
    data = []
    for i in range(len(stream)):
        if i % 6 == 0:
            data.append("\n")
        data.append(format_spec.format(stream[i]))
    return data


def parse_coordinates(inp: list[str]) -> np.ndarray:
    def iter_over_coarse_mesh() -> Generator[tuple[float, int], None, None]:
        is_first = True
        i = 0
        length = len(inp)
        while i < length:
            coordinate = float(inp[i])
            if is_first:
                i += 1
                is_first = False
            else:
                i += 2
            if length <= i:
                yield coordinate, 1
                break
            else:
                fine_bins = int(float(inp[i]))
                i += 1
            yield coordinate, fine_bins

    def iter_over_fine_mesh(_iter_over_coarse_mesh) -> Generator[float, None, None]:
        prev_coordinate: float | None = None
        prev_fine_bins: int | None = None
        for coordinate, fine_bins in _iter_over_coarse_mesh:
            if prev_fine_bins == 1:
                if prev_coordinate is None:
                    raise ValueError("Invalid mesh spec")
                yield prev_coordinate
            elif prev_coordinate is not None:
                if prev_fine_bins is None:
                    raise ValueError("Invalid mesh spec")
                res = np.linspace(
                    prev_coordinate,
                    coordinate,
                    prev_fine_bins + 1,
                    endpoint=True,
                    dtype=float,
                )
                yield from res[:-1]
            prev_coordinate = coordinate
            prev_fine_bins = fine_bins
        yield prev_coordinate

    return np.fromiter(iter_over_fine_mesh(iter_over_coarse_mesh()), dtype=float)


def make_geometry_spec(ibins, jbins, kbins, origin=None, axs=None, vec=None) -> GeometrySpec:
    """Make Cartesian or Cylinder geometry specification from with given parameters.

    The parameters are converted to numpy arrays.

    Args:
        ibins:  X or R bins
        jbins:  Y or Z bins
        kbins:  Z or Theta bins
        origin: origin point
        axs:    Cylinder mesh axis
        vec:    Cylinder mesh angle reference vector

    Returns:
        spec - new geometry specification
    """
    origin, ibins, jbins, kbins = (
        np.asarray(x, dtype=float) for x in (origin, ibins, jbins, kbins)
    )
    if axs is None:
        geometry_spec = gs.CartesianGeometrySpec(ibins, jbins, kbins)
        if origin is not None and not np.array_equal(origin, geometry_spec.origin):
            msg = "Incompatible cartesian bins and origin"
            raise ValueError(msg)
    else:
        axs, vec = map(np.asarray, [axs, vec])
        geometry_spec = gs.CylinderGeometrySpec(
            ibins,
            jbins,
            kbins,
            origin=origin,
            axs=axs,
            vec=vec,
        )
    return geometry_spec
