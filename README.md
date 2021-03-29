# moin2hugo

> A converter from MoinMoin wiki (moinwiki) data directory to hugo content directory.

Moin2Hugo converts moinmoin site directory to hugo content directory.

* Convert syntax directory (without going through transforming to HTML).
* Generate clean and tidy markdown source text.
* Keep semantics as possible.


## Usage

```
Usage: moin2hugo [OPTIONS] SRC DST

  Convert moinmoin site directory to hugo content directory.

Options:
  -c, --config PATH
  -v, --verbose
  --help             Show this message and exit.
```

## Configuration

Paramater | Default | Description
-- | -- | --
`moin_site_config.*` | - | see below
`hugo_config.*` | - | see below

### MoinSiteConfig

Moin wiki parser configuration.

Paramater | Default | Description
-- | -- | --
`bang_meta` |`True` | corresponding with moin site config: `bang_meta`

### HugoConfig

Hugo formatting configuration.

Paramater | Default | Description
-- | -- | --
`detect_table_header_heuristically` | `True` | make table header by heuristics
`increment_heading_level` | `True` | increment heading level (e.g. moin's h1 -> hugo's h2)
`root_path` | `/` | root path of hugo site in url
`use_figure_shortcode` | `True` | use `figure` shortcode
`goldmark_unsafe` | `True` | corresponding with hugo config: `markup.goldman.render.goldmark_unsafe`
`disable_path_to_lower` | `True` | corresponding with hugo config: `disablePathLower`

## Notes

### Unsupported Syntax

Following syntaxes are not supported or limitedly supported.

MoinMoin Syntax | Meaning in MoinMoin | Converted into
-------|---------------------|--------------
`MeatBall:InterWiki` | interwiki link | output as it is
`(indent) item`   | itemlist with no bullet | bullet itemlist
` . item`  | itemlist with no bullet | bullet itemlist
` a. item` | alphabetically ordered itemlist | numbered itemlist
`{{drawing:twiki.tdraw}}` |inline drawing diagram | output as it is
`-----` (variable length) |variable length horizontal rule |fixed length horizontal rule


### Unsafe rendering option

`hugo_config.goldmark_unsafe` option enables to output raw html tags.

Following syntaxes are converted only in this mode.

MoinMoin Syntax | Meaning in MoinMoin | Converted into
-------|---------------------|--------------
`__text__`    | underline text decoration | `<u>` tag
`~+larger+~`  | big text decoration | `<big>` tag
`~-smaller-~` | small text decoration | `<small>` tag
`^super^script` | superscript text decoration | `<sup>` tag
`,,sub,,script` | subscript text decoration | `<sub>` tag
`{{attachment:object.mp4}}` | embedding object | `<object>` tag


### Macro

Only a part of macros are supported.

* `<<BR>>`: output whitespace before `\n`.
* `<<TableOfContents>>`: do nothing.


### Parser


## References

- [HelpOnMoinWikiSyntax - MoinMoin](http://moinmo.in/HelpOnMoinWikiSyntax)
- [yuin/goldmark: A markdown parser written in Go. Easy to extend, standard(CommonMark) compliant, well structured.](https://github.com/yuin/goldmark)
- [CommonMark Spec](https://spec.commonmark.org/)


## License

GPLv3
