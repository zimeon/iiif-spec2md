#!/usr/bin/env python3
import pathlib
import re
import xml.etree.ElementTree as ET

spec_src = "../ocfl-spec/draft/spec/index.html"
spec_dst = "spec/index.md"
impl_src = "../ocfl-spec/draft/implementation-notes/index.html"
impl_dst = "implementation-notes/index.md"

class Bwaa(Exception):

    pass

def get_anchor(element):
    """Look for id tags in element and make markdown anchor."""
    anchor = element.attrib.get('id', None)
    return anchor

def process_para(element):
    """Process a paragraph."""
    if element.text is not None:
        print("\n", element.text, "\n")
    if element.tail is not None:
        print("\n", element.tail, "\n")

def process_pre(element):
    """Process a pre example block."""
    print("```")
    print(element.text.strip())
    print("```")
    tail = element.tail.strip()
    if tail not in (None, ""):
        raise Bwaa("Unexpected tail text ", tail)

def process_section(element, level=2):
    """Process one <section> block."""
    anchor = get_anchor(element)
    for child in element:
        if child.tag == 'section':
            process_section(child, (level + 1))
        elif child.tag in ('h1', 'h2', 'h3'):
            print("### Heading")
            print("{. #%s}" % (anchor))
        elif child.tag == 'p':
            process_para(child)
        elif child.tag == 'pre':
            process_pre(child)
        elif child.tag in ('ol', 'dl', 'ul'):
            print('LIST')
        elif child.tag == "table":
            print('TABLE')
        elif child.tag == "blockquote":
            print('BLOCKQUOTE')
        else:
            raise Bwaa("level%d unknown child: ", level, child.tag, child.attrib)

def convert(src, dst):
    # Read XML
    print("Reading %s" % (src))
    path = pathlib.Path(src)
    src_xml = path.read_text()
    # Remove non-XML bit
    src_xml = re.sub(' async ', ' ', src_xml)
    src_xml = re.sub('&mdash;', '&#x2014;', src_xml)
    root = ET.fromstring(src_xml)
    body = root.find('body')
    for child in body:
        print("> level1: ", child.tag, child.attrib)
        # At the top level we expect only <section> blocks, we will
        # parse these recursively
        if child.tag != 'section':
            raise Bwaa("Unexpected tag")
        process_section(child, 2)

try:
    convert(spec_src, spec_dst)
    #convert(impl_src, impl_dst)
except Bwaa as e:
    print(e)
