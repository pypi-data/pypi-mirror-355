import argparse
from pathlib import Path

import asdf

from stpreview.downsample import (
    OBSERVATORIES,
    downsample_asdf_by,
    downsample_asdf_to,
    known_asdf_observatory,
)
from stpreview.image import north_pole_angle, write_image


def command():
    parser = argparse.ArgumentParser()
    parser.add_argument("INPUT", type=Path, help="path to ASDF file with 2D image data")
    parser.add_argument("OUTPUT", type=Path, help="path to output image file")
    parser.add_argument(
        "--observatory",
        type=str,
        choices=OBSERVATORIES,
        help="(if omitted, will attempt to infer from file)",
        required=False,
    )
    parser.add_argument(
        "--compass",
        action="store_true",
        help="draw a north arrow on the image",
    )

    subparsers = parser.add_subparsers(dest="subcommand")

    to_parser = subparsers.add_parser(
        "to", help="downsample the given ASDF image by the given integer factor"
    )
    to_parser.add_argument(
        "SHAPE",
        type=int,
        nargs="+",
        help="desired pixel shape of output image",
    )

    by_parser = subparsers.add_parser(
        "by",
        help="downsample the given ASDF image to the desired shape (the output image may be smaller than the desired shape, if no even factor exists)",
    )
    by_parser.add_argument(
        "FACTOR",
        type=int,
        nargs="+",
        help="integer factor by which to downsample input data",
    )

    arguments = parser.parse_args()

    observatory = arguments.observatory
    if observatory is None:
        observatory = known_asdf_observatory(arguments.INPUT)

    if arguments.subcommand == "to":
        data = downsample_asdf_to(
            input=arguments.INPUT, shape=arguments.SHAPE, observatory=observatory
        )
    elif arguments.subcommand == "by":
        data = downsample_asdf_by(
            input=arguments.INPUT, factor=arguments.FACTOR, observatory=observatory
        )

    if arguments.compass:
        with asdf.open(arguments.INPUT, memmap=True) as file:
            wcs = file[observatory]["meta"]["wcs"]
            north_arrow_angle = north_pole_angle(wcs).degree - 90
    else:
        north_arrow_angle = None

    write_image(
        data,
        arguments.OUTPUT,
        shape=arguments.SHAPE if arguments.subcommand == "to" else None,
        north_arrow_angle=north_arrow_angle,
    )


if __name__ == "__main__":
    command()
