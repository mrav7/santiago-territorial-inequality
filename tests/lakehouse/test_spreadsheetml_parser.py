"""Pure-parser contracts; run: python -m unittest discover -s tests/lakehouse -v."""
from collections import Counter
from pathlib import Path
import sys
import unittest
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "databricks/src"))
from ingestion.spreadsheetml import parse_spreadsheetml


def workbook(rows, table_attributes="", sheet="Hoja1"):
    return f'''<Workbook xmlns="urn:schemas-microsoft-com:office:spreadsheet"
        xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet">
        <Worksheet ss:Name="{sheet}"><Table {table_attributes}>{rows}</Table></Worksheet>
        </Workbook>'''


def cell(text):
    return f'<Cell><Data ss:Type="String">{text}</Data></Cell>'


def row(*values):
    return '<Row>' + ''.join(cell(v) for v in values) + '</Row>'


class SpreadsheetMLTests(unittest.TestCase):
    def parse(self, body, attributes=""):
        return parse_spreadsheetml(workbook(row('intro') + row('', '', 'IADM41 (M$) IPP') +
                                  row('CODIGO', 'MUNICIPIO', '2024') + body, attributes), 'Hoja1')

    def test_explicit_sheet(self):
        parsed = self.parse(row('13101', 'SANTIAGO', '10'))
        self.assertEqual(parsed.sheet, 'Hoja1')
        self.assertEqual(parsed.rows, [['13101', 'SANTIAGO', '10']])

    def test_missing_sheet(self):
        with self.assertRaisesRegex(ValueError, 'sheet'):
            parse_spreadsheetml(workbook(row('intro')), 'Other')

    def test_missing_table(self):
        xml = workbook('').replace('<Table >', '').replace('</Table>', '')
        with self.assertRaisesRegex(ValueError, 'Table'):
            parse_spreadsheetml(xml, 'Hoja1')

    def test_wrong_namespace(self):
        with self.assertRaisesRegex(ValueError, 'Workbook'):
            parse_spreadsheetml('<Workbook/>', 'Hoja1')

    def test_invalid_xml(self):
        with self.assertRaises(ET.ParseError):
            parse_spreadsheetml('<Workbook>', 'Hoja1')

    def test_sparse_cell(self):
        parsed = self.parse('<Row>' + cell('13101') + '<Cell ss:Index="3"><Data>9</Data></Cell></Row>')
        self.assertEqual(parsed.rows, [['13101', None, '9']])

    def test_merge_across(self):
        parsed = self.parse('<Row><Cell ss:MergeAcross="1"><Data>note</Data></Cell>' + cell('9') + '</Row>')
        self.assertEqual(parsed.rows, [['note', None, '9']])

    def test_sparse_after_merge(self):
        parsed = self.parse('<Row><Cell ss:MergeAcross="1"><Data>note</Data></Cell>'
                            '<Cell ss:Index="4"><Data>end</Data></Cell></Row>')
        self.assertEqual(parsed.rows, [['note', None, None, 'end']])
        self.assertEqual(len(parsed.columns), 4)

    def test_missing_data_and_explicit_empty(self):
        parsed = self.parse('<Row><Cell/><Cell><Data/></Cell>' + cell('0') + '</Row>')
        self.assertEqual(parsed.rows, [[None, '', '0']])

    def test_different_widths(self):
        parsed = self.parse(row('1') + row('2', 'name', '5', 'extra'))
        self.assertEqual(parsed.rows, [['1', None, None, None], ['2', 'name', '5', 'extra']])
        self.assertEqual(parsed.columns[-1], 'columna_4')

    def test_declared_width(self):
        parsed = self.parse(row('1'), 'ss:ExpandedColumnCount="5"')
        self.assertEqual(parsed.width, 5)
        self.assertEqual(parsed.rows, [['1', None, None, None, None]])

    def test_overlap_rejected(self):
        with self.assertRaisesRegex(ValueError, 'overlapping'):
            self.parse('<Row>' + cell('1') + '<Cell ss:Index="1"><Data>x</Data></Cell></Row>')

    def test_sparse_row(self):
        parsed = self.parse('<Row ss:Index="5">' + cell('001') + '</Row>')
        self.assertEqual(parsed.rows, [[None]*3, ['001', None, None]])

    def test_invalid_merge(self):
        with self.assertRaisesRegex(ValueError, 'MergeAcross'):
            self.parse('<Row><Cell ss:MergeAcross="-1"><Data>x</Data></Cell></Row>')

    def test_vertical_merge_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Vertical merges'):
            self.parse('<Row><Cell ss:MergeDown="1"><Data>x</Data></Cell></Row>')

    def test_empty_header_rejected(self):
        with self.assertRaisesRegex(ValueError, 'header is empty'):
            parse_spreadsheetml(workbook(row('intro') + row('x') + '<Row/>'), 'Hoja1')

    def test_empty_table(self):
        with self.assertRaisesRegex(ValueError, 'descriptor/header'):
            parse_spreadsheetml(workbook(''), 'Hoja1')

    def test_descriptor_year(self):
        parsed = self.parse(row('1', 'name', '5'))
        self.assertEqual(parsed.columns, ['codigo_comuna', 'nombre_comuna', 'iadm41_2024'])

    def test_name_aliases(self):
        for code in ('CODIGO', 'CODIGO COMUNA', 'Código comuna'):
            for name in ('MUNICIPIO', 'COMUNA', 'NOMBRE COMUNA'):
                xml = workbook(row('intro') + row('', '') + row(code, name) + row('001', ' name '))
                parsed = parse_spreadsheetml(xml, 'Hoja1')
                self.assertEqual(parsed.columns, ['codigo_comuna', 'nombre_comuna'])
                self.assertEqual(parsed.rows, [['001', ' name ']])

    def test_indicator_a_names(self):
        xml = workbook(row('intro') + row('', '', 'MMPQC (MTS²) Parks', 'MMPZC (MTS²) Squares') +
                       row('CODIGO', 'MUNICIPIO', '2024', '2024'))
        self.assertEqual(parse_spreadsheetml(xml, 'Hoja1').columns,
                         ['codigo_comuna', 'nombre_comuna', 'mmpqc_2024', 'mmpzc_2024'])

    def test_duplicate_names_collision(self):
        xml = workbook(row('intro') + row('', '', '', '') + row('X', 'X', 'X_2', 'X'))
        parsed = parse_spreadsheetml(xml, 'Hoja1')
        self.assertEqual(parsed.columns, ['x', 'x_3', 'x_2', 'x_4'])
        self.assertEqual(parsed.columns, parse_spreadsheetml(xml, 'Hoja1').columns)

    def test_no_business_cleaning_or_row_removal(self):
        parsed = self.parse(row('001', ' name ', 'No Aplica') + row('2', 'N', 'No Recepcionado') + '<Row/>')
        self.assertEqual(parsed.rows, [['001', ' name ', 'No Aplica'], ['2', 'N', 'No Recepcionado'], [None]*3])

    def assert_real(self, suffix, columns, first_rows, tokens):
        path = next((ROOT / 'data/raw').glob(f'*{suffix}_*.xls'))
        parsed = parse_spreadsheetml(path.read_bytes(), 'Hoja1')
        self.assertEqual(parsed.columns, columns)
        self.assertEqual(parsed.xml_row_count, 55)
        self.assertEqual(len(parsed.rows), 52)
        self.assertEqual(parsed.rows[:3], first_rows)
        self.assertEqual(parsed.rows[-1][0:2], ['13605', 'PEÑAFLOR'])
        self.assertTrue(all(len(r) == len(columns) for r in parsed.rows))
        observed = Counter(v for r in parsed.rows for v in r if v in ('No Aplica', 'No Recepcionado'))
        self.assertEqual(dict(observed), tokens)
        self.assertEqual(len({r[0] for r in parsed.rows}), 52)

    def test_real_source_a(self):
        self.assert_real('20260402222841', ['codigo_comuna', 'nombre_comuna', 'mmpqc_2024', 'mmpzc_2024'],
                         [['13101', 'SANTIAGO', '1592984', '756436'],
                          ['13102', 'CERRILLOS', '74008', '661'],
                          ['13103', 'CERRO NAVIA', '264630', '480007']],
                         {'No Aplica': 3, 'No Recepcionado': 4})

    def test_real_source_b(self):
        self.assert_real('20260402223904', ['codigo_comuna', 'nombre_comuna', 'iadm41_2024'],
                         [['13101', 'SANTIAGO', '123162816'],
                          ['13102', 'CERRILLOS', '19206241'],
                          ['13103', 'CERRO NAVIA', '3525077']], {})


if __name__ == '__main__':
    unittest.main()
