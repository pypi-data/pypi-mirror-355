#!/usr/bin/env python3
"""Dummy implementation of calculate_ome_impi_XTIPC."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def ask_input(prompt: str, default: str, cli_value: str | None) -> str:
    if cli_value is not None:
        return cli_value
    print(prompt, end="", flush=True)
    line = sys.stdin.readline().strip()
    return line or default


def main() -> None:
    parser = argparse.ArgumentParser(description="Dummy ome executable")
    parser.add_argument("prefix")
    parser.add_argument("--orbital_suffix", default=None)
    args = parser.parse_args()

    print(
        "Dummy ome executable. You will be asked for the orbital file suffix. "
        "Press Enter to accept the default shown in brackets."
    )

    _ = ask_input(
        "Orbital file suffix: ",
        default="cutatom_check",
        cli_value=args.orbital_suffix,
    )

    Path(f"{args.prefix}.cst_ome").write_text("dummy ome\n")
    Path(f"{args.prefix}.castep").write_text("dummy castep\n")

if __name__ == "__main__":
    main()
