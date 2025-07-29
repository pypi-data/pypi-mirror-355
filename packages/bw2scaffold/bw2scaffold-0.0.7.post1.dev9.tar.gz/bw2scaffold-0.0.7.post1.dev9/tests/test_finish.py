import pytest

from bw2scaffold.cli import finish


def test_finish(capfd):
    """Verify that an empty call to finish raises an AssertionError."""
    with pytest.raises(AssertionError):
        finish("")
