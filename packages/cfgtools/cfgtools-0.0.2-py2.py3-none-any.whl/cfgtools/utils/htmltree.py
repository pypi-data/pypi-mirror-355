"""Defines HTMLTreeMaker."""

from typing import Self

__all__ = ["HTMLTreeMaker"]


class HTMLTreeMaker:
    """
    Make an HTML tree.

    Parameters
    ----------
    value : str, optional
        Value of child node, by default None.
    clsname : str | None, optional
        Class name, by default None. If not specifeid, the class name will
        be "m" ("m" for "main").
    default_level : int, optional
        Default levels to set open, by default 2.

    """

    def __init__(
        self,
        value: str | None = None,
        clsname: str | None = None,
        default_level: int = 3,
        /,
    ) -> None:
        self.__val = value
        self.__cls = "m" if clsname is None else clsname
        self.__default_level = default_level
        self.__children: list[Self] = []

    def add(
        self, maybe_value: str | Self | list[Self], maybe_cls: str | None = None
    ) -> None:
        """
        Add a child node, and return it.

        Parameters
        ----------
        maybe_value : str | Self | list[Self]
            Node value or the instance(s) of the child node(s).
        maybe_cls : str | None, optional
            May be used as the class name, by default None.

        Returns
        -------
        Self
            The new node.

        """
        if isinstance(maybe_value, str):
            self.__children.append(self.__class__(maybe_value, maybe_cls))
        elif isinstance(maybe_value, list):
            if maybe_cls:
                for x in maybe_value:
                    if not isinstance(x, self.__class__):
                        raise TypeError(
                            f"object of type {x.__class__.__name__} is not allowed "
                            "to be a child node"
                        )
                    x.setcls(maybe_cls)
            self.__children.extend(maybe_value)
        else:
            if not isinstance(maybe_value, self.__class__):
                raise TypeError(
                    f"object of type {maybe_value.__class__.__name__} is not allowed "
                    "to be a child node"
                )
            if maybe_cls:
                maybe_value.setcls(maybe_cls)
            self.__children.append(maybe_value)

    def discard(self, index: int, /) -> None:
        """Discard the n-th child node."""
        self.__children = self.__children[:index] + self.__children[index:]

    def get(self, index: int, /) -> Self:
        """Get the n-th child node."""
        return self.__children[index]

    def setval(self, value: str, /) -> None:
        """Set the node value."""
        self.__val = value

    def getval(self) -> str | None:
        """Get the node value."""
        return self.__val

    def setcls(self, clsname: str, /) -> None:
        """Set the node class name."""
        self.__cls = clsname

    def getcls(self) -> str | None:
        """Get the node class name."""
        return self.__cls

    def has_child(self) -> bool:
        """Return whether there is a child node."""
        return bool(self.__children)

    def make(self, clsname: str | None = None, style: str | None = None) -> str:
        """Make a string of the HTML tree."""
        if clsname is None:
            clsname = "tree"
        if style is None:
            style = f"""<style type="text/css">
.{clsname} li>details>summary>span.open,
.{clsname} li>details[open]>summary>span.closed {{
    display: none;
}}
.{clsname} li>details[open]>summary>span.open {{
    display: inline;
}}
.{clsname} li>details>summary {{
    display: block;
    cursor: pointer;
}}
</style>"""
        return f'{style}\n<ul class="{clsname}">\n{self.make_plain(0)}\n</ul>'

    def make_plain(self, level: int, /) -> str:
        """Make a string of the HTML tree without css style."""
        if not self.__children:
            return f'<li class="{self.__cls}"><span>{self.__val}</span></li>'
        children_str = "\n".join(x.make_plain(level + 1) for x in self.__children)
        if self.__val is None:
            return children_str
        details_open = " open" if level < self.__default_level else ""
        return (
            f'<li class="{self.__cls}"><details{details_open}><summary>{self.__val}'
            f'</summary>\n<ul class="{self.__cls}">\n{children_str}\n</ul>\n'
            "</details></li>"
        )

    def show(self, clsname: str | None = None, style: str | None = None) -> "HTMLRepr":
        """Show the html tree."""
        return HTMLRepr(self.make(clsname, style))


class HTMLRepr:
    """Represent an html object."""

    def __init__(self, html_str: str) -> None:
        self.html_str = html_str

    def _repr_html_(self) -> str:
        return self.html_str
