__author__ = 'thorwhalen'
"""
functions that work on soup, soup tags, etc.
"""

import bs4

from ut.pgenerator.get import last_element
from tempfile import mkdtemp
import os
import ut.pstr.to as strto
import ut.parse.util as parse_util
import ut.pstr.trans as pstr_trans


def root_parent(s):
    return last_element(s.parents)


def open_tag_in_firefox(tag):
    save_file = os.path.join(mkdtemp(), 'tmp.html')
    strto.file(tag.prettify(), save_file)
    parse_util.open_in_firefox(save_file)


def add_text_to_parse_dict(
    soup, parse_dict, key, name, attrs, text_transform=pstr_trans.strip
):
    tag = soup.find(name=name, attrs=attrs)
    if tag:
        if text_transform:
            parse_dict[key] = text_transform(tag.text)
        else:
            parse_dict[key] = tag.text
    return parse_dict


def get_element(node, path_to_element):
    for p in path_to_element:
        if isinstance(p, str):
            p = p.split('.')
        if isinstance(p, dict):
            node = node.find(**p)
        else:
            node = node.find(*p)
    return node


def get_elements(nodes, path_to_element):
    """
    Recursiverly get elements from soup, soup tags, result sets, etc. by specifying a node (or nodes) and
    a list of paths to follow.
    :param nodes:
    :param path_to_element: list of paths. A path can be a period-separated string, a list (of findAll args), or a
        dict (of findAll kwargs)
    :return: a list of elements that were found
    """
    if not isinstance(nodes, (bs4.element.ResultSet, tuple, list)):
        nodes = [nodes]

    cumul = []
    for node in nodes:
        for i, p in enumerate(path_to_element):
            if isinstance(p, str):
                p = p.split('.')
            if isinstance(p, dict):
                _nodes = node.findAll(**p)
            else:
                _nodes = node.findAll(*p)
            _path_to_element = path_to_element[(i + 1) :]
            if len(_path_to_element) > 0:
                cumul.extend(get_elements(_nodes, _path_to_element))
            else:
                cumul.extend(_nodes)
    return cumul




def extract_attributes(tag, attributes):
    """
    Extracts specified attributes from a BeautifulSoup tag and returns them in a dictionary.
    
    :param tag: BeautifulSoup tag from which attributes will be extracted.
    :param attributes: List of attribute names to extract from the tag.
    :return: Dictionary with keys as attribute names and values as attribute values.
    
    Example:
    >>> from bs4 import BeautifulSoup
    >>> soup = BeautifulSoup('<div id="main" class="container"></div>', 'html.parser')
    >>> div_tag = soup.find('div')
    >>> extract_attributes(div_tag, ['id', 'class'])
    {'id': 'main', 'class': ['container']}
    """
    return {attr: tag.get(attr) for attr in attributes if tag.has_attr(attr)}


def text_of_first_found(soup, name, attrs=None):
    """
    Finds the first tag that matches the given name and attributes in a BeautifulSoup object and returns its text.
    
    :param soup: BeautifulSoup object to search within.
    :param name: Name of the tag to find.
    :param attrs: Dictionary of attributes to match.
    :return: Text content of the first found tag or None if no tag is found.
    
    Example:
    >>> from bs4 import BeautifulSoup
    >>> soup = BeautifulSoup('<div><p class="text">Hello</p><p>World</p></div>', 'html.parser')
    >>> text_of_first_found(soup, 'p', {'class': 'text'})
    'Hello'
    """
    tag = soup.find(name, attrs=attrs)
    return tag.text if tag else None


def replace_tag_with_text(soup, name, replacement_text, attrs=None):
    """
    Replaces all tags in a BeautifulSoup object that match the given name and attributes with a text node.
    
    :param soup: BeautifulSoup object to modify.
    :param name: Name of the tag to replace.
    :param replacement_text: Text to replace the tag with.
    :param attrs: Dictionary of attributes to match the tags.
    
    Example:
    >>> from bs4 import BeautifulSoup
    >>> soup = BeautifulSoup('<div><p>Remove me</p></div>', 'html.parser')
    >>> replace_tag_with_text(soup, 'p', 'Replaced')
    >>> str(soup)
    '<div>Replaced</div>'
    """
    for tag in soup.find_all(name, attrs=attrs):
        tag.replace_with(replacement_text)
