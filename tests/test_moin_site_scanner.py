from datetime import datetime, timedelta, timezone
from typing import TypeAlias

import pytest

from moin2x.moin_site_scanner import MoinAttachment, MoinPageInfo, MoinSiteScanner

from .conftest import MoinAbspathFixture, MoinSitedirFixture

MoinPagesFixture: TypeAlias = list[MoinPageInfo]


@pytest.fixture
def moin_pages(
    moin_sitedir: MoinSitedirFixture, moin_abspath: MoinAbspathFixture
) -> MoinPagesFixture:
    pages: list[MoinPageInfo] = []

    tokyo_tz = timezone(timedelta(hours=+9), "JST")
    pages.append(
        MoinPageInfo(
            name="FrontPage",
            filepath=moin_abspath("FrontPage/revisions/00000002"),
            updated=datetime(2019, 5, 22, 13, 16, 17, 699187, tzinfo=tokyo_tz),
            attachments=set([]),
        )
    )

    pages.append(
        MoinPageInfo(
            name="テスト",
            filepath=moin_abspath("(e38386e382b9e38388)/revisions/00000002"),
            updated=datetime(2019, 5, 22, 13, 54, 54, 621428, tzinfo=tokyo_tz),
            attachments=set(
                [
                    MoinAttachment(
                        name="file_example_JPG_100kB.jpg",
                        filepath=moin_abspath(
                            "(e38386e382b9e38388)/attachments/file_example_JPG_100kB.jpg"
                        ),
                    ),  # NOQA
                ]
            ),
        )
    )

    pages.append(
        MoinPageInfo(
            name="テスト/page_test/ページ",
            updated=datetime(2012, 2, 2, 18, 34, 47, tzinfo=tokyo_tz),
            filepath=moin_abspath(
                "(e38386e382b9e383882f)page_test(2fe3839ae383bce382b8)/revisions/00000003"
            ),  # NOQA
            attachments=set([]),
        )
    )

    pages.append(
        MoinPageInfo(
            name="テスト/attachments_test",
            updated=datetime(2019, 5, 22, 13, 54, 54, 621428, tzinfo=tokyo_tz),
            filepath=moin_abspath("(e38386e382b9e383882f)attachments_test/revisions/00000002"),
            attachments=set(
                [
                    MoinAttachment(
                        name="file_example_JPG_100kB.jpg",
                        filepath=moin_abspath(
                            "(e38386e382b9e383882f)attachments_test/attachments/file_example_JPG_100kB.jpg"
                        ),
                    ),  # NOQA
                    MoinAttachment(
                        name="file_example_PNG_500kB.png",
                        filepath=moin_abspath(
                            "(e38386e382b9e383882f)attachments_test/attachments/file_example_PNG_500kB.png"
                        ),
                    ),  # NOQA
                ]
            ),
        )
    )
    return pages


def test_scan_pages(moin_sitedir: MoinSitedirFixture, moin_pages: MoinPagesFixture):
    scanner = MoinSiteScanner(moin_sitedir)
    expected = moin_pages
    for page in scanner.scan_pages():
        for i, e in enumerate(expected):
            if page.name == e.name:
                assert page == e
                expected = expected[:i] + expected[i + 1 :]
                break
        else:
            raise AssertionError("%r in results doesn't exists in expected" % page)

    if expected:
        raise AssertionError("expected elems are missing: %r" % expected)
