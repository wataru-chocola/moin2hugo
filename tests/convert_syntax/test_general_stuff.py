from moin2hugo.moin_parser import MoinParser

import pytest


@pytest.mark.parametrize(
    ("data", "expected"), [
        ("test\ntest", "test\ntest"),
        ("'''''test'''''\ntest", "***test***\ntest"),
    ]
)
def test_endling_newline(data, expected, formatter_object):
    page = MoinParser.parse(data, 'PageName')
    assert formatter_object.format(page) == expected
    assert page.source_text == data


@pytest.mark.parametrize(
    # all markdown escaping are located in test_formatter.py
    ("data", "expected"), [
        ("line with spaces  \ntest", "line with spaces\ntest"),
        ("line1\n/* xyz */    line2", "line1\nline2"),
        ("line1  /* xyz */  \nline2", "line1\nline2"),
        ("_test_", r"\_test\_"),
        ("'''***'''", r"**\*\*\***"),
    ]
)
def test_escape(data, expected, formatter_object):
    page = MoinParser.parse(data, 'PageName')
    assert formatter_object.format(page) == expected
    assert page.source_text == data


@pytest.mark.parametrize(
    ("data", "expected"), [
        ("<<TableOfContents>>", ''),
        ("<<BR>>", '  \n'),
        ("||a||b<<BR>>c||", '| a | b<br />c |\n'),
        ("<<UnsupportedMacro>>", r'\<\<UnsupportedMacro\>\>'),
    ]
)
def test_macro(data, expected, formatter_object):
    page = MoinParser.parse(data, 'PageName')
    assert formatter_object.format(page) == expected
    assert page.source_text == data


@pytest.mark.parametrize(
    ("data", "expected"), [
        ("## this is comment", ''),
        ("Hello, /* this is comment */ world", 'Hello,  world'),
        ("Hello, /* ''' comment */ world", 'Hello,  world'),
    ]
)
def test_comment(data, expected, formatter_object):
    page = MoinParser.parse(data, 'PageName')
    assert formatter_object.format(page) == expected
    assert page.source_text == data


@pytest.mark.parametrize(
    ("data", "expected"), [
        (":)", ":simple_smile:"),
    ]
)
def test_smiley(data, expected, formatter_object):
    page = MoinParser.parse(data, 'PageName')
    assert formatter_object.format(page) == expected
    assert page.source_text == data


@pytest.mark.parametrize(
    ("data", "expected"), [
        ("= head1 =", "# head1\n\n"),
        ("= head1 =\n", "# head1\n\n"),
        ("===== head5 =====", "##### head5\n\n"),
        ("====== head5 ======", "##### head5\n\n"),

        ("====== *head* #5 ======", "##### \\*head\\* \\#5\n\n"),
    ]
)
def test_heading(data, expected, formatter_object):
    page = MoinParser.parse(data, 'PageName')
    assert formatter_object.format(page) == expected
    assert page.source_text == data


@pytest.mark.parametrize(
    ("data", "expected"), [
        ("----", "----\n\n"),
        ("-----------------", "----\n\n"),
    ]
)
def test_horizontal_rules(data, expected, formatter_object):
    page = MoinParser.parse(data, 'PageName')
    assert formatter_object.format(page) == expected
    assert page.source_text == data


@pytest.mark.parametrize(
    ("data", "expected"), [
        ("&uuml;", "&uuml;"),
        ("&#42;", "&#42;"),
        ("&#x42;", "&#x42;"),
    ]
)
def test_entities(data, expected, formatter_object):
    page = MoinParser.parse(data, 'PageName')
    assert formatter_object.format(page) == expected
    assert page.source_text == data
