import pytest

from moin2kibun.config import FormatConfig
from moin2kibun.formatter import KibunFormatter
from moin2x.moin_parser import MoinParser


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        ("= head1 =", "## head1\n\n"),
        ("= head1 =\n", "## head1\n\n"),
        ("===== head5 =====", "###### head5\n\n"),
        ("====== head5 ======", "###### head5\n\n"),
        ("====== *head* #5 ======", "###### \\*head\\* \\#5\n\n"),
    ],
)
def test_heading_with_incremented_header_level(data: str, expected: str):
    page = MoinParser.parse(data, "PageName")
    assert KibunFormatter.format(page, pagename="PageName") == expected
    assert page.source_text == data


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        ("= head1 =", "# head1\n\n"),
        ("= head1 =\n", "# head1\n\n"),
        ("===== head5 =====", "##### head5\n\n"),
        ("====== head5 ======", "##### head5\n\n"),
        ("====== *head* #5 ======", "##### \\*head\\* \\#5\n\n"),
    ],
)
def test_heading_without_incremented_header_level(data: str, expected: str):
    page = MoinParser.parse(data, "PageName")
    kibun_config = FormatConfig(increment_heading_level=False)
    assert KibunFormatter.format(page, pagename="PageName", config=kibun_config) == expected
    assert page.source_text == data


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        ("----", "----\n\n"),
        ("-----------------", "----\n\n"),
    ],
)
def test_horizontal_rules(data: str, expected: str):
    page = MoinParser.parse(data, "PageName")
    assert KibunFormatter.format(page, pagename="PageName") == expected
    assert page.source_text == data
