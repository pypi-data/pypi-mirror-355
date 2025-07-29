from logging import getLogger
from pathlib import Path

import pytest

from abara_file_io import read_yaml, write_yaml

log = getLogger(__name__)


@pytest.mark.parametrize(
    ('sample_dicts'),
    [
        pytest.param(1, id='flat_dict'),
        pytest.param(
            2,
            id='section_dict1',
        ),
        pytest.param(
            3,
            id='section_dict2',
        ),
        pytest.param(
            4,
            id='empty_dict',
        ),
    ],
    indirect=['sample_dicts'],
)
def test_write_yaml(
    sample_dicts: dict[str, dict | str | bool],
    tmp_path: Path,
) -> None:
    file_path = tmp_path / 'tmp' / f'test_yaml_file_{sample_dicts["name"]}.yml'

    data = {}
    if isinstance(sample_dicts['data'], dict):
        data = sample_dicts['data']

    write_yaml(data, file_path)

    assert Path(file_path).exists()
    assert read_yaml(file_path) == data
