#!/usr/bin/env python3
"""Dummy implementation of weighted_den.x."""

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
    parser = argparse.ArgumentParser(description="Dummy weighted_den.x")
    parser.add_argument("prefix")
    parser.add_argument("--output_format", type=int, choices=[1, 2, 3], default=None)
    args = parser.parse_args()

    print(
        "Dummy weighted_den.x executable. You will be prompted for the output "
        "file format. Enter 1 for .pot, 2 for .check, or 3 for .grd. Press "
        "Enter to accept the default."
    )

    fmt = ask_input(
        "Output format (1=pot,2=check,3=grd): ",
        default=3,
        cli_value=args.output_format,
    )

    ext = {1: "pot", 2: "check", 3: "grd"}.get(fmt, "grd")

    Path(f"{args.prefix}_wden.{ext}").write_text("dummy weighted density\n")

if __name__ == "__main__":
    main()
