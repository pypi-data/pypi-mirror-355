from pathlib import Path
from typing import IO, Any

import pytest
from ruamel.yaml.parser import ParserError

from abara_file_io.common_io_wrapper import (
    common_file_read_exception_handling,
    common_file_write_exception_handling,
)


@pytest.mark.parametrize(
    'exception',
    [
        pytest.param(FileNotFoundError, id='FileNotFoundError'),
        pytest.param(PermissionError, id='PermissionError'),
        pytest.param(IsADirectoryError, id='IsADirectoryError'),
        pytest.param(OSError, id='OSError'),
        pytest.param(ParserError, id='ParserError'),
    ],
)
def test_common_file_read_exception_handling(exception: Exception, tmp_path: Path) -> None:
    def dummy_func(file: object) -> None:
        raise exception

    path = tmp_path / 'dummy_file.txt'
    path.touch()

    response = common_file_read_exception_handling(
        func=dummy_func, return_empty_value='', path=path
    )

    assert response == ''


@pytest.mark.parametrize(
    'exception',
    [
        pytest.param(PermissionError, id='PermissionError'),
        pytest.param(IsADirectoryError, id='IsADirectoryError'),
        pytest.param(OSError, id='OSError'),
    ],
)
def test_common_file_write_exception_handling(exception: Exception, tmp_path: Path) -> None:
    def dummy_func(file: object, f: IO[Any]) -> None:
        raise exception

    path = tmp_path / 'dummy_file.txt'

    data = {'key': 'value'}

    response = common_file_write_exception_handling(func=dummy_func, data=data, path=path)

    assert not response
