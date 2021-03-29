from moin2hugo.moin_parser import MoinParser
from moin2hugo.formatter.hugo import HugoFormatter
from moin2hugo.page_tree import AttachmentImage
from moin2hugo.config import HugoConfig

import pytest
from unittest import mock


@pytest.mark.parametrize(
    ("data", "expected"), [
        ("MeatBall:InterWiki", r"MeatBall:InterWiki"),
        ("HelpOnEditing/SubPages", "[HelpOnEditing/SubPages](/HelpOnEditing/SubPages)"),
        ("PageName", "PageName"),
        ("!TestName", "!TestName"),
        ("fake@example.com", "<fake@example.com>"),
        ("https://www.markdownguide.org", "<https://www.markdownguide.org>"),
        ('[[free link]]', '[free link](/free%20link)'),
        ('[[SomePage|Some Page]]', '[Some Page](/SomePage)'),
        ('[[SomePage#subsection|subsection of Some Page]]', '[subsection of Some Page](/SomePage#subsection)'),  # noqa
        ('[[SomePage|{{attachment:image.png}}]]', '[![SomePage](image.png "SomePage")](/SomePage)'),  # noqa
        ('[[SomePage|some Page|target="_blank"]]', '[some Page](/SomePage)'),
        ('[[attachment:SomePage/image.png]]', '[SomePage/image.png](/SomePage/image.png)'),
        ('[[attachment:SomePage/image.png|image.png|title="png"]]', '[image.png](/SomePage/image.png "png")'),  # noqa
        ('[[drawing:SomePage/image.png]]', r'\[\[drawing:SomePage/image.png\]\]'),
        ('[[http://example.net/|example site]]', '[example site](http://example.net/)'),
        ('[[otherwiki:somepage]]', r'\[\[otherwiki:somepage\]\]'),

        # rel links
        ('[[../RelPage|Relative Link]]', '[Relative Link](/RelPage)'),
        ('[[/RelPage|Relative Link]]', '[Relative Link](RelPage)'),

        # escape
        ('[[SomePage|Some[x]Page]]', '[Some\\[x\\]Page](/SomePage)'),
        ('[[SamePage#ああ|subsection of Some Page]]', '[subsection of Some Page](/SamePage#ああ)'),  # noqa
        ('[[SamePage#%E3%81%82|subsection of Some Page]]', '[subsection of Some Page](/SamePage#%E3%81%82)'),  # noqa
        ('[[SamePage#a(a)a|subsection of Some Page]]', '[subsection of Some Page](/SamePage#a\\(a\\)a)'),  # noqa
        ("https://www.markdownguide.org/<a>aa", "<https://www.markdownguide.org/\\<a\\>aa>"),
        ("https://www.markdownguide.org#a>aa", "<https://www.markdownguide.org#a\\>aa>"),
    ]
)
def test_links(data, expected):
    page = MoinParser.parse(data, 'PageName')
    assert HugoFormatter.format(page, pagename='PageName') == expected
    assert page.source_text == data


@pytest.mark.parametrize(
    ("data", "expected"), [
        # attachment
        ("{{attachment:image.png}}", "![](image.png)"),
        ("{{attachment:image.png|title}}", '![title](image.png "title")'),
        ('{{attachment:image.png|title|width=100 height=150 xxx=11}}', '![title](image.png "title")'),  # noqa
        ("{{attachment:image.txt}}", "```\nhello\n```\n\n[image.txt](image.txt)"),
        ("{{attachment:image.pdf}}", '<object data="image.pdf" type="application/pdf">image.pdf</object>'),  # noqa
        # page
        ("{{pagename}}", '<object data="/pagename" type="text/html" width="100%">pagename</object>'),  # noqa
        # drawing
        ("{{drawing:twikitest.tdraw}}", r"\{\{drawing:twikitest.tdraw\}\}"),
        # external graphic
        ("{{http://example.net/image.png}}", "![](http://example.net/image.png)"),
        ('{{http://example.net/image.png|alt text|align="position"}}', '![alt text](http://example.net/image.png "alt text")'),  # noqa

        # escape
        ("{{http://example.net/im(a)ge.png}}", "![](http://example.net/im\\(a\\)ge.png)"),
        ('{{attachment:*a*.png|<"a">}}', '![\\<\\"a\\"\\>](%2Aa%2A.png "\\<\\"a\\"\\>")'),  # noqa
        ("{{attachment:*a*.pdf}}", '<object data="%2Aa%2A.pdf" type="application/pdf">*a*.pdf</object>'),  # noqa
        ("{{attachment:<a>.pdf}}", '<object data="%3Ca%3E.pdf" type="application/pdf">&lt;a&gt;.pdf</object>'),  # noqa
    ]
)
def test_transclude(data, expected):
    mock_io = mock.mock_open(read_data="hello")
    page = MoinParser.parse(data, 'PageName')
    with mock.patch('moin2hugo.formatter.hugo.open', mock_io):
        assert HugoFormatter.format(page, pagename='PageName') == expected
    assert page.source_text == data


@pytest.mark.parametrize(
    ("data", "expected"), [
        ('{{attachment:image.png|title|width=100,height=150,xxx=test}}', ('100', '150')),

        # This comes from Moin-1.9's HelpOnLinking, but doesn't work (maybe bug)
        ('{{attachment:image.png|title|width=100 height=150}}', ('100 height=150', None)),
    ]
)
def test_transclude_attrs(data, expected):
    page = MoinParser.parse(data, 'PageName')
    attach_image: AttachmentImage = page.children[0].children[0]
    expected_width, expected_height = expected
    assert isinstance(attach_image, AttachmentImage)
    if expected_width is None:
        assert attach_image.attrs.width is None
    else:
        assert attach_image.attrs.width == expected_width
    if expected_height is None:
        assert attach_image.attrs.height is None
    else:
        assert attach_image.attrs.height == expected_height


@pytest.mark.parametrize(
    ("data", "expected"), [
        ("{{attachment:image.pdf}}", r'\{\{attachment\:image.pdf\}\}'),
        ("{{attachment:<a>.pdf}}", r'\{\{attachment\:\<a\>.pdf\}\}'),
    ]
)
def test_transclude_without_unsafe(data, expected, caplog):
    page = MoinParser.parse(data, 'PageName')
    ret = HugoFormatter.format(page, config=HugoConfig(goldmark_unsafe=False), pagename='PageName')
    assert ret == expected, page.tree_repr(include_src=True)
    assert 'goldmark_unsafe' in caplog.text
