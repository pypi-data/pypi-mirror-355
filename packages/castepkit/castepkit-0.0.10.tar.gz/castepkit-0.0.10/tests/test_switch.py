# ruff: noqa: E402
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.modules.pop("castepkit", None)

import pytest

from common import prepare_test_data
from castepkit.switch import create_switch_file

TEST_DATA = Path(__file__).parent / "data" / "GaAs"


@pytest.fixture
def tmp_gaas(tmp_path):
    return prepare_test_data(TEST_DATA, tmp_path, prefix="GaAs_Optics")


def test_create_switch_file(tmp_gaas):
    cell = tmp_gaas / "GaAs_Optics.cell"
    radius = {"Ga": 0.79, "As": 0.79}
    cut = {"Ga": "keep", "As": "cut"}
    out = create_switch_file(cell, radius, cut)
    assert out.exists()
    expected = [
        "%BLOCK ATOM_DOMAIN",
        "Ga 0.79d0",
        "As 0.79d0",
        "%ENDBLOCK ATOM_DOMAIN",
        "",
        "%BLOCK CUT_ATOM",
        "Ga      keep 2",
        "As      cut 2",
        "%ENDBLOCK CUT_ATOM",
    ]
    assert out.read_text().strip().splitlines() == expected


def test_create_switch_defaults(tmp_gaas):
    cell = tmp_gaas / "GaAs_Optics.cell"
    radius = {"Ga": 0.79}
    cut = {"As": "cut"}
    out = create_switch_file(cell, radius, cut)
    lines = out.read_text().strip().splitlines()
    from castepkit.switch import DEFAULT_RADII
    assert "Ga 0.79d0" in lines
    assert f"As {DEFAULT_RADII['As']}d0" in lines
    assert "Ga      keep 2" in lines
    assert "As      cut 2" in lines


def test_switch_cli(tmp_gaas):
    cell = tmp_gaas / "GaAs_Optics.cell"
    script = Path(__file__).resolve().parents[1] / "src" / "castepkit" / "scripts" / "create_switch.py"
    cmd = [
        sys.executable,
        str(script),
        str(cell),
        "--radius",
        "Ga=0.79",
        "--radius",
        "As=0.79",
        "--cut",
        "Ga=keep",
        "--cut",
        "As=cut",
    ]
    subprocess.run(cmd, check=True)
    assert (tmp_gaas / "GaAs_Optics.switch").is_file()


def test_switch_cli_index(tmp_gaas):
    cell = tmp_gaas / "GaAs_Optics.cell"
    script = Path(__file__).resolve().parents[1] / "src" / "castepkit" / "scripts" / "create_switch.py"
    cmd = [
        sys.executable,
        str(script),
        str(cell),
        "--radius",
        "Ga[1]=0.79",
        "--cut",
        "As[1]=cut",
    ]
    subprocess.run(cmd, check=True)
    assert (tmp_gaas / "GaAs_Optics.switch").is_file()
