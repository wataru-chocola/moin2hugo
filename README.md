# moin2hugo

Convert moinwiki's data directory into hugo content directory structure.

## Usage

## Configuration

Paramater | Default | Description
-- | -- | --
`moin_site_config.*` | - | see below
`hugo_config.*` | - | see below

### MoinSiteConfig

### HugoConfig

Hugo formatting configuration.

Paramater | Default | Description
-- | -- | --
`detect_table_header_heuristically` | `True` | make table header by heuristics
`increment_heading_level` | `True` | increment heading level (e.g. moin's h1 -> hugo's h2)
`root_path` | `/` | root path of hugo site in url
`goldmark_unsafe` | `True` | correspondings with hugo's config: `markup.goldman.render.goldmark_unsafe`
`disable_path_to_lower` | `True` | corrensponding with hugo's config: `disablePathLower`

## References

- [HelpOnMoinWikiSyntax - MoinMoin](http://moinmo.in/HelpOnMoinWikiSyntax)
- [yuin/goldmark: A markdown parser written in Go. Easy to extend, standard(CommonMark) compliant, well structured.](https://github.com/yuin/goldmark)
- [CommonMark Spec](https://spec.commonmark.org/)
