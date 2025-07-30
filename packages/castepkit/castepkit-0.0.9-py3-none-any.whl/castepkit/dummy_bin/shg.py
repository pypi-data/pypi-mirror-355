#!/usr/bin/env python3
"""Dummy implementation of the SHG executable."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def ask_input(prompt: str, default, cli_value):
    if cli_value is not None:
        return cli_value
    print(prompt, end="", flush=True)
    line = sys.stdin.readline().strip()
    if line:
        return type(default)(line)
    return default


def main() -> None:
    parser = argparse.ArgumentParser(description="Dummy SHG executable")
    parser.add_argument("prefix")
    parser.add_argument("--scissors", type=float, default=None)
    parser.add_argument("--direction", default=None)
    parser.add_argument("--band_resolved", type=int, choices=[0, 1], default=None)
    parser.add_argument("--rank_number", type=int, default=None)
    parser.add_argument("--unit", type=int, choices=[0, 1], default=None)
    parser.add_argument("--output_level", type=int, choices=[0, 1], default=None)
    parser.add_argument("--is_metal", type=int, choices=[1, 2], default=None)
    parser.add_argument("--energy_range", type=int, choices=[0, 1, 2], default=None)
    args = parser.parse_args()

    print(
        "Dummy SHG executable. You will be prompted for several parameters. "
        "Press Enter at any prompt to accept the displayed default value."
    )

    _ = ask_input("Scissors: ", 0.0, args.scissors)
    direction = ask_input("Direction: ", "123", args.direction)
    band_resolved = ask_input("Band resolved (0/1): ", 0, args.band_resolved)
    _ = ask_input("Rank number: ", 0, args.rank_number)
    _ = ask_input("Unit (0=pm/V,1=esu): ", 0, args.unit)
    _ = ask_input("Output level (0/1): ", 0, args.output_level)
    _ = ask_input("Is metal (1/2): ", 2, args.is_metal)
    _ = ask_input("Energy range (0/1/2): ", 0, args.energy_range)

    prefix = args.prefix

    Path(f"{prefix}.castep").write_text("dummy castep\n")
    if direction == "all":
        Path(f"{prefix}.chi_all").write_text("dummy chi\n")
    else:
        Path(f"{prefix}.chi{direction}").write_text("dummy chi\n")

    if band_resolved == 1:
        Path(f"{prefix}.shg_weight_veocc").write_text("dummy weight veocc\n")
        Path(f"{prefix}.shg_weight_veunocc").write_text("dummy weight veunocc\n")

if __name__ == "__main__":
    main()
