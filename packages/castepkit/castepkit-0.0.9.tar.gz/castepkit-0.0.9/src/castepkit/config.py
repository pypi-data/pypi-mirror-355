import os
import shutil
from pathlib import Path

import toml
from platformdirs import user_config_dir

CONFIG_PATH = Path(user_config_dir("castepkit")) / "config.toml"

__all__ = [
    "load_config",
    "get_exec_path",
    "use_mpi",
    "get_nproc",
    "get_env_vars",
]

_MODULES = ["compiler/intel/2021.3.0", "mpi/intelmpi/2021.3.0"]
_MODULES_CHECKED = False


def _check_required_modules() -> None:
    """Verify the Intel compiler and MPI modules are loaded."""
    global _MODULES_CHECKED
    if _MODULES_CHECKED:
        return
    _MODULES_CHECKED = True

    loaded = os.environ.get("LOADEDMODULES")
    if not loaded:
        print(
            "WARNING: LOADEDMODULES environment variable not set. "
            "Unable to verify loaded modules."
        )
        return

    loaded_set = set(filter(None, loaded.split(":")))
    missing = [m for m in _MODULES if m not in loaded_set]
    if missing:
        mods = " ".join(missing)
        print(
            f"WARNING: Required modules not loaded: {mods}.\n"
            "Please run 'module load " + mods + "' before using castepkit-cut or castepkit-dens."
        )


def load_config():
    if CONFIG_PATH.is_file():
        return toml.load(CONFIG_PATH)
    return {}


def get_exec_path(name: str) -> str:
    """Return path to external executable or a bundled dummy."""
    config = load_config()
    path = config.get("executables", {}).get(name, name)

    # Use configured path if it exists or is on PATH
    if Path(path).is_file() or shutil.which(path):
        final_path = path
    else:
        # Fall back to bundled dummy script within the package
        dummy = Path(__file__).parent / "dummy_bin" / f"{name}.py"
        if dummy.is_file():
            final_path = str(dummy)
        else:
            # Also check for a repository-level dummy program (for tests)
            repo_dummy = Path(__file__).resolve().parents[2] / "dummy_bin" / f"{name}.py"
            if repo_dummy.is_file():
                final_path = str(repo_dummy)
            else:
                final_path = path

    if name in {"weighted_den"} and "dummy_bin" not in str(final_path):
        _check_required_modules()

    return final_path


def use_mpi() -> bool:
    config = load_config()
    return config.get("mpirun", {}).get("enabled", False)


def get_nproc() -> int:
    config = load_config()
    return config.get("mpirun", {}).get("nproc", 1)


def get_env_vars() -> dict:
    config = load_config()
    env_section = config.get("environment", {})

    result = {}
    for key, value in env_section.items():
        if key == "LD_LIBRARY_PATH":
            # Append to current system value
            current = os.environ.get("LD_LIBRARY_PATH", "")
            value = value + (":" + current if current else "")
        result[key] = value
    return result
