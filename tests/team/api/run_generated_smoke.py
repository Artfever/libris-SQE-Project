"""Run a small generated-data smoke suite against a fresh disposable H2 instance."""
import json
import secrets
import sys
import unittest
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'fixtures'))
from circulation import Api, seed  # noqa: E402
from verify_h2 import JAR, start_app, stop_app  # noqa: E402
from generate_cases import generate  # noqa: E402


class GeneratedApiSmoke(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not JAR.is_file():
            raise RuntimeError('Build the backend JAR first; see tests/team/api/README.md')
        cls.password = secrets.token_urlsafe(24) + 'Aa1!'
        cls.process = start_app(18082, cls.password)
        try:
            cls.api = Api('http://127.0.0.1:18082')
            cls.api.login(cls.password)
            cls.manifest = seed(cls.api, secrets.token_urlsafe(24) + 'Aa1!')
            cls.cases = generate(json.loads((HERE / 'openapi.json').read_text(encoding='utf-8')))
        except BaseException:
            stop_app(cls.process)
            raise

    @classmethod
    def tearDownClass(cls):
        stop_app(cls.process)

    def test_generated_required_fields_then_borrow_and_return(self):
        api, manifest = self.api, self.manifest
        book_id = manifest['items']['book']['id']
        date_case = next(c for c in self.cases if c['field'] == 'borrowDate' and c['partition'] == 'date')
        baseline = {'bookId': book_id, 'studentId': manifest['student']['id'], 'borrowDate': date_case['value']}
        for field in ('studentId', 'borrowDate'):
            for partition in ('omitted', 'null'):
                with self.subTest(field=field, partition=partition):
                    case = next(c for c in self.cases if c['operation'] == 'borrowItem' and c['field'] == field and c['partition'] == partition)
                    payload = dict(baseline)
                    if case['value'] == {'$omit': True}:
                        del payload[field]
                    else:
                        payload[field] = case['value']
                    self.assert_borrow_rejected(payload, 'VALIDATION_ERROR', book_id)
        item_ids = {f'{kind}Id': item['id'] for kind, item in manifest['items'].items()}
        boundary_cases = [c for c in self.cases if c['field'] == 'x-non-null-count']
        self.assertEqual({c['partition'] for c in boundary_cases}, {'count-0', 'count-1', 'count-2'})
        for case in boundary_cases:
            if case['rule_expected'] == 'invalid':
                with self.subTest(partition=case['partition']):
                    self.assert_borrow_rejected(
                        self.with_items(baseline, item_ids, case['value']), 'INVALID_REQUEST', book_id
                    )
        valid_case = next(c for c in boundary_cases if c['rule_expected'] == 'valid')
        created = api.call(
            'POST', '/api/borrow-records',
            self.with_items(baseline, item_ids, valid_case['value']), expected=201,
        )
        self.assertEqual(created['status'], 'BORROWED')
        self.assertFalse(api.call('GET', f'/api/books/{book_id}')['available'])
        self.assertEqual(api.count('/api/borrow-records'), 1)
        api.call('POST', f"/api/borrow-records/{created['id']}/return", expected=204)
        self.assertTrue(api.call('GET', f'/api/books/{book_id}')['available'])
        history = api.call('GET', '/api/borrow-records')
        self.assertEqual(history['totalElements'], 1)
        self.assertEqual(history['content'][0]['status'], 'RETURNED')

    @staticmethod
    def with_items(baseline, item_ids, fields):
        payload = {name: value for name, value in baseline.items() if name not in item_ids}
        return payload | {field: item_ids[field] for field in fields}

    def assert_borrow_rejected(self, payload, code, book_id):
        request = urllib.request.Request(
            self.api.base_url + '/api/borrow-records',
            data=json.dumps(payload).encode('utf-8'),
            method='POST',
            headers={
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'X-XSRF-TOKEN': self.api.csrf_token,
            },
        )
        with self.assertRaises(urllib.error.HTTPError) as captured:
            self.api.opener.open(request, timeout=15)
        with captured.exception as error:
            self.assertEqual(error.code, 400)
            self.assertEqual(json.load(error)['code'], code)
        self.assertTrue(self.api.call('GET', f'/api/books/{book_id}')['available'])
        self.assertEqual(self.api.count('/api/borrow-records'), 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
