#!/usr/bin/env python3
"""Extended spectra with fine/hyperfine structure for cc̄, bb̄ and cb̄.

Levels: 1S–4S, 1P–3P, 1D–2D (our n counts radial excitations from 1;
Eichten & Quigg use the principal n, so our 1P = their 2P, our 1D = their 3D).

    python fine_structure_tables.py [--potential martin|log|cornell]

Writes results/fine_structure_<potential>.md and .json.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from quarkonium import POTENTIALS, spectrum
from quarkonium.spin_dependent import full_spectrum

LEVELS = [("1S", 1, 0), ("2S", 2, 0), ("3S", 3, 0), ("4S", 4, 0),
          ("1P", 1, 1), ("2P", 2, 1), ("3P", 3, 1),
          ("1D", 1, 2), ("2D", 2, 2)]
R_MAX = {"1S": 10, "2S": 14, "3S": 18, "4S": 22, "1P": 14, "2P": 18, "3P": 22, "1D": 18, "2D": 22}

# PDG 2022 masses (GeV) for the states the thesis compared against, plus a few more.
PDG = {
    "cc": {"11S0": 2.9839, "13S1": 3.0969, "21S0": 3.6375, "23S1": 3.6861,
           "13P0": 3.4147, "13P1": 3.5107, "11P1": 3.5254, "13P2": 3.5562,
           "13D1": 3.7737, "13D2": 3.8237, "13D3": 3.8427,
           "23P2": 3.9225},
    "bb": {"11S0": 9.3987, "13S1": 9.4603, "21S0": 9.9990, "23S1": 10.0234, "33S1": 10.3551, "43S1": 10.5794,
           "13P0": 9.8594, "13P1": 9.8928, "11P1": 9.8993, "13P2": 9.9122,
           "23P0": 10.2325, "23P1": 10.2555, "21P1": 10.2598, "23P2": 10.2687,
           "13D2": 10.1637, "33P1": 10.5134, "33P2": 10.5240},
    "cb": {"11S0": 6.2745, "21S0": 6.8712},
}

# Eichten & Quigg 1994, Table C ("calculated", Buchmüller–Tye potential), GeV.
# Keys use OUR radial-n labels; E&Q's principal-n labels in comments.
EQ94 = {
    "11S0": 6.264, "13S1": 6.337,                       # 1S
    "13P0": 6.700, "1P1'": 6.736, "1P1": 6.730, "13P2": 6.747,   # 2P
    "21S0": 6.856, "23S1": 6.899,                       # 2S
    "13D1": 7.012, "1D2'": 7.012, "1D2": 7.009, "13D3": 7.005,   # 3D
    "23P0": 7.108, "2P1'": 7.142, "2P1": 7.135, "23P2": 7.153,   # 3P
    "31S0": 7.244, "33S1": 7.280,                       # 3S
    "41S0": 7.562, "43S1": 7.594,                       # 4S
}


def label_key(f):
    # FineLevel labels are like "13P2", "1P1", "1P1'"; already the key format
    return f.label


def main(pname: str):
    P = POTENTIALS[pname]
    out_dir = Path(__file__).parent / "results"
    out_dir.mkdir(exist_ok=True)
    md = [f"# Fine structure, {P.label} potential (α_s = {P.alpha_s})\n",
          "Our n counts radial excitations (1P = E&Q 2P, 1D = E&Q 3D). "
          "J = L states of B_c are mixed; the primed state is the heavier one.\n"]
    data = {}
    for pair, (q1, q2), title in (("cc", ("c", "c"), "Charmonium"), ("bb", ("b", "b"), "Bottomonium"),
                                  ("cb", ("c", "b"), "B_c")):
        S = spectrum(P, q1, q2, levels=LEVELS, r_max=R_MAX)
        levels = full_spectrum(S)
        data[pair] = {f.label: {"J": f.J, "mass": f.mass, "shift": f.shift} for f in levels}
        md.append(f"## {title}\n")
        hdr = ["State", "J", "Spin-avg", "Shift (MeV)", "Mass", "PDG"] + (["E&Q 1994"] if pair == "cb" else [])
        md.append("| " + " | ".join(hdr) + " |"); md.append("|" + "---|" * len(hdr))
        for f in levels:
            m0 = f.mass - f.shift
            pdg = PDG[pair].get(f.label)
            row = [f.label, str(f.J), f"{m0:.4f}", f"{1000*f.shift:+.1f}", f"{f.mass:.4f}",
                   f"{pdg:.4f}" if pdg else "-"]
            if pair == "cb":
                eq = EQ94.get(f.label)
                row.append(f"{eq:.3f}" if eq else "-")
            md.append("| " + " | ".join(row) + " |")
        md.append("")
    text = "\n".join(md)
    (out_dir / f"fine_structure_{pname}.md").write_text(text)
    (out_dir / f"fine_structure_{pname}.json").write_text(json.dumps(data, indent=2))
    print(text)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--potential", default="martin", choices=["martin", "log", "cornell"])
    main(ap.parse_args().potential)
