from typing import Tuple

import pytest

import moin2x.moinutils


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        ('target="_blank",&do=get', {"target": "_blank", "&do": "get"}),
    ],
)
def test_parse_quoted_separated(data: str, expected: dict[str, str]):
    _, ret, _ = moin2x.moinutils.parse_quoted_separated(data)
    assert ret == expected


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        ('target="_blank",&do=get', [("target", "_blank"), ("&do", "get")]),
        ('target="_blank",&do=get,&test', [("target", "_blank"), ("&do", "get"), "&test"]),
        ('target="_blank",&do=get ,a  ', [("target", "_blank"), ("&do", "get"), "a"]),
        ('a=b=c,"x=y"', [("a", "b=c"), "x=y"]),
        ("a=", [("a", "")]),
        ('a="""b"', [("a", '"b')]),
        ("width=100 height=150 xxx=11", [("width", "100 height=150 xxx=11")]),
    ],
)
def test_parse_quoted_separated_ext(data: str, expected: list[Tuple[str, str] | str]):
    ret = moin2x.moinutils.parse_quoted_separated_ext(data)
    assert ret == expected


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        ("%E3%83%86%E3%82%B9%E3%83%88", "テスト"),
    ],
)
def test_url_unquote(data: str, expected: str):
    ret = moin2x.moinutils.url_unquote(data)
    assert ret == expected
