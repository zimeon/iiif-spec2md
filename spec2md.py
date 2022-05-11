#!/usr/bin/env python3
"""Hack to help convert OCFL specs to Markdown."""
from collections import OrderedDict
import json
import os
import pathlib
import re
import textwrap
import xml.etree.ElementTree as ET

spec_src = "../ocfl-spec/draft/spec/index.html"
spec_dst = "docs/spec.md"
impl_src = "../ocfl-spec/draft/implementation-notes/index.html"
impl_dst = "docs/impl.md"
text_width = 72


class Bwaa(Exception):
    """My exception."""

    pass


class Markdown_Writer(object):
    """Write markdown output."""

    def __init__(self, ofh, refs):
        """Initialize and set output filehandle."""
        self.ofh = ofh
        self.refs = refs
        self.refs_used = {}
        self.refs_normative = set()

    def ref_link(self, matchobj):
        """Make reference markdown link from label."""
        label = matchobj.group(2)
        if matchobj.group(1) == "!":
            self.refs_normative.add(label)
        if label not in self.refs:
            raise Bwaa("Reference with label " + label + " not in references file")
        anchor = 'ref-' + re.sub(r'''[\s_]+''', '-', label.lower())
        self.refs_used[label] = anchor
        return "\[[" + label + "](#" + anchor + ")\]"

    def write_references(self):
        """Write referencese section base on refs_used."""
        normative = []
        informative = []
        for label in sorted(self.refs_used.keys()):
            anchor = self.refs_used[label]
            md = '<span id="%s"/>**\[%s]** %s' % (anchor, label, self.refs[label])
            if label in self.refs_normative:
                normative.append(md)
            else:
                informative.append(md)
        if normative:
            self.line("### Normative")
            self.para("{: #normative-references}")
            for md in normative:
                self.para(md)
        if informative:
            self.line("### Informative")
            self.para("{: #informative-references}")
            for md in informative:
                self.para(md)

    def munge_and_link(self, *args):
        """Sort out spaces and also link refs."""
        text = re.sub(r'''\s+''', ' ', " ".join(args))
        text = re.sub(r'''\[\[(\!)?(\S+)\]\]''', self.ref_link, text)
        return text

    def line(self, *args):
        """Write a line."""
        text = self.munge_and_link(*args)
        self.ofh.write(textwrap.fill(text.strip(), width=text_width, break_long_words=False) + "\n")

    def long_line(self, *args):
        """Write a line without wrapping."""
        text = self.munge_and_link(*args)
        self.ofh.write(text.strip() + "\n")

    def para(self, *args):
        """Write a paragraph or block of Markdown, line with blank line following."""
        self.line(*args)
        self.ofh.write("\n")

    def example(self, text, prefix=''):
        """Write a preformatted example in Markdown."""
        self.ofh.write(prefix + "```\n" + text.strip() + "\n```\n\n")


class Converter(object):
    """Convert from ReSpec HTML to Markdown."""

    def __init__(self):
        """Initialize."""
        self.writer = None
        with open("references.json", "r") as fh:
            self.refs = json.load(fh)
        self.init_new_conversion()

    def init_new_conversion(self):
        """Initialize new conversion of a file."""
        self.run = 0  # will be incremented to 1 by init_first_run
        self.section = OrderedDict()  # anchor -> heading including number

    def init_new_run(self):
        """Initilize for new run within a conversion."""
        self.run += 1
        self.passed_sotd = False
        self.section_number = [0]  # will be incremented to 1 on first use

    def get_anchor(self, element):
        """Look for id tags in element."""
        anchor = element.attrib.get('id', None)
        return anchor

    def process_para_inner(self, element, prefix=''):
        """Return string from paragraph like content."""
        txt = ""
        if element.text is not None:
            txt += element.text
        for child in element:
            text = child.text.strip() if child.text is not None else None
            if child.tag == 'a':
                if text is None:
                    anchor = child.attrib["href"].lstrip("#")
                    if anchor in self.section:
                        text = self.section[anchor]
                    elif self.run == 2:
                        raise Bwaa("No section heading for anchor " + anchor)
                    else:
                        text = 'FIXME-IN-RUN-2'
                if 'href' in child.attrib:
                    txt += "[" + text + "](" + child.attrib['href'] + ")"
                else:
                    txt += "[" + text + "](#" + text + ")"
            elif child.tag == 'code':
                txt += "`" + text + "`"
            elif child.tag == 'span':
                # We only use <span. for id= anchors for errors and warnings,
                # we just replicate this in output
                txt += '<span id="' + child.attrib['id'] + '">' + text + "</span>"
            elif child.tag == 'i':
                txt += "_" + text + "_"
            elif child.tag == 'pre':
                self.process_pre(child, prefix)
            else:
                raise Bwaa("Unrecognized element in para_inner: " + child.tag)
            if child.tail is not None and child.tail.strip() not in (None, ''):
                txt += child.tail
        if element.tail.strip() not in (None, ''):
            txt += element.tail
        return txt

    def process_para(self, element, prefix=''):
        """Process a paragraph."""
        txt = prefix + self.process_para_inner(element, prefix)
        self.writer.para(txt)

    def process_pre(self, element, prefix=''):
        """Process a pre example block."""
        self.writer.example(element.text, prefix=prefix)
        tail = element.tail.strip()
        if tail not in (None, ""):
            raise Bwaa("Unexpected tail text ", tail)

    def process_section(self, element, level=1):
        """Process one <section> block."""
        section_number = ''
        if self.passed_sotd:
            # Now numbering sections
            if level > (len(self.section_number) + 1):
                # One level deeper, add extra number
                self.section_number.append(1)
            elif level == (len(self.section_number) + 1):
                # Next section at same level
                self.section_number[level - 2] += 1
            else:
                # Up a level
                self.section_number.pop()
                self.section_number[level - 2] += 1
            section_number = '.'.join(str(n) for n in self.section_number)
            section_number += '. ' if level == 2 else ' '
        print("> level %d, section %s, attribs %s" % (level, section_number, element.attrib))
        if 'id' not in element.attrib:
            pass
        elif element.attrib['id'] == 'sotd':
            self.writer.line("## Status of This Document")
            self.writer.para("{: #sotd}")
            self.writer.para("This document is draft of a potential specification. It has no official standing of any kind and does not represent the support or consensus of any standards organisation.")
            self.passed_sotd = True
            self.writer.para("INSERT_TOC_HERE")
            return
        elif element.attrib['id'] == 'conformance':
            section_heading = section_number + "Conformance"
            self.section['conformance'] = section_heading
            self.writer.line("## " + section_heading)
            self.writer.para("{: #conformance}")
            self.writer.para("As well as sections marked as non-normative, all authoring guidelines, diagrams, examples, and notes in this specification are non-normative. Everything else in this specification is normative.")
            self.writer.para("The key words may, must, must not, should, and should not are to be interpreted as described in [RFC2119].")
            return
        anchor = self.get_anchor(element)
        for child in element:
            if child.tag == 'section':
                self.process_section(child, (level + 1))
            elif child.tag in ('h1', 'h2', 'h3'):
                section_heading = section_number + child.text
                if anchor is None:
                    anchor = re.sub(r'''\s+''', '-', child.text.lower())
                if self.run == 1:
                    if anchor in self.section:
                        raise Bwaa("duplicate section anchor " + anchor)
                    self.section[anchor] = section_heading
                self.writer.line("#" * level, " ", section_heading)
                self.writer.para("{: #%s}" % (anchor))
                if child.tail.strip() not in (None, ""):
                    raise Bwaa("Unexpected tail text ", child.tail)
            elif child.tag == 'p':
                self.process_para(child)
            elif child.tag == 'pre':
                self.process_pre(child)
            elif child.tag == 'ul':
                for item in child:
                    self.process_para(item, prefix="  * ")
            elif child.tag == 'ol':
                n = 1
                for item in child:
                    self.process_para(item, prefix="  %d. " % n)
                    n += 1
            elif child.tag == 'dl':
                dt = "MISSING"
                for item in child:
                    if item.tag == 'dt':
                        for dfn in item:
                            dt = dfn.text.strip()
                    elif item.tag == 'dd':
                        self.process_para(item, prefix="  * **" + dt + ":** ")
                    else:
                        Bwaa("Unexpected tag in dl: " * item.tag)
            elif child.tag == "table":
                row_num = 0
                for head_and_body in child:
                    for row in head_and_body:
                        row_num += 1
                        div_text = "| "
                        row_text = "| "
                        for cell in row:
                            div_text += "--- | "
                            row_text += self.process_para_inner(cell) + " | "
                        if row_num == 2:
                            self.writer.long_line("| --- | --- |")
                        self.writer.long_line(row_text)
                self.writer.line("")
            elif child.tag == "blockquote":
                # We expect just paragraps inside blockquote
                for p in child:
                    if p.tag == 'p':
                        self.process_para(p, prefix='> ')
                    elif p.tag == 'pre':
                        self.process_pre(p, prefix='> ')
                    else:
                        raise Bwaa("Unexpected element in blockquote: " + p.tag)

            else:
                raise Bwaa("level%d unknown child: ", level, child.tag, child.attrib)

    def convert(self, src, dst, preamble=None):
        """Convert src ReSpec HTML to dst in Markdown."""
        self.init_new_conversion()
        # Read XML
        print("Reading %s" % (src))
        path = pathlib.Path(src)
        src_xml = path.read_text()
        # Remove non-XML bit
        src_xml = re.sub(' async ', ' ', src_xml)
        src_xml = re.sub('&mdash;', '&#x2014;', src_xml)
        root = ET.fromstring(src_xml)
        # Have parsed XML in root, now open dst for output and
        # then convert the chunks of the file by <section>
        for output_file in (os.devnull, dst):
            self.init_new_run()
            with open(output_file, 'w', encoding='utf-8') as ofh:
                print("# PASS %d" % (self.run))
                ofh.write("---\n---\n")  # Jekyll frontmatter
                if preamble:
                    ofh.write(pathlib.Path(preamble).read_text())
                self.writer = Markdown_Writer(ofh, self.refs)
                body = root.find('body')
                for child in body:
                    # At the top level we expect only <section> blocks, we will
                    # parse these recursively
                    if child.tag != 'section':
                        raise Bwaa("Unexpected tag")
                    self.process_section(child, 2)
                # Finally, add references
                self.section['references'] = "References"
                self.writer.line("## " + "References")
                self.writer.para("{: #references}")
                self.writer.write_references()


cnv = Converter()
try:
    cnv.convert(src=spec_src, dst=spec_dst, preamble="spec_preamble.md")
    cnv.convert(src=impl_src, dst=impl_dst, preamble="impl_preamble.md")
except Bwaa as e:
    print(e)
