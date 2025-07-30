import json
import os
import pytest

from newrelic_lambda.lambda_handler import extract_event_source_arn

FIXTURE = os.path.join(
    os.curdir, "tests", "fixtures", "lambda", "event_source_info.json"
)


def _load_tests():
    with open(FIXTURE, "r") as fh:
        js = fh.read()
    return json.loads(js)


def _parametrize_test(fixture):
    # pytest.mark.parametrize expects each test to be a tuple
    return tuple([fixture["expected_arn"], fixture["event"]])


_fixtures = [_parametrize_test(f) for f in _load_tests().values()]


@pytest.mark.parametrize("expected_arn,event", _fixtures)
def test_labels(expected_arn, event):
    extracted_arn = extract_event_source_arn(event)

    assert extracted_arn == expected_arn
