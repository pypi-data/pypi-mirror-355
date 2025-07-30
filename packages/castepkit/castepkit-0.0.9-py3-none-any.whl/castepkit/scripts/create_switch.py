#!/usr/bin/env python3
"""Command-line interface for generating CASTEP ``.switch`` files."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure the project src directory is on sys.path when executed directly
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from castepkit.switch import create_switch_file
import re


def _parse_key(key: str):
    match = re.match(r"^([A-Za-z]+)(?:\[(\d+)\]|:(\d+))?$", key)
    if match:
        element = match.group(1)
        idx = match.group(2) or match.group(3)
        if idx is not None:
            return (element, int(idx))
        return element
    return key


def _parse_assignments(values: list[str]) -> dict:
    result: dict = {}
    for item in values:
        if "=" not in item:
            raise argparse.ArgumentTypeError("Expected NAME=VALUE")
        key, val = item.split("=", 1)
        result[_parse_key(key)] = val
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a CASTEP .switch file")
    parser.add_argument("cell_file", help="Input .cell file")
    parser.add_argument(
        "--radius",
        action="append",
        default=[],
        metavar="ATOM=RADIUS",
        help="Set cutting radius for atom",
    )
    parser.add_argument(
        "--cut",
        action="append",
        default=[],
        metavar="ATOM=ACTION",
        help="Set cut action (keep/cut) for atom",
    )
    parser.add_argument("-o", "--output", help="Output .switch file")

    args = parser.parse_args()

    radius_dict = {k: float(v) for k, v in _parse_assignments(args.radius).items()}
    cut_dict = _parse_assignments(args.cut)

    create_switch_file(args.cell_file, radius_dict, cut_dict, fn_switch=args.output)


if __name__ == "__main__":
    main()
