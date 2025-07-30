import json
import os
import pytest

from newrelic_lambda.lambda_handler import (
    get_attributes_for_event_type,
    detect_event_type,
)

FIXTURE = os.path.join(
    os.curdir, "tests", "fixtures", "lambda", "event_source_info.json"
)


def _load_tests():
    with open(FIXTURE, "r") as fh:
        js = fh.read()
    return json.loads(js)


def _parametrize_test(fixture):
    # pytest.mark.parametrize expects each test to be a tuple
    return tuple([fixture["expected_attributes"], fixture["event"]])


_fixtures = [_parametrize_test(f) for f in _load_tests().values()]


@pytest.mark.parametrize("expected_attributes,event", _fixtures)
def test_labels(expected_attributes, event):
    event_type = detect_event_type(event)
    detected_attributes = get_attributes_for_event_type(event_type, event)

    assert detected_attributes == expected_attributes
