from logging import WARNING, getLogger
from pathlib import Path
from textwrap import dedent

import pytest

log = getLogger()


@pytest.fixture(autouse=True)
def log_level_set() -> None:
    getLogger('chardet').setLevel(WARNING)


# test_str


@pytest.fixture(scope='session')
def sample_str() -> str:
    text = """\
    瑣　事

    　人生を幸福にするためには、日常の瑣事を愛さなければならぬ。雲の光、竹の戦ぎ、群雀の声、行人の顔、――あらゆる日常の瑣事のうちに無上の甘露味を感じなければならぬ。
    　人生を幸福にするためには？　しかし瑣事を愛するものは瑣事のために苦しまなければならぬ。庭前の古池に飛びこんだ蛙は百年の愁いを破ったであろう。が、古池を飛び出した蛙は百年の愁いを与えたかもしれない。いや、芭蕉の一生は享楽の一生であるとともに、誰の目にも受苦の一生である。我々も微妙に楽しむためには、やはりまた微妙に苦しまなければならぬ。
    　人生を幸福にするためには、日常の瑣事に苦しまなければならぬ。雲の光、竹の戦ぎ、群雀の声、行人の顔、――あらゆる日常の瑣事のうちに堕地獄の苦痛を感じなければならぬ。
    """  # noqa: E501
    return dedent(text)


@pytest.fixture(scope='session')
def create_sample_text_file(tmp_path_factory: pytest.TempPathFactory, sample_str: str) -> Path:
    dir_path = tmp_path_factory.mktemp('pytest')
    file_path = dir_path / 'sample_text.txt'
    file_path.touch()
    file_path.write_text(sample_str)
    return file_path


@pytest.fixture
def create_sample_text_files_multiple_encodings(
    tmp_path_factory: pytest.TempPathFactory, sample_str: str, request: pytest.FixtureRequest
) -> Path:
    dir_path: Path = tmp_path_factory.mktemp('pytest')
    file_path: Path = dir_path / f'sample_text_{request.param}.txt'
    file_path.touch()
    file_path.write_text(sample_str, encoding=str(request.param), newline='\n')
    return file_path


@pytest.fixture
def create_sample_text_encode_false_detection(
    tmp_path_factory: pytest.TempPathFactory,
) -> dict[str, str | Path]:
    dir_path: Path = tmp_path_factory.mktemp('pytest')
    file_path: Path = dir_path / 'sample_text_fail.txt'
    file_path.touch()

    data = 'あ'
    file_path.write_text(data, encoding='cp932', newline='\r\n')
    return {'data': data, 'path': file_path}


# test_dicts


@pytest.fixture
def sample_dicts(request: pytest.FixtureRequest) -> dict[str, dict | str | bool]:
    match request.param:
        case 1:
            return {
                'data': {'foo': 1, 'bar': 2.236, 'baz': 'three', 'qux': True},
                'name': 'flat_dict',
                'expected': True,
                'ini_expected': True,
            }
        case 2:
            return {
                'data': {
                    'section1': {'foo': 'one', 'bar': 2.828, 'baz': 'three', 'qux': True},
                    'section2': {'foo': 1.732, 'bar': 'two', 'baz': 3, 'qux': False},
                },
                'name': 'section_dict1',
                'expected': True,
                'ini_expected': True,
            }
        case 3:
            return {
                'data': {
                    'section1': {'foo': {'qux': 4}, 'bar': 'two', 'baz': 3.14},
                    'section2': {
                        'foo': 'one',
                        'bar': [1, 2, 3],
                        'baz': {'qux': 130, 'quux': 256},
                    },
                },
                'name': 'section_dict2',
                'expected': True,
                'ini_expected': False,
            }
        case _:
            return {'data': {}, 'name': 'Empty_Dict', 'expected': False, 'ini_expected': False}
