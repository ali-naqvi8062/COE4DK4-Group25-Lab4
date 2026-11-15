"""Create an editable Word report from the same content as the PDF report."""
from html.parser import HTMLParser

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor
from reportlab.platypus import Paragraph, Table, Image, Spacer, PageBreak, Preformatted

import report
from common import ROOT


class InlineText(HTMLParser):
    def __init__(self, paragraph):
        super().__init__(convert_charrefs=True)
        self.paragraph = paragraph
        self.italic = self.bold = self.superscript = False
        self.link = None

    def handle_starttag(self, tag, attrs):
        if tag == "i": self.italic = True
        elif tag == "b": self.bold = True
        elif tag == "super": self.superscript = True
        elif tag == "br": self.paragraph.add_run().add_break()
        elif tag == "link": self.link = dict(attrs).get("href")

    def handle_endtag(self, tag):
        if tag == "i": self.italic = False
        elif tag == "b": self.bold = False
        elif tag == "super": self.superscript = False
        elif tag == "link": self.link = None

    def handle_data(self, data):
        run = self.paragraph.add_run(data)
        if self.italic: run.italic = True
        if self.bold: run.bold = True
        if self.superscript: run.font.superscript = True
        if self.link:
            relationship = self.paragraph.part.relate_to(
                self.link,
                "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink",
                is_external=True)
            link = OxmlElement("w:hyperlink")
            link.set(qn("r:id"), relationship)
            run.font.color.rgb = RGBColor.from_string("0000FF")
            link.append(run._r)
            self.paragraph._p.append(link)


def inline(paragraph, value):
    InlineText(paragraph).feed(value)


def border(cell, edge, size="4"):
    props = cell._tc.get_or_add_tcPr()
    borders = props.find(qn("w:tcBorders"))
    if borders is None:
        borders = OxmlElement("w:tcBorders"); props.append(borders)
    element = OxmlElement("w:" + edge)
    for key, value in {"val": "single", "sz": size, "color": "444444"}.items():
        element.set(qn("w:" + key), value)
    borders.append(element)


def make_word(flowables):
    doc = Document()
    section = doc.sections[0]
    section.page_width = Inches(8.5); section.page_height = Inches(11)
    section.left_margin = section.right_margin = Inches(1)
    section.top_margin = Pt(65); section.bottom_margin = Pt(60)
    section.footer_distance = Pt(25)
    section.different_first_page_header_footer = True

    for name in ["Normal", "Title", "Heading 1", "Heading 2", "Caption"]:
        style = doc.styles[name]
        style.font.name = "Times New Roman"
        style.font.color.rgb = RGBColor(0,0,0)
        style.font.bold = name.startswith("Heading")
        fonts = style.element.get_or_add_rPr().rFonts
        for key in list(fonts.attrib):
            if "theme" in key.lower(): del fonts.attrib[key]
        for element in style.element.xpath(".//w:pBdr"):
            element.getparent().remove(element)
        style.paragraph_format.space_before = Pt(0)
    normal = doc.styles["Normal"]
    normal.font.size = Pt(11)
    normal.paragraph_format.line_spacing = Pt(14)
    normal.paragraph_format.space_after = Pt(9)
    normal.paragraph_format.widow_control = True
    for name in ["Heading 1", "Heading 2"]:
        style = doc.styles[name]
        style.font.size = Pt(12); style.font.bold = True
        style.paragraph_format.line_spacing = Pt(15)
        style.paragraph_format.space_after = Pt(12)
    doc.styles["Caption"].font.size = Pt(9)
    doc.styles["Caption"].font.italic = True
    doc.styles["Caption"].paragraph_format.line_spacing = Pt(11)
    doc.styles["Caption"].paragraph_format.space_after = Pt(12)
    doc.styles["Title"].font.size = Pt(14)
    doc.styles["Title"].paragraph_format.line_spacing = Pt(22)
    doc.styles["Title"].paragraph_format.space_after = Pt(0)

    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = footer.add_run(); run.font.size = Pt(9)
    field = OxmlElement("w:fldSimple"); field.set(qn("w:instr"), "PAGE")
    run._r.addnext(field)

    break_before = False
    leading_space = 0
    for item in flowables:
        if isinstance(item, PageBreak):
            break_before = True
        elif isinstance(item, Spacer):
            if not doc.paragraphs:
                leading_space = item.height
            elif item.height > 0:
                p = doc.add_paragraph()
                p.paragraph_format.line_spacing = Pt(1)
                p.paragraph_format.space_after = Pt(max(0,item.height-1))
                p.paragraph_format.space_before = Pt(0)
                p.add_run().font.size = Pt(1)
        elif isinstance(item, Paragraph):
            kind = item.style.name
            style = {"Cover":"Title", "Heading":"Heading 1", "Caption":"Caption"}.get(kind,"Normal")
            p = doc.add_paragraph(style=style)
            p.paragraph_format.page_break_before = break_before
            break_before = False
            if leading_space:
                p.paragraph_format.space_before = Pt(leading_space); leading_space=0
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            if kind in ["Cover","Caption"]: p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            if kind == "Heading": p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            if kind == "Caption":
                p.paragraph_format.keep_with_next = item.text.startswith("Table")
            if kind == "Cover": p.paragraph_format.keep_with_next = False
            inline(p,item.text)
        elif isinstance(item, Table):
            rows = item._cellvalues
            table = doc.add_table(rows=len(rows),cols=len(rows[0]))
            table.alignment = WD_TABLE_ALIGNMENT.CENTER
            table.autofit = False
            widths = item._colWidths
            for col, width in zip(table.columns,widths): col.width=Pt(width)
            for i,row in enumerate(rows):
                trpr = table.rows[i]._tr.get_or_add_trPr()
                trpr.append(OxmlElement("w:cantSplit"))
                if i == 0: trpr.append(OxmlElement("w:tblHeader"))
                for j,value in enumerate(row):
                    cell = table.cell(i,j); cell.width=Pt(widths[j])
                    cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
                    props = cell._tc.get_or_add_tcPr()
                    margins = OxmlElement("w:tcMar")
                    for edge, amount in [("top",80),("bottom",80),("left",100),("right",100)]:
                        margin = OxmlElement("w:"+edge)
                        margin.set(qn("w:w"),str(amount)); margin.set(qn("w:type"),"dxa")
                        margins.append(margin)
                    props.append(margins)
                    if i == 0:
                        shade=OxmlElement("w:shd"); shade.set(qn("w:fill"),"EEEEEE"); props.append(shade)
                        border(cell,"top"); border(cell,"bottom")
                    if i == len(rows)-1: border(cell,"bottom")
                    p=cell.paragraphs[0]
                    p.paragraph_format.space_after=Pt(0)
                    p.paragraph_format.line_spacing=Pt(11)
                    p.paragraph_format.keep_with_next=False
                    inline(p,value.text)
                    for run in p.runs: run.font.size=Pt(9)
        elif isinstance(item, Image):
            p=doc.add_paragraph()
            p.alignment=WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_after=Pt(0)
            p.paragraph_format.keep_with_next=True
            p.paragraph_format.line_spacing=1
            pic=p.add_run().add_picture(item.filename,width=Pt(item.drawWidth),height=Pt(item.drawHeight))
            pic._inline.docPr.set("descr",item.filename.rsplit("/",1)[-1].replace("_"," "))
        elif isinstance(item, Preformatted):
            p=doc.add_paragraph()
            p.paragraph_format.line_spacing=Pt(10)
            p.paragraph_format.space_after=Pt(9)
            p.paragraph_format.keep_together=True
            run=p.add_run("\n".join(item.lines))
            run.font.name="Courier New"; run.font.size=Pt(8)
        else:
            raise TypeError(type(item))
    doc.core_properties.title="COE4DK4 Group 25 Lab 4 Report"
    doc.core_properties.author="Group 25"
    doc.core_properties.subject="Simulation of ARQ Protocols"
    output=ROOT / "output/docx/COE4DK4_Group25_Lab4_Report.docx"
    output.parent.mkdir(parents=True,exist_ok=True)
    doc.save(output)
    print(output)


class WordBuilder:
    def __init__(self,*args,**kwargs): pass
    def build(self,flowables,**kwargs): make_word(flowables)


if __name__ == "__main__":
    # Capture the existing report's layout objects without changing its PDF.
    report.OUT=ROOT / "tmp/word-source"
    report.TABLES=report.OUT / "tables"
    report.TABLES.mkdir(parents=True,exist_ok=True)
    report.SimpleDocTemplate=WordBuilder
    report.build_report()
