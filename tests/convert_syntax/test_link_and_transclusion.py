from moin2hugo.moin_parser import MoinParser

import pytest
from unittest import mock


@pytest.mark.parametrize(
    ("data", "expected"), [
        ("MeatBall:InterWiki", "MeatBall:InterWiki"),
        ("HelpOnEditing/SubPages", "[HelpOnEditing/SubPages](HelpOnEditing/SubPages)"),
        ("PageName", "PageName"),
        ("!TestName", "!TestName"),
        ("fake@example.com", "<fake@example.com>"),
        ("https://www.markdownguide.org", "<https://www.markdownguide.org>"),
        ('[[free link]]', '[free link](free link)'),
        ('[[SomePage|Some Page]]', '[Some Page](SomePage)'),
        ('[[SamePage#subsection|subsection of Some Page]]', '[subsection of Some Page](SamePage#subsection)'),  # noqa
        ('[[SomePage|{{attachment:imagefile.png}}]]', '[![](filepath/PageName/imagefile.png "SomePage")](SomePage)'),  # noqa
        ('[[SomePage|some Page|target="_blank"]]', '[some Page](SomePage)'),
        ('[[attachment:SomePage/image.png]]', '[SomePage/image.png](SomePage/image.png)'),
        ('[[attachment:SomePage/image.png|image.png|title="png"]]', '[image.png](SomePage/image.png "png")'),  # noqa
        ('[[drawing:SomePage/image.png]]', '[[drawing:SomePage/image.png]]'),
        ('[[http://example.net/|example site]]', '[example site](http://example.net/)'),
        ('[[otherwiki:somepage]]', 'otherwiki:somepage'),
    ]
)
def test_links(data, expected, formatter_object):
    page = MoinParser.parse(data, 'PageName')
    assert formatter_object.format(page) == expected


@pytest.mark.parametrize(
    ("data", "expected"), [
        # attachment
        ("{{attachment:image.png}}", "![](filepath/PageName/image.png)"),
        ("{{attachment:image.png|title}}", '![](filepath/PageName/image.png "title")'),
        ('{{attachment:image.png|title|width=100 height=150 xxx=11}}', '![](filepath/PageName/image.png "title")'),  # noqa
        ("{{attachment:image.txt}}", "```\nhello\n```\n\n[image.txt](url/PageName/image.txt)"),
        ("{{attachment:image.pdf}}", '<object data="url/PageName/image.pdf" type="application/pdf">image.pdf</object>'),  # noqa
        # page
        ("{{pagename}}", '<object data="url/pagename" type="text/html">pagename</object>'),
        # drawing
        ("{{drawing:twikitest.tdraw}}", "{{drawing:twikitest.tdraw}}"),
        # external graphic
        ("{{http://example.net/image.png}}", "![](http://example.net/image.png)"),
        ('{{http://example.net/image.png|alt text|align="position"}}', '![alt text](http://example.net/image.png "alt text")'),  # noqa
    ]
)
def test_transclude(data, expected, formatter_object):
    mock_io = mock.mock_open(read_data="hello")
    page = MoinParser.parse(data, 'PageName')
    with mock.patch('moin2hugo.formatter.open', mock_io):
        assert formatter_object.format(page) == expected



