def test_dropbox_is_marked_as_not_watchdog_submission(dropbox):
    assert not dropbox.from_watchdog


def test_dropbox_is_marked_as_watchdog_submission(watchdog_dropbox):
    assert watchdog_dropbox.from_watchdog
