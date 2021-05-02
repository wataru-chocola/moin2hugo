import pytest
import textwrap

from moin2hugo.path_builder import HugoPathBuilder
from moin2hugo.formatter import HugoFormatter
from moin2hugo.formatter.hugo_utils import comment_out_shortcode, escape_shortcode


@pytest.mark.parametrize(
    ("data", "expected"), [
        (("PageName", "PageName/foo"), "foo"),
        (("PageName/foo", "PageName/foo/bar"), "bar"),
        (("PageName/foo1", "PageName/foo2/bar"), "/PageName/foo2/bar"),
        ((None, "PageName"), "/PageName"),
        (("PageName/foo", "PageName/foo"), ""),
    ]
)
def test_page_url(data, expected):
    base, target = data
    path_builder = HugoPathBuilder(disable_path_to_lower=True)
    url = path_builder.page_url(target, base)
    assert url == expected


@pytest.mark.parametrize(
    ("data", "expected"), [
        (("PageName", "PageName/foo"), "foo"),
        (("PageName/foo1", "PageName/foo2/bar"), "/hugo/PageName/foo2/bar"),
    ]
)
def test_page_url_with_root_path(data, expected):
    base, target = data
    path_builder = HugoPathBuilder(disable_path_to_lower=True, root_path='/hugo')
    url = path_builder.page_url(target, base)
    assert url == expected


@pytest.mark.parametrize(
    ("data", "expected"), [
        (("PageName", "a.png", "PageName/foo"), "foo/a.png"),
        (("PageName/foo", "a.png", "PageName/foo/bar"), "bar/a.png"),
        (("PageName/foo1", "a.png", "PageName/foo2/bar"), "/PageName/foo2/bar/a.png"),
        ((None, "a.png", "PageName"), "/PageName/a.png"),
        (("PageName/foo", "a.png", "PageName/foo"), "a.png"),
    ]
)
def test_attachment_url(data, expected):
    base, filename, target = data
    path_builder = HugoPathBuilder(disable_path_to_lower=True)
    url = path_builder.attachment_url(target, filename, base)
    assert url == expected


@pytest.mark.parametrize(
    ("data", "expected"), [
        (("PageName", "a.png", "PageName/foo"), "foo/a.png"),
        (("PageName/foo1", "a.png", "PageName/foo2/bar"), "/hugo/PageName/foo2/bar/a.png"),
    ]
)
def test_attachment_url_with_root_path(data, expected):
    base, filename, target = data
    path_builder = HugoPathBuilder(disable_path_to_lower=True, root_path='/hugo')
    url = path_builder.attachment_url(target, filename, base)
    assert url == expected


@pytest.mark.parametrize(
    ("data", "expected"), [
        ('{{<abc>}}', '{{</*abc*/>}}'),
        ('{{< `abc` >}}', '{{</* `abc` */>}}'),
        ('{{%abc%}}', '{{%/*abc*/%}}'),
        ('{{<abc>}} {{<abc>}}', '{{</*abc*/>}} {{</*abc*/>}}'),

        ("""\
         {{< abc `bar
         baz` xyz >}}
         """,
         """\
         {{</* abc `bar
         baz` xyz */>}}
         """),

        ('{{<abc%}}', '{{<abc%}}'),
        ("""\
         {{< abc `bar
         baz xyz >}}
         """,
         """\
         {{< abc `bar
         baz xyz >}}
         """),
    ]
)
def test_comment_out_shortcoe(data, expected):
    data = textwrap.dedent(data)
    expected = textwrap.dedent(expected)
    ret = comment_out_shortcode(data)
    assert ret == expected


@pytest.mark.parametrize(
    ("data", "expected"), [
        ('{{<abc>}}', r'{{\<abc>}}'),
        ('{{< `abc` >}}', r'{{\< `abc` >}}'),
        ('{{%abc%}}', r'{{\%abc%}}'),
        ('{{<abc>}} {{<abc>}}', r'{{\<abc>}} {{\<abc>}}'),
    ]
)
def test_escape_shortcode_in_markdown(data, expected):
    data = textwrap.dedent(data)
    expected = textwrap.dedent(expected)
    ret = escape_shortcode(data)
    assert ret == expected


@pytest.mark.parametrize(
    ("data", "expected"), [
        ('{{<abc>}}', r'{{&lt;abc>}}'),
        ('{{< `abc` >}}', r'{{&lt; `abc` >}}'),
        ('{{%abc%}}', r'{{&#37;abc%}}'),
        ('{{<abc>}} {{<abc>}}', r'{{&lt;abc>}} {{&lt;abc>}}'),
    ]
)
def test_escape_shortcoe_in_html(data, expected):
    data = textwrap.dedent(data)
    expected = textwrap.dedent(expected)
    ret = escape_shortcode(data, in_html=True)
    assert ret == expected
