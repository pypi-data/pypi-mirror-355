from logging import getLogger
from pathlib import Path

import pytest

from abara_file_io import read_ini, write_ini

log = getLogger(__name__)


@pytest.mark.parametrize(
    ('sample_dicts'),
    [
        pytest.param(1, id='flat_dict'),
        pytest.param(
            2,
            id='section_dict',
        ),
        pytest.param(
            3,
            id='error_dict',
        ),
        pytest.param(
            4,
            id='empty_dict',
        ),
    ],
    indirect=['sample_dicts'],
)
def test_write_ini(
    sample_dicts: dict[str, dict | str],
    tmp_path: Path,
) -> None:
    file_path = tmp_path / 'tmp' / f'test_ini_file_{sample_dicts["name"]}.ini'

    data = {}
    if isinstance(sample_dicts['data'], dict):
        data = sample_dicts['data']

    result = write_ini(data, file_path)

    assert result == sample_dicts['ini_expected']


@pytest.mark.parametrize(
    ('sample_dicts'),
    [
        pytest.param(1, id='flat_dict'),
        pytest.param(
            2,
            id='section_dict',
        ),
        pytest.param(
            3,
            id='error_dict',
        ),
        pytest.param(
            4,
            id='empty_dict',
        ),
    ],
    indirect=['sample_dicts'],
)
def test_read_ini(
    sample_dicts: dict[str, dict | str],
    tmp_path: Path,
) -> None:
    file_path = tmp_path / 'tmp' / f'test_ini_file_{sample_dicts["name"]}.ini'

    data = {}
    if isinstance(sample_dicts['data'], dict):
        data = sample_dicts['data']

    write_ini(data, file_path)
    read_data = read_ini(file_path)

    if sample_dicts['ini_expected']:
        assert data == read_data
    else:
        assert read_data == {}
