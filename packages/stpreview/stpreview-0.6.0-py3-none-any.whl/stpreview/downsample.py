from pathlib import Path
from typing import Optional, Union

import asdf
import numpy
from skimage.measure import block_reduce

OBSERVATORIES = ["roman", "jwst"]


def known_asdf_observatory(input: Path, known: Optional[list[str]] = None) -> str:
    """
    find which observatory key exists in the given ASDF file

    :param input: ASDF file
    :param known: list of known observatory keys
    :returns: first observatory to be found in the file
    """

    if known is None:
        known = OBSERVATORIES

    with asdf.open(input, memmap=True) as file:
        for name in known:
            if name in file:
                return name
        else:
            raise KeyError(
                f"no known observatory found in file (out of {OBSERVATORIES})"
            )


def downsample_asdf_by(
    input: Path,
    factor: Union[int, tuple[int, ...]],
    func=numpy.nanmean,
    observatory: Optional[str] = None,
) -> numpy.ndarray:
    """
    downsample an ASDF image by the specified factor

    :param input: ASDF file with 2D image data
    :param factor: factor by which to downsample image resolution
    :param func: aggregation function to pass to `skimage.measure.block_reduce`
    :param observatory: space telescope to use
    :returns: downsampled image array
    """

    if observatory is None:
        observatory = known_asdf_observatory(input)

    with asdf.open(input, memmap=True) as file:
        data = file[observatory]["data"]

        # if error array is present, set nodata values to NaN
        if "err" in file[observatory]:
            err = file[observatory]["err"]
            data = numpy.where(~numpy.isfinite(err) | (err <= 0), numpy.nan, data)

        block_size: list[int] = list(data.shape)
        if isinstance(factor, int):
            block_size[-2] = factor
            block_size[-1] = factor
        else:
            block_size[-2] = factor[-2]
            block_size[-1] = factor[-1]

        # for index, dimension in enumerate(data.shape):
        #     if dimension % block_size[index] != 0:
        #         raise RuntimeError(f"{by} is not an even factor of {data.shape}")

        return block_reduce(data, block_size=tuple(block_size), func=func)


def downsample_asdf_to(
    input: Path,
    shape: tuple[int, int],
    func=numpy.nanmean,
    observatory: Optional[str] = None,
) -> numpy.ndarray:
    """
    attempt to downsample an ASDF image to (near) the specified resolution

    :param input: ASDF file with 2D image data
    :param shape: resolution to which to downsample
    :param func: aggregation function to pass to `skimage.measure.block_reduce`
    :param observatory: space telescope to use
    :returns: downsampled image array
    """

    if observatory is None:
        observatory = known_asdf_observatory(input)

    with asdf.open(input, memmap=True) as file:
        original_shape = file[observatory]["data"].shape

    factor = tuple(
        numpy.ceil(numpy.array(original_shape) / numpy.array(shape)).astype(int)
    )

    return downsample_asdf_by(input=input, factor=factor, func=func)
