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
    MoinParser.format(data, 'PageName', formatter_object)
    captured = capsys.readouterr()
    assert captured.out == expected


@pytest.mark.parametrize(
    ("data", "expected"), [
        ("----", "----\n\n"),
        ("-----------------", "----\n\n"),
    ]
)
def test_horizontal_rules(data, expected, formatter_object, capsys):
    MoinParser.format(data, 'PageName', formatter_object)
    captured = capsys.readouterr()
    # TODO: remove rstrip()
    assert captured.out.rstrip(' ') == expected


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
    MoinParser.format(data, 'PageName', formatter_object)
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
    MoinParser.format(data, 'PageName', formatter_object)
    captured = capsys.readouterr()
    # TODO: remove rstrip()
    assert captured.out.rstrip() == expected


@pytest.mark.parametrize(
    ("data", "expected"), [
        ("MeatBall:InterWiki", "MeatBall:InterWiki"),
        ("HelpOnEditing/SubPages", "[HelpOnEditing/SubPages](HelpOnEditing/SubPages)"),
        ("PageName", "PageName"),
        ("!TestName", "!TestName"),
        ("fake@example.com", "<fake@example.com>"),
        ("https://www.markdownguide.org", "<https://www.markdownguide.org>"),
        ('[[free link]]', '[free link](free link)'),
        ('[[SamePage|Some Page]]', '[Some Page](SamePage)'),
        ('[[SamePage#subsection|subsection of Some Page]]', '[subsection of Some Page](SamePage#subsection)'),  # noqa
        # TODO: ('[[SomePage|{{attachment:imagefile.png}}]]', ''),
        # TODO: ('[[SomePage|some Page|target="_blank"]]', ''),
        ('[[attachment:SomePage/image.png]]', '[SomePage/image.png](SomePage/image.png)'),
        ('[[attachment:SomePage/image.png|image.png|title="png"]]', '[image.png](SomePage/image.png "png")'),  # noqa
        ('[[drawing:SomePage/image.png]]', '[[drawing:SomePage/image.png]]'),
        ('[[http://example.net/|example site]]', '[example site](http://example.net/)'),
        ('[[otherwiki:somepage]]', 'otherwiki:somepage'),
    ]
)
def test_links(data, expected, formatter_object, capsys):
    MoinParser.format(data, 'PageName', formatter_object)
    captured = capsys.readouterr()
    # TODO: remove rstrip()
    assert captured.out.rstrip() == expected


@pytest.mark.parametrize(
    ("data", "expected"), [
        ("&uuml;", "&uuml;"),
        ("&#42;", "&#42;"),
        ("&#x42;", "&#x42;"),
    ]
)
def test_entities(data, expected, formatter_object, capsys):
    MoinParser.format(data, 'PageName', formatter_object)
    captured = capsys.readouterr()
    # TODO: remove rstrip()
    assert captured.out.rstrip() == expected


# TODO:
@pytest.mark.skip("not implemented")
@pytest.mark.parametrize(
    ("data", "expected"), [
        (" . hoge", "* hoge"),
        (" * hoge", "* hoge"),
        (" 1. hoge", "1. hoge"),
        (" a. hoge", "1. hoge"),
    ]
)
def test_item_lists(data, expected, formatter_object, capsys):
    MoinParser.format(data, 'PageName', formatter_object)
    captured = capsys.readouterr()
    # TODO: remove rstrip()
    assert captured.out.rstrip() == expected


@pytest.mark.parametrize(
    ("data", "expected"), [
        ("{{drawing:twikitest.tdraw}}", "{{drawing:twikitest.tdraw}}"),
    ]
)
def test_transclude(data, expected, formatter_object, capsys):
    MoinParser.format(data, 'PageName', formatter_object)
    captured = capsys.readouterr()
    # TODO: remove rstrip()
    assert captured.out.rstrip() == expected
