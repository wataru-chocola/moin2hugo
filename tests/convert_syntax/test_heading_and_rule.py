from moin2hugo.moin_parser import MoinParser
from moin2hugo.formatter.hugo import HugoFormatter

import pytest


@pytest.mark.parametrize(
    ("data", "expected"), [
        ("= head1 =", "# head1\n\n"),
        ("= head1 =\n", "# head1\n\n"),
        ("===== head5 =====", "##### head5\n\n"),
        ("====== head5 ======", "##### head5\n\n"),

        ("====== *head* #5 ======", "##### \\*head\\* \\#5\n\n"),
    ]
)
def test_heading(data, expected):
    page = MoinParser.parse(data, 'PageName')
    assert HugoFormatter.format(page, pagename='PageName') == expected
    assert page.source_text == data


@pytest.mark.parametrize(
    ("data", "expected"), [
        ("----", "----\n\n"),
        ("-----------------", "----\n\n"),
    ]
)
def test_horizontal_rules(data, expected):
    page = MoinParser.parse(data, 'PageName')
    assert HugoFormatter.format(page, pagename='PageName') == expected
    assert page.source_text == data
