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

    def test_invalid_bounds_fail_instead_of_silently_generating(self):
        props = self.spec['components']['schemas']['BorrowRequest']['properties']
        props['studentId'].update(minimum=5, maximum=2)
        with self.assertRaises(ValueError):
            generate(self.spec)


if __name__ == '__main__':
    unittest.main()
