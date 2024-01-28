import textwrap
from typing import Any

import pytest

from moin2kibun.config import FormatConfig
from moin2kibun.formatter import KibunFormatter
from moin2kibun.path_builder import KibunPathBuilder
from moin2x.page_tree import Pagelink, PageRoot, Paragraph, ParsedText, Remark, Strong, Text


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        (
            {
                "children": [
                    (
                        Paragraph,
                        {
                            "children": [
                                (Text, {"content": "before"}),
                                (Text, {"content": "after"}),
                            ]
                        },
                    )
                ]
            },
            {
                "children": [
                    (
                        Paragraph,
                        {
                            "children": [
                                (Text, {"content": "beforeafter"}),
                            ]
                        },
                    )
                ]
            },
        ),
        (
            {
                "children": [
                    (
                        Paragraph,
                        {
                            "children": [
                                (Text, {"content": "before"}),
                                (Remark, {"content": "inline comment"}),
                                (Text, {"content": "after"}),
                            ]
                        },
                    )
                ]
            },
            {
                "children": [
                    (
                        Paragraph,
                        {
                            "children": [
                                (Text, {"content": "beforeafter"}),
                            ]
                        },
                    )
                ]
            },
        ),
        (
            {
                "children": [
                    (
                        Paragraph,
                        {
                            "children": [
                                (Text, {"content": "before"}),
                                (Strong, {"content": "inline comment"}),
                                (Text, {"content": "after"}),
                            ]
                        },
                    )
                ]
            },
            {
                "children": [
                    (
                        Paragraph,
                        {
                            "children": [
                                (Text, {"content": "before"}),
                                (Strong, {"content": "inline comment"}),
                                (Text, {"content": "after"}),
                            ]
                        },
                    )
                ]
            },
        ),
    ],
)
def test_consolidate(data: dict[str, Any], expected: dict[str, Any]):
    formatter = KibunFormatter()
    data_page = PageRoot.from_dict(data)
    expected_page = PageRoot.from_dict(expected)
    ret = formatter._consolidate(data_page)  # type: ignore
    assert ret == expected_page


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        ("## hello", r"\#\# hello"),
        ("test\n====", "test\n\\=\\=\\=\\="),
        ("test\n----", "test\n\\-\\-\\-\\-"),
        ("line with spaces  \ntest", "line with spaces\ntest"),
        ("__test__", r"\_\_test\_\_"),
        ("_test_", r"\_test\_"),
        ("***", r"\*\*\*"),
        ("> something", r"\> something"),
        ("something >", r"something \>"),
        ("1. test", r"1\. test"),
        ("- test", r"\- test"),
        ("* test", r"\* test"),
        ("+ test", r"\+ test"),
        ("    foo\n  bar", "foo\nbar"),
        ("`test`", r"\`test\`"),
        ("---\n", "\\-\\-\\-\n"),
        ("[aa](something)", r"\[aa\](something)"),
        ("[aa][1]", r"\[aa\]\[1\]"),
        ("[1]: something", r"\[1\]: something"),
        ("![aa](something)", r"\!\[aa\](something)"),
        ("<fake@example.com>", r"\<fake@example.com\>"),
        (r"\10,000", r"\\10,000"),
        (r"{{% test %}}", r"\{\{% test %\}\}"),
        ("abc | def", r"abc \| def"),
        # extended markdown
        ("```\ncode\n```", "\\`\\`\\`\ncode\n\\`\\`\\`"),
        ("[^1]: test", r"\[^1\]: test"),
        ("Heading {#custom-id}", r"Heading \{\#custom-id\}"),
        ("Term\n: Desc", "Term\n: Desc"),
        ("~~Test~~", r"\~\~Test\~\~"),
        (":smiley:", r"\:smiley\:"),
        # don't do unnecessary escaping which spoils readability.
        ("1 + 2", "1 + 2"),
        ("1 - 2", "1 - 2"),
        ("hello, world!", "hello, world!"),
        ("term: definition", "term: definition"),
        ("word (desc)", "word (desc)"),
        ("<br>", r"\<br\>"),
    ],
)
def test_text_escape(data: str, expected: str):
    text = Text(data)
    assert KibunFormatter.format(text) == expected


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        (
            """\
         line 1
         <>!{}()*_-
         """,
            """\
         ```
         line 1
         <>!{}()*_-
         ```
         """,
        ),
        (
            """\
         line 1
         ```
         <>!{}()*_-
         """,
            """\
         ````
         line 1
         ```
         <>!{}()*_-
         ````
         """,
        ),
    ],
)
def test_codeblock(data: str, expected: str):
    data = textwrap.dedent(data)
    expected = textwrap.dedent(expected).rstrip()

    e = ParsedText(content=data)
    assert KibunFormatter.format(e) == expected


def test_root_path():
    pagelink = Pagelink(pagename="SomePage")
    config = FormatConfig(root_path="/kibun")
    kibun_path_builder = KibunPathBuilder(root_path=config.root_path)
    ret = KibunFormatter.format(
        pagelink, pagename="PageName", config=config, path_builder=kibun_path_builder
    )
    assert ret == "[](/kibun/SomePage)"
