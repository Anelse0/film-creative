#!/usr/bin/env python3
"""Minimal .xlsx reader/writer (standard library only).

Reads cell values from every worksheet of an OOXML workbook: shared strings,
inline strings, numbers, booleans and formulas (the cached value when present,
otherwise the formula text prefixed with "="). Writes a plain workbook with
inline strings for test fixtures and small exports. It is not a general
spreadsheet library: styles, merged cells, charts and dates-as-formats are
ignored; Excel serial times are returned as floats for the caller to interpret.
"""
import re
import zipfile
from xml.etree import ElementTree as ET

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
      "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"}
REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"


def column_index(ref):
    """'C7' -> 3 (1-based column)."""
    letters = re.match(r"[A-Z]+", ref).group(0)
    n = 0
    for ch in letters:
        n = n * 26 + ord(ch) - 64
    return n


def column_letter(index):
    out = ""
    while index:
        index, rem = divmod(index - 1, 26)
        out = chr(65 + rem) + out
    return out


def _shared_strings(zf):
    if "xl/sharedStrings.xml" not in zf.namelist():
        return []
    root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
    out = []
    for si in root.findall("m:si", NS):
        out.append("".join(t.text or "" for t in si.iter("{%s}t" % NS["m"])))
    return out


def _sheet_paths(zf):
    wb = ET.fromstring(zf.read("xl/workbook.xml"))
    rels = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
    targets = {}
    for rel in rels.findall("{%s}Relationship" % REL_NS):
        target = rel.get("Target")
        if target.startswith("/"):
            target = target[1:]
        elif not target.startswith("xl/"):
            target = "xl/" + target
        targets[rel.get("Id")] = target
    sheets = []
    for sheet in wb.find("m:sheets", NS).findall("m:sheet", NS):
        rid = sheet.get("{%s}id" % NS["r"])
        sheets.append((sheet.get("name"), targets[rid]))
    return sheets


def read_workbook(path):
    """Return {sheet_name: [[cell, ...], ...]} with 1-based row/col padding kept.

    Rows are lists indexed from column A (index 0). Empty cells are None.
    """
    result = {}
    with zipfile.ZipFile(path) as zf:
        shared = _shared_strings(zf)
        for name, target in _sheet_paths(zf):
            root = ET.fromstring(zf.read(target))
            rows = []
            data = root.find("m:sheetData", NS)
            if data is None:
                result[name] = rows
                continue
            for row in data.findall("m:row", NS):
                r = int(row.get("r"))
                while len(rows) < r:
                    rows.append([])
                cells = rows[r - 1]
                for c in row.findall("m:c", NS):
                    col = column_index(c.get("r"))
                    while len(cells) < col:
                        cells.append(None)
                    kind = c.get("t")
                    v = c.find("m:v", NS)
                    f = c.find("m:f", NS)
                    value = None
                    if kind == "s" and v is not None:
                        value = shared[int(v.text)]
                    elif kind == "inlineStr":
                        is_ = c.find("m:is", NS)
                        value = "".join(t.text or "" for t in is_.iter("{%s}t" % NS["m"])) if is_ is not None else ""
                    elif kind == "b" and v is not None:
                        value = v.text == "1"
                    elif kind == "str" and v is not None:
                        value = v.text
                    elif v is not None and v.text is not None:
                        text = v.text
                        value = float(text) if re.fullmatch(r"-?\d+(\.\d+)?(E[-+]?\d+)?", text, re.I) else text
                        if isinstance(value, float) and value.is_integer() and "." not in text and "E" not in text.upper():
                            value = int(value)
                    elif f is not None:
                        value = "=" + (f.text or "")
                    cells[col - 1] = value
            result[name] = rows
    return result


def _xml_escape(text):
    return (str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def write_workbook(path, sheets):
    """Write {sheet_name: [[value, ...], ...]} as a minimal .xlsx (inline strings).

    Numbers are written as numbers, None skipped, everything else as text.
    Intended for fixtures and small exports, not for styled deliverables.
    """
    names = list(sheets)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml",
                    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                    '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                    '<Default Extension="xml" ContentType="application/xml"/>'
                    '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
                    + "".join(f'<Override PartName="/xl/worksheets/sheet{i+1}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>' for i in range(len(names)))
                    + "</Types>")
        zf.writestr("_rels/.rels",
                    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                    f'<Relationships xmlns="{REL_NS}">'
                    '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
                    "</Relationships>")
        zf.writestr("xl/workbook.xml",
                    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                    f'<workbook xmlns="{NS["m"]}" xmlns:r="{NS["r"]}"><sheets>'
                    + "".join(f'<sheet name="{_xml_escape(n)}" sheetId="{i+1}" r:id="rId{i+1}"/>' for i, n in enumerate(names))
                    + "</sheets></workbook>")
        zf.writestr("xl/_rels/workbook.xml.rels",
                    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                    f'<Relationships xmlns="{REL_NS}">'
                    + "".join(f'<Relationship Id="rId{i+1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{i+1}.xml"/>' for i in range(len(names)))
                    + "</Relationships>")
        for i, name in enumerate(names):
            body = []
            for r, row in enumerate(sheets[name], start=1):
                cells = []
                for c, value in enumerate(row, start=1):
                    if value is None:
                        continue
                    ref = f"{column_letter(c)}{r}"
                    if isinstance(value, bool):
                        cells.append(f'<c r="{ref}" t="b"><v>{int(value)}</v></c>')
                    elif isinstance(value, (int, float)):
                        cells.append(f'<c r="{ref}"><v>{value}</v></c>')
                    elif isinstance(value, str) and value.startswith("="):
                        cells.append(f'<c r="{ref}"><f>{_xml_escape(value[1:])}</f></c>')
                    else:
                        cells.append(f'<c r="{ref}" t="inlineStr"><is><t xml:space="preserve">{_xml_escape(value)}</t></is></c>')
                body.append(f'<row r="{r}">{"".join(cells)}</row>')
            zf.writestr(f"xl/worksheets/sheet{i+1}.xml",
                        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                        f'<worksheet xmlns="{NS["m"]}"><sheetData>{"".join(body)}</sheetData></worksheet>')
    return path
