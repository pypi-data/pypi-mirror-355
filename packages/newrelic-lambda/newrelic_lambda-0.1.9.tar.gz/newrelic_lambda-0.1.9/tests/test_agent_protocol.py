import os

from newrelic_lambda.agent_protocol import ServerlessModeProtocol, ServerlessModeSession
import newrelic.agent


class Context(object):
    aws_request_id = "foobar"
    invoked_function_arn = "arn"
    function_name = "foobar"
    function_version = "$LATEST"
    memory_limit_in_mb = 128


def test_named_pipe_write(readable_fifo):
    assert os.path.exists("/tmp/newrelic-telemetry")

    if ServerlessModeProtocol is not None:
        # New Relic Agent >=5.16
        protocol = ServerlessModeProtocol(newrelic.agent.global_settings())
        protocol.finalize()
    else:
        # New Relic Agent <5.16
        session = ServerlessModeSession(
            "http://localhost", "foobar", newrelic.agent.global_settings()
        )
        session.finalize()

    assert os.read(readable_fifo, 1024).decode().startswith('[1,"NR_LAMBDA_MONITORING"')
