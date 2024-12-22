import os
import re
from enum import Enum

from htmlnode import LeafNode, ParentNode


class TextType(Enum):
    TEXT = "text"
    BOLD = "bold"
    ITALIC = "italic"
    CODE = "code"
    LINK = "link"
    IMAGE = "image"


class TextNode:
    def __init__(self, text, text_type, url=None):
        self.text = text
        self.text_type = text_type
        self.url = url

    def __eq__(self, other):
        if not isinstance(other, TextNode):
            raise NotImplementedError(
                "Equality only defined for TextNode objects")
        return vars(self) == vars(other)

    def __repr__(self):
        return f"TextNode({self.text}, {self.text_type.value}, {self.url})"


def text_node_to_html_node(text_node):
    match text_node.text_type:
        case TextType.TEXT:
            return LeafNode(None, text_node.text, None)
        case TextType.BOLD:
            return LeafNode("b", text_node.text, None)
        case TextType.ITALIC:
            return LeafNode("i", text_node.text, None)
        case TextType.CODE:
            return LeafNode("code", text_node.text, None)
        case TextType.LINK:
            return LeafNode("a", text_node.text, {"href": text_node.url})
        case TextType.IMAGE:
            return LeafNode("img", None, {"src": text_node.url, "alt": text_node.text})
        case _:
            raise ValueError


def split_nodes_delimiter(old_nodes, delimiter, text_type):
    new_nodes = []
    for node in old_nodes:
        if node.text_type != TextType.TEXT:
            new_nodes.append(node)
            continue

        parts = node.text.split(delimiter)
        for i, part in enumerate(parts):
            if part:
                if i % 2 == 0:
                    new_nodes.append(TextNode(part, node.text_type))
                else:
                    new_nodes.append(TextNode(part, text_type))

    return new_nodes


def extract_markdown_images(text):
    matches = re.findall(r"!\[.*\]\(.*\)", text)
    images = []
    for match in matches:
        pos_right_square_brack = match.index("]")
        images.append(
            (
                match[2: pos_right_square_brack - 1],
                match[pos_right_square_brack + 2: -1],
            )
        )
    return images


def extract_markdown_links(text):
    matches = re.findall(r"\[.*\]\(.*\)", text)
    links = []
    for match in matches:
        pos_right_square_brack = match.index("]")
        pos_right_round_brack = match.index(")")
        links.append(
            (
                match[1: pos_right_square_brack],
                match[pos_right_square_brack + 2: pos_right_round_brack],
            )
        )
    return links


def split_nodes_image(old_nodes):
    new_nodes = []
    for node in old_nodes:
        if node.text_type != TextType.TEXT:
            new_nodes.append(node)
            continue

        text = node.text
        images = extract_markdown_images(text)
        if not images:
            new_nodes.append(node)
            continue

        last_pos = 0
        for alt_text, url in images:
            start_pos = text.find(f"![{alt_text}]({url})", last_pos)
            if start_pos > last_pos:
                new_nodes.append(
                    TextNode(text[last_pos:start_pos], TextType.TEXT))
            new_nodes.append(TextNode(alt_text, TextType.IMAGE, url))
            last_pos = start_pos + len(f"![{alt_text}]({url})")

        if last_pos < len(text):
            new_nodes.append(TextNode(text[last_pos:], TextType.TEXT))

    return new_nodes


def split_nodes_link(old_nodes):
    new_nodes = []
    for node in old_nodes:
        if node.text_type != TextType.TEXT:
            new_nodes.append(node)
            continue

        text = node.text
        links = extract_markdown_links(text)
        if not links:
            new_nodes.append(node)
            continue

        last_pos = 0
        for link_text, url in links:
            start_pos = text.find(f"[{link_text}]({url})", last_pos)
            if start_pos > last_pos:
                new_nodes.append(
                    TextNode(text[last_pos:start_pos], TextType.TEXT))
            new_nodes.append(TextNode(link_text, TextType.LINK, url))
            last_pos = start_pos + len(f"[{link_text}]({url})")

        if last_pos < len(text):
            new_nodes.append(TextNode(text[last_pos:], TextType.TEXT))

    return new_nodes


def markdown_to_blocks(markdown):
    blocks = markdown.split("\n\n")
    blocks = filter(lambda x: x != "", blocks)
    blocks = list(map(lambda x: x.lstrip().rstrip(), blocks))
    return blocks


def text_to_textnodes(text):
    nodes = [TextNode(text, TextType.TEXT)]

    nodes = split_nodes_image(nodes)
    nodes = split_nodes_link(nodes)
    nodes = split_nodes_delimiter(nodes, "**", TextType.BOLD)
    nodes = split_nodes_delimiter(nodes, "*", TextType.ITALIC)

    nodes = split_nodes_delimiter(nodes, "`", TextType.CODE)

    return nodes


def block_to_block_type(text):
    if re.match(r"^#{1,6} ", text):
        return "heading"
    elif text.startswith("```") and text.endswith("```"):
        return "code"
    elif all(line.startswith("> ") for line in text.splitlines()):
        return "quote"
    elif all(re.match(r"^[-*] ", line) for line in text.splitlines()):
        return "unordered_list"
    elif all(re.match(r"^\d+\. ", line) for line in text.splitlines()):
        return "ordered_list"
    else:
        return "paragraph"


def text_to_children(text):
    text_nodes = text_to_textnodes(text)
    return [text_node_to_html_node(node) for node in text_nodes]


def process_block(block):
    block_type = block_to_block_type(block)

    match block_type:
        case "heading":
            level = len(re.match(r"^(#{1,6})", block).group(1))
            content = block[level + 1:]
            return ParentNode(f"h{level}",  text_to_children(content), None)

        case "code":
            code_content = block[3:-3].strip()
            return ParentNode("pre", [LeafNode("code", code_content, None)], None)

        case "quote":
            lines = [line[2:] for line in block.splitlines()]
            content = "\n".join(lines)
            return ParentNode("blockquote", text_to_children(content), None)

        case "unordered_list":
            items = block.splitlines()
            list_items = [
                ParentNode("li", text_to_children(item[2:]), None) for item in items
            ]
            return ParentNode("ul", list_items, None)

        case "ordered_list":
            items = block.splitlines()
            list_items = [
                ParentNode("li", text_to_children(
                    re.sub(r"^\d+\. ", "", item)), None)
                for item in items
            ]
            return ParentNode("ol", list_items, None)

        case "paragraph":
            return ParentNode("p", text_to_children(block), None)


def markdown_to_html_node(markdown):
    blocks = markdown_to_blocks(markdown)
    block_nodes = [process_block(block) for block in blocks]

    return ParentNode("div", block_nodes, None)


def extract_title(markdown):
    lines = markdown.splitlines()
    for line in lines:
        if line.startswith("# "):
            return line[2:].strip()
    raise ValueError("No H1 header found in the markdown")
