import subprocess
import sys
from pathlib import Path

import pytest

from castepkit.config import get_exec_path


def test_dummy_shg_cli(tmp_path):
    prefix = tmp_path / "dummy"
    exe = Path(get_exec_path("shg"))
    if exe.suffix != ".py":
        pytest.skip("Real shg executable configured; skipping wrapper test")

    input_str = (
        "\n".join(
            [
                "0.0",  # scissors
                "211",  # direction
                "1",  # band_resolved
                "0",  # rank_number
                "0",  # unit
                "0",  # output_level
                "2",  # is_metal
                "0",  # energy_range
            ]
        )
        + "\n"
    )
    if exe.suffix != ".py":
        if not exe.is_file():
            pytest.skip("Real shg executable not available")
        cmd = [str(exe), str(prefix)]
    else:
        cmd = [sys.executable, str(exe), str(prefix)]
    subprocess.run(cmd, input=input_str.encode(), check=True)
    assert (tmp_path / "dummy.chi211").is_file()
    assert (tmp_path / "dummy.shg_weight_veocc").is_file()
    assert (tmp_path / "dummy.shg_weight_veunocc").is_file()


def test_dummy_weighted_den_cli(tmp_path):
    prefix = tmp_path / "dummy"
    exe = Path(get_exec_path("weighted_den"))
    if exe.suffix != ".py":
        pytest.skip("Real shg executable configured; skipping wrapper test")
        cmd = [str(exe), str(prefix)]
    else:
        cmd = [sys.executable, str(exe), str(prefix)]
    subprocess.run(cmd, input=b"1\n", check=True)
    assert (tmp_path / "dummy_wden.pot").is_file()
