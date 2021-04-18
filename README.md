# moin2hugo

> A converter from MoinMoin wiki (moinwiki) data directory to Hugo content directory.

Moin2Hugo converts MoinMoin site directory to hugo content directory.

* Convert syntax directory (without going through transforming to HTML).
* Generate clean and tidy markdown source text.
* Keep semantics as possible.


## Usage

```
Usage: moin2hugo [OPTIONS] SRC DST

  Convert MoinMoin site directory to Hugo content directory.

Options:
  -c, --config PATH
  -v, --verbose
  --help             Show this message and exit.
```

## Configuration

### Config File Format

Write config file in YAML format.

```yaml
# config.yaml
hugo_config:
  root_path: /docs
  use_extended_markdown_table: true
```

### Paramaters

Configurable paramaters are below.

Paramater | Default | Description
-- | -- | --
`moin_site_config.*` | - | see `MoinSiteConfig`
`hugo_config.*` | - | see `HugoConfig`

### MoinSiteConfig

Moin wiki parser configuration.

Paramater | Default | Description
-- | -- | --
`bang_meta` |`True` | corresponding with moin site config: `bang_meta`
`page_front_page` |`FrontPage` | corresponding with moin site config: `page_front_page`

### HugoConfig

Hugo formatting configuration.

Paramater | Default | Description
-- | -- | --
`detect_table_header_heuristically` | `True` | make table header by heuristics
`use_extended_markdown_table` | `False` | use [hugo-shortcode-extended-markdown-table][hugo-shortcode-extended-markdown-table] to support table colspan/rowspan
`increment_heading_level` | `True` | increment heading level (e.g. Moin's h1 -> Hugo's h2)
`root_path` | `/` | root path of hugo site in url
`use_figure_shortcode` | `True` | use `figure` shortcode
`goldmark_unsafe` | `True` | corresponding with hugo config: `markup.goldman.render.goldmark_unsafe`
`disable_path_to_lower` | `True` | corresponding with hugo config: `disablePathLower`
`remove_path_accents` | `False` | corresponding with hugo config: `removePathAccents`

[hugo-shortcode-extended-markdown-table]: https://github.com/wataru-chocola/hugo-shortcode-extended-markdown-table

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


### Tag attributes

In Moinmoin, you can specify tag attributes in link, image, embedded object like:

```
{{attachment:image.png|title|width=100,height=150}}
```

The support status for these attributes is here:

Tag | Attribute | Support Status
--- | --------- | --------------
Link   |`class`     | unsupported
Link   |`title`     | supported
Link   |`target`    | supported
Link   |`accesskey` | unsupported
Link   |`rel`       | unsupported
Image  |`class`     | unsupported
Image  |`alt`       | supported
Image  |`title`     | supported
Image  |`longdesc`  | unsupported (deprecated in HTML5)
Image  |`width`     | supported only if `hugo_config.use_figure_shortcode=True`
Image  |`height`    | supported only if `hugo_config.use_figure_shortcode=True`
Image  |`align`     | unsupported
Object |`class`     | unsupported
Object |`title`     | supported
Object |`mimetype`  | supported
Object |`width`     | supported
Object |`height`    | supported
Object |`standby`   | unsupported (deprecated in HTML5)


### Table attributes

In Moinmoin, you can specify table attributes in table, table row and table cell.

```
||<tablestyle="width: 90%;" rowstyle="width: 30%;" rowclass="header"> A || B || C ||
||<|2> old-style rowspan ||<colspan=2> new-style colspan ||
||b ||c ||
```

The support status for these attributes is here:

Element | Attribute | Support Status
--- | --------- | --------------
Table, Row, Cell |`class`   | unsupported
Table, Row, Cell |`id`      | unsupported
Table, Row, Cell |`style`   | unsupported
Table, Row, Cell |`width`   | unsupported
Table, Row, Cell |`height`  | unsupported
Table, Row, Cell |`align`   | partially supported
Table, Row, Cell |`valign`  | unsupported
Table, Row, Cell |`bgcolor` | unsupported
Cell             |`colspan` | supported if `hugo_config.use_extended_markdown_table` enabled
Cell             |`rowspan` | supported if `hugo_config.use_extended_markdown_table` enabled
Cell             |`abbr`    | unsupported



### Macro

Only a part of macros are supported.

* `<<BR>>`: output whitespace before `\n`.
* `<<TableOfContents>>`: do nothing.


### Parser

Supported parsers:

* `highlight`
* `diff`, `cplusplus`, `python`, `java`, `pascal`, `irssi`
* `text`
* `csv`


## References

- [HelpOnMoinWikiSyntax - MoinMoin](http://moinmo.in/HelpOnMoinWikiSyntax)
- [yuin/goldmark: A markdown parser written in Go. Easy to extend, standard(CommonMark) compliant, well structured.](https://github.com/yuin/goldmark)
- [CommonMark Spec](https://spec.commonmark.org/)


## License

GPLv3
