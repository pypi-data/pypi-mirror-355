from pathlib import Path

import pytest

from castepkit.config import get_exec_path


def test_get_exec_path_uses_dummy():
    exe = Path(get_exec_path("shg"))

    assert exe.is_file()
    if exe.suffix != ".py":
        pytest.skip("Real shg executable configured; skipping wrapper test")
    else:
        assert exe.name == "shg.py"
