#!/usr/bin/env python3
"""Regenerate every numerical table in the thesis (Tables 2–15) from scratch
and write them to results/ as Markdown and JSON.

    python reproduce_thesis.py            # ~30 s
    python reproduce_thesis.py --plots    # also save the Fig. 9 wavefunctions

PDG reference values are the ones quoted in the thesis (Workman et al. 2022).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from quarkonium import (
    CORNELL, LOGARITHMIC, MARTIN, LEVELS,
    bc_mass, hyperfine_splitting, singlet_triplet, spectrum, splittings,
)

POTS = [("Power-law", MARTIN), ("Logarithmic", LOGARITHMIC), ("Cornell", CORNELL)]
PAIRS = {"bb": ("b", "b"), "cc": ("c", "c"), "cb": ("c", "b")}

# Experimental spin-averaged masses quoted in thesis Tables 5, 6 (GeV)
PDG_MASS = {
    "cc": {"1S": 3.069, "2S": 3.674, "1P": 3.525},
    "bb": {"1S": 9.445, "2S": 10.017, "3S": 10.355, "1P": 9.899, "2P": 10.260},
}
PDG_HYP = {"cc": {"1S": 0.113, "2S": 0.0486}, "bb": {"1S": 0.0623, "2S": 0.0243}}
PDG_BC_SINGLET = {"1S": 6.2745, "2S": 6.8712}


def md_table(header, rows, fmt="{:.4f}"):
    out = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    for r in rows:
        cells = [c if isinstance(c, str) else fmt.format(c) for c in r]
        out.append("| " + " | ".join(cells) + " |")
    return "\n".join(out)


def main(plots: bool = False):
    out_dir = Path(__file__).parent / "results"
    out_dir.mkdir(exist_ok=True)
    md = ["# Reproduced thesis tables\n"]
    data = {}

    # ---- solve everything ------------------------------------------------
    S = {}
    for pname, P in POTS:
        for pair, (q1, q2) in PAIRS.items():
            S[pname, pair] = spectrum(P, q1, q2)
            data.setdefault(pname, {})[pair] = {
                lab: {"E": st.E, "mass": st.mass, "R0sq": st.R_at_origin_sq()}
                for lab, st in S[pname, pair].items()
            }

    # ---- Tables 2–4: eigenvalues -------------------------------------------
    for tno, (pname, _) in zip((2, 3, 4), POTS):
        rows = [[lab] + [S[pname, p][lab].E for p in ("bb", "cc", "cb")] for lab, _, _ in LEVELS]
        md += [f"## Table {tno}: energy eigenvalues, {pname} potential (GeV)\n",
               md_table(["Level", "Bottomonium", "Charmonium", "Bc"], rows), ""]

    # ---- Tables 5, 6, 14: spin-averaged masses -----------------------------
    for tno, pair, title in ((5, "cc", "charmonium"), (6, "bb", "bottomonium"), (14, "cb", "Bc")):
        rows = []
        for lab, _, _ in LEVELS:
            pdg = PDG_MASS.get(pair, {}).get(lab)
            rows.append([lab] + [S[p, pair][lab].mass for p, _ in POTS] + [f"{pdg:.3f}" if pdg else "-"])
        md += [f"## Table {tno}: spin-averaged mass spectrum of {title} (GeV)\n",
               md_table(["Level", "Power-law", "Logarithmic", "Cornell", "PDG"], rows), ""]

    # ---- Tables 7, 8, 15(a): level splittings ------------------------------
    pdg_split = {
        "bb": {"3S-1S": 0.910, "2S-1S": 0.572, "1P-1S": 0.454, "2P-1S": 0.815, "2P-1P": 0.361},
        "cc": {"2S-1S": 0.605, "1P-1S": 0.456},
    }
    for tno, pair, title in ((7, "bb", "bottomonium"), (8, "cc", "charmonium"), ("15a", "cb", "Bc")):
        sp = {p: splittings({lab: st.mass for lab, st in S[p, pair].items()}) for p, _ in POTS}
        rows = []
        for key in ("3S-1S", "2S-1S", "1P-1S", "2P-1S", "2P-1P"):
            pdg = pdg_split.get(pair, {}).get(key)
            rows.append([key] + [sp[p][key] for p, _ in POTS] + [f"{pdg:.3f}" if pdg else "-"])
        md += [f"## Table {tno}: level splittings of {title} (GeV)\n",
               md_table(["", "Power-law", "Logarithmic", "Cornell", "PDG"], rows), ""]

    # ---- Tables 9–11: |R(0)|^2 ---------------------------------------------
    for tno, pair, title in ((9, "bb", "bottomonium"), (10, "cc", "charmonium"), (11, "cb", "Bc")):
        rows = [[lab] + [S[p, pair][lab].R_at_origin_sq() for p, _ in POTS] for lab in ("1S", "2S", "3S")]
        md += [f"## Table {tno}: |R(0)|² for {title} (GeV³)\n",
               md_table(["Level", "Power-law", "Logarithmic", "Cornell"], rows), ""]

    # ---- Table 12: hyperfine splittings ------------------------------------
    rows = []
    hyp = {}
    for lab in ("1S", "2S", "3S"):
        for pair, name in (("cc", "M(J/ψ)-M(ηc)"), ("bb", "M(Υ)-M(ηb)"), ("cb", "M(Bc*)-M(Bc)")):
            vals = [hyperfine_splitting(S[p, pair][lab]) for p, _ in POTS]
            hyp[pair, lab] = dict(zip([p for p, _ in POTS], vals))
            pdg = PDG_HYP.get(pair, {}).get(lab)
            rows.append([f"{lab} {name}"] + vals + [f"{pdg:.4f}" if pdg else "-"])
    md += ["## Table 12: hyperfine splittings (GeV)\n",
           md_table(["Mesons", "Power-law", "Logarithmic", "Cornell", "PDG"], rows), ""]

    # ---- Table 13: E_Bc - (E_bb + E_cc)/2 ----------------------------------
    rows = []
    for lab, _, _ in LEVELS:
        rows.append([lab] + [S[p, "cb"][lab].E - 0.5 * (S[p, "bb"][lab].E + S[p, "cc"][lab].E) for p, _ in POTS])
    md += ["## Table 13: E_Bc − ½(E_bb + E_cc) (GeV)\n",
           md_table(["Level", "Power-law", "Logarithmic", "Cornell"], rows, "{:.5f}"), ""]

    # ---- Table 15(b): Bc singlet/triplet masses, power-law -----------------
    rows = []
    bc = {}
    for lab in ("1S", "2S", "3S"):
        st = S["Power-law", "cb"][lab]
        # eq. (42) with model masses == eq. (40); kept for traceability
        m_avg = bc_mass(st.E, S["Power-law", "bb"][lab].E, S["Power-law", "cc"][lab].E,
                        S["Power-law", "bb"][lab].mass, S["Power-law", "cc"][lab].mass)
        singlet, triplet = singlet_triplet(m_avg, hyp["cb", lab]["Power-law"])
        bc[lab] = {"spin_avg": m_avg, "Bc": singlet, "Bc*": triplet}
        pdg = PDG_BC_SINGLET.get(lab)
        rows.append([lab, singlet, triplet, f"{pdg:.4f}" if pdg else "-"])
    md += ["## Table 15: Bc (¹S₀) and Bc* (³S₁) masses, power-law potential (GeV)\n",
           md_table(["State", "Bc", "Bc*", "PDG(¹S₀)"], rows), ""]
    data["Bc_powerlaw"] = bc

    # ---- write ---------------------------------------------------------------
    (out_dir / "tables.md").write_text("\n".join(md))
    (out_dir / "results.json").write_text(json.dumps(data, indent=2))
    print("\n".join(md))
    print(f"\nWritten to {out_dir}/tables.md and results.json")

    if plots:
        from quarkonium.plots import (
            potentials_plot, splitting_plot, trial_energy_plot, wavefunction_plot,
        )
        potentials_plot(out_dir / "fig3_potentials.png")
        trial_energy_plot(out_dir / "fig8_trial_energies.png")
        for pname, _ in POTS:
            slug = pname.lower().replace("-", "")
            wavefunction_plot(out_dir / f"fig9_{slug}.png",
                              {pair: S[pname, pair] for pair in PAIRS}, pname)
        for fno, pair, title in ((10, "bb", "bottomonium"), (11, "cc", "charmonium"), (12, "cb", "$B_c$")):
            splitting_plot(out_dir / f"fig{fno}_splittings_{pair}.png",
                           {p: S[p, pair] for p, _ in POTS}, title, pdg_split.get(pair))
        print("Figures 3, 8, 9, 10–12 saved to", out_dir)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--plots", action="store_true")
    main(plots=ap.parse_args().plots)
