from logging import getLogger
from pathlib import Path

import pytest

from abara_file_io import read_text, write_text

log = getLogger(__name__)


def test_read_text(create_sample_text_file: Path, sample_str: str) -> None:
    read_data = read_text(create_sample_text_file)
    assert isinstance(read_data, str)
    assert read_data == sample_str


def test_write_text(tmp_path: Path, sample_str: str) -> None:
    file_path = tmp_path / 'pytest' / 'pytest_str.txt'
    write_text(sample_str, file_path)
    read_data = file_path.read_text(encoding='utf_8')
    assert read_data == sample_str


@pytest.mark.parametrize(
    'create_sample_text_files_multiple_encodings',
    [('utf_8'), ('shift_jis'), ('utf_16'), ('euc_jp')],
    indirect=['create_sample_text_files_multiple_encodings'],
)
def test_read_text_multiple_encodings(
    create_sample_text_files_multiple_encodings: Path, sample_str: str
) -> None:
    read_data = read_text(create_sample_text_files_multiple_encodings)
    assert read_data == sample_str


def test_encode_false_detection(
    create_sample_text_encode_false_detection: dict[str, str | Path],
) -> None:
    read_data = read_text(create_sample_text_encode_false_detection['path'])
    assert read_data == create_sample_text_encode_false_detection['data']


def test_bat_file(tmp_path: Path, sample_str: str) -> None:
    file_path = tmp_path / 'pytest' / 'pytest_bat.bat'
    write_text(sample_str, file_path)
    read_data = read_text(file_path)
    assert read_data == sample_str
