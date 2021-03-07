import pytest
import textwrap

from moin2hugo.moin_parser import MoinParser, _getTableAttrs
from moin2hugo.formatter import Formatter


@pytest.fixture
def formatter_object():
    return Formatter()


@pytest.mark.parametrize(
    ("data", "expected"), [
        (":)", ":simple_smile:"),
    ]
)
def test_smiley(data, expected, formatter_object):
    page = MoinParser.parse(data, 'PageName', formatter_object)
    # TODO: remove trailing space
    ret = formatter_object.format(page).rstrip()
    assert ret == expected


def test_codeblock(formatter_object):
    code_block_text = """\
    {{{#!highlight python
    import sys
    sys.out.write("Hello, World")
    }}}
    """
    expected = """\
    ```python
    import sys
    sys.out.write("Hello, World")
    ```
    """
    page = MoinParser.parse(textwrap.dedent(code_block_text), 'PageName', formatter_object)
    expected = textwrap.dedent(expected).rstrip()
    assert formatter_object.format(page) == expected


@pytest.mark.parametrize(
    ("data", "expected"), [
        ('<bgcolor="#00FF00" rowspan="2">', {'bgcolor': '"#00FF00"', 'rowspan': '"2"'}),
        ('<#TGIF rowspan="2">', {}),
    ]
)
def test_getTableAttrs(data, expected, formatter_object):
    ret = _getTableAttrs(data)
    assert ret == expected


@pytest.mark.parametrize(
    ("data", "expected"), [
        ("= head1 =", "# head1\n\n"),
        ("===== head5 =====", "##### head5\n\n"),
        ("====== head5 ======", "##### head5\n\n"),
    ]
)
def test_heading(data, expected, formatter_object):
    page = MoinParser.parse(data, 'PageName', formatter_object)
    assert formatter_object.format(page) == expected


@pytest.mark.parametrize(
    # TODO: remove trailing spaces
    ("data", "expected"), [
        ("----", "----\n\n "),
        ("-----------------", "----\n\n "),
    ]
)
def test_horizontal_rules(data, expected, formatter_object):
    page = MoinParser.parse(data, 'PageName', formatter_object)
    assert formatter_object.format(page) == expected


@pytest.mark.parametrize(
    ("data", "expected"), [
        # TODO: remove trailing spaces
        ("__underlined text__", "__underlined text __"),
        ("__underlined\ntext__", "__underlined text __"),
        ("--(stroke)--", "~~stroke ~~"),
        ("''italic''", "*italic *"),
        ("'''strong'''", "**strong **"),
        ("'''''italic and strong'''''", "***italic and strong ***"),
        ("''this is italic and '''this is strong'''''", "*this is italic and **this is strong ***"),
        ("'''this is strong and ''this is italic'''''", "**this is strong and *this is italic ***"),
        ("~-smaller-~", "<small>smaller </small>"),   # TODO
        ("~+larger+~", "<big>larger </big>"),   # TODO
    ]
)
def test_decorations_ml(data, expected, formatter_object):
    page = MoinParser.parse(data, 'PageName', formatter_object)
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
    page = MoinParser.parse(data, 'PageName', formatter_object)
    # TODO: remove trailing space
    ret = formatter_object.format(page).rstrip()
    assert ret == expected


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
def test_links(data, expected, formatter_object):
    page = MoinParser.parse(data, 'PageName', formatter_object)
    # TODO: remove trailing space
    ret = formatter_object.format(page).rstrip()
    assert ret == expected


@pytest.mark.parametrize(
    ("data", "expected"), [
        ("&uuml;", "&uuml;"),
        ("&#42;", "&#42;"),
        ("&#x42;", "&#x42;"),
    ]
)
def test_entities(data, expected, formatter_object):
    page = MoinParser.parse(data, 'PageName', formatter_object)
    # TODO: remove rstrip()
    assert formatter_object.format(page).rstrip() == expected


# TODO:
# @pytest.mark.skip("not implemented")
@pytest.mark.parametrize(
    ("data", "expected"), [
        # (" . hoge", "* hoge"),
        (" * hoge", "* hoge \n"),
        # (" 1. hoge", "1. hoge"),
        # (" a. hoge", "1. hoge"),
    ]
)
def test_itemlists(data, expected, formatter_object):
    page = MoinParser.parse(data, 'PageName', formatter_object)
    assert formatter_object.format(page) == expected


@pytest.mark.parametrize(
    ("data", "expected"), [
        ("{{drawing:twikitest.tdraw}}", "{{drawing:twikitest.tdraw}}"),
    ]
)
def test_transclude(data, expected, formatter_object):
    page = MoinParser.parse(data, 'PageName', formatter_object)
    # TODO: remove rstrip()
    assert formatter_object.format(page).rstrip() == expected
