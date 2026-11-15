"""Carrega qualquer conjunto do Atlas como matrizes (canais, tempo) numa grade regular.

Generaliza data_yeast.py. Usado para montar o corpus doador do teste de
transferencia entre organismos.
"""
import numpy as np
import pandas as pd

# os 5 canais que levedura e CHO-K1 compartilham, na MESMA ordem sempre
SHARED = ["temperature_C", "pH", "DO_percent", "dCO2_percent", "permittivity_pF_cm"]


def load(release_dir, dataset_id, channels=SHARED, dt_h=None, min_len=128):
    runs = pd.read_csv(f"{release_dir}/runs.csv")
    obs = pd.read_csv(f"{release_dir}/observations.csv.gz")
    meta = runs[runs.dataset_id == dataset_id].set_index("run_id")
    obs = obs[obs.run_id.isin(meta.index) & obs.variable.isin(channels)]

    out = {}
    for rid, g in obs.groupby("run_id"):
        wide = g.pivot_table(index="time_h", columns="variable", values="value", aggfunc="mean")
        missing = [c for c in channels if c not in wide.columns]
        if missing:
            continue
        t = wide.dropna(how="all").index.to_numpy()
        if len(t) < min_len:
            continue
        step = dt_h if dt_h else float(np.median(np.diff(t)))
        grid = np.arange(t[0], t[-1] + step / 2, step)
        d = wide.reindex(wide.index.union(grid)).sort_index()
        d = d.interpolate(method="index", limit_area="inside").reindex(grid)
        X = d[channels].to_numpy(dtype=np.float64).T
        if X.shape[1] < min_len:
            continue
        out[rid] = dict(run_id=rid, t=grid, X=X, dense=list(channels), dt_h=step,
                        nan_frac=float(np.isnan(X).any(axis=0).mean()),
                        meta=meta.loc[rid].to_dict())
    return out


if __name__ == "__main__":
    import sys
    rel = sys.argv[1]
    for ds in ("uhlendorff2026", "uhlendorff2026_cho"):
        r = load(rel, ds)
        if not r:
            print(f"{ds}: nenhuma corrida com os 5 canais")
            continue
        T = pd.Series({k: v["X"].shape[1] for k, v in r.items()})
        dts = pd.Series({k: v["dt_h"] for k, v in r.items()})
        nan = pd.Series({k: v["nan_frac"] for k, v in r.items()})
        print(f"{ds}: {len(r)} corridas com os 5 canais compartilhados")
        print(f"  T: min={T.min()} med={int(T.median())} max={T.max()}")
        print(f"  dt_h: min={dts.min():.4f} med={dts.median():.4f} max={dts.max():.4f}")
        print(f"  NaN apos interpolacao: max={nan.max():.1%}, corridas com >2%: {(nan>0.02).sum()}")
        print(f"  pontos totais utilizaveis: {int(T.sum()*5):,}")
        one = r[sorted(r)[0]]
        print(f"  faixas do canal no exemplo {one['run_id'].split(':')[-1]}:")
        for i, c in enumerate(one["dense"]):
            x = one["X"][i][np.isfinite(one["X"][i])]
            print(f"    {c:22s} [{x.min():9.3f}, {x.max():9.3f}]")
        print()
