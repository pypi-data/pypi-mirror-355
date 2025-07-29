from configparser import ConfigParser
from logging import getLogger
from os import PathLike
from pathlib import Path
from typing import IO, Any, cast

from abara_file_io.common_io_wrapper import (
    common_file_read_exception_handling,
    common_file_write_exception_handling,
)

log = getLogger(__name__)


type IniConfigValue = str | int | float | bool


def _restore_ini_config(input_str: str) -> IniConfigValue:
    """iniファイル化でstrに変換された値を元に戻す

    Args:
        input_str (str): iniから読み込んだ値

    Returns:
        IniConfigValue: 修正された値
    """
    try:
        return int(input_str)
    except ValueError:
        pass

    try:
        return float(input_str)
    except ValueError:
        pass

    if input_str == 'True':
        return True
    if input_str == 'False':
        return False

    return input_str


def _restore_ini_configs(input_dict: dict[str, str]) -> dict[str, IniConfigValue]:
    """辞書内のvalueをini化する前の元の型に復元する

    Args:
        input_dict (dict[str, str]): iniファイルから読み込んだ辞書

    Returns:
        dict[str, IniConfigValue]: 型を修正された辞書
    """
    return {key: _restore_ini_config(value) for key, value in input_dict.items()}


def read_ini(
    path: str | PathLike[str],
) -> dict[str, IniConfigValue] | dict[str, dict[str, IniConfigValue]]:
    """iniをファイルを読み込み、辞書に変換して出力する

    iniはstr以外を扱えないので、辞書に変換する時に自動的にint,float,boolをpythonの型に変換する
    ソースとなる辞書に文字列で'True'や'12.34'などを保存していた場合も、strやfloatに変換される

    Args:
        path (str | PathLike[str]): _description_

    Returns:
        dict[str, IniConfigValue] | dict[str, dict[str, IniConfigValue]]:
            IniConfigValueはiniに保存できるstr,int,float,boolの4種類のどれか
    """

    def read_ini_core(
        f: IO[Any],
    ) -> ConfigParser:
        config = ConfigParser()
        config.read_file(f)
        return config

    config = common_file_read_exception_handling(
        func=read_ini_core, return_empty_value=ConfigParser(), path=path
    )

    config_sections = config.sections()
    config_result: dict = {}
    if len(config_sections) > 1:
        for i in config_sections:
            config_result[i] = _restore_ini_configs(dict(config.items(i)))
    elif len(config_sections) == 1:
        config_result = _restore_ini_configs(dict(config.items(config_sections[0])))
    else:
        log.warning('iniファイルのセクションが存在しません')
        config_result = {}

    return config_result


def _correct_all_input_values(input_dict: dict) -> bool:
    """入力された辞書のvalueが全てIniConfig = str | int | float | bool であればTrueを返す

    Args:
        input_dict (dict): 判定する辞書

    Returns:
        bool: 全てが str | int | float | bool であればTrue
    """
    return all(isinstance(i, (str, int, float, bool)) for i in input_dict.values())


def _data_ini_convertible_is_decision(
    data: dict[str, IniConfigValue] | dict[str, dict[str, IniConfigValue]],
) -> ConfigParser:
    """入力されたデータをiniに変換できるか判定してconfigparserに書き込む

    Args:
        data (dict[str, IniConfigValue] | dict[str, dict[str, IniConfigValue]]):
            iniに書き込む辞書データ

    Returns:
        ConfigParser: 辞書の内容を格納したconfigparser
    """
    config = ConfigParser()

    data_values_all_dict_type: bool = all(isinstance(i, dict) for i in data.values())
    data_values_all_ini_config_type = all(
        _correct_all_input_values(i) for i in data.values() if isinstance(i, dict)
    )
    if len(data) == 0:
        log.warning('入力された内容が空の辞書です')

    elif data_values_all_dict_type and data_values_all_ini_config_type:
        log.debug('multi section')
        multi_section_data = cast('dict[str, dict[str, IniConfigValue]]', data)
        for i in multi_section_data:
            config.add_section(i)
            for key, value in multi_section_data[i].items():
                config[i][key] = str(value)

    elif _correct_all_input_values(data):
        log.debug('single section')
        config.add_section('configs')
        for key, value in data.items():
            config['configs'][key] = str(value)
    else:
        log.warning('入力された内容がini化できない形式です')

    return config


def write_ini(
    data: dict[str, IniConfigValue] | dict[str, dict[str, IniConfigValue]],
    path: str | PathLike[str],
) -> bool:
    """辞書をiniファイルとして保存する

    保存できる要素は IniConfigValue = str | int | float | bool の4種類
    それ以外のSequence型はiniでは保存できない
    Args:
        data (dict[str, IniConfigValue] | dict[str, dict[str, IniConfigValue]]):
            iniに書き込む辞書オブジェクト
        path (str | PathLike[str]): 保存するファイルパス、ファイル名の拡張子まで記入

    Returns:
        bool: ファイルの保存に成功したらTrue、失敗したらFalse
    """
    path = Path(path)

    config = _data_ini_convertible_is_decision(data)

    if len(config.sections()) == 0:
        return False

    def write_ini_core(
        config: object,
        f: IO[Any],
    ) -> None:
        if isinstance(config, ConfigParser):
            config.write(f)

    return common_file_write_exception_handling(func=write_ini_core, data=config, path=path)
