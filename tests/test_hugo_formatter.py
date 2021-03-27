from moin2hugo.formatter import HugoFormatter
from moin2hugo.page_tree import PageRoot, Text, ParsedText, Paragraph, Remark, Strong

import pytest
import textwrap


@pytest.mark.parametrize(
    ("data", "expected"), [
        ({'children': [
            (Paragraph, {'children': [
                (Text, {'content': 'before'}),
                (Text, {'content': 'after'}),
            ]})]},
         {'children': [
            (Paragraph, {'children': [
                (Text, {'content': 'beforeafter'}),
            ]})]}
         ),
        ({'children': [
            (Paragraph, {'children': [
                (Text, {'content': 'before'}),
                (Remark, {'content': 'inline comment'}),
                (Text, {'content': 'after'}),
            ]})]},
         {'children': [
            (Paragraph, {'children': [
                (Text, {'content': 'beforeafter'}),
            ]})]}
         ),
        ({'children': [
            (Paragraph, {'children': [
                (Text, {'content': 'before'}),
                (Strong, {'content': 'inline comment'}),
                (Text, {'content': 'after'}),
            ]})]},
         {'children': [
            (Paragraph, {'children': [
                (Text, {'content': 'before'}),
                (Strong, {'content': 'inline comment'}),
                (Text, {'content': 'after'}),
            ]})]}
         ),
        ]
)
def test_consolidate(data, expected):
    formatter = HugoFormatter()
    data_page = PageRoot.from_dict(data)
    expected_page = PageRoot.from_dict(expected)
    ret = formatter._consolidate(data_page)
    assert ret == expected_page


@pytest.mark.parametrize(
    ("data", "expected"), [
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
        ("[aa](something)", r"\[aa\]\(something\)"),
        ("[aa][1]", r"\[aa\]\[1\]"),
        ("[1]: something", r"\[1\]\: something"),
        ("![aa](something)", r"\!\[aa\]\(something\)"),
        ("<fake@example.com>", r"\<fake@example.com\>"),
        (r"\10,000", r"\\10,000"),
        (r"{{% test %}}", r"\{\{% test %\}\}"),
        ("abc | def", r"abc \| def"),

        # extended markdown
        ("```\ncode\n```", "\\`\\`\\`\ncode\n\\`\\`\\`"),
        ("[^1]: test", r"\[^1\]\: test"),
        ("Heading {#custom-id}", r"Heading \{\#custom-id\}"),
        ("Term\n: Desc", "Term\n\\: Desc"),
        ("~~Test~~", r"\~\~Test\~\~"),
        (":smiley:", r"\:smiley\:"),

        # don't do unnecessary escaping which spoils readability.
        ("1 + 2", "1 + 2"),
        ("1 - 2", "1 - 2"),
        ("hello, world!", "hello, world!"),

        ("<br>", r"\<br\>"),
    ]
)
def test_text_escape(data, expected):
    text = Text(data)
    assert HugoFormatter.format(text) == expected


@pytest.mark.parametrize(
    ("data", "expected"), [
        ("""\
         line 1
         <>!{}()*_-
         """,
         """\
         ```
         line 1
         <>!{}()*_-
         ```
         """),
        ("""\
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
         """),

    ]
)
def test_codeblock(data, expected):
    data = textwrap.dedent(data)
    expected = textwrap.dedent(expected).rstrip()

    e = ParsedText(content=data)
    assert HugoFormatter.format(e) == expected
