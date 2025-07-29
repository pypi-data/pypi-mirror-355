from logging import getLogger
from os import PathLike
from typing import IO, Any

from abara_file_io.common_io_wrapper import (
    common_file_read_exception_handling,
    common_file_write_exception_handling,
)

log = getLogger(__name__)


def read_text(path: str | PathLike[str]) -> str:
    """テキスト形式のファイルをstrとして読み込む

    UTF-8以外のファイルはchardetで文字コードを自動判定する

    Args:
        path (Path | str): 開くファイルのパス

    Returns:
        str: 読み込んだ文字列、もしファイルが読み込めない場合は空文字列を返す
    """

    def read_text_core(f: IO[Any]) -> str:
        return f.read()

    return common_file_read_exception_handling(
        func=read_text_core,
        return_empty_value='',
        path=path,
    )


def write_text(data: str, path: str | PathLike[str]) -> bool:
    r"""strデータをファイルを書き込む

    テキストファイルを標準的な UTF-8 + \n の形式で保存する
    ただし拡張子.batと.cmdを指定した場合のみ、例外として Shift-JIS + \r\n で保存する

    Args:
        data (str): 書き込む文字列データ
        path (str | PathLike[str]): 保存するファイルのパス（拡張子まで記述）

    Returns:
        bool: ファイルの保存に成功したらTrue、失敗したらFalse
    """

    def write_text_core(
        data: object,
        f: IO[Any],
    ) -> None:
        f.write(data)

    return common_file_write_exception_handling(func=write_text_core, data=data, path=path)
