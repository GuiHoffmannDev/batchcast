"""Varredura honesta de configuracao do TimesFM 3.0 antes de fixar o braco A.

Testa znorm, padding, averaging simetrico. Reportado no RESULTS.md para que a
escolha de configuracao nao seja garimpo de resultado.
"""
import itertools, sys, time
import numpy as np, pandas as pd
sys.path.insert(0, "spike")
import timesfm
from data_yeast import load
from metrics import coverage, mase, wql

H, C = 64, 192
runs = load(sys.argv[1])
keys = sorted(runs)[:6]
fc = timesfm.TimesFM3Forecaster.from_pretrained("google/timesfm-3.0-pytorch", device="cpu")

grid = list(itertools.product([False, True], ["none", "edge"], [False, True]))
rows = []
for znorm, pad, sym in grid:
    for k in keys:
        X = runs[k]["X"]; T = X.shape[1]
        for cut in [C, (C + T - H) // 2, T - H]:
            ctx, y = X[:, cut - C:cut], X[:, cut:cut + H]
            if not (np.isfinite(ctx).all() and np.isfinite(y).all()):
                continue
            o = fc.predict(context=ctx, horizon=H, return_quantiles=True,
                           use_znorm=znorm, padding_mode=pad, use_symmetric_averaging=sym)
            p, q = np.asarray(o.forecast), np.asarray(o.quantiles)
            for v, ch in enumerate(runs[k]["dense"]):
                rows.append(dict(znorm=znorm, pad=pad, sym=sym, channel=ch,
                                 mase=mase(y, p, ctx)[v], wql=wql(y, q, ctx)[v],
                                 cov=coverage(y, q)[v]))
d = pd.DataFrame(rows)
print("=== mediana global por configuracao ===")
g = d.groupby(["znorm", "pad", "sym"])[["mase", "wql", "cov"]].median().round(3)
print(g.sort_values("mase").to_string())
print("\n=== melhor config, MASE mediano por canal ===")
best = g.sort_values("mase").index[0]
sel = d[(d.znorm == best[0]) & (d.pad == best[1]) & (d.sym == best[2])]
print(f"best={best}")
print(sel.groupby("channel")[["mase", "wql", "cov"]].median().round(3).to_string())
