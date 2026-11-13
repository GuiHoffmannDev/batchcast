"""Carrega uhlendorff2026 (52 corridas de levedura) do Bioprocess Atlas como matrizes (variates, T).

Reamostra na grade nominal de 0.25 h. Corridas com buraco grande sao reportadas, nao silenciadas.
"""
import numpy as np
import pandas as pd

DENSE = ["temperature_C", "pH", "DO_percent", "dCO2_percent", "permittivity_pF_cm"]
SPARSE = ["vcd_cells_mL", "viability_percent", "ethanol_pct_ww", "extract_plato"]
DT_H = 0.25


def load(release_dir, dataset_id="uhlendorff2026"):
    runs = pd.read_csv(f"{release_dir}/runs.csv")
    obs = pd.read_csv(f"{release_dir}/observations.csv.gz")
    meta = runs[runs.dataset_id == dataset_id].set_index("run_id")
    obs = obs[obs.run_id.isin(meta.index)]

    out = {}
    for rid, g in obs.groupby("run_id"):
        wide = g.pivot_table(index="time_h", columns="variable", values="value", aggfunc="mean")
        dense_t = wide[DENSE].dropna(how="all").index.to_numpy()
        if len(dense_t) < 64:
            continue
        # grade nominal regular de ponta a ponta
        t0, t1 = dense_t[0], dense_t[-1]
        grid = np.arange(t0, t1 + DT_H / 2, DT_H)
        d = wide.reindex(wide.index.union(grid)).sort_index()
        d = d.interpolate(method="index", limit_area="inside")
        d = d.reindex(grid)

        X = d[DENSE].to_numpy(dtype=np.float64).T          # (5, T)
        gap = np.isnan(X).any(axis=0)
        Y = d[[c for c in SPARSE if c in d.columns]].to_numpy(dtype=np.float64).T

        out[rid] = dict(
            run_id=rid, t=grid, X=X, Y=Y,
            dense=DENSE, sparse=[c for c in SPARSE if c in d.columns],
            nan_frac=float(gap.mean()),
            meta=meta.loc[rid].to_dict(),
        )
    return out


if __name__ == "__main__":
    import sys
    runs = load(sys.argv[1])
    print(f"{len(runs)} corridas carregadas")
    bad = {k: v["nan_frac"] for k, v in runs.items() if v["nan_frac"] > 0.02}
    print(f"corridas com >2% de NaN apos interpolacao: {len(bad)}")
    for k, v in sorted(bad.items(), key=lambda kv: -kv[1])[:8]:
        print(f"  {k} {v:.1%}")
    shp = pd.Series({k: v["X"].shape[1] for k, v in runs.items()})
    print(f"\nT por corrida: min={shp.min()} med={int(shp.median())} max={shp.max()}")
    one = runs[sorted(runs)[0]]
    print(f"exemplo {one['run_id']}: X={one['X'].shape} Y={one['Y'].shape}")
    print(f"  dense={one['dense']}")
    print(f"  sparse={one['sparse']}")
    print("\n=== condicoes experimentais (para desenho de divisao) ===")
    md = pd.DataFrame([v["meta"] for v in runs.values()], index=list(runs))
    for c in ["organism", "strain", "mode", "condition", "perturbation_type", "campaign", "working_volume_L"]:
        if c in md.columns:
            vc = md[c].astype(str).value_counts()
            print(f"  {c}: {dict(vc.head(8))}")
