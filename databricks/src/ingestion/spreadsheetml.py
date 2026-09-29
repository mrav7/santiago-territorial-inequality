"""Technical SpreadsheetML 2003 decoding for the two SINIM Bronze sources.

Cell text is preserved verbatim (including special tokens); no business typing,
territorial filtering or empty-row removal occurs here.
"""
from dataclasses import dataclass
import re
import unicodedata
from xml.etree import ElementTree as ET

SS = "{urn:schemas-microsoft-com:office:spreadsheet}"


@dataclass
class ParsedSpreadsheet:
    sheet: str
    columns: list[str]
    rows: list[list[str | None]]
    header: list[str | None]
    descriptors: list[str | None]
    xml_row_count: int
    width: int
    observed_data_types: list[str]


def _name_text(value: str | None) -> str:
    text = unicodedata.normalize("NFKD", value or "")
    return " ".join(text.encode("ascii", "ignore").decode("ascii").split())


def _columns(header, descriptors):
    bases = []
    for position, (head, descriptor) in enumerate(zip(header, descriptors), 1):
        head, descriptor = _name_text(head), _name_text(descriptor)
        if head.upper() in {"CODIGO", "CODIGO COMUNA"}:
            name = "codigo_comuna"
        elif head.upper() in {"MUNICIPIO", "COMUNA", "NOMBRE COMUNA"}:
            name = "nombre_comuna"
        else:
            indicator = re.match(r"([A-Z]{2,}[0-9]*)\b", descriptor)
            if indicator:
                name = indicator[1].lower()
                if re.fullmatch(r"[0-9]{4}", head):
                    name += "_" + head
            else:
                name = re.sub(r"[^a-z0-9]+", "_", (head or descriptor).lower()).strip("_")
                name = name or f"columna_{position}"
        bases.append(name)
    # First occurrence keeps its name. Repeats get _2, _3, ...; skip names
    # reserved by any original column, so x, x, x_2 cannot collide.
    reserved, used, unique = set(bases), set(), []
    for base in bases:
        name, suffix = base, 2
        while name in used or (name != base and name in reserved):
            name = f"{base}_{suffix}"
            suffix += 1
        used.add(name)
        unique.append(name)
    return unique


def parse_spreadsheetml(content: bytes | str, sheet_name: str, skiprows: int = 2) -> ParsedSpreadsheet:
    """Decode a Workbook with explicit sheet and descriptor/header row positions.

    SINIM files have whitespace before the XML declaration; only that leading
    whitespace is removed. XML encoding is handled by ElementTree, never ignored.
    ss:Index is one-based; merged positions and absent Data elements become None.
    Rows are padded to max(observed width, ExpandedColumnCount), without truncation.
    """
    if skiprows < 1:
        raise ValueError("skiprows must leave a descriptor row before the header")
    root = ET.fromstring(content.lstrip())
    if root.tag != SS + "Workbook":
        raise ValueError("Expected a SpreadsheetML 2003 Workbook root")
    worksheets = [w for w in root.findall(SS + "Worksheet") if w.get(SS + "Name") == sheet_name]
    if len(worksheets) != 1:
        raise ValueError(f"Expected exactly one sheet {sheet_name!r}; found {len(worksheets)}")
    tables = worksheets[0].findall(SS + "Table")
    if len(tables) != 1:
        raise ValueError("Expected exactly one usable Table in the sheet")
    table = tables[0]
    matrix, data_types = [], set()
    for row in table.findall(SS + "Row"):
        values = []
        row_index = int(row.get(SS + "Index", str(len(matrix) + 1)))
        if row_index <= len(matrix):
            raise ValueError("Row ss:Index overlaps a previous row")
        matrix.extend([[] for _ in range(row_index - len(matrix) - 1)])
        for cell in row.findall(SS + "Cell"):
            index = int(cell.get(SS + "Index", str(len(values) + 1)))
            merged = int(cell.get(SS + "MergeAcross", "0"))
            if index <= len(values) or merged < 0:
                raise ValueError("Invalid/overlapping Cell ss:Index or ss:MergeAcross")
            if int(cell.get(SS + "MergeDown", "0")) != 0:
                raise ValueError("Vertical merges are outside the SINIM parser contract")
            values.extend([None] * (index - len(values) - 1))
            data = cell.find(SS + "Data")
            # Preserve an explicit empty Data as empty text, absent Data as None.
            values.append(None if data is None else "".join(data.itertext()))
            if data is not None and data.get(SS + "Type") is not None:
                data_types.add(data.get(SS + "Type"))
            values.extend([None] * merged)
        matrix.append(values)
    if len(matrix) <= skiprows:
        raise ValueError("Table does not contain the required descriptor/header rows")
    expanded_width = int(table.get(SS + "ExpandedColumnCount", "0"))
    if expanded_width < 0:
        raise ValueError("ExpandedColumnCount must be nonnegative")
    width = max(expanded_width, max(map(len, matrix)))
    if not width or not any(value is not None and value.strip() for value in matrix[skiprows]):
        raise ValueError("Table header is empty")
    matrix = [row + [None] * (width - len(row)) for row in matrix]
    header, descriptors = matrix[skiprows], matrix[skiprows - 1]
    return ParsedSpreadsheet(
        sheet_name, _columns(header, descriptors), matrix[skiprows + 1:],
        header, descriptors, len(matrix), width, sorted(data_types),
    )
