from __future__ import annotations

import textwrap
from typing import Any, Dict, List, Literal, Optional, Type, TypeVar

import attr
import cssutils  # type: ignore


@attr.s(slots=True)
class PageElement(object):
    content: str = attr.ib(default="")

    parent: Optional[PageElement] = attr.ib(
        default=None, init=False, repr=False, eq=False, metadata={"exclude_content": True}
    )
    children: List[PageElement] = attr.ib(default=attr.Factory(list), init=False)
    source_text: str = attr.ib(default="", repr=False, metadata={"exclude_content": True})
    source_frozen: bool = attr.ib(default=False, repr=False, metadata={"exclude_content": True})

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> PageElement:
        initable_fields = dict([(k, v) for k, v in attr.fields_dict(cls).items() if v.init])
        init_args = dict([(k, v) for k, v in data.items() if k in initable_fields])
        obj = cls(**init_args)
        for _class, c_init_data in data.get("children", []):
            obj.add_child(_class.from_dict(c_init_data), propagate_source_text=False)
        return obj

    @property
    def content_hash(self) -> int:
        def get_hash(obj: Any) -> int:
            if isinstance(obj, PageElement):
                return obj.content_hash
            else:
                return hash(obj)

        hash_value = 0
        for field in attr.fields(self.__class__):  # type: ignore
            assert isinstance(field, attr.Attribute)
            if field.metadata.get("exclude_content", False):
                continue
            value = self.__getattribute__(field.name)
            hash_value += hash(field.name)
            if isinstance(value, list):
                hash_value += hash((field.name, sum([get_hash(c) for c in value])))
            elif isinstance(value, dict):
                tmp_value = 0
                for k, v in value.items():
                    tmp_value += hash((k, get_hash(v)))
                hash_value += hash((field.name, tmp_value))
            else:
                hash_value += hash((field.name, value))
        return hash((self.__class__.__name__, hash_value))

    @property
    def parents(self) -> List[PageElement]:
        ret: List[PageElement] = []
        tmp = self.parent
        while tmp is not None:
            ret.append(tmp)
            tmp = tmp.parent
        return ret

    @property
    def descendants(self) -> List[PageElement]:
        ret: List[PageElement] = []
        for c in self.children:
            ret.append(c)
            ret += c.descendants
        return ret

    @property
    def prev_sibling(self) -> Optional[PageElement]:
        if self.parent is None:
            return None
        idx = [i for i, x in enumerate(self.parent.children) if x is self][0]
        if idx == 0:
            return None
        return self.parent.children[idx - 1]

    @property
    def next_sibling(self) -> Optional[PageElement]:
        if self.parent is None:
            return None
        idx = [i for i, x in enumerate(self.parent.children) if x is self][0]
        if idx == len(self.parent.children) - 1:
            return None
        return self.parent.children[idx + 1]

    def in_x(self, x: List[Type[PageElement]], upper_bound: List[Type[PageElement]] = []) -> bool:
        above_me = [self] + self.parents
        for e in above_me:
            if isinstance(e, tuple(upper_bound)):
                return False
            if isinstance(e, tuple(x)):
                return True
        return False

    def add_content(self, content: str) -> None:
        self.content += content

    def add_child(
        self, child: PageElement, propagate_source_text: bool = True, at: Optional[int] = None
    ) -> None:
        if at is None:
            self.children.append(child)
        else:
            self.children.insert(at, child)
        child.parent = self
        if propagate_source_text:
            child.propagate_source_text(child.source_text)

    def del_child(self, at: int) -> None:
        child = self.children[at]
        self.children = self.children[0:at] + self.children[at + 1 :]
        del child

    def add_source_text(self, source_text: str, freeze: bool = False) -> None:
        self.source_text += source_text
        self.propagate_source_text(source_text)
        if freeze:
            self.source_frozen = True

    def propagate_source_text(self, source_text: str) -> None:
        for p in self.parents:
            if p.source_frozen:
                break
            p.source_text += source_text

    def tree_repr(self, include_src: bool = False) -> str:
        def _shorten(text: str, width: int = 40) -> str:
            placeholder = "[...]"
            assert width > len(placeholder)
            if len(text) > width:
                return text[: width - len(placeholder)] + placeholder
            return text

        classname = self.__class__.__name__
        description = "{classname}:".format(classname=classname)
        if self.content:
            summary = repr(_shorten(self.content, 40))
            description += " content={summary}".format(summary=summary)
        if include_src and self.source_text:
            summary = repr(_shorten(self.source_text, 40))
            description += " source={summary}".format(summary=summary)

        for e in self.children:
            description += "\n"
            description += textwrap.indent(e.tree_repr(include_src=include_src), "    ")
        return description


# General Objects
#
@attr.s(slots=True)
class PageRoot(PageElement):
    pass


@attr.s(slots=True)
class Raw(PageElement):
    pass


@attr.s(slots=True)
class Paragraph(PageElement):
    pass


@attr.s(slots=True)
class Text(PageElement):
    pass


@attr.s(slots=True)
class SGMLEntity(PageElement):
    pass


# Moinwiki Special Objects
#
@attr.s(slots=True)
class Macro(PageElement):
    macro_name: str = attr.ib(kw_only=True)
    macro_args: Optional[str] = attr.ib(kw_only=True)
    markup: str = attr.ib(kw_only=True)


@attr.s(slots=True)
class Comment(PageElement):
    pass


@attr.s(slots=True)
class Smiley(PageElement):
    pass


@attr.s(slots=True)
class Remark(PageElement):
    pass


# Codeblock (Parsed Text)
#
@attr.s(slots=True)
class ParsedText(PageElement):
    parser_name: str = attr.ib(default="")
    parser_args: Optional[str] = attr.ib(default=None)


@attr.s(slots=True)
class Codeblock(PageElement):
    syntax_id: Optional[str] = attr.ib(default=None)


# Table
#
T_TABLE_ATTR = TypeVar("T_TABLE_ATTR", bound="TableAttrBase")
TableAttrDict = Dict[str, Any]


@attr.s
class TableAttrBase:
    _attribute_prefix: str = ""

    class_: Optional[str] = attr.ib(kw_only=True, default=None)
    id_: Optional[str] = attr.ib(kw_only=True, default=None)
    style: Optional[str] = attr.ib(kw_only=True, default=None)

    width: Optional[str] = attr.ib(kw_only=True, default=None)
    height: Optional[str] = attr.ib(kw_only=True, default=None)

    align: Optional[str] = attr.ib(kw_only=True, default=None)
    valign: Optional[str] = attr.ib(kw_only=True, default=None)
    bgcolor: Optional[str] = attr.ib(kw_only=True, default=None)

    @classmethod
    def filter_target_attrs(cls, data: TableAttrDict) -> TableAttrDict:
        result = {}
        for k, v in data.items():
            if k.startswith(cls._attribute_prefix):
                result[k[len(cls._attribute_prefix) :]] = v
        return result

    @classmethod
    def from_dict(cls: Type[T_TABLE_ATTR], data: TableAttrDict) -> T_TABLE_ATTR:
        tmp_data: Dict[str, Any] = cls.filter_target_attrs(data)
        if "class" in tmp_data:
            tmp_data["class_"] = tmp_data["class"]
            del tmp_data["class"]
        if "id" in tmp_data:
            tmp_data["id_"] = tmp_data["id"]
            del tmp_data["id"]
        initable_fields = dict([(k, v) for k, v in attr.fields_dict(cls).items() if v.init])
        init_args = dict([(k, v) for k, v in tmp_data.items() if k in initable_fields])

        if "style" in init_args:
            style = cssutils.parseStyle(init_args["style"])
            if style.width:
                init_args["width"] = style.width
            if style.height:
                init_args["height"] = style.height
            if style.textAlign:
                init_args["align"] = style.textAlign
            if style.backgroundColor:
                init_args["bgcolor"] = style.backgroundColor

        obj = cls(**init_args)
        return obj


@attr.s
class TableAttr(TableAttrBase):
    _attribute_prefix: str = "table"


@attr.s
class TableRowAttr(TableAttrBase):
    _attribute_prefix: str = "row"


@attr.s
class TableCellAttr(TableAttrBase):
    _attribute_prefix: str = ""

    colspan: Optional[int] = attr.ib(
        kw_only=True, default=None, converter=attr.converters.optional(int)
    )
    rowspan: Optional[int] = attr.ib(
        kw_only=True, default=None, converter=attr.converters.optional(int)
    )
    abbr: Optional[str] = attr.ib(kw_only=True, default=None)


@attr.s(slots=True)
class Table(PageElement):
    attrs: TableAttr = attr.ib(default=attr.Factory(TableAttr))


@attr.s(slots=True)
class TableRow(PageElement):
    attrs: TableRowAttr = attr.ib(default=attr.Factory(TableRowAttr))
    is_header: bool = attr.ib(default=False)


@attr.s(slots=True)
class TableCell(PageElement):
    attrs: TableCellAttr = attr.ib(default=attr.Factory(TableCellAttr))


# Heading / Horizontal Rule
#
@attr.s(slots=True)
class Heading(PageElement):
    depth: int = attr.ib(kw_only=True)


@attr.s(slots=True)
class HorizontalRule(PageElement):
    pass


# Decorations
#
@attr.s(slots=True)
class Underline(PageElement):
    pass


@attr.s(slots=True)
class Strike(PageElement):
    pass


@attr.s(slots=True)
class Small(PageElement):
    pass


@attr.s(slots=True)
class Big(PageElement):
    pass


@attr.s(slots=True)
class Emphasis(PageElement):
    pass


@attr.s(slots=True)
class Strong(PageElement):
    pass


@attr.s(slots=True)
class Sup(PageElement):
    pass


@attr.s(slots=True)
class Sub(PageElement):
    pass


@attr.s(slots=True)
class Code(PageElement):
    pass


# Links
LinkAttrKey = Literal["class", "title", "target", "accesskey", "rel"]
LinkAttrDict = Dict[LinkAttrKey, Any]


@attr.s(frozen=True, slots=True)
class LinkAttr:
    class_: Optional[str] = attr.ib(kw_only=True, default=None)
    title: Optional[str] = attr.ib(kw_only=True, default=None)
    target: Optional[str] = attr.ib(kw_only=True, default=None)
    accesskey: Optional[str] = attr.ib(kw_only=True, default=None)
    rel: Optional[str] = attr.ib(kw_only=True, default=None)

    @classmethod
    def from_dict(cls, data: LinkAttrDict) -> LinkAttr:
        tmp_data: Dict[str, Any] = dict(
            [(k, v) for k, v in data.items()]
        )  # noqa: workaround: mypy claims Literal is invalid as deepcopy()'s arg
        if "class" in tmp_data:
            tmp_data["class_"] = tmp_data["class"]
        initable_fields = dict([(k, v) for k, v in attr.fields_dict(cls).items() if v.init])
        init_args = dict([(k, v) for k, v in tmp_data.items() if k in initable_fields])
        obj = cls(**init_args)
        return obj


@attr.s(slots=True)
class LinkBase(PageElement):
    attrs: LinkAttr = attr.ib(default=attr.Factory(LinkAttr))


@attr.s(slots=True)
class Link(LinkBase):
    url: str = attr.ib(kw_only=True)


@attr.s(slots=True)
class Pagelink(LinkBase):
    pagename: str = attr.ib(kw_only=True)
    queryargs: Optional[Dict[str, str]] = attr.ib(default=None)
    anchor: Optional[str] = attr.ib(default=None)


@attr.s(slots=True)
class Interwikilink(LinkBase):
    wikiname: str = attr.ib(kw_only=True)
    pagename: str = attr.ib(kw_only=True)
    queryargs: Optional[Dict[str, str]] = attr.ib(default=None)
    anchor: Optional[str] = attr.ib(default=None)


@attr.s(slots=True)
class AttachmentLink(LinkBase):
    pagename: str = attr.ib(kw_only=True)
    filename: str = attr.ib(kw_only=True)
    queryargs: Optional[Dict[str, str]] = attr.ib(default=None)


@attr.s(slots=True)
class Url(PageElement):
    pass


# Itemlist
#
@attr.s(slots=True)
class BulletList(PageElement):
    pass


@attr.s(slots=True)
class NumberList(PageElement):
    pass


@attr.s(slots=True)
class DefinitionList(PageElement):
    pass


@attr.s(slots=True)
class DefinitionTerm(PageElement):
    pass


@attr.s(slots=True)
class DefinitionDesc(PageElement):
    pass


@attr.s(slots=True)
class Listitem(PageElement):
    pass


# Transclusion (Image Embedding)
ImageAttrKey = Literal["class", "alt", "title", "longdesc", "width", "height", "align"]
ImageAttrDict = Dict[ImageAttrKey, Any]


@attr.s(frozen=True, slots=True)
class ImageAttr:
    class_: Optional[str] = attr.ib(kw_only=True, default=None)
    alt: Optional[str] = attr.ib(kw_only=True, default=None)
    title: Optional[str] = attr.ib(kw_only=True, default=None)
    longdesc: Optional[str] = attr.ib(kw_only=True, default=None)  # deprecated in HTML5
    width: Optional[str] = attr.ib(kw_only=True, default=None)
    height: Optional[str] = attr.ib(kw_only=True, default=None)
    align: Optional[str] = attr.ib(kw_only=True, default=None)

    @classmethod
    def from_dict(cls, data: ImageAttrDict) -> ImageAttr:
        tmp_data: Dict[str, Any] = dict(
            [(k, v) for k, v in data.items()]
        )  # noqa: workaround: mypy claims Literal is invalid as deepcopy()'s arg
        if "class" in tmp_data:
            tmp_data["class_"] = tmp_data["class"]
        initable_fields = dict([(k, v) for k, v in attr.fields_dict(cls).items() if v.init])
        init_args = dict([(k, v) for k, v in tmp_data.items() if k in initable_fields])
        obj = cls(**init_args)
        return obj


@attr.s(slots=True)
class AttachmentImage(PageElement):
    pagename: str = attr.ib(kw_only=True)
    filename: str = attr.ib(kw_only=True)
    attrs: ImageAttr = attr.ib(default=attr.Factory(ImageAttr))


@attr.s(slots=True)
class Image(PageElement):
    src: str = attr.ib(kw_only=True)
    attrs: ImageAttr = attr.ib(default=attr.Factory(ImageAttr))


# Transclusion (Object Embedding)
ObjectAttrKey = Literal["class", "title", "width", "height", "mimetype", "standby"]
ObjectAttrDict = Dict[ObjectAttrKey, Any]


@attr.s(frozen=True, slots=True)
class ObjectAttr:
    class_: Optional[str] = attr.ib(kw_only=True, default=None)
    title: Optional[str] = attr.ib(kw_only=True, default=None)
    width: Optional[str] = attr.ib(kw_only=True, default=None)
    height: Optional[str] = attr.ib(kw_only=True, default=None)
    mimetype: Optional[str] = attr.ib(kw_only=True, default=None)
    standby: Optional[str] = attr.ib(kw_only=True, default=None)  # deprecated in HTML5

    @classmethod
    def from_dict(cls, data: ObjectAttrDict) -> ObjectAttr:
        tmp_data: Dict[str, Any] = dict(
            [(k, v) for k, v in data.items()]
        )  # noqa: workaround: mypy claims Literal is invalid as deepcopy()'s arg
        if "class" in tmp_data:
            tmp_data["class_"] = tmp_data["class"]
        initable_fields = dict([(k, v) for k, v in attr.fields_dict(cls).items() if v.init])
        init_args = dict([(k, v) for k, v in tmp_data.items() if k in initable_fields])
        obj = cls(**init_args)
        return obj


@attr.s(slots=True)
class Transclude(PageElement):
    pagename: str = attr.ib(kw_only=True)
    attrs: ObjectAttr = attr.ib(default=attr.Factory(ObjectAttr))


@attr.s(slots=True)
class AttachmentTransclude(PageElement):
    pagename: str = attr.ib(kw_only=True)
    filename: str = attr.ib(kw_only=True)
    attrs: ObjectAttr = attr.ib(default=attr.Factory(ObjectAttr))


# Transclude (Other)
@attr.s(slots=True)
class AttachmentInlined(PageElement):
    pagename: str = attr.ib(kw_only=True)
    filename: str = attr.ib(kw_only=True)
    link_text: str = attr.ib(kw_only=True)
