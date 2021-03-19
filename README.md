# moin2hugo

Convert moinwiki's data directory into hugo content directory structure.

## Usage

## Configuration

Paramater | Default | 
-- | -- | --
`moin_site_config.*` | - | see below
`hugo_config.*` | - | see below

### MoinSiteConfig

### HugoConfig

Hugo site configuration.

Paramater | Default | Corrensponding Hogo's setting
-- | -- | --
`goldmark_unsafe` | `True` | `markup.goldman.render.goldmark_unsafe`
`disablePathToLower` | `True` | `disablePathLower`

## References

- [HelpOnMoinWikiSyntax - MoinMoin](http://moinmo.in/HelpOnMoinWikiSyntax)
- [yuin/goldmark: A markdown parser written in Go. Easy to extend, standard(CommonMark) compliant, well structured.](https://github.com/yuin/goldmark)
- [CommonMark Spec](https://spec.commonmark.org/)
