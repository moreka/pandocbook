import os
import time
import sys

import bibtexparser
import panflute as pf

from filters.handlers import *
from filters.aux import loadyaml


def load_bibfile(doc):
    bibfile = doc.get_metadata("bibfile", "")
    if bibfile:
        doc.bibfile = os.path.join(doc.sourcedir, bibfile)
    else:
        doc.bibfile = ""
    if doc.bibfile:
        with open(doc.bibfile) as bibtex_file:
            doc.bibentries = bibtexparser.load(bibtex_file).entries_dict
    else:
        doc.bibentries = {}


def initialize_logger(doc, filename):
    logdir = doc.get_metadata("logdir", "log")
    if not os.path.isdir(logdir):
        logdir = ""
    logfilename = (
        os.path.join(logdir, os.path.basename(filename) + ".log")
        if filename
        else "book-filter.log"
    )
    doc.logfile = open(logfilename, "w", encoding="utf-8")
    doc.logfile.write("Created at " + time.strftime("%m/%d/%Y %H:%M:%S"))
    doc.logfile.write("LOG: argv:" + str(sys.argv) + "\n")
    doc.logfile.write("Metadata:\n" + str(doc.metadata) + "\n")
    doc.logfile.write(doc.format + "\n")


def action(e, doc):
    """apply handlers one by one to the element, until one of them 
       returns an element. Otherwise, keep the element unchanged."""

    for h in doc.handlers:
        f = h(e, doc)
        if f is not None:
            return f
    return e


def prepare(doc): 
    """Initial function called at the beginning of the filter"""

    filename = doc.get_metadata("filename", "")
    doc.sourcedir = doc.get_metadata("sourcedir", "content/")
    doc.chapternum = doc.get_metadata("chapternum", default="99")
    doc.format = "latex"  # FIXME

    load_bibfile(doc)
    initialize_logger(doc, filename)
    
    doc.label_descriptions = {}  # FIXME: eventually handle different files, counters
    # doc.searchtext = ""          # FIXME: sth for index?

    # if doc.format == "html":
    #     doc.toc = removekeys(loadyaml("toc.yaml"), doc.chapternum + ".")
    #     pdflink(doc)

    auxfilename = doc.get_metadata("auxfile", "bookaux.yaml")
    doc.labels = loadyaml(auxfilename)
    
    # doc.currentlevel = 1
    # doc.currentplace = [doc.chapternum]
    # doc.footnotecounter = 1
    # doc.footnotecontents = []
    doc.latex_headers = {
            1: "chapter",
            2: "section",
            3: "subsection",
            4: "subsubsection",
            5: "paragraph",
            6: "subparagraph",
    }

    doc.handlers = [
        h_paragraph,
        # h_csvtable,
        # h_add_search,
        # h_block_header,
        h_link_ref,
        h_latex_headers,
        h_latex_div,
        h_latex_image,
        # h_latex_cite,
        # h_html_footnote,
        # h_html_header,
        # h_emph,
        h_math,
        # h_html_image,
        # h_html_code_block
    ]

def finalize(doc):
    doc.logfile.close()


def main(doc=None):
    return pf.run_filter(action, prepare=prepare, finalize=finalize, doc=doc)


if __name__ == "__main__":
    main()
