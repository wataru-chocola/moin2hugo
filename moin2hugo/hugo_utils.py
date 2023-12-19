import re
from typing import Dict, Optional


def make_shortcode(
    shortcode: str, attrs: Dict[str, Optional[str]] = {}, inner_markdonify: bool = False
) -> str:
    if inner_markdonify:
        start_delimiter, end_delimiter = ("{{%", "%}}")
    else:
        start_delimiter, end_delimiter = ("{{<", ">}}")
    if attrs:
        attrs_str: list[str] = []
        for k, v in attrs.items():
            if v is None:
                attrs_str.append("%s" % k)
            else:
                attrs_str.append('%s="%s"' % (k, v))
        content = "%s %s" % (shortcode, " ".join(attrs_str))
    else:
        content = shortcode
    return f"{start_delimiter} {content} {end_delimiter}"


def comment_out_shortcode(text: str) -> str:
    # noqa: https://discourse.gohugo.io/t/how-is-the-hugo-doc-site-showing-shortcodes-in-code-blocks/9074
    shortcode_rule = r"""
    (?P<start>{{(?:(?P<bracket><)|%))
      (?P<shortcode>
        (?:
          [^`\n]+?(?=`|\n|>}}|%}})
          |
          `[^`]*`
        )*?
      )
    (?P<end>(?(bracket)>|%)}})
    """
    shortcode_re = re.compile(shortcode_rule, re.UNICODE | re.VERBOSE | re.DOTALL)
    ret = re.sub(shortcode_re, r"\g<start>/*\g<shortcode>*/\g<end>", text)
    return ret


def search_shortcode_delimiter(text: str) -> bool:
    shortcode_rule = r"{{(<|%)(?!/[*])"
    return bool(re.search(shortcode_rule, text))


def escape_shortcode(text: str, in_html: bool = False) -> str:
    shortcode_rule = r"{{(?P<delimiter>(<|%))"
    shortcode_re = re.compile(shortcode_rule, re.UNICODE | re.VERBOSE | re.DOTALL)
    ret = ""
    if in_html:
        lastpos = 0
        for m in re.finditer(shortcode_re, text):
            ret += text[lastpos : m.start()]
            if m.group("delimiter") == "<":
                ret += "{{&lt;"
            else:
                ret += "{{&#37;"
            lastpos = m.end()
        ret += text[lastpos:]
    else:
        ret = re.sub(shortcode_re, r"{{\\\g<delimiter>", text)
    return ret
