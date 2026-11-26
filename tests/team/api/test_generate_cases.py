import copy
import json
import unittest
from pathlib import Path

from generate_cases import generate

SPEC = Path(__file__).with_name('openapi.json')


class GeneratorTests(unittest.TestCase):
    def setUp(self):
        self.spec = json.loads(SPEC.read_text(encoding='utf-8'))

    def select(self, spec, field, partition):
        return next(c for c in generate(spec) if c['field'] == field and c['partition'] == partition)

    def test_required_and_optional(self):
        cases = generate(self.spec)
        self.assertEqual(self.select(self.spec, 'studentId', 'omitted')['schema_expected'], 'invalid')
        self.assertEqual(self.select(self.spec, 'studentId', 'null')['schema_expected'], 'invalid')
        self.assertEqual(self.select(self.spec, 'dueDate', 'omitted')['schema_expected'], 'valid')

    def test_changed_constraints_produce_boundary_cases(self):
        changed = copy.deepcopy(self.spec)
        props = changed['components']['schemas']['BorrowRequest']['properties']
        props['studentId']['minimum'] = 2
        props['borrowerName']['maxLength'] = 3
        expected = [('studentId', 'minimum-below', 1, 'invalid'), ('studentId', 'minimum-at', 2, 'valid'),
                    ('studentId', 'minimum-above', 3, 'valid'), ('borrowerName', 'maxLength-below', 'xx', 'valid'),
                    ('borrowerName', 'maxLength-at', 'xxx', 'valid'), ('borrowerName', 'maxLength-above', 'xxxx', 'invalid')]
        for field, partition, value, validity in expected:
            with self.subTest(field=field, partition=partition):
                case = self.select(changed, field, partition)
                self.assertEqual((case['value'], case['schema_expected']), (value, validity))
        self.assertFalse(any(c['partition'].startswith(('minimum-', 'maxLength-')) for c in generate(self.spec)))

    def test_path_parameter_and_invalid_date_are_generated(self):
        cases = generate(self.spec)
        self.assertTrue(any(c['operation'] == 'returnItem' and c['location'] == 'path' and c['field'] == 'id' for c in cases))
        self.assertEqual(self.select(self.spec, 'borrowDate', 'invalid-date')['schema_expected'], 'invalid')

    def test_required_request_body_partitions_are_generated(self):
        cases = [c for c in generate(self.spec) if c['location'] == 'requestBody']
        self.assertEqual([(c['partition'], c['schema_expected']) for c in cases],
                         [('omitted', 'invalid'), ('null-body', 'invalid')])
        self.assertEqual(cases[0]['value'], {'$omit': True})
        self.assertEqual(cases[1]['value'], {'$raw-json': 'null'})

    def test_unsupported_schema_constraints_fail_loudly(self):
        props = self.spec['components']['schemas']['BorrowRequest']['properties']
        for keyword, value in [('pattern', '^[A-Z]+$'), ('enum', ['A', 'B'])]:
            with self.subTest(keyword=keyword):
                props['borrowerName'][keyword] = value
                with self.assertRaisesRegex(ValueError, keyword):
                    generate(self.spec)
                del props['borrowerName'][keyword]
        props['borrowerName']['format'] = 'email'
        with self.assertRaisesRegex(ValueError, 'Unsupported string format'):
            generate(self.spec)
        del props['borrowerName']['format']

    def test_unsupported_request_schema_features_fail_loudly(self):
        changed = copy.deepcopy(self.spec)
        operation = changed['paths']['/api/borrow-records']['post']
        operation['requestBody']['content']['text/plain'] = {'schema': {'type': 'string'}}
        with self.assertRaisesRegex(ValueError, 'Only application/json'):
            generate(changed)
        del operation['requestBody']['content']['text/plain']
        changed['components']['schemas']['BorrowRequest']['allOf'] = []
        with self.assertRaisesRegex(ValueError, 'Composite request schemas'):
            generate(changed)

    def test_invalid_bounds_fail_instead_of_silently_generating(self):
        props = self.spec['components']['schemas']['BorrowRequest']['properties']
        props['studentId'].update(minimum=5, maximum=2)
        with self.assertRaises(ValueError):
            generate(self.spec)
        props['studentId'].pop('minimum')
        props['studentId'].pop('maximum')
        props['studentId']['minimum'] = 1
        props['studentId']['exclusiveMinimum'] = True
        with self.assertRaisesRegex(ValueError, 'Exclusive integer bounds'):
            generate(self.spec)


if __name__ == '__main__':
    unittest.main()
