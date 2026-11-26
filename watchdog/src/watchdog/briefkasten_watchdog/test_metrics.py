from prometheus_client import generate_latest
from pytest import mark

from briefkasten_watchdog import registry_for


LAST_SUCCESS = b'briefkasten_watchdog_last_success_unixtime'


def test_receive_pushes_last_success():
    assert LAST_SUCCESS in generate_latest(registry_for('receive'))


@mark.parametrize('command', ['submit', 'prune'])
def test_other_commands_leave_last_success_alone(command):
    metrics = generate_latest(registry_for(command))
    assert LAST_SUCCESS not in metrics
    assert b'briefkasten_watchdog_pending_test_submission_count' in metrics
