from typing import Dict, List, Optional


class HTMLNode:
    def __init__(
        self,
        tag=None,
        value=None,
        children=None,
        props=None,
    ) -> None:
        self.tag = tag
        self.value = value
        self.children = children
        self.props = props

    def to_html(self) -> str:
        raise NotImplementedError

    def props_to_html(self) -> str:
        s = ""
        if self.props:
            for k, v in self.props.items():
                s += f' {k}="{v}"'
        return s

    def __repr__(self) -> str:
        return f"HTMLNode({self.tag}, {self.value}, {self.children}, {self.props})"


class LeafNode(HTMLNode):
    def __init__(
        self,
        tag,
        value,
        props,
    ) -> None:
        super().__init__(tag, value, None, props)

    def to_html(self) -> str:
        if self.value is None:
            raise ValueError("Value of a LeafNode can't be None")

        if self.tag is None:
            return self.value

        return f"<{self.tag}{self.props_to_html()}>{self.value}</{self.tag}>"


class ParentNode(HTMLNode):
    def __init__(
        self,
        tag,
        children,
        props,
    ) -> None:
        super().__init__(tag, None, children, props)

    def to_html(self) -> str:
        if self.tag is None:
            raise ValueError("Tag in ParentNode can't be none")

        if self.children is None:
            raise ValueError("children in ParentNode can't be none")

        s = f"<{self.tag}>"
        for child in self.children:
            s += child.to_html()

        s += f"</{self.tag}>"
        return s
