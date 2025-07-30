# カスタム指示

- importは可能な限り`import xxx`形式で書く (`from xxx import yyy`ではなく)
- タイプヒントは可能な限り書く
  - `typing.List`ではなく`list`を使用する。`dict`やその他も同様。
  - `typing.Optional`ではなく`| None`を使用する。
- docstringは基本的には概要のみ書く
- ログは`logging`を使う
- 日付関連の処理は`datetime`を使う
- ファイル関連の処理は`pathlib`を使う
- テーブルデータの処理には`polars`を使う (`pandas`は使わない)
- モジュール追加時は`README.md`も更新する
- `make format`でコードを整形する

## テストコード

- テストコードは`pytest`で書く
- テストコードは`pytilpack/xxx_.py`に対して`tests/xxx_test.py`として配置する

テストコードの例:

```python
"""テストコード。"""

import pathlib

import pytest
import pytilpack.xxx_


@pytest.mark.parametrize(
    "x,expected",
    [
        ("test1", "test1"),
        ("test2", "test2"),
    ],
)
def test_yyy(tmp_path: pathlib.Path, x: str, expected: str) -> None:
    """yyyのテスト。"""
    actual = pytilpack.xxx_.yyy(tmp_path, x)
    assert actual == expected

```

- テストコードを書いたら `uv run pytest` でテストを実行する

## リリース手順

- DEVELOPMENT.mdを参照
