#!/usr/bin/env python3
"""Refit V = A + B r^alpha to PDG 2024 at fixed exponents and save
results/fit_power_<alpha>.json.      python scan_exponent.py 0.35
"""
import json, sys
from pathlib import Path
from quarkonium.fit import fit, register_power_family

alpha = float(sys.argv[1])
key = register_power_family(alpha)
r = fit(key, verbose=False)
print(r.summary())
out = Path(__file__).parent / "results"
(out / f"fit_{key}.json").write_text(json.dumps({
    "family": key, "alpha": alpha, "names": r.names, "x": r.x.tolist(), "errors": r.errors.tolist(),
    "cov": None if r.cov is None else r.cov.tolist(), "chi2": r.chi2, "dof": r.dof, "seconds": r.seconds,
    "residuals": [{"pair": p, "label": l, "exp": e, "model": m, "pull": q} for p, l, e, m, q in r.residuals],
}, indent=2))
