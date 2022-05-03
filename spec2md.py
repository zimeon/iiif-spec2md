#!/usr/bin/env python3
import pathlib
import re
import textwrap
import xml.etree.ElementTree as ET

spec_src = "../ocfl-spec/draft/spec/index.html"
spec_dst = "spec/index.md"
impl_src = "../ocfl-spec/draft/implementation-notes/index.html"
impl_dst = "implementation-notes/index.md"
text_width = 72

class Bwaa(Exception):

    pass


def write_line(*args):
    """Write a line."""
    text = " ".join(args)
    text = re.sub(r'''\s+''', ' ',text)
    print(textwrap.fill(text.strip(), width=text_width, break_long_words=False))

def write_para(*args):
    """Write a paragraph or block of Markdown, line with blank line following."""
    write_line(*args)
    print("")

def write_example(text):
    """Write a preformatted example in Markdown."""
    print("```")
    print(text.strip())
    print("```\n")

def get_anchor(element):
    """Look for id tags in element and make markdown anchor."""
    anchor = element.attrib.get('id', None)
    return anchor

def process_para(element):
    """Process a paragraph."""
    if element.text is not None:
        write_para(element.text)
    for child in element:
        write_line("FIXME <" + child.tag + ">")
    if element.tail.strip() not in (None, ''):
        write_para(element.tail)

def process_pre(element):
    """Process a pre example block."""
    write_example(element.text)
    tail = element.tail.strip()
    if tail not in (None, ""):
        raise Bwaa("Unexpected tail text ", tail)

def process_section(element, level=1):
    """Process one <section> block."""
    if element.attrib['id'] == 'sotd':
        write_para("## Status of This Document", "{. #sotd}")
        write_para("This document is draft of a potential specification. It has no official standing of any kind and does not represent the support or consensus of any standards organisation.")
        write_para("INSERT_TOC_HERE")
        return
    elif element.attrib['id'] == 'conformance':
        write_para("## Conformance")
        write_para("As well as sections marked as non-normative, all authoring guidelines, diagrams, examples, and notes in this specification are non-normative. Everything else in this specification is normative.")
        write_para("The key words may, must, must not, should, and should not are to be interpreted as described in [RFC2119].")
        return
    anchor = get_anchor(element)
    for child in element:
        if child.tag == 'section':
            process_section(child, (level + 1))
        elif child.tag in ('h1', 'h2', 'h3'):
            write_line("#" * level, " ", child.text)
            write_para("{. #%s}" % (anchor))
            if child.tail.strip() not in (None, ""):
                raise Bwaa("Unexpected tail text ", child.tail)
        elif child.tag == 'p':
            process_para(child)
        elif child.tag == 'pre':
            process_pre(child)
        elif child.tag in ('ol', 'dl', 'ul'):
            write_para('LIST')
        elif child.tag == "table":
            write_para('TABLE')
        elif child.tag == "blockquote":
            write_para('BLOCKQUOTE')
        else:
            raise Bwaa("level%d unknown child: ", level, child.tag, child.attrib)

def convert(src, dst):
    # Read XML
    write_para("Reading %s" % (src))
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
