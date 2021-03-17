from moin2hugo.moin_parser import MoinParser

import pytest
from unittest import mock


@pytest.mark.parametrize(
    ("data", "expected"), [
        ("MeatBall:InterWiki", r"MeatBall\:InterWiki"),
        ("HelpOnEditing/SubPages", "[HelpOnEditing/SubPages](url/HelpOnEditing/SubPages)"),
        ("PageName", "PageName"),
        ("!TestName", "!TestName"),
        ("fake@example.com", "<fake@example.com>"),
        ("https://www.markdownguide.org", "<https://www.markdownguide.org>"),
        ('[[free link]]', '[free link](url/free%20link)'),
        ('[[SomePage|Some Page]]', '[Some Page](url/SomePage)'),
        ('[[SamePage#subsection|subsection of Some Page]]', '[subsection of Some Page](url/SamePage#subsection)'),  # noqa
        ('[[SomePage|{{attachment:image.png}}]]', '[![](url/PageName/image.png "SomePage")](url/SomePage)'),  # noqa
        ('[[SomePage|some Page|target="_blank"]]', '[some Page](url/SomePage)'),
        ('[[attachment:SomePage/image.png]]', '[SomePage/image.png](url/SomePage/image.png)'),
        ('[[attachment:SomePage/image.png|image.png|title="png"]]', '[image.png](url/SomePage/image.png "png")'),  # noqa
        ('[[drawing:SomePage/image.png]]', r'\[\[drawing\:SomePage/image.png\]\]'),
        ('[[http://example.net/|example site]]', '[example site](http://example.net/)'),
        ('[[otherwiki:somepage]]', r'otherwiki\:somepage'),

        # escape
        ('[[SomePage|Some[x]Page]]', '[Some\\[x\\]Page](url/SomePage)'),
        ('[[SamePage#ああ|subsection of Some Page]]', '[subsection of Some Page](url/SamePage#ああ)'),  # noqa
        ('[[SamePage#%E3%81%82|subsection of Some Page]]', '[subsection of Some Page](url/SamePage#%E3%81%82)'),  # noqa
        ('[[SamePage#a(a)a|subsection of Some Page]]', '[subsection of Some Page](url/SamePage#a\\(a\\)a)'),  # noqa
        ("https://www.markdownguide.org/<a>aa", "<https://www.markdownguide.org/\\<a\\>aa>"),
        ("https://www.markdownguide.org#a>aa", "<https://www.markdownguide.org#a\\>aa>"),
    ]
)
def test_links(data, expected, formatter_object):
    page = MoinParser.parse(data, 'PageName')
    assert formatter_object.format(page) == expected


@pytest.mark.parametrize(
    ("data", "expected"), [
        # attachment
        ("{{attachment:image.png}}", "![](url/PageName/image.png)"),
        ("{{attachment:image.png|title}}", '![](url/PageName/image.png "title")'),
        ('{{attachment:image.png|title|width=100 height=150 xxx=11}}', '![](url/PageName/image.png "title")'),  # noqa
        ("{{attachment:image.txt}}", "```\nhello\n```\n\n[image.txt](url/PageName/image.txt)"),
        ("{{attachment:image.pdf}}", '<object data="url/PageName/image.pdf" type="application/pdf">image.pdf</object>'),  # noqa
        # page
        ("{{pagename}}", '<object data="url/pagename" type="text/html">pagename</object>'),
        # drawing
        ("{{drawing:twikitest.tdraw}}", r"\{\{drawing\:twikitest.tdraw\}\}"),
        # external graphic
        ("{{http://example.net/image.png}}", "![](http://example.net/image.png)"),
        ('{{http://example.net/image.png|alt text|align="position"}}', '![alt text](http://example.net/image.png "alt text")'),  # noqa

        # escape
        ("{{http://example.net/im(a)ge.png}}", "![](http://example.net/im\\(a\\)ge.png)"),
        ('{{attachment:*a*.png|<"a">}}', '![](url/PageName/%2Aa%2A.png "\\<\\"a\\"\\>")'),
        ("{{attachment:*a*.pdf}}", '<object data="url/PageName/%2Aa%2A.pdf" type="application/pdf">*a*.pdf</object>'),  # noqa
        ("{{attachment:<a>.pdf}}", '<object data="url/PageName/%3Ca%3E.pdf" type="application/pdf">&lt;a&gt;.pdf</object>'),  # noqa
    ]
)
def test_transclude(data, expected, formatter_object):
    mock_io = mock.mock_open(read_data="hello")
    page = MoinParser.parse(data, 'PageName')
    with mock.patch('moin2hugo.formatter.open', mock_io):
        assert formatter_object.format(page) == expected
