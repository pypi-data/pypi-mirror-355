from __future__ import annotations

from pathlib import Path

from castep_outputs import parse_cell_param_file

__all__ = ["create_switch_file"]


# Covalent radii in angstrom extracted from the ``mendeleev`` package.
# Values cover all elements up to Z=118.
DEFAULT_RADII: dict[str, float] = {
    "H": 0.32,
    "He": 0.46,
    "Li": 1.33,
    "Be": 1.02,
    "B": 0.85,
    "C": 0.75,
    "N": 0.71,
    "O": 0.63,
    "F": 0.64,
    "Ne": 0.67,
    "Na": 1.55,
    "Mg": 1.39,
    "Al": 1.26,
    "Si": 1.16,
    "P": 1.11,
    "S": 1.03,
    "Cl": 0.99,
    "Ar": 0.96,
    "K": 1.96,
    "Ca": 1.71,
    "Sc": 1.48,
    "Ti": 1.36,
    "V": 1.34,
    "Cr": 1.22,
    "Mn": 1.19,
    "Fe": 1.16,
    "Co": 1.11,
    "Ni": 1.1,
    "Cu": 1.12,
    "Zn": 1.18,
    "Ga": 1.24,
    "Ge": 1.21,
    "As": 1.21,
    "Se": 1.16,
    "Br": 1.14,
    "Kr": 1.17,
    "Rb": 2.1,
    "Sr": 1.85,
    "Y": 1.63,
    "Zr": 1.54,
    "Nb": 1.47,
    "Mo": 1.38,
    "Tc": 1.28,
    "Ru": 1.25,
    "Rh": 1.25,
    "Pd": 1.2,
    "Ag": 1.28,
    "Cd": 1.36,
    "In": 1.42,
    "Sn": 1.4,
    "Sb": 1.4,
    "Te": 1.36,
    "I": 1.33,
    "Xe": 1.31,
    "Cs": 2.32,
    "Ba": 1.96,
    "La": 1.8,
    "Ce": 1.63,
    "Pr": 1.76,
    "Nd": 1.74,
    "Pm": 1.73,
    "Sm": 1.72,
    "Eu": 1.68,
    "Gd": 1.69,
    "Tb": 1.68,
    "Dy": 1.67,
    "Ho": 1.66,
    "Er": 1.65,
    "Tm": 1.64,
    "Yb": 1.7,
    "Lu": 1.62,
    "Hf": 1.52,
    "Ta": 1.46,
    "W": 1.37,
    "Re": 1.31,
    "Os": 1.29,
    "Ir": 1.22,
    "Pt": 1.23,
    "Au": 1.24,
    "Hg": 1.33,
    "Tl": 1.44,
    "Pb": 1.44,
    "Bi": 1.51,
    "Po": 1.45,
    "At": 1.47,
    "Rn": 1.42,
    "Fr": 2.23,
    "Ra": 2.01,
    "Ac": 1.86,
    "Th": 1.75,
    "Pa": 1.69,
    "U": 1.7,
    "Np": 1.71,
    "Pu": 1.72,
    "Am": 1.66,
    "Cm": 1.66,
    "Bk": 1.68,
    "Cf": 1.68,
    "Es": 1.65,
    "Fm": 1.67,
    "Md": 1.73,
    "No": 1.76,
    "Lr": 1.61,
    "Rf": 1.57,
    "Db": 1.49,
    "Sg": 1.43,
    "Bh": 1.41,
    "Hs": 1.34,
    "Mt": 1.29,
    "Ds": 1.28,
    "Rg": 1.21,
    "Cn": 1.22,
    "Nh": 1.36,
    "Fl": 1.43,
    "Mc": 1.62,
    "Lv": 1.75,
    "Ts": 1.65,
    "Og": 1.57,
}


def _get(mapping: dict, atom, element, default=None):
    """Return mapping value for ``atom`` or ``element`` with fallback to ``default``."""
    if atom in mapping:
        return mapping[atom]
    if element in mapping:
        return mapping[element]
    return default


def create_switch_file(
    fn_cell: str | Path,
    radius_dict: dict,
    cut_dict: dict,
    *,
    fn_switch: str | Path | None = None,
) -> Path:
    """Create a ``.switch`` file for ``atom_cutting``.

    Parameters
    ----------
    fn_cell : str or Path
        Path to the CASTEP ``.cell`` file.
    radius_dict : dict
        Mapping from atom label to cutting radius in angstrom. Entries
        override the built-in :data:`DEFAULT_RADII` table. Keys can be
        element symbols (e.g. ``"Ga"``) or tuples like ``("Ga", 1)`` matching
        the ``positions_frac`` keys returned by
        :func:`castep_outputs.parse_cell_param_file`.
    cut_dict : dict
        Mapping from atom label to the action ``"keep"`` or ``"cut"``.
        Unspecified atoms default to ``"keep"``.
    fn_switch : str or Path, optional
        Output file name. Defaults to ``<prefix>.switch`` where ``prefix`` is
        derived from ``fn_cell``.

    Returns
    -------
    Path
        Path to the created switch file.
    """
    fn_cell = Path(fn_cell)
    if fn_switch is None:
        fn_switch = fn_cell.with_suffix(".switch")
    fn_switch = Path(fn_switch)

    with fn_cell.open() as f:
        data = parse_cell_param_file(f)[0]

    atoms = list(data.get("positions_frac", {}).keys())

    lines = ["%BLOCK ATOM_DOMAIN"]
    for atom in atoms:
        element = atom[0] if isinstance(atom, tuple) else atom
        radius = _get(radius_dict, atom, element, DEFAULT_RADII.get(element))
        if radius is None:
            raise KeyError(f"Missing radius for {atom}")
        radius_str = str(radius)
        if isinstance(radius, (int, float)):
            radius_str = f"{radius}d0"
        elif not radius_str.lower().endswith("d0"):
            radius_str += "d0"
        lines.append(f"{element} {radius_str}")
    lines.append("%ENDBLOCK ATOM_DOMAIN")
    lines.append("")
    lines.append("%BLOCK CUT_ATOM")
    for atom in atoms:
        element = atom[0] if isinstance(atom, tuple) else atom
        action = _get(cut_dict, atom, element, "keep")
        if isinstance(action, bool) or isinstance(action, int):
            action = "keep" if bool(action) else "cut"
        lines.append(f"{element}      {action} 2")
    lines.append("%ENDBLOCK CUT_ATOM")

    fn_switch.write_text("\n".join(lines) + "\n")
    return fn_switch
