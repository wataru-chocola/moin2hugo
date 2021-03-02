import pytest

from moin2hugo.moin_parser import MoinParser
from moin2hugo.formatter import Formatter


@pytest.fixture
def formatter_object():
    return Formatter()


@pytest.mark.parametrize(
    ("data", "expected"), [
        ("= head1 =", "# head1\n\n"),
        ("===== head5 =====", "##### head5\n\n"),
        ("====== head5 ======", "##### head5\n\n"),
    ]
)
def test_heading(data, expected, formatter_object, capsys):
    MoinParser.format(data, formatter_object)
    captured = capsys.readouterr()
    assert captured.out == expected


@pytest.mark.parametrize(
    ("data", "expected"), [
        ("__underlined text__", "__underlined text__"),
        ("__underlined\ntext__", "__underlined text__"),
        ("--(stroke)--", "~~stroke~~"),
        ("''italic''", "*italic*"),
        ("'''strong'''", "**strong**"),
        ("'''''italic and strong'''''", "***italic and strong***"),
        ("''this is italic and '''this is strong'''''", "*this is italic and **this is strong***"),
        ("'''this is strong and ''this is italic'''''", "**this is strong and *this is italic***"),
        ("~-smaller-~", "<small>smaller</small>"),   # TODO
        ("~+larger+~", "<big>larger</big>"),   # TODO
    ]
)
def test_decorations_ml(data, expected, formatter_object, capsys):
    MoinParser.format(data, formatter_object)
    captured = capsys.readouterr()
    # TODO: remove rstrip()
    assert captured.out.rstrip() == expected


@pytest.mark.parametrize(
    ("data", "expected"), [
        ("^super^script", "<sup>super</sup>script"),   # TODO
        (",,sub,,script", "<sub>sub</sub>script"),   # TODO
        ("`inline code`", "`inline code`"),
        ("{{{this is ``code``}}}", "```this is ``code`` ```"),
    ]
)
def test_decorations_sl(data, expected, formatter_object, capsys):
    MoinParser.format(data, formatter_object)
    captured = capsys.readouterr()
    # TODO: remove rstrip()
    assert captured.out.rstrip() == expected
