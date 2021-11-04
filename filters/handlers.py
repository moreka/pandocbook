import re

import panflute as pf

from pylatexenc.latex2text import LatexNodes2Text


def labelref(e):
    """If e has an id, use e.identifier, otherwise create a label from e's content"""
    if e.identifier:
        return e.identifier
    regex = re.compile(r"[^a-zA-Z\-]")
    t = regex.sub("", pf.stringify(e).replace(" ", "-"))[:25]
    if t:
        return t
    return "temp-label"


def getlabel(label, doc):
    """
    Return name (e.g., `Theorem 12.1`) and link (e.g. 'blah.html#mainthm') for a given label.
    Uses the labels dictionary that is initialized from a yaml file 
    and is updated from the LateX aux file.
    """
    name, number, file = get_full_label(label, doc)
    return f"{name} {number}", f"{file}#{label}"


def get_full_label(label, doc):
    """
    Return (name,number,file) given a label
    """
    T = doc.labels.get(label, None)
    if not T:
        return "??", "??", ""
    name = doc.label_classes.get(T["class"], T["class"].capitalize())
    number = T["number"] if T["number"] else ""
    file = T["file"] + ".html" if T["file"] != doc.get_metadata("filename", "") else ""
    return name, number, file


def math2unicode(math):
    pattern = r'\$([^\$]+)\$'

    def repl(matchobj):
        s = matchobj.group(1)
        return LatexNodes2Text().latex_to_text("\\("+s+"\\)")

    return re.sub(pattern, repl, math)


def h_latex_headers(e, doc):
    """make headers correspond to names in latex_headers (chapter, section, subsection, etc.).
    updates the doc.label_descriptions"""

    if not isinstance(e, pf.Header):
        return None
    if isinstance(e.parent, pf.BlockQuote):
        return None

    label = labelref(e)

    if label and e.level in doc.latex_headers:
        doc.label_descriptions[label] = doc.latex_headers[e.level].capitalize()

    if doc.format != "latex":
        return None

    labeltext = f"\\label{{{label}}}" if label else ""
    h = e.level

    doc.logfile.write(str(h) + " " + pf.stringify(e) + "\n")

    if not h in doc.latex_headers:
        raise Exception(f"Invalid header level {h} in {e}")

    header = "\\" + doc.latex_headers[h]
    return pf.Para(
        pf.RawInline(header + "{", format="latex"),
        *e.content,
        pf.RawInline("}" + labeltext, format="latex"),
    )


def h_paragraph(e, doc):
    """Make lines starting with bold become paragraphs."""
    if not isinstance(e, pf.Strong) or doc.format != "latex":
        return None
    if (
        isinstance(e.parent, pf.Para)
        and e.parent.parent == doc
        and e.parent.content.index(e) == 0
    ):
        return pf.RawInline(r"\paragraph{" + pf.stringify(e) + "}", format="latex")
    return None


def h_link_ref(e, doc):
    """Change links of class .ref to latex labels"""
    if not isinstance(e, pf.Link):
        return None
    if not e.classes:
        return None
    
    label = "".join(pf.stringify(a) for a in e.content)
    if label[0] == "#":
        label = label[1:]
    if not label:
        label = "???"
    
    if doc.format == "latex":
        if "ref" in e.classes or "eqref" in e.classes:
            return pf.RawInline(f"\\pref{{{label}}}", format="latex")
        else:
            e.url = e.url.replace("_", "%5F")
            return e

    if doc.format == "html":
        name, link = getlabel(label, doc)
        if "ref" in e.classes or "eqref" in e.classes:
            return pf.RawInline(fr"<a href='{link}'>{name}</a>", format="html")
    return e


def h_math(e, doc):
    if not isinstance(e, pf.Math):
        return None
    if not e.format:
        return None

    if e.format == "DisplayMath":
        reg = r"\\label\{eq:([a-zA-Z\:\_\-0-9]+)\}"
        if re.search(reg, e.text):
            if doc.format == "latex":
                return pf.RawInline("\\begin{equation}"+e.text + "\\end{equation}", format="latex")
            else:
                # TODO: what about align environments?
                raise NotImplementedError("have to implement the HTML version / add eqn numbers inside the equation")
            
    return e


def h_latex_div(e, doc):
    r"""make every div with class=foo to begin{foo} ... end{foo}
    if there is title then it is begin{foo}[title] instead
    if there is an identifier then we add \label[foo]{id}"""
    if not isinstance(e, pf.Div):
        return None
    if not len(e.classes):
        return None

    c = e.classes[0]
    title = e.attributes.get("title", "")

    if title and doc.format != "latex":
        title = math2unicode(title)
        e.attributes["title"] = title

    name = c.capitalize()
    if title:
        name += f" ({title}) "
    e.attributes["name"] = name

    if e.identifier:
        doc.label_descriptions[e.identifier] = c.capitalize()

    if doc.format == "html" and c == "quote":
        return pf.BlockQuote(e)
    if doc.format != "latex":
        return e

    label = labelref(e)
    before = f"\\begin{{{c}}}[{title}]" if title else f"\\begin{{{c}}}"
    if label:
        before += f" \\label{{{label}}}"
    after = f"\\end{{{c}}}"

    _before = pf.RawBlock(before, format="latex")
    _after = pf.RawBlock(after, format="latex")
    e.content = [_before] + list(e.content) + [_after]
    return e


def h_latex_image(e, doc):
    """
    Handle images with automatic scaling.
    Image classes: (for tufte)
    full : full page  - figure*
    margin: margin figure - marginfigure
    """
    if not isinstance(e, pf.Para) or doc.format != "latex":
        return None
    if not len(e.content) == 1:
        return None
    if not isinstance(e.content[0], pf.Image):
        return None

    img: pf.Image = e.content[0]
    capoffset = ""
    figoffset = ""
    preamble = ""
    if "offset" in img.attributes:
        capoffset = f"[][{img.attributes['offset']}]"
    if "full" in img.classes:
        fig = "figure*"
        # preamble = "\n" + r"\classiccaptionstyle"
        scale = "width=0.9\\paperwidth, height=0.3\\paperheight, keepaspectratio"
    elif "margin" in img.classes:
        fig = "marginfigure"
        figoffset = capoffset[2:] if capoffset else ""
        capoffset = ""
        scale = r"width=\linewidth, height=1.5in, keepaspectratio"
    else:
        fig = "figure"
        scale = "width=\\textwidth, height=0.25\\paperheight, keepaspectratio"
    before = f"\n\\begin{{{fig}}}{figoffset}\n{preamble}\\centering\n"
    label = img.identifier
    end = f"\n\\end{{{fig}}}\n"
    graphic = f"\\includegraphics[{scale}]{{{img.url}}}\n"
    if label:
        end = fr"\label{{{label}}}" + end
    _before = pf.RawInline(before + graphic + f"\\caption{capoffset}{{", format="latex")
    _after = pf.RawInline("}\n" + end, format="latex")
    return pf.Para(_before, *img.content, _after)

