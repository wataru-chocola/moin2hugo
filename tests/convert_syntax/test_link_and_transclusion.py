import textwrap
from typing import Optional, Tuple
from unittest import mock

import pytest

from moin2hugo.config import HugoConfig
from moin2hugo.formatter.hugo import HugoFormatter
from moin2hugo.moin_parser import MoinParser
from moin2hugo.page_tree import AttachmentImage


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        ("MeatBall:InterWiki", r"MeatBall:InterWiki"),
        ("HelpOnEditing/SubPages", "[HelpOnEditing/SubPages](/HelpOnEditing/SubPages)"),
        ("PageName", "PageName"),
        ("!TestName", "!TestName"),
        ("fake@example.com", "<fake@example.com>"),
        ("https://www.markdownguide.org", "<https://www.markdownguide.org>"),
        ("[[free link]]", "[free link](/free-link)"),
        ("[[SomePage|Some Page]]", "[Some Page](/SomePage)"),
        (
            "[[SomePage#subsection|subsection of Some Page]]",
            "[subsection of Some Page](/SomePage#subsection)",
        ),  # noqa
        (
            "[[SomePage|{{attachment:image.png}}]]",
            '[![SomePage](image.png "SomePage")](/SomePage)',
        ),  # noqa
        ('[[SomePage|some Page|target="_blank"]]', "[some Page](/SomePage)"),
        ("[[attachment:SomePage/image.png]]", "[SomePage/image.png](/SomePage/image.png)"),
        (
            '[[attachment:SomePage/image.png|image.png|title="png"]]',
            '[image.png](/SomePage/image.png "png")',
        ),  # noqa
        ("[[drawing:SomePage/image.png]]", r"\[\[drawing:SomePage/image.png\]\]"),
        ("[[http://example.net/|example site]]", "[example site](http://example.net/)"),
        ("[[interwiki-like:somepage]]", r"[interwiki-like:somepage](interwiki-like-somepage)"),
        # rel links
        ("[[../RelPage|Relative Link]]", "[Relative Link](/RelPage)"),
        ("[[/RelPage|Relative Link]]", "[Relative Link](RelPage)"),
        # escape
        ("[[SomePage|Some[x]Page]]", "[Some\\[x\\]Page](/SomePage)"),
        (
            "[[SamePage#ああ|subsection of Some Page]]",
            "[subsection of Some Page](/SamePage#ああ)",
        ),  # noqa
        (
            "[[SamePage#%E3%81%82|subsection of Some Page]]",
            "[subsection of Some Page](/SamePage#%E3%81%82)",
        ),  # noqa
        (
            "[[SamePage#a(a)a|subsection of Some Page]]",
            "[subsection of Some Page](/SamePage#a\\(a\\)a)",
        ),  # noqa
        ("[[SamePage|su{{shortcode]]", r"[su\{\{shortcode](/SamePage)"),  # noqa
        ("https://www.markdownguide.org/<a>aa", "<https://www.markdownguide.org/\\<a\\>aa>"),
        ("https://www.markdownguide.org#a>aa", "<https://www.markdownguide.org#a\\>aa>"),
    ],
)
def test_links(data: str, expected: str):
    page = MoinParser.parse(data, "PageName")
    assert HugoFormatter.format(page, pagename="PageName") == expected
    assert page.source_text == data


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        # attachment
        ("{{attachment:image.png}}", "![](image.png)"),
        ("{{attachment:image.png|title}}", '![title](image.png "title")'),
        (
            "{{attachment:image.png|title|width=100,height=150,xxx=11}}",
            '{{< figure src="image.png" title="title" alt="title" width="100" height="150" >}}',
        ),  # noqa
        (
            "{{attachment:image.pdf}}",
            '<object data="image.pdf" type="application/pdf">image.pdf</object>',
        ),  # noqa
        # page
        (
            "{{pagename}}",
            '<object data="/pagename" type="text/html" width="100%">pagename</object>',
        ),  # noqa
        # drawing
        ("{{drawing:twikitest.tdraw}}", r"\{\{drawing:twikitest.tdraw\}\}"),
        # external graphic
        ("{{http://example.net/image.png}}", "![](http://example.net/image.png)"),
        (
            '{{http://example.net/image.png|alt text|align="position"}}',
            '![alt text](http://example.net/image.png "alt text")',
        ),  # noqa
        # escape
        ("{{http://example.net/im(a)ge.png}}", "![](http://example.net/im\\(a\\)ge.png)"),
        ('{{attachment:*a*.png|<"a">}}', '![\\<\\"a\\"\\>](a.png "\\<\\"a\\"\\>")'),  # noqa
        (
            "{{attachment:*a*.pdf}}",
            '<object data="a.pdf" type="application/pdf">*a*.pdf</object>',
        ),  # noqa
        (
            "{{attachment:<a>.pdf}}",
            '<object data="a.pdf" type="application/pdf">&lt;a&gt;.pdf</object>',
        ),  # noqa
    ],
)
def test_transclude(data: str, expected: str):
    page = MoinParser.parse(data, "PageName")
    assert HugoFormatter.format(page, pagename="PageName") == expected, page.tree_repr()
    assert page.source_text == data


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        ("{{attachment:image.png|title|width=100,height=150,xxx=test}}", ("100", "150")),
        # This comes from Moin-1.9's HelpOnLinking, but doesn't work (maybe bug)
        ("{{attachment:image.png|title|width=100 height=150}}", ("100 height=150", None)),
    ],
)
def test_transclude_attrs(data: str, expected: Tuple[Optional[str], Optional[str]]):
    page = MoinParser.parse(data, "PageName")
    attach_image = page.children[0].children[0]
    assert isinstance(attach_image, AttachmentImage)
    expected_width, expected_height = expected
    if expected_width is None:
        assert attach_image.attrs.width is None
    else:
        assert attach_image.attrs.width == expected_width
    if expected_height is None:
        assert attach_image.attrs.height is None
    else:
        assert attach_image.attrs.height == expected_height


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        ("{{attachment:image.pdf}}", r"\{\{attachment\:image.pdf\}\}"),
        ("{{attachment:<a>.pdf}}", r"\{\{attachment\:\<a\>.pdf\}\}"),
    ],
)
def test_transclude_without_unsafe(data: str, expected: str, caplog: pytest.LogCaptureFixture):
    page = MoinParser.parse(data, "PageName")
    ret = HugoFormatter.format(page, config=HugoConfig(goldmark_unsafe=False), pagename="PageName")
    assert ret == expected, page.tree_repr(include_src=True)
    assert "goldmark_unsafe" in caplog.text


@pytest.mark.parametrize(
    ("text", "content", "expected"),
    [
        (
            "{{attachment:text.txt}}",
            "hello",
            """\
         ```text
         hello
         ```

         [text.txt](text.txt)
         """,
        ),
        (
            "{{attachment:code.py}}",
            """\
         import sys
         sys.write("hello")
         """,
            """\
         ```python
         import sys
         sys.write("hello")
         ```

         [code.py](code.py)
         """,
        ),
        (
            "{{attachment:table.CSV}}",
            """\
         a,b,c
         d,e,f
         """,
            """\
         | a | b | c |
         |---|---|---|
         | d | e | f |

         [table.CSV](table.CSV)
         """,
        ),
    ],
)
def test_transclude_inline_attachment(text: str, content: str, expected: str):
    content = textwrap.dedent(content)
    expected = textwrap.dedent(expected).rstrip()
    mock_io = mock.mock_open(read_data=content)
    page = MoinParser.parse(text, "PageName")
    with mock.patch("moin2hugo.formatter.hugo.open", mock_io):
        assert HugoFormatter.format(page, pagename="PageName") == expected
    assert page.source_text == text
