from logging import getLogger
from os import PathLike
from typing import IO, Any

from ruamel.yaml import YAML

from abara_file_io.common_io_wrapper import (
    common_file_read_exception_handling,
    common_file_write_exception_handling,
)

log = getLogger(__name__)


def read_yaml(path: str | PathLike[str]) -> dict:
    """YAMLファイルの読み込み

        リスト、もしくは辞書型の変数として読み込む
        読み込みに失敗した場合は空の辞書を返す

    Args:
        path (Union[Path, str]): 書き込むファイル名

    Returns:
        Union[dict, None]:
            正確にはdictのインスタンスのruamel.yaml.comments.CommentedMap
    """

    def read_yaml_core(
        f: IO[Any],
    ) -> dict:
        yaml = YAML()
        return yaml.load(f)

    return common_file_read_exception_handling(
        func=read_yaml_core, return_empty_value={}, path=path
    )


def write_yaml(data: list | dict, path: str | PathLike[str]) -> bool:
    """YAMLファイルとして出力する

        第一引数で受け取ったパスに、第二引数で受け取った内容をYAMLとして書き込む。

    Args:
        data (dict): yamlに書き込む辞書オブジェクト
        path (str | PathLike): 保存するファイルパス、ファイル名の拡張子まで記入

    Returns:
        bool: ファイルの保存に成功したらTrue、失敗したらFalse
    """

    def write_yaml_core(
        data: object,
        f: IO[Any],
    ) -> None:
        yaml.dump(data, f)

    yaml = YAML()
    yaml.indent(mapping=2, sequence=4, offset=2)

    return common_file_write_exception_handling(func=write_yaml_core, data=data, path=path)
