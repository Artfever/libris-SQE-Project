"""Verify circulation through the HTTP API on a fresh disposable H2 server."""
import itertools
import json
import secrets
import unittest
import urllib.error
import urllib.request
from datetime import date, timedelta

from run_generated_smoke import Api, GeneratedApiFixture

LOANS = '/api/borrow-records'
ITEMS = {'bookId': 'books', 'magazineId': 'magazines', 'newspaperId': 'newspapers'}


class CirculationIntegration(GeneratedApiFixture):
    def setUp(self):
        self.ids = {field: self.manifest['items'][field[:-2]]['id'] for field in ITEMS}
        self.student = self.manifest['student']['id']
        self.borrow_date = next(
            case['value'] for case in self.cases
            if case['field'] == 'borrowDate' and case['partition'] == 'date'
        )
        self.baseline = {'bookId': self.ids['bookId'], 'studentId': self.student,
                         'borrowDate': self.borrow_date}

    def request(self, method, path, payload=None, client=None, csrf=True,
                content_type='application/json'):
        client = client or self.api
        headers = {'Accept': 'application/json'}
        if payload is not None:
            headers['Content-Type'] = content_type
        if csrf and client.csrf_token:
            headers['X-XSRF-TOKEN'] = client.csrf_token
        body = None if payload is None else (payload if isinstance(payload, bytes)
                                             else json.dumps(payload).encode('utf-8'))
        request = urllib.request.Request(client.base_url + path, body, headers, method=method)
        try:
            response = client.opener.open(request, timeout=15)
        except urllib.error.HTTPError as error:
            response = error
        with response:
            raw = response.read()
            return response.code, json.loads(raw) if raw else None, response.headers

    def snapshot(self):
        available = {
            field: self.api.call('GET', f'/api/{kind}/{self.ids[field]}')['available']
            for field, kind in ITEMS.items()
        }
        loans = self.api.call('GET', LOANS + '?size=100')
        self.assertEqual(len(loans['content']), loans['totalElements'])
        records = {row['id']: row for row in loans['content']}
        # Overdue days may change if the clock crosses midnight during a run.
        for row in records.values():
            row.pop('daysOverdue', None)
        return available, records

    def reject(self, status, code, path=LOANS, payload=None, **kwargs):
        before = self.snapshot()
        actual, result, _ = self.request(kwargs.pop('method', 'POST'), path, payload, **kwargs)
        self.assertEqual(actual, status)
        self.assertEqual((result['status'], result['code'], result['path']), (status, code, path))
        self.assertIsInstance(result['fieldErrors'], list)
        self.assertEqual(self.snapshot(), before)
        return result

    def borrow(self, field, payload, client=None):
        available, history = self.snapshot()
        self.assertTrue(available[field])
        status, loan, headers = self.request('POST', LOANS, payload, client=client)
        self.assertEqual(status, 201)
        loan_id = loan['id']
        self.assertEqual(headers['Location'], f'{LOANS}/{loan_id}')
        self.assertEqual((loan['itemId'], loan['itemType'], loan['studentId'], loan['status']),
                         (self.ids[field], field[:-2].upper(), self.student, 'BORROWED'))
        self.assertEqual(loan['borrowDate'], payload['borrowDate'])
        default_due = date.fromisoformat(payload['borrowDate']) + timedelta(days=14)
        self.assertEqual(loan['dueDate'], payload.get('dueDate') or default_due.isoformat())
        profile = self.api.call('GET', f'/api/students/{self.student}')
        for name in ('name', 'email', 'phone'):
            self.assertEqual(loan['borrower' + name.capitalize()], profile[name])
        self.assertIsNone(loan.get('returnDate'))
        stored = {key: value for key, value in loan.items() if key != 'daysOverdue'}
        self.assertEqual(self.snapshot(), (available | {field: False}, history | {loan_id: stored}))
        return loan_id

    def return_item(self, field, loan_id, client=None):
        available, history = self.snapshot()
        self.assertFalse(available[field])
        self.assertEqual(history[loan_id]['status'], 'BORROWED')
        today = date.today()
        status, body, _ = self.request('POST', f'{LOANS}/{loan_id}/return', client=client)
        self.assertEqual((status, body), (204, None))
        returned = self.snapshot()[1][loan_id]['returnDate']
        self.assertIn(date.fromisoformat(returned), {today, date.today()})
        record = history[loan_id] | {'returnDate': returned, 'status': 'RETURNED'}
        self.assertEqual(self.snapshot(), (available | {field: True}, history | {loan_id: record}))

    def test_generated_body_field_partitions(self):
        for case in self.cases:
            if case['operation'] != 'borrowItem' or case['field'] == 'x-non-null-count':
                continue
            field, partition, value = case['field'], case['partition'], case['value']
            with self.subTest(field=field, partition=partition):
                payload = dict(self.baseline)
                if partition.startswith('int64-'):
                    if field in ITEMS:
                        payload.pop('bookId')
                    payload[field] = value
                    if case['schema_expected'] == 'valid':
                        self.reject(404, 'NOT_FOUND', payload=payload)
                    else:
                        self.reject(400, 'INVALID_REQUEST', payload=payload)
                    continue
                selected = 'bookId'
                if field in ITEMS and partition == 'integer':
                    selected = field
                    payload.pop('bookId')
                    value = self.ids[field]
                elif field == 'studentId' and partition == 'integer':
                    value = self.student
                if value == {'$omit': True}:
                    payload.pop(field, None)
                else:
                    payload[field] = value
                if case['schema_expected'] == 'invalid':
                    if partition in ('omitted', 'null'):
                        result = self.reject(400, 'VALIDATION_ERROR', payload=payload)
                        self.assertIn(field, {error['field'] for error in result['fieldErrors']})
                    else:
                        self.reject(400, 'INVALID_REQUEST', payload=payload)
                elif not any(payload.get(item) is not None for item in ITEMS):
                    self.reject(400, 'INVALID_REQUEST', payload=payload)
                else:
                    loan = self.borrow(selected, payload)
                    self.return_item(selected, loan)

    def test_item_selection_decision_table(self):
        generated = {
            len(case['value']): case['rule_expected'] == 'valid'
            for case in self.cases if case['field'] == 'x-non-null-count'
        }
        self.assertEqual(generated, {0: False, 1: True, 2: False})
        for flags in itertools.product((False, True), repeat=len(ITEMS)):
            fields = [item for item, flag in zip(ITEMS, flags) if flag]
            with self.subTest(selected=fields):
                payload = {'studentId': self.student, 'borrowDate': self.borrow_date}
                payload.update({field: self.ids[field] for field in fields})
                if generated.get(len(fields), False):
                    self.return_item(fields[0], self.borrow(fields[0], payload))
                else:
                    self.reject(400, 'INVALID_REQUEST', payload=payload)

    def test_item_existence_availability_and_return_transitions(self):
        missing = -1
        for field in ITEMS:
            with self.subTest(item=field):
                payload = {'studentId': self.student, 'borrowDate': self.borrow_date}
                self.reject(404, 'NOT_FOUND', payload=payload | {field: missing})
                loan = self.borrow(field, payload | {field: self.ids[field]})
                self.reject(400, 'UNAVAILABLE', payload=payload | {field: self.ids[field]})
                self.return_item(field, loan)
                self.reject(400, 'ALREADY_RETURNED', path=f'{LOANS}/{loan}/return')
        self.reject(404, 'NOT_FOUND', payload=self.baseline | {'studentId': missing})
        self.reject(404, 'NOT_FOUND', path=f'{LOANS}/{missing}/return')

    def test_return_path_partitions_and_wrong_method(self):
        cases = [case for case in self.cases if case['operation'] == 'returnItem']
        for case in cases:
            partition = case['partition']
            with self.subTest(partition=partition):
                if partition == 'integer':
                    loan = self.borrow('bookId', self.baseline)
                    self.return_item('bookId', loan)
                elif partition == 'omitted':
                    self.reject(404, 'NOT_FOUND', path=f'{LOANS}/return')
                else:
                    value = 'null' if case['value'] is None else case['value']
                    path = f'{LOANS}/{value}/return'
                    if partition.startswith('int64-') and case['schema_expected'] == 'valid':
                        self.reject(404, 'NOT_FOUND', path=path)
                    else:
                        self.reject(400, 'INVALID_ARGUMENT', path=path)
        self.reject(405, 'METHOD_NOT_ALLOWED', path=f'{LOANS}/1/return', method='GET')

    def test_malformed_json_and_return_id_have_client_error_responses(self):
        self.reject(400, 'INVALID_REQUEST', payload=b'{"studentId":')
        self.reject(400, 'INVALID_ARGUMENT', path=f'{LOANS}/not-a-number/return')

    def test_borrow_request_body_and_media_type(self):
        self.reject(400, 'INVALID_REQUEST', payload=b'')
        self.reject(400, 'INVALID_REQUEST', payload=[])
        self.reject(415, 'UNSUPPORTED_MEDIA_TYPE', payload=self.baseline, content_type='text/plain')

    def login(self, username, password):
        client = Api(self.api.base_url)
        client.refresh_csrf()
        client.call('POST', '/api/auth/login', {'username': username, 'password': password})
        client.refresh_csrf()
        return client

    def test_roles_and_csrf(self):
        student = self.login(self.manifest['student']['username'], self.student_password)
        anonymous = Api(self.api.base_url)
        anonymous.refresh_csrf()
        self.reject(401, 'UNAUTHORIZED', payload=self.baseline, client=anonymous)
        self.reject(403, 'FORBIDDEN', payload=self.baseline, client=student)
        self.reject(403, 'FORBIDDEN', payload=self.baseline, csrf=False)
        password = secrets.token_urlsafe(24) + 'Aa1!'
        self.api.call('POST', '/api/librarians', {
            'username': 'sqe_librarian', 'password': password, 'name': 'Synthetic Librarian',
            'age': 30, 'phone': '03000000000',
        }, expected=201)
        librarian = self.login('sqe_librarian', password)
        loan = self.borrow('bookId', self.baseline, client=librarian)
        path = f'{LOANS}/{loan}/return'
        self.reject(401, 'UNAUTHORIZED', path=path, client=anonymous)
        self.reject(403, 'FORBIDDEN', path=path, client=student)
        self.reject(403, 'FORBIDDEN', path=path, csrf=False)
        own = student.call('GET', f'{LOANS}/my?size=100')['content']
        self.assertIn(loan, {record['id'] for record in own})
        self.assertEqual({record['studentId'] for record in own}, {self.student})
        self.return_item('bookId', loan, client=librarian)

    def test_explicit_due_dates_around_borrow_date(self):
        start = date.fromisoformat(self.borrow_date)
        for offset in (-1, 0, 1):
            with self.subTest(offset=offset):
                payload = self.baseline | {'dueDate': (start + timedelta(days=offset)).isoformat()}
                self.return_item('bookId', self.borrow('bookId', payload))


if __name__ == '__main__':
    unittest.main(verbosity=2)
