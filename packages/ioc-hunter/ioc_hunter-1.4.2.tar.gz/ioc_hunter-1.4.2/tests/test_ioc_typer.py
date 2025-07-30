import os
from ioc_hunter import type_ioc
import pytest
import json


with open(os.path.join(os.path.dirname(__file__), 'test_ioc_typer.json'), 'rb') as f:
    data = json.load(f)

inputs = []
for type, values in data.items():
    for value in values:
        inputs.append((type, value))


@pytest.mark.parametrize('expected_type,value', inputs)
def test_typer(expected_type, value):
    found_type = type_ioc(value)
    assert expected_type == found_type
