# Abara File IO

<p>
<img src="https://img.shields.io/badge/-Python-ffd448.svg?logo=python&style=flat">
<img src="https://img.shields.io/badge/license-MIT-blue.svg?style=flat">
</p>

## Description

Pythonのローカルファイルの読み書きを、細々とした設定なしに最適な方法で実行するライブラリ。

text、ini、json、yaml、tomlに対応。

読み込み時は自動的に文字コードを判定。  
書き込み時は常に文字コード `UTF-8` 、改行コード `\n` を使用。

## Dependency

[tomli\-w](https://pypi.org/project/tomli-w/)

[ruamel\.yaml](https://pypi.org/project/ruamel.yaml/)

[charset\-normalizer](https://pypi.org/project/charset-normalizer/)

## Install

pip

```
pip install abara-file-io
```

uv

```
uv add abara-file-io
```

## Usage

### ファイルの読み込み

ファイルを読み込む場合はread_から始まる関数を使用する。

```python
from abara_file_io import read_text, read_ini, read_json, read_yaml, read_toml

path = './parent/stem.suffix'

text_response: str = read_text(path)

ini_response: dict = read_ini(path)

json_response: dict = read_json(path)

yaml_response: dict = read_yaml(path)

toml_response: dict = read_toml(path)
```

読み込みは第1引数にファイルのパス（ `str` か、pathlibの `Path` オブジェクト）を指定するだけで動作する。

エンコードは最初に `UTF-8` を試し、違った場合はcharset\-normalizerで自動的に判定して読み込むので煩わされる必要がない。

読み込み時に存在しないファイルパスを指定などしてエラーが出た場合もエラーで停止しない仕様。  
その場合は空の `str` もしくは `dict` を返すので、必要に応じて処理を分岐させることができる。

### ファイルの書き込み

書き込む場合はwrite_から始まる関数を使用する。

```python
from abara_file_io import write_text, write_ini, write_json, write_yaml, write_toml

path = './parent/stem.suffix'

str_data = 'Beautiful is better than ugly.'

dict_data = {'foo': 'bar', 'baz': 'qux'}

write_text(str_data, path)

write_ini(dict_data, path)

write_json(dict_data, path)

write_yaml(dict_data, path)

write_toml(dict_data, path)
```

書き込みは第1引数に書き込むオブジェクト。  
第2引数に保存するファイル拡張子まで含めたパス（ `str` か、pathlibの `Path` オブジェクト）を入れる。

常に文字コード `UTF-8` 、改行コード `\n` で保存されるのでWindowsで指定を忘れてしまうことがなく安全。  
拡張子を `.bat` と `.cmd` にした場合のみ、 `UTF-8` では動作しないため自動的にShift-JIS（ `CP932` ）と `\r\n` で保存される。

書き込みに保存先パスの指定ミス等で処理が失敗してもエラーで停止しない仕様。  
もし失敗時に何をさせたい場合、全ての関数は書き込みに成功したら `True` 、失敗したら `False` を返すので、必要に応じて処理を分岐させることができる。

## Licence

[MIT](https://www.tldrlegal.com/license/mit-license)
