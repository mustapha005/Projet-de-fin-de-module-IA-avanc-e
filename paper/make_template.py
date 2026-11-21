"""Build paper/template_2col.docx: an IEEE-conference-like pandoc reference document.

Run with the paper environment: .venv-paper/Scripts/python.exe paper/make_template.py
Two columns are set on the final section; build.py inserts the single-column title
section and full-width sections around elements marked wide.
"""
from pathlib import Path

from docx import Document
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Mm, Pt, RGBColor

HERE = Path(__file__).resolve().parent
FONT = 'Times New Roman'


def style(document, name, kind=WD_STYLE_TYPE.PARAGRAPH, base='Normal'):
    try:
        return document.styles[name]
    except KeyError:
        created = document.styles.add_style(name, kind)
        if kind == WD_STYLE_TYPE.PARAGRAPH and base:
            created.base_style = document.styles[base]
        return created


def font(target, size, bold=None, italic=None, caps=None, color=RGBColor(0, 0, 0)):
    target.font.name = FONT
    target.font.size = Pt(size)
    target.font.color.rgb = color
    if bold is not None:
        target.font.bold = bold
    if italic is not None:
        target.font.italic = italic
    if caps is not None:
        target.font.small_caps = caps
    fonts = target.element.get_or_add_rPr().get_or_add_rFonts()
    for attribute in ('w:asciiTheme', 'w:hAnsiTheme', 'w:eastAsiaTheme', 'w:cstheme'):
        fonts.attrib.pop(qn(attribute), None)
    for attribute in ('w:ascii', 'w:hAnsi', 'w:cs', 'w:eastAsia'):
        fonts.set(qn(attribute), FONT)


def paragraph(target, align=None, before=0, after=0, line=None, indent=None, keep=False):
    p = target.paragraph_format
    if align is not None:
        p.alignment = align
    p.space_before, p.space_after = Pt(before), Pt(after)
    if line:
        p.line_spacing = line
    if indent is not None:
        p.first_line_indent = indent
    p.keep_with_next = keep


def main():
    document = Document()
    section = document.sections[0]
    section.page_width, section.page_height = Mm(210), Mm(297)
    section.top_margin, section.bottom_margin = Mm(19), Mm(25)
    section.left_margin = section.right_margin = Mm(15)
    columns = OxmlElement('w:cols')
    columns.set(qn('w:num'), '2')
    columns.set(qn('w:space'), str(int(Mm(5).twips)))
    section._sectPr.append(columns)

    normal = document.styles['Normal']
    font(normal, 10)
    paragraph(normal, WD_ALIGN_PARAGRAPH.JUSTIFY, 0, 0, 1.0, Mm(3.5))
    for name in ('Body Text', 'First Paragraph', 'Compact'):
        s = style(document, name)
        font(s, 10)
        paragraph(s, WD_ALIGN_PARAGRAPH.JUSTIFY, 0, 2 if name != 'Compact' else 0, 1.0, Mm(3.5))
    title = style(document, 'Title')
    font(title, 22, bold=False)
    for border in title.element.findall('.//' + qn('w:pBdr')):
        border.getparent().remove(border)
    paragraph(title, WD_ALIGN_PARAGRAPH.CENTER, 0, 6, 1.0, Mm(0))
    author = style(document, 'Author')
    font(author, 11)
    paragraph(author, WD_ALIGN_PARAGRAPH.CENTER, 0, 10, 1.0, Mm(0))
    for name in ('Abstract', 'AbstractTitle', 'Keywords'):
        s = style(document, name)
        font(s, 9, bold=True)
        paragraph(s, WD_ALIGN_PARAGRAPH.JUSTIFY, 0, 4, 1.0, Mm(3.5))
    heading1 = style(document, 'Heading 1')
    font(heading1, 10, bold=False, caps=True)
    paragraph(heading1, WD_ALIGN_PARAGRAPH.CENTER, 8, 4, 1.0, Mm(0), keep=True)
    heading2 = style(document, 'Heading 2')
    font(heading2, 10, bold=False, italic=True)
    paragraph(heading2, WD_ALIGN_PARAGRAPH.LEFT, 6, 3, 1.0, Mm(0), keep=True)
    heading3 = style(document, 'Heading 3')
    font(heading3, 10, italic=True)
    paragraph(heading3, WD_ALIGN_PARAGRAPH.LEFT, 4, 2, 1.0, Mm(3.5), keep=True)
    for name in ('Table Caption', 'Image Caption', 'Caption'):
        s = style(document, name)
        font(s, 8)
        paragraph(s, WD_ALIGN_PARAGRAPH.CENTER, 3, 4, 1.0, Mm(0))
    figure = style(document, 'Captioned Figure')
    paragraph(figure, WD_ALIGN_PARAGRAPH.CENTER, 4, 0, 1.0, Mm(0), keep=True)
    for name in ('Figure',):
        s = style(document, name)
        paragraph(s, WD_ALIGN_PARAGRAPH.CENTER, 4, 0, 1.0, Mm(0), keep=True)
    bibliography = style(document, 'Bibliography')
    font(bibliography, 8)
    paragraph(bibliography, WD_ALIGN_PARAGRAPH.LEFT, 0, 1, 1.0, Mm(0))
    quote = style(document, 'Block Text')
    font(quote, 9.5, italic=True)
    paragraph(quote, WD_ALIGN_PARAGRAPH.JUSTIFY, 2, 4, 1.0, Mm(0))
    marker = style(document, 'SectionMarker')
    font(marker, 1)
    paragraph(marker, None, 0, 0, 1.0, Mm(0))
    table = style(document, 'Table', WD_STYLE_TYPE.TABLE, base=None)
    font(table, 7)
    code = style(document, 'Verbatim Char', WD_STYLE_TYPE.CHARACTER, base=None)
    code.font.name = 'Consolas'
    code.font.size = Pt(8.5)
    document.add_paragraph('Template body (replaced by pandoc).')
    document.save(HERE / 'template_2col.docx')
    print('Wrote', HERE / 'template_2col.docx')


if __name__ == '__main__':
    main()
