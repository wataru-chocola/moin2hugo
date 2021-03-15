from moin2hugo.moin_parser import MoinParser

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
    ]
)
def test_decorations_ml(data, expected, formatter_object):
    page = MoinParser.parse(data, 'PageName')
    assert formatter_object.format(page) == expected


@pytest.mark.parametrize(
    ("data", "expected"), [
        ("^super^script", "<sup>super</sup>script"),   # TODO
        (",,sub,,script", "<sub>sub</sub>script"),   # TODO
        ("`inline code`", "`inline code`"),
        ("{{{this is ``code``}}}", "```this is ``code`` ```"),
    ]
)
def test_decorations_sl(data, expected, formatter_object):
    page = MoinParser.parse(data, 'PageName')
    assert formatter_object.format(page) == expected

