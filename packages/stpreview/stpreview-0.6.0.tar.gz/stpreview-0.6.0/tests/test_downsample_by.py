import os

import asdf
import pytest
from test_data import (
    DATA_DIRECTORY,
    SHARED_DATA_DIRECTORY,
    level1_science_raw,
    level2_image,
    level3_mosaic,
)

from stpreview.downsample import downsample_asdf_by

OBSERVATORY = "roman"


@pytest.mark.parametrize(
    "input",
    [
        level1_science_raw(DATA_DIRECTORY),
        level2_image(DATA_DIRECTORY),
        level3_mosaic(DATA_DIRECTORY),
    ],
)
@pytest.mark.parametrize(
    "factor",
    [2, 4, (2, 4)],
)
def test_dummy_data(input, factor):
    with asdf.open(input) as file:
        original_shape = file[OBSERVATORY]["data"].shape

    downsampled_shape = [1 for _ in original_shape]
    downsampled_shape[-2] = int(
        original_shape[-2] / (factor if isinstance(factor, int) else factor[-2])
    )
    downsampled_shape[-1] = int(
        original_shape[-1] / (factor if isinstance(factor, int) else factor[-1])
    )
    downsampled_shape = tuple(downsampled_shape)
    assert original_shape != downsampled_shape

    result = downsample_asdf_by(input, factor=factor)

    assert result.shape == downsampled_shape


@pytest.mark.parametrize(
    "input",
    [
        level2_image(DATA_DIRECTORY),
        level3_mosaic(DATA_DIRECTORY),
    ],
)
@pytest.mark.parametrize(
    "factor",
    [(2, 2), (4, 4), (2, 4)],
)
def test_command(input, factor, tmp_path):
    with asdf.open(input) as file:
        original_shape = file[OBSERVATORY]["data"].shape

    downsampled_shape = [1 for _ in original_shape]
    downsampled_shape[-2] = int(
        original_shape[-2] / (factor if isinstance(factor, int) else factor[-2])
    )
    downsampled_shape[-1] = int(
        original_shape[-1] / (factor if isinstance(factor, int) else factor[-1])
    )
    downsampled_shape = tuple(downsampled_shape)
    assert original_shape != downsampled_shape

    output = tmp_path / f"{input.stem}.png"

    command = f"stpreview --observatory roman {input} {output} by {' '.join(str(v) for v in factor)}"
    print(command)
    exit_code = os.system(command)
    assert exit_code == 0


@pytest.mark.shareddata
@pytest.mark.skipif(
    not SHARED_DATA_DIRECTORY.exists(), reason="can't reach shared data directory"
)
@pytest.mark.parametrize(
    "input",
    [
        filename
        for filename in SHARED_DATA_DIRECTORY.iterdir()
        if filename.suffix.lower() == ".asdf"
    ]
    if SHARED_DATA_DIRECTORY.exists()
    else [],
)
@pytest.mark.parametrize(
    "factor",
    [(2, 2), (4, 4), (2, 4)],
)
def test_sample_data(input, factor):
    with asdf.open(input) as file:
        original_shape = file[OBSERVATORY]["data"].shape

    downsampled_shape = [1 for _ in original_shape]
    downsampled_shape[-2] = int(
        original_shape[-2] / (factor if isinstance(factor, int) else factor[-2])
    )
    downsampled_shape[-1] = int(
        original_shape[-1] / (factor if isinstance(factor, int) else factor[-1])
    )
    downsampled_shape = tuple(downsampled_shape)
    assert original_shape != downsampled_shape

    result = downsample_asdf_by(input, factor=factor)

    assert result.shape == downsampled_shape
