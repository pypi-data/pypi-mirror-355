#!/usr/bin/env python3
"""Dummy implementation of atom_cutting_impi_XTIPC."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def ask_input(prompt: str, default: int, cli_value: int | None) -> int:
    if cli_value is not None:
        return cli_value
    print(prompt, end="", flush=True)
    line = sys.stdin.readline().strip()
    return int(line) if line else default


def main() -> None:
    parser = argparse.ArgumentParser(description="Dummy atom_cutting")
    parser.add_argument("prefix")
    parser.add_argument("--input_type", type=int, choices=[1, 2], default=None)
    args = parser.parse_args()

    print(
        "Dummy atom_cutting executable. You will be asked for the wavefunction "
        "input type. Press Enter to accept the default shown in brackets."
    )

    _ = ask_input(
        "Input type (1=charge, 2=orbitals): ",
        default=2,
        cli_value=args.input_type,
    )

    prefix = args.prefix

    Path(f"{prefix}.cutatom_check").write_text("dummy cutatom check\n")
    Path(f"{prefix}_den.grd").write_text("dummy density grid\n")
    Path(f"{prefix}.castep").write_text("dummy castep\n")
    Path(f"{prefix}.castep_bin").write_text("dummy castep bin\n")

if __name__ == "__main__":
    main()
