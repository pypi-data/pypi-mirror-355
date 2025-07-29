import json
from logging import getLogger
from os import PathLike
from typing import IO, Any

from abara_file_io.common_io_wrapper import (
    common_file_read_exception_handling,
    common_file_write_exception_handling,
)

log = getLogger(__name__)


def read_json(path: str | PathLike[str]) -> dict:
    """jsonファイルを読み込む

    Args:
        path (str): 読み込むjsonファイルのパス

    Returns:
        dict: 辞書
    """

    def read_json_core(
        f: IO[Any],
    ) -> dict:
        return json.load(f)

    return common_file_read_exception_handling(
        func=read_json_core, return_empty_value={}, path=path
    )


def write_json(data: dict, path: str | PathLike[str], *, ensure_ascii: bool = False) -> bool:
    r"""jsonファイルを書き込む

    Args:
        data (dict): jsonに書き込む辞書オブジェクト
        path (str | PathLike): 保存するファイルパス、ファイル名の拡張子まで記入
        ensure_ascii (bool): 非ASCII文字をエスケープする('あ'→'\\u3042')

    Returns:
        bool: ファイルの保存に成功したらTrue、失敗したらFalse
    """

    def write_json_core(
        data: object,
        f: IO[Any],
    ) -> None:
        json.dump(data, f, indent=2, ensure_ascii=ensure_ascii)

    return common_file_write_exception_handling(func=write_json_core, data=data, path=path)
