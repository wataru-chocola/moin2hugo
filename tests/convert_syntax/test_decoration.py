from moin2hugo.moin_parser import MoinParser
from moin2hugo.formatter.hugo import HugoFormatter
from moin2hugo.config import HugoConfig

import pytest


@pytest.mark.parametrize(
    ("data", "expected"), [
        ("__underlined text__", "<u>underlined text</u>"),
        ("__underlined\ntext__", "<u>underlined\ntext</u>"),
        ("--(stroke)--", "~~stroke~~"),
        ("''italic''", "*italic*"),
        ("'''strong'''", "**strong**"),
        ("'''''italic and strong'''''", "***italic and strong***"),
        ("''this is italic and '''this is strong'''''", "*this is italic and **this is strong***"),
        ("'''this is strong and ''this is italic'''''", "**this is strong and *this is italic***"),
        ("~-smaller-~", "<small>smaller</small>"),
        ("~+larger+~", "<big>larger</big>"),

        ("__underlined<x /> text__", "<u>underlined&lt;x /&gt; text</u>"),
        ("~-smal<x />ler-~", "<small>smal&lt;x /&gt;ler</small>"),
        ("~+larg<x />er+~", "<big>larg&lt;x /&gt;er</big>"),
    ]
)
def test_decorations_ml(data, expected):
    page = MoinParser.parse(data, 'PageName')
    assert HugoFormatter.format(page, pagename='PageName') == expected
    assert page.source_text == data


@pytest.mark.parametrize(
    ("data", "expected"), [
        ("^super^script", "<sup>super</sup>script"),
        (",,sub,,script", "<sub>sub</sub>script"),
        ("`inline code`", "`inline code`"),
        ("{{{this is ``code``}}}", "```this is ``code`` ```"),

        ("^su<x />per^script", "<sup>su&lt;x /&gt;per</sup>script"),
        (",,su<x />b,,script", "<sub>su&lt;x /&gt;b</sub>script"),
    ]
)
def test_decorations_sl(data, expected):
    page = MoinParser.parse(data, 'PageName')
    assert HugoFormatter.format(page, pagename='PageName') == expected
    assert page.source_text == data


@pytest.mark.parametrize(
    ("data", "expected"), [
        ("__underlined '''x''' text__", "<u>underlined **x** text</u>"),
    ]
)
def test_decorations_not_fully_work(data, expected, caplog):
    page = MoinParser.parse(data, 'PageName')
    assert HugoFormatter.format(page, pagename='PageName') == expected
    assert 'unsupported: non-Text' in caplog.text


@pytest.mark.parametrize(
    ("data", "expected"), [
        ("__underlined '''x''' text__", r"\_\_underlined '''x''' text\_\_"),
        ("~-smaller-~", r"\~\-smaller\-\~"),
        ("~+larger+~", r"\~\+larger\+\~"),

        ("^super^script", r"^super^script"),
        (",,sub,,script", r",,sub,,script"),
        ("^su<x />per^script", r"^su\<x /\>per^script"),
        (",,su<x />b,,script", r",,su\<x /\>b,,script"),
    ]
)
def test_decorations_without_unsafe(data, expected, caplog):
    page = MoinParser.parse(data, 'PageName')
    ret = HugoFormatter.format(page, config=HugoConfig(goldmark_unsafe=False), pagename='PageName')
    assert ret == expected, page.tree_repr(include_src=True)
    assert 'goldmark_unsafe' in caplog.text
