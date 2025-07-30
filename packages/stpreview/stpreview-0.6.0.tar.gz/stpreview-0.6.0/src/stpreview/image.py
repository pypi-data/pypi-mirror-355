from pathlib import Path
from typing import Optional, Union

import astropy
import astropy.visualization
import gwcs
import numpy
from matplotlib import pyplot
from matplotlib.colors import Colormap
from mpl_toolkits.axes_grid1.anchored_artists import AnchoredDirectionArrows


def north_pole_angle(
    wcs: gwcs.WCS,
    pixel: tuple[int, int] = (0, 0),
    ddec: astropy.coordinates.Angle = 0.1 * astropy.units.arcsec,
) -> astropy.coordinates.Angle:
    """
    Computes counterclockwise angle between positive x-axis and sky North.


    :param wcs: world coordinate system of ASDF image
    :param pixel: reference pixel (x,y) in image from which to find angle
    :param ddec: small angular offset for computing direction of North.
        No need to change this value unless pixel is very close to North pole.
    :returns: angle between sky North and pixel coordinate x-axis,
        along tangent line of great circle running through pixel and sky North.
    """

    pixel_coordinate = wcs.pixel_to_world(*pixel)
    pixel_coordinate = pixel_coordinate.transform_to("icrs")
    offset_coordinate = pixel_coordinate.directional_offset_by(
        0.0 * astropy.units.deg, ddec
    )

    north_pixel = numpy.asarray(wcs.world_to_pixel(offset_coordinate))
    distance = north_pixel - numpy.asarray(pixel)

    return astropy.coordinates.Angle(
        numpy.rad2deg(numpy.arctan2(distance[1], distance[0])) * astropy.units.deg
    )


def percentile_normalization(
    data: numpy.ndarray,
    percentile: float,
    stretch: astropy.visualization.BaseStretch = None,
) -> astropy.visualization.ImageNormalize:
    """
    stretch the given data based on the given percentile
    """

    if stretch is None:
        stretch = astropy.visualization.LinearStretch()

    interval = astropy.visualization.PercentileInterval(percentile)
    vmin, vmax = interval.get_limits(data)

    normalization = astropy.visualization.ImageNormalize(
        vmin=vmin, vmax=vmax, stretch=stretch
    )

    return normalization


def write_image(
    data: numpy.ndarray,
    output: Path,
    shape: Optional[tuple[int, int]] = None,
    normalization: Optional[astropy.visualization.ImageNormalize] = None,
    colormap: Optional[Union[str, Colormap]] = None,
    north_arrow_angle: Optional[float] = None,
):
    """
    write data as an image to the given path
    """

    if normalization is None:
        if numpy.any(~numpy.isnan(data)):
            normalization = percentile_normalization(data, percentile=90)

    if colormap is None:
        colormap = "afmhot"

    if shape is None:
        shape = data.shape

    dpi = 100
    figure = pyplot.figure(figsize=numpy.array(shape) / dpi)
    axis = figure.add_subplot(1, 1, 1)
    axis.imshow(data, norm=normalization, cmap=colormap, origin="lower")

    if north_arrow_angle is not None:
        arrow = AnchoredDirectionArrows(
            axis.transAxes,
            label_x="E",
            label_y="N",
            length=-0.15,
            aspect_ratio=-1,
            sep_y=-0.1,
            sep_x=0.04,
            angle=north_arrow_angle,
            color="white",
            back_length=0,
        )
        axis.add_artist(arrow)

    pyplot.axis("off")
    figure.savefig(output, dpi=dpi, bbox_inches="tight")
