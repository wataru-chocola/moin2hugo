import pytest

from moin2hugo.config import HugoConfig
from moin2hugo.formatter import HugoFormatter
from moin2x.moin_parser import MoinParser


@pytest.mark.parametrize(
    ("data", "expected"),
    [
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
    ],
)
def test_decorations_ml(data: str, expected: str):
    page = MoinParser.parse(data, "PageName")
    assert HugoFormatter.format(page, pagename="PageName") == expected
    assert page.source_text == data


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        ("^super^script", "<sup>super</sup>script"),
        (",,sub,,script", "<sub>sub</sub>script"),
        ("`inline code`", "`inline code`"),
        ("{{{this is ``code``}}}", "```this is ``code`` ```"),
        ("^su<x />per^script", "<sup>su&lt;x /&gt;per</sup>script"),
        (",,su<x />b,,script", "<sub>su&lt;x /&gt;b</sub>script"),
        # shortcode
        ("^su{{%hoge%}}per^script", "<sup>su{{&#37;hoge%}}per</sup>script"),
        ("`inline {{%test%}} code`", "`inline {{%/*test*/%}} code`"),
    ],
)
def test_decorations_sl(data: str, expected: str):
    page = MoinParser.parse(data, "PageName")
    assert HugoFormatter.format(page, pagename="PageName") == expected
    assert page.source_text == data


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        ("a'''b'''c", "a**b**c"),
        ("a''b''c", "a*b*c"),
        ("a'''(b'''c", "a **(b**c"),
        ("'''(b'''c", "**(b**c"),
        ("a'''b)'''c", "a**b)** c"),
        ("a'''(b)'''c", "a **(b)** c"),
        ("a''(b)''c", "a *(b)* c"),
        ("a'''''b'''''c", "a***b***c"),
        ("a'''b*'''c", r"a**b\*** c"),
        ("a''' b '''c", "a **b** c"),
    ],
)
def test_strong_and_emphasis_spaces(data: str, expected: str):
    # see: https://spec.commonmark.org/0.29/#emphasis-and-strong-emphasis
    # left-flanking delimiter run, right-flanking delimiter run
    page = MoinParser.parse(data, "PageName")
    assert HugoFormatter.format(page, pagename="PageName") == expected, page.tree_repr()
    assert page.source_text == data


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        ("__underlined '''x''' text__", "<u>underlined **x** text</u>"),
    ],
)
def test_decorations_not_fully_work(data: str, expected: str, caplog: pytest.LogCaptureFixture):
    page = MoinParser.parse(data, "PageName")
    assert HugoFormatter.format(page, pagename="PageName") == expected
    assert "unsupported: non-Text" in caplog.text


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        ("__underlined '''x''' text__", r"\_\_underlined '''x''' text\_\_"),
        ("~-smaller-~", r"\~\-smaller\-\~"),
        ("~+larger+~", r"\~\+larger\+\~"),
        ("^super^script", r"^super^script"),
        (",,sub,,script", r",,sub,,script"),
        ("^su<x />per^script", r"^su\<x /\>per^script"),
        (",,su<x />b,,script", r",,su\<x /\>b,,script"),
    ],
)
def test_decorations_without_unsafe(data: str, expected: str, caplog: pytest.LogCaptureFixture):
    page = MoinParser.parse(data, "PageName")
    ret = HugoFormatter.format(page, config=HugoConfig(goldmark_unsafe=False), pagename="PageName")
    assert ret == expected, page.tree_repr(include_src=True)
    assert "goldmark_unsafe" in caplog.text
