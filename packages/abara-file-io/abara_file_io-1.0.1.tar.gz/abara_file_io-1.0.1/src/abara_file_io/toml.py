import tomllib
from logging import getLogger
from os import PathLike
from typing import IO, Any

import tomli_w

from abara_file_io.common_io_wrapper import (
    common_file_read_exception_handling,
    common_file_write_exception_handling,
)

log = getLogger(__name__)


def read_toml(path: str | PathLike[str]) -> dict:
    """TOMLファイルを読み込む

        読み込みに失敗した場合は空の辞書を返す

    Args:
        path (Union[Path, str]): 読み込むファイルのパス

    Returns:
        Union[dict, None]:
            正確にはdictのインスタンスのruamel.yaml.comments.CommentedMap
    """

    def read_toml_core(
        f: IO[Any],
    ) -> dict:
        return tomllib.load(f)

    return common_file_read_exception_handling(
        func=read_toml_core, return_empty_value={}, path=path, mode='rb'
    )


def write_toml(data: dict, path: str | PathLike[str]) -> bool:
    """TOMLとして書き込む

        第一引数で受け取ったパスに、第二引数で受け取った内容をTOMLとして書き込む。
        ※tomli_wが必要
        tomli_wでの書き込みはコメントが消えるので注意
        保持したい場合はtomlkitを使うこと

    Args:
        data (dict): tomlに書き込む辞書オブジェクト
        path (str | PathLike): 保存するファイルパス、ファイル名の拡張子まで記入

    Returns:
        bool: ファイルの保存に成功したらTrue、失敗したらFalse
    """

    def write_toml_core(
        data: object,
        f: IO[Any],
    ) -> None:
        if isinstance(data, dict):
            tomli_w.dump(data, f)

    return common_file_write_exception_handling(
        func=write_toml_core, data=data, path=path, mode='wb'
    )
