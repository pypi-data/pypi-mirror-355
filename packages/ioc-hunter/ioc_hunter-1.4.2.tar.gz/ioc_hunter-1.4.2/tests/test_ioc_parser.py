import os
from ioc_hunter import parse_iocs
import pytest
from deepdiff import DeepDiff
import json

with open(os.path.join(os.path.dirname(__file__), 'test_ioc_parser.json'), 'rb') as f:
    tests = json.load(f)

new_data = []

@pytest.mark.parametrize('input_vars,expected_output', [(x['inputs'], x['expected_output']) for x in tests])
def test_parser(input_vars, expected_output):
    found_iocs = parse_iocs(**input_vars)
    new_data.append({"inputs": input_vars, "expected_output": found_iocs})
    diff = DeepDiff(expected_output, found_iocs, ignore_order=True)
    # import pprint
    # pprint.pprint(diff)
    assert str(diff) == '{}'


def sort_values(dictionary):
    for key, value in dictionary.items():
        if isinstance(value, list):
            dictionary[key] = sorted(value)
        elif isinstance(value, dict):
            sort_values(value)



def test_save_output():
    if False:
        for item in new_data:
            sort_values(item)
        with open(os.path.join(os.path.dirname(__file__), 'test_ioc_parser.json'), 'w') as f:
            json.dump(new_data, f, sort_keys=True, indent=2)
