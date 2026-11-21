"""Generate EP/BVA candidates from a JSON OpenAPI 3.0 contract.

Candidates are input data, not claims that a request was run or accepted.
"""
import argparse
import json
from pathlib import Path


def candidates(schema, required):
    typ = schema.get('type')
    nullable = schema.get('nullable', False)
    values = []
    def add(group, value, expected, note=''):
        values.append({'partition': group, 'value': value, 'schema_expected': expected, 'note': note})
    add('omitted', {'$omit': True}, 'invalid' if required else 'valid')
    add('null', None, 'valid' if nullable else 'invalid')
    if typ == 'integer':
        lo, hi = schema.get('minimum'), schema.get('maximum')
        if schema.get('exclusiveMinimum') or schema.get('exclusiveMaximum'):
            raise ValueError('Exclusive integer bounds are not yet supported')
        if lo is not None and hi is not None and lo > hi:
            raise ValueError('minimum exceeds maximum')
        sample = lo if lo is not None else min(1, hi) if hi is not None else 1
        add('integer', sample, 'valid', 'Database existence is a separate business rule')
        for name, bound in [('minimum', lo), ('maximum', hi)]:
            if bound is not None:
                for offset, suffix in [(-1, 'below'), (0, 'at'), (1, 'above')]:
                    v = bound + offset
                    valid = (lo is None or v >= lo) and (hi is None or v <= hi)
                    add(f'{name}-{suffix}', v, 'valid' if valid else 'invalid')
        add('wrong-type', 'not-an-integer', 'invalid')
    elif typ == 'string':
        if schema.get('format') == 'date':
            add('date', '2026-11-21', 'valid')
            add('invalid-date', '2026-02-30', 'invalid')
            add('invalid-format', 'not-a-date', 'invalid')
            if 'minLength' in schema or 'maxLength' in schema:
                raise ValueError('Length bounds on date fields are not supported')
        else:
            lo, hi = schema.get('minLength', 0), schema.get('maxLength')
            if hi is not None and lo > hi:
                raise ValueError('minLength exceeds maxLength')
            add('string', 'x' * lo, 'valid')
            for name, bound in [('minLength', schema.get('minLength')), ('maxLength', hi)]:
                if bound is not None:
                    for offset, suffix in [(-1, 'below'), (0, 'at'), (1, 'above')]:
                        length = bound + offset
                        if length < 0:
                            continue
                        valid = length >= lo and (hi is None or length <= hi)
                        add(f'{name}-{suffix}', 'x' * length, 'valid' if valid else 'invalid')
            add('wrong-type', {'not': 'a string'}, 'invalid')
    else:
        raise ValueError(f'Unsupported schema type: {typ!r}')
    return values


def generate(spec):
    components = spec['components']['schemas']
    output = []
    for path, methods in spec['paths'].items():
        for method, operation in methods.items():
            if method.lower() not in ('get', 'post', 'put', 'patch', 'delete'):
                continue
            for parameter in operation.get('parameters', []):
                for case in candidates(parameter['schema'], parameter.get('required', False)):
                    output.append({'operation': operation['operationId'], 'method': method.upper(), 'path': path,
                                   'location': parameter['in'], 'field': parameter['name'], **case})
            request = operation.get('requestBody', {}).get('content', {}).get('application/json', {}).get('schema', {})
            if '$ref' in request:
                ref = request['$ref']
                if not ref.startswith('#/components/schemas/'):
                    raise ValueError('Only local component schema references are supported')
                request = components[ref.rsplit('/', 1)[-1]]
            required = set(request.get('required', []))
            for field, schema in request.get('properties', {}).items():
                for case in candidates(schema, field in required):
                    output.append({'operation': operation['operationId'], 'method': method.upper(), 'path': path,
                                   'location': 'body', 'field': field, **case})
            rule = request.get('x-non-null-count')
            if rule:
                minimum, maximum = rule['minimum'], rule['maximum']
                fields = rule['fields']
                if len(set(fields)) != len(fields) or not set(fields) <= request['properties'].keys():
                    raise ValueError('Count rule needs unique request fields')
                if not 0 <= minimum <= maximum <= len(fields):
                    raise ValueError('Count rule bounds must fit the available fields')
                boundaries = {bound + offset for bound in (minimum, maximum) for offset in (-1, 0, 1)}
                for count in sorted(boundaries & set(range(len(fields) + 1))):
                    output.append({
                        'operation': operation['operationId'],
                        'method': method.upper(),
                        'path': path,
                        'location': 'body',
                        'field': 'x-non-null-count',
                        'partition': f'count-{count}',
                        'value': fields[:count],
                        'rule_expected': 'valid' if minimum <= count <= maximum else 'invalid',
                    })
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('spec', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    data = json.dumps(generate(json.loads(args.spec.read_text(encoding='utf-8'))), indent=2) + '\n'
    if args.output:
        args.output.write_text(data, encoding='utf-8')
    else:
        print(data, end='')


if __name__ == '__main__':
    main()
