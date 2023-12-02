from moin2x.page_tree import Link, PageRoot, Paragraph, Text


def test_initialize_page_elements():
    PageRoot()
    Text(content="test")


def test_from_dict():
    expected = PageRoot()
    p = Paragraph()
    text = Text(content="link: ")
    link = Link(url="http://example.com")
    p.add_child(text)
    p.add_child(link)
    expected.add_child(p)

    page_dict = {
        "children": [
            (
                Paragraph,
                {
                    "children": [
                        (Text, {"content": "link: "}),
                        (Link, {"url": "http://example.com"}),
                    ]
                },
            )
        ]
    }
    ret = PageRoot.from_dict(page_dict)
    assert ret == expected


def test_content_hash():
    text1 = Text(content="text")
    text2 = Text(content="text")
    assert text1.content_hash == text2.content_hash

    text3 = Text(content="text modified")
    assert text1.content_hash != text3.content_hash

    link1 = Link(url="http://example.com/path1")
    link2 = Link(url="http://example.com/path2")
    assert link1.content_hash != link2.content_hash

    page1 = Paragraph()
    page1.add_child(Text(content="text"))
    page2 = Paragraph()
    page2.add_child(Text(content="text"))
    assert page1.content_hash == page2.content_hash
    assert page1.content_hash != text1.content_hash

    page3 = Paragraph()
    page3.add_child(Text(content="text modified"))
    assert page1.content_hash != page3.content_hash
