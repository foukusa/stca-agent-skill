#!/usr/bin/env python3
"""Check the minimum STCA runtime and the APIs used by its agent workflows.

Ordinary use accepts compatible installed packages. The historical dependency
snapshot is checked only when a caller explicitly requests ``--locked``.
"""
from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import inspect
import json
from pathlib import Path
import re
import sys


MINIMUM_PYTHON = (3, 10)
MINIMUMS = {
    "numpy": "1.24", "pandas": "2.0", "scipy": "1.10",
    "rdkit": "2023.9", "scikit-learn": "1.5", "threadpoolctl": "3.1",
}
MODULES = {"scikit-learn": "sklearn"}
ASSETS = Path(__file__).resolve().parents[1] / "assets"


def version_tuple(value):
    match = re.match(r"^(\d+)(?:\.(\d+))?(?:\.(\d+))?", str(value))
    if not match:
        raise ValueError(f"Unrecognised package version: {value!r}")
    return tuple(int(part or 0) for part in match.groups())


def _check_maccs():
    from rdkit import Chem
    from rdkit.Chem import MACCSkeys
    panel = json.loads((ASSETS / "runtime_compatibility.json").read_text(encoding="utf-8"))
    if panel.get("schema") != "stca-runtime-maccs-panel-v1" or not panel.get("molecules"):
        raise ValueError("Missing or invalid MACCS compatibility panel.")
    failures = []
    for item in panel["molecules"]:
        mol = Chem.MolFromSmiles(item["smiles"])
        if mol is None:
            failures.append({"smiles": item["smiles"], "reason": "cannot_parse"})
            continue
        observed = MACCSkeys.GenMACCSKeys(mol).ToBitString()
        if len(observed) != 167 or observed != item["maccs167"]:
            failures.append({"smiles": item["smiles"], "reason": "MACCS167_panel_mismatch"})
    if failures:
        raise ValueError(json.dumps(failures, ensure_ascii=False))
    return {"molecules": len(panel["molecules"]), "bits": 167,
            "reference_rdkit": panel.get("reference_rdkit"),
            "scope": "Small functional panel; not universal cross-version equivalence."}


def _check_fit_apis():
    import numpy as np
    import pandas as pd
    from scipy.stats import pearsonr
    from sklearn.manifold import TSNE
    from threadpoolctl import threadpool_limits
    from rdkit import Chem
    from rdkit.Chem import AllChem
    if not bool(np.isfinite(np.asarray([1, 2, 3], dtype=float)).all()):
        raise ValueError("NumPy numerical operations failed.")
    if pd.to_numeric(pd.Series(["1", "2"]), errors="raise").tolist() != [1, 2]:
        raise ValueError("pandas numeric conversion failed.")
    correlation = float(pearsonr([1, 2, 3], [2, 4, 6])[0])
    if not np.isclose(correlation, 1):
        raise ValueError("SciPy correlation API failed.")
    if "max_iter" not in inspect.signature(TSNE).parameters:
        raise ValueError("Automatic ECFP4 splitting needs TSNE(max_iter=...), available in scikit-learn >=1.5.")
    TSNE(n_components=2, max_iter=1000, init="pca", learning_rate="auto")
    with threadpool_limits(limits=1):
        fp = AllChem.GetMorganFingerprintAsBitVect(Chem.MolFromSmiles("CCO"), 2, nBits=2048)
    if len(fp) != 2048:
        raise ValueError("ECFP4 Morgan radius-2 / 2048-bit API failed.")
    return {"numerical_apis": True, "tsne_max_iter_api": True,
            "thread_limit_api": True, "ecfp4_radius": 2, "ecfp4_bits": 2048}


def _locked_versions(mode):
    if mode == "chem":
        return {"rdkit": "2025.9.4"}
    versions = {}
    for line in (ASSETS / "requirements-py312.txt").read_text().splitlines():
        match = re.fullmatch(r"([A-Za-z0-9_.-]+)==([^\s;]+)", line.strip())
        if match:
            versions[match.group(1)] = match.group(2)
    if not versions:
        raise ValueError("The archival dependency snapshot is empty.")
    return versions


def probe_current(mode="fit", locked=False):
    if mode not in {"chem", "fit"}:
        raise ValueError("Runtime mode must be chem or fit.")
    required = {"rdkit": MINIMUMS["rdkit"]} if mode == "chem" else dict(MINIMUMS)
    versions, errors, checks = {}, [], {}
    if sys.version_info[:2] < MINIMUM_PYTHON:
        errors.append("requires_Python_3.10_or_newer")
    if locked and sys.version_info[:2] != (3, 12):
        errors.append("explicit_archival_lock_requires_Python_3.12")
    for name, minimum in required.items():
        try:
            importlib.import_module(MODULES.get(name, name))
            version = importlib.metadata.version(name)
            versions[name] = version
            if version_tuple(version) < version_tuple(minimum):
                errors.append(f"{name}>={minimum}_required; found={version}")
        except (ImportError, OSError, ValueError, RuntimeError) as exc:
            errors.append(f"{name}: {type(exc).__name__}: {exc}")
    if locked:
        try:
            for name, expected in _locked_versions(mode).items():
                observed = importlib.metadata.version(name)
                versions[name] = observed
                if version_tuple(observed) != version_tuple(expected):
                    errors.append(f"archival_lock:{name}=={expected}_required; found={observed}")
        except (OSError, ValueError, importlib.metadata.PackageNotFoundError) as exc:
            errors.append(f"archival_lock: {type(exc).__name__}: {exc}")
    if not errors:
        try:
            checks["maccs167_panel"] = _check_maccs()
            if mode == "fit":
                checks["fit_apis"] = _check_fit_apis()
        except (ImportError, OSError, ValueError, RuntimeError, AttributeError, TypeError) as exc:
            errors.append(f"functional_check: {type(exc).__name__}: {exc}")
    return {"ready": not errors, "python": sys.executable,
            "python_version": sys.version.split()[0], "mode": mode,
            "dependency_mode": "locked" if locked else "compatible",
            "minimum_python": "3.10", "minimum_packages": required,
            "packages": versions, "functional_checks": checks, "errors": errors}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("chem", "fit"), default="fit")
    parser.add_argument("--locked", action="store_true", help="Explicit archival snapshot check only")
    args = parser.parse_args(argv)
    result = probe_current(args.mode, args.locked)
    print(json.dumps(result, ensure_ascii=False, allow_nan=False))
    return 0 if result["ready"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
