"""Demonstrate two hypothetical specification changes without changing the real contract."""
import copy
import json
from pathlib import Path
from generate_cases import generate

root = Path(__file__).parent
original = json.loads((root / 'openapi.json').read_text(encoding='utf-8'))
changed = copy.deepcopy(original)
props = changed['components']['schemas']['BorrowRequest']['properties']
props['studentId']['minimum'] = 2
props['borrowerName']['maxLength'] = 3
fields = {'studentId', 'borrowerName'}
result = {
    'description': 'Hypothetical constraints for generator demonstration only; not application rules.',
    'changes': ['studentId minimum: absent -> 2', 'borrowerName maxLength: absent -> 3'],
    'before': [c for c in generate(original) if c['field'] in fields],
    'after': [c for c in generate(changed) if c['field'] in fields],
}
(root / 'constraint-change-demo.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
