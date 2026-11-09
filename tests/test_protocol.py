import json
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from ring_protocol_lab import Config, generate, validate
from ring_protocol_lab.svg import render


class ProtocolTests(unittest.TestCase):
    def test_adjacent_count(self):
        self.assertEqual(len(generate(Config(16))), 16 * 13)

    def test_skip_count(self):
        self.assertEqual(len(generate(Config(16, 2))), 16 * 12)

    def test_no_drive_measure_overlap(self):
        for step in range(1, 8):
            for r in generate(Config(8, step)):
                self.assertTrue({r['drive_plus'], r['drive_minus']}.isdisjoint({r['measure_plus'], r['measure_minus']}))

    def test_wrapping_drive(self):
        rows = generate(Config(8, 3))
        self.assertEqual([r for r in rows if r['excitation'] == 7][0]['drive_minus'], 2)

    def test_wrapping_measurement(self):
        rows = generate(Config(8))
        self.assertTrue(any(r['measure_plus'] == 7 and r['measure_minus'] == 0 for r in rows))

    def test_one_based_labels(self):
        zero, one = generate(Config(8)), generate(Config(8, 1, 1))
        self.assertEqual(one, [{k: v + 1 for k, v in r.items()} for r in zero])

    def test_opposite_preserves_reverse_drives(self):
        rows = generate(Config(8, 4))
        self.assertEqual({r['excitation'] for r in rows}, set(range(8)))
        self.assertEqual(len(rows), 32)

    def test_minimum_ring(self):
        self.assertEqual(len(generate(Config(4))), 4)

    def test_invalid_configs(self):
        for values in [(3, 1, 0), (513, 1, 0), (8, 0, 0), (8, 8, 0), (8, 1, 2), (4, 2, 0), (True, 1, 0), (8.0, 1, 0)]:
            with self.subTest(values=values), self.assertRaises(ValueError):
                Config(*values)

    def test_validation_good(self):
        self.assertEqual(validate(generate(Config(8)), Config(8)), 40)

    def test_validation_corrupt_value(self):
        rows = generate(Config(8)); rows[0]['measure_minus'] = 99
        with self.assertRaisesRegex(ValueError, 'row 0'):
            validate(rows, Config(8))

    def test_validation_missing_and_extra(self):
        rows = generate(Config(8))
        for bad in (rows[:-1], rows + rows[:1], None):
            with self.assertRaises(ValueError):
                validate(bad, Config(8))

    def test_validation_schema_and_boolean(self):
        for value in ('3', True):
            rows = generate(Config(8)); rows[0]['measure_plus'] = value
            with self.assertRaises(ValueError):
                validate(rows, Config(8))
        rows = generate(Config(8)); rows[0]['surprise'] = 1
        with self.assertRaises(ValueError):
            validate(rows, Config(8))

    def test_svg_xml_and_labels(self):
        root = ET.fromstring(render(Config(8, 2, 1), 1))
        ns = '{http://www.w3.org/2000/svg}'
        self.assertEqual(len(root.findall(ns + 'line')), 5)
        self.assertEqual(root.find(ns + 'title').text, 'Ring protocol: excitation 1, 8 electrodes')

    def test_svg_invalid_excitation(self):
        for label in (-1, 8, True):
            with self.assertRaises(ValueError):
                render(Config(8), label)


class CLITests(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run([sys.executable, '-m', 'ring_protocol_lab', *args], capture_output=True, text=True)

    def test_json_stdout(self):
        result = self.run_cli('generate', '-n', '4', '--index-base', '0')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(json.loads(result.stdout)['rows']), 4)

    def test_csv_stdout(self):
        result = self.run_cli('generate', '-n', '4', '--index-base', '1', '--format', 'csv')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines()[1], '1,1,2,3,4')

    def test_index_base_required(self):
        result = self.run_cli('generate')
        self.assertEqual(result.returncode, 2)
        self.assertIn('--index-base', result.stderr)

    def test_file_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            file = str(Path(tmp) / 'protocol.json')
            result = self.run_cli('generate', '-n', '8', '--index-base', '0', '-o', file)
            self.assertEqual(result.returncode, 0, result.stderr)
            result = self.run_cli('validate', '-n', '8', '--index-base', '0', file)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('40 rows', result.stdout)
            result = self.run_cli('validate', '-n', '8', '--index-base', '1', file)
            self.assertEqual(result.returncode, 2)

    def test_config_requires_integers(self):
        with tempfile.TemporaryDirectory() as tmp:
            file = Path(tmp) / 'protocol.json'
            generated = self.run_cli('generate', '-n', '8', '--index-base', '0')
            for field, value in [('electrodes', 8.0), ('drive_step', True),
                                 ('index_base', False)]:
                document = json.loads(generated.stdout)
                document['config'][field] = value
                file.write_text(json.dumps(document))
                result = self.run_cli('validate', '-n', '8', '--index-base', '0', str(file))
                self.assertEqual(result.returncode, 2, result.stdout)

    def test_bad_file_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            file = Path(tmp) / 'broken.json'; file.write_text('[]')
            result = self.run_cli('validate', '--index-base', '0', str(file))
            self.assertEqual(result.returncode, 2)
            self.assertNotIn('Traceback', result.stderr)


if __name__ == '__main__':
    unittest.main()
