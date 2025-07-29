from collections.abc import Callable
from logging import getLogger
from os import PathLike
from pathlib import Path
from typing import IO, Any, Literal, TypeVar

from charset_normalizer import from_path
from ruamel.yaml.parser import ParserError

log = getLogger(__name__)


T = TypeVar('T', bound=object)


def _decision_encoding(func: Callable[[IO[Any]], T], path: Path) -> T | None:
    """charset_normalizerの文字コード判定を候補順に全て試行する

    Returns:
        T | None: 呼び出し時に設定した戻り値の型
    """
    results = from_path(path)

    for i in results:
        try:
            with path.open(mode='r', encoding=i.encoding) as f:
                return func(f)
        except UnicodeDecodeError:
            log.debug(f'文字コード{i.encoding}での読み込み試行失敗')
    return None


def common_file_read_exception_handling(
    func: Callable[[IO[Any]], T],
    return_empty_value: T,
    path: str | PathLike[str],
    *,
    mode: Literal['r', 'rb'] = 'r',
    encoding: str | None = 'utf_8',
) -> T:
    """ファイル読み込み時の汎用的な例外処理をするラッパー関数

    Args:
        func (Callable[[IO[Any]], T]): openしたファイルの読み込みをする関数
        return_empty_value (T): 読み込み処理の失敗時に戻る値。これによって戻り値の型も決定する
        path (str | PathLike[str]): 開くファイルのパス
        mode (Literal['r', 'rb';], optional): 読み込むファイルを開く時のmode. Defaults to 'r'.
        encoding (str | None): 読み込む時の文字コード Defaults to 'utf_8'.

    Returns:
        T: 呼び出し時にreturn_empty_valueで設定した戻り値の型
    """
    p = Path(path)

    if mode == 'rb':
        encoding = None

    try:
        with p.open(mode=mode, encoding=encoding) as f:
            read_data: T = func(f)
    except UnicodeDecodeError:
        result = _decision_encoding(func=func, path=p)

        if result is not None:
            return result

        log.warning(
            '読み込もうとしたファイルの文字コードが{encoding}ではなかった為、charset-normalizerを使い文字コードの判定を試みましたが失敗しました'
            f'(return empty {type(return_empty_value)}: {path})'
        )
    except FileNotFoundError:
        log.warning(
            '読み込もうとしたファイルが存在しません'
            f'(return empty {type(return_empty_value)}): {path}'
        )
    except PermissionError:
        log.warning(
            '読み込み権限がないか、ファイルへのパスが正しく指定されていません'
            f'(return empty {type(return_empty_value)}): {path}'
        )
    except IsADirectoryError:
        log.warning(
            '読み込もうとしたパスがディレクトリを指しています'
            f'(return empty {type(return_empty_value)}): {path}'
        )
    except OSError:
        log.warning(f'OSで問題が発生しました(return empty {type(return_empty_value)}): {path}')
    except ParserError:
        log.warning(f'ファイルの記述が不正です(return empty {type(return_empty_value)}): {path}')
    else:
        return read_data

    return return_empty_value


def common_file_write_exception_handling(
    func: Callable[[object, IO[Any]], None],
    data: object,
    path: str | PathLike[str],
    *,
    mode: Literal['w', 'wb'] = 'w',
) -> bool:
    """ファイル書き込み時の汎用的な例外処理をするラッパー関数

    Args:
        func (Callable[[object, IO[Any]], None]):
            openしたファイルに対して書き込み処理をする関数
        data (T): 書き込むデータ
        path (str | PathLike[str]): 保存するファイルのパス
        mode (Literal['w', 'wb'], optional): 書き込むファイルをopenする時のmode. Defaults to 'r'.

    Returns:
        bool: 処理の成功失敗の判定のための戻り値
    """
    p = Path(path)

    encoding = 'utf_8'
    newline = '\n'
    if p.suffix in {'.bat', '.cmd'}:
        encoding = 'cp932'
        newline = '\r\n'
    if mode == 'wb':
        encoding = None
        newline = None

    result: bool = False

    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        with Path(p).open(mode=mode, encoding=encoding, newline=newline) as f:
            func(data, f)
    except PermissionError:
        log.warning(f'書き込み権限がないか、ファイルへのパスが正しく指定されていません: {path}')
    except IsADirectoryError:
        log.warning(f'書き込もうとしたパスがディレクトリを指しています: {path}')
    except OSError:
        log.warning(f'OSで問題が発生しました: {path}')
    else:
        result = True

    return result
