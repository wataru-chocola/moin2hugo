from moin2hugo.page_tree import PageRoot, Paragraph, Text, Link


def test_initialize_page_elements():
    PageRoot()
    Text(content="test")


def test_from_dict():
    expected = PageRoot()
    p = Paragraph()
    text = Text(content="link: ")
    link = Link(target="http://example.com", title="test link")
    p.add_child(text)
    p.add_child(link)
    expected.add_child(p)

    page_dict = {
        'children': [
            (Paragraph, {
                'children': [
                    (Text, {'content': 'link: '}),
                    (Link, {'target': 'http://example.com', 'title': 'test link'})
                ]})
        ]
    }
    ret = PageRoot.from_dict(page_dict)
    assert ret == expected
